# -*- coding: utf-8 -*-
"""
Impact Analysis of Manufacturing Equipment Upgrade
(Staggered DiD Analysis with Utilization Weighting - Focus on Rate & OLS)

Author: Go Sato
Description:
    This script is dedicated to the Static DiD analysis, quantifying the overall 
    effect of the upgrade on error rates and continuous outcomes (MTBF/WBF).
    It excludes Survival Analysis models (KMF, Cox, AFT).
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
# Removed: from lifelines import CoxPHFitter, WeibullAFTFitter, KaplanMeierFitter
import statsmodels.formula.api as smf
import statsmodels.api as sm
from datetime import datetime, timedelta
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# ==========================================
# 1. Dummy Data Generator (Identical structure required)
# ==========================================
class DummyDataGenerator:
    def __init__(self, n_tools=20, start_date='2024-01-01', periods=365):
        self.n_tools = n_tools
        self.start_date = pd.to_datetime(start_date)
        self.periods = periods
        self.tools = [f'TOOL_{i:02d}' for i in range(1, n_tools + 1)]
        
    def generate_datasets(self):
        """Generates Installation, Production, and Error datasets."""
        print("Generating Dummy Data...")
        
        # --- 1. Installation Dates (Staggered) ---
        install_map = {}
        treated_tools = self.tools[:self.n_tools // 2]
        for tool in treated_tools:
            offset = np.random.randint(self.periods // 4, self.periods * 3 // 4)
            install_date = self.start_date + timedelta(days=offset)
            install_map[tool] = install_date
        df_install = pd.DataFrame(list(install_map.items()), columns=['Tool', 'Install_Date'])
        
        # --- 2. Production Data (Daily - Varying Utilization) ---
        prod_data = []
        date_range = pd.date_range(self.start_date, periods=self.periods)
        tool_capacity = {t: np.random.uniform(0.2, 1.0) for t in self.tools} 
        
        for t in self.tools:
            base_prod = 1000 * tool_capacity[t] 
            for d in date_range:
                daily_prod = int(np.random.normal(base_prod, 50))
                daily_prod = max(0, daily_prod)
                prod_data.append({'Tool': t, 'Date': d, 'Production_Count': daily_prod})
        df_production = pd.DataFrame(prod_data)
        
        # --- 3. Error Data ---
        error_data = []
        base_error_prob_per_unit = 0.0005
        effect_size = 0.5 
        
        for t in self.tools:
            t_prod = df_production[df_production['Tool'] == t]
            install_dt = install_map.get(t, pd.NaT)
            
            for _, row in t_prod.iterrows():
                units = row['Production_Count']
                d = row['Date']
                prob = base_error_prob_per_unit
                is_treated = False
                if pd.notna(install_dt) and d >= install_dt:
                    prob *= effect_size
                    is_treated = True
                n_errors = np.random.binomial(units, prob)
                
                if n_errors > 0:
                    for _ in range(n_errors):
                        err_time = d + timedelta(hours=np.random.randint(0, 24))
                        error_data.append({
                            'Tool': t,
                            'Error_Date': err_time,
                            'Is_Intro': is_treated
                        })
                        
        df_errors = pd.DataFrame(error_data)
        
        return df_install, df_production, df_errors

# ==========================================
# 2. Static DiD Analysis Logic
# ==========================================
class DiDAnalyzer:
    def __init__(self, df_install, df_prod, df_errors):
        self.df_install = df_install
        self.df_prod = df_prod
        self.df_errors = df_errors
        self.processed_data = None
        
    def calculate_utilization_metrics(self):
        """
        [Step 1] Metric Calculation: Calculates WBF which is used to derive 
        MTBF and identify error intervals.
        """
        print("\n[Step 1] Calculating Utilization & WBF (Work Between Failures)...")
        
        global_avg_daily_prod = self.df_prod['Production_Count'].mean()
        print(f"  Global Avg Daily Production: {global_avg_daily_prod:.1f} units")
        
        df_err = self.df_errors.sort_values(['Tool', 'Error_Date']).copy()
        df_err['Prev_Error_Date'] = df_err.groupby('Tool')['Error_Date'].shift(1)
        
        # Calculate raw MTBF (Time)
        df_err['Time_Interval_Hours'] = (df_err['Error_Date'] - df_err['Prev_Error_Date']).dt.total_seconds() / 3600.0
        
        # Calculate "Production between failures" (WBF)
        wbf_list = []
        for idx, row in df_err.iterrows():
            if pd.isna(row['Prev_Error_Date']):
                wbf_list.append(np.nan)
                continue
                
            mask = (self.df_prod['Tool'] == row['Tool']) & \
                   (self.df_prod['Date'] >= row['Prev_Error_Date'].floor('D')) & \
                   (self.df_prod['Date'] <= row['Error_Date'].floor('D'))
            prod_sum = self.df_prod.loc[mask, 'Production_Count'].sum()
            wbf_list.append(prod_sum)
            
        df_err['WBF_Units'] = wbf_list
        
        # Aggregate to monthly level for DiD panel construction
        df_err['Month'] = df_err['Error_Date'].dt.to_period('M').dt.to_timestamp()
        
        self.processed_data = df_err
        print(f"  Processed {len(self.processed_data)} error intervals.")

    def run_staggered_did(self):
        """
        [Step 2] Staggered Difference-in-Differences (DiD)
        Runs GLM (Negative Binomial) for Count Rate with Production Offset.
        """
        print("\n[Step 2] Running Staggered DiD Analysis (Count Rate)...")
        
        # --- Aggregating Data to Monthly Level ---
        df_daily = self.df_prod.copy()
        df_daily['Month'] = df_daily['Date'].dt.to_period('M').dt.to_timestamp()
        
        df_daily['Install_Date'] = self.df_install['Tool'].map(self.df_install.set_index('Tool')['Install_Date'])
        
        # Define Treatment Group (Tools that eventually get the device)
        df_daily['Treated_Group'] = df_daily['Install_Date'].notna().astype(int)
        
        # Define Post Period (Staggered: specific to each tool)
        df_daily['Post'] = 0
        mask_treated = (df_daily['Treated_Group'] == 1) & (df_daily['Date'] >= df_daily['Install_Date'])
        df_daily.loc[mask_treated, 'Post'] = 1
        
        # Merge Error Counts
        df_errors_monthly = self.processed_data.groupby(['Tool', 'Month'])['Error_Date'].count().rename('Error_Count').reset_index()
        
        df_monthly_panel = pd.merge(
            df_daily.groupby(['Tool', 'Month', 'Treated_Group', 'Post'])['Production_Count'].sum().reset_index(),
            df_errors_monthly,
            on=['Tool', 'Month'],
            how='left'
        ).fillna(0)
        
        df_monthly_panel = df_monthly_panel[df_monthly_panel['Production_Count'] > 0]
        
        # *** Key Logic: Effective Denominator (Offset) ***
        df_monthly_panel['log_production'] = np.log(df_monthly_panel['Production_Count'])
        
        # --- Modeling (GLM Negative Binomial) ---
        formula = "Error_Count ~ Treated_Group + Post + Treated_Group:Post"
        
        print("  Fitting GLM (Negative Binomial) with Production Offset...")
        model = smf.glm(formula=formula, data=df_monthly_panel, 
                        offset=df_monthly_panel['log_production'],
                        family=sm.families.NegativeBinomial()).fit()
        
        print(model.summary())
        
        # Run OLS for WBF/MTBF (simple placeholder, requires correct aggregation/censoring)
        # For simplicity in the combined script, we focus on the rate model,
        # as WBF is primarily analyzed in the Survival script.
        
        # --- Visualization (Parallel Trend Check) ---
        plt.figure(figsize=(10, 6))
        sns.lineplot(data=df_monthly_panel, x='Month', y='Error_Count', hue='Treated_Group', style='Post', estimator='mean', errorbar=None)
        plt.title("Parallel Trend Check (Monthly Error Counts)")
        plt.xlabel("Month")
        plt.ylabel("Avg Error Count")
        plt.grid(True)
        plt.savefig("did_trend_plot.png")
        print("  -> Saved 'did_trend_plot.png'")

# ==========================================
# 3. Main Execution
# ==========================================
if __name__ == "__main__":
    gen = DummyDataGenerator(n_tools=20, periods=365)
    df_install, df_prod, df_errors = gen.generate_datasets()
    
    print("\n--- Running Static DiD Analysis (Count Rate) ---")
    analyzer = DiDAnalyzer(df_install, df_prod, df_errors)
    
    analyzer.calculate_utilization_metrics()
    
    analyzer.run_staggered_did()
    
    print("\nStatic DiD analysis completed successfully.")
