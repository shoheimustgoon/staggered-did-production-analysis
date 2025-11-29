# -*- coding: utf-8 -*-
"""
Survival Analysis Toolkit (KMF, Cox PH, Weibull AFT)
Duration metric: WBF (Work Between Failures, utilizing production volume)

Author: Go Sato
Description:
    This script is dedicated to running robust survival models (Cox, AFT)
    using the utilization-corrected metric (WBF) derived from the manufacturing data.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from lifelines import CoxPHFitter, WeibullAFTFitter, KaplanMeierFitter
from datetime import datetime, timedelta
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# ==========================================
# 1. Dummy Data Generator (Duplicated for standalone execution)
# ==========================================
class DummyDataGenerator:
    def __init__(self, n_tools=20, start_date='2024-01-01', periods=365):
        self.n_tools = n_tools
        self.start_date = pd.to_datetime(start_date)
        self.periods = periods
        self.tools = [f'TOOL_{i:02d}' for i in range(1, n_tools + 1)]
        
    def generate_datasets(self):
        print("Generating Dummy Data...")
        
        install_map = {}
        treated_tools = self.tools[:self.n_tools // 2]
        
        for tool in treated_tools:
            offset = np.random.randint(self.periods // 4, self.periods * 3 // 4)
            install_date = self.start_date + timedelta(days=offset)
            install_map[tool] = install_date
            
        df_install = pd.DataFrame(list(install_map.items()), columns=['Tool', 'Install_Date'])
        
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
# 2. Survival Analysis Logic
# ==========================================
class EffectAnalyzer:
    def __init__(self, df_install, df_prod, df_errors):
        self.df_install = df_install
        self.df_prod = df_prod
        self.df_errors = df_errors
        self.processed_data = None
        
    def calculate_utilization_metrics(self):
        """
        [Step 1] Metric Calculation: WBF (Work Between Failures)
        WBF is the utilization-corrected duration metric used for Survival Analysis.
        """
        print("\n[Step 1] Calculating Utilization & WBF (Work Between Failures)...")
        
        global_avg_daily_prod = self.df_prod['Production_Count'].mean()
        print(f"  Global Avg Daily Production: {global_avg_daily_prod:.1f} units")
        
        df_err = self.df_errors.sort_values(['Tool', 'Error_Date']).copy()
        df_err['Prev_Error_Date'] = df_err.groupby('Tool')['Error_Date'].shift(1)
        
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
        
        self.processed_data = df_err.dropna(subset=['WBF_Units'])
        print(f"  Processed {len(self.processed_data)} error intervals.")

    def run_survival_analysis(self):
        """
        [Step 2] Runs KMF, Cox PH, and Weibull AFT models on WBF.
        """
        print("\n[Step 2] Running Survival Analysis (KMF, Cox PH & AFT) on WBF...")
        
        df = self.processed_data.copy()
        df['Group'] = df['Is_Intro'].apply(lambda x: 'New_Device' if x else 'Old_Device')
        
        # 1. Kaplan-Meier Plot
        plt.figure(figsize=(10, 6))
        kmf = KaplanMeierFitter()
        
        for name, grouped_df in df.groupby('Group'):
            kmf.fit(grouped_df["WBF_Units"], label=name)
            kmf.plot_survival_function()
            
        plt.title("Survival Function (Based on Production Units)")
        plt.xlabel("Production Count between Failures (WBF)")
        plt.ylabel("Survival Probability")
        plt.grid(True, linestyle='--')
        plt.savefig("survival_plot_WBF.png")
        print("  -> Saved 'survival_plot_WBF.png'")
        
        # 2. Cox Proportional Hazards
        df_model = df[['WBF_Units', 'Group']].copy()
        df_model['Event'] = 1 
        df_model['Is_New'] = (df_model['Group'] == 'New_Device').astype(int)
        
        print("\n  --- Cox Proportional Hazards Model Results ---")
        try:
            cph = CoxPHFitter()
            cph.fit(df_model[['WBF_Units', 'Event', 'Is_New']], duration_col='WBF_Units', event_col='Event')
            cph.print_summary()
        except Exception as e:
            print(f"  Cox fitting failed: {e}")

        # 3. AFT (Weibull)
        print("\n  --- Weibull AFT Model Results ---")
        try:
            aft = WeibullAFTFitter()
            df_model['WBF_Units'] = df_model['WBF_Units'].clip(lower=0.1)
            aft.fit(df_model[['WBF_Units', 'Event', 'Is_New']], duration_col='WBF_Units', event_col='Event')
            
            print(aft.summary[['exp(coef)', 'p']])
        except Exception as e:
            print(f"  AFT fitting failed: {e}")

# ==========================================
# 3. Main Execution
# ==========================================
if __name__ == "__main__":
    gen = DummyDataGenerator(n_tools=20, periods=365)
    df_install, df_prod, df_errors = gen.generate_datasets()
    
    print("\n--- Running Survival Analysis Toolkit (KMF, Cox, AFT) ---")
    analyzer = EffectAnalyzer(df_install, df_prod, df_errors)
    
    analyzer.calculate_utilization_metrics()
    
    analyzer.run_survival_analysis()
    
    print("\nSurvival analysis completed successfully.")
