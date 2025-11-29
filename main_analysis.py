# -*- coding: utf-8 -*-
"""
Impact Analysis of Manufacturing Equipment Upgrade
(Staggered DiD & Survival Analysis with Utilization Weighting)

Author: Go Sato
Description:
    This script generates dummy data simulating a manufacturing line (e.g., Bread Factory analogy)
    and performs statistical analysis to verify the effect of a new equipment component.
    It handles staggered installation dates and varying utilization rates.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from lifelines import CoxPHFitter, WeibullAFTFitter, KaplanMeierFitter
import statsmodels.formula.api as smf
import statsmodels.api as sm
from datetime import datetime, timedelta
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# ==========================================
# 1. Dummy Data Generator
# ==========================================
class DummyDataGenerator:
    def __init__(self, n_tools=20, start_date='2024-01-01', periods=365):
        self.n_tools = n_tools
        self.start_date = pd.to_datetime(start_date)
        self.periods = periods
        self.tools = [f'TOOL_{i:02d}' for i in range(1, n_tools + 1)]
        
    def generate_datasets(self):
        """
        Generates 3 datasets:
        1. Installation Data (When the new device was installed)
        2. Production Data (Daily production counts -> Represents Utilization)
        3. Error Data (Error logs)
        """
        print("Generating Dummy Data...")
        
        # --- 1. Installation Dates (Staggered) ---
        # Half of the tools get the new device at random times (Staggered adoption)
        install_map = {}
        treated_tools = self.tools[:self.n_tools // 2]
        
        for tool in treated_tools:
            # Install sometime in the middle of the period
            offset = np.random.randint(self.periods // 4, self.periods * 3 // 4)
            install_date = self.start_date + timedelta(days=offset)
            install_map[tool] = install_date
            
        df_install = pd.DataFrame(list(install_map.items()), columns=['Tool', 'Install_Date'])
        
        # --- 2. Production Data (Daily - Varying Utilization) ---
        # Some tools run 24/7 (high load), others run sparingly (low load)
        prod_data = []
        date_range = pd.date_range(self.start_date, periods=self.periods)
        
        # Utilization factor for each tool (0.2 to 1.0)
        tool_capacity = {t: np.random.uniform(0.2, 1.0) for t in self.tools} 
        
        for t in self.tools:
            base_prod = 1000 * tool_capacity[t] # Max 1000 units/day
            for d in date_range:
                # Add random fluctuation
                daily_prod = int(np.random.normal(base_prod, 50))
                daily_prod = max(0, daily_prod)
                prod_data.append({'Tool': t, 'Date': d, 'Production_Count': daily_prod})
                
        df_production = pd.DataFrame(prod_data)
        
        # --- 3. Error Data ---
        # Logic: Errors depend on accumulated production volume, not just time.
        # The new device (After Install) reduces error probability by 50%.
        error_data = []
        
        base_error_prob_per_unit = 0.0005 # Probability of error per unit produced
        effect_size = 0.5 # New device reduces errors (Improvement)
        
        for t in self.tools:
            t_prod = df_production[df_production['Tool'] == t]
            install_dt = install_map.get(t, pd.NaT)
            
            for _, row in t_prod.iterrows():
                units = row['Production_Count']
                d = row['Date']
                
                # Determine probability based on intervention status
                prob = base_error_prob_per_unit
                is_treated = False
                if pd.notna(install_dt) and d >= install_dt:
                    prob *= effect_size # Apply improvement
                    is_treated = True
                
                # Simulate errors (Poisson/Binomial process)
                n_errors = np.random.binomial(units, prob)
                
                if n_errors > 0:
                    for _ in range(n_errors):
                        # Add random timestamp within the day
                        err_time = d + timedelta(hours=np.random.randint(0, 24))
                        error_data.append({
                            'Tool': t,
                            'Error_Date': err_time,
                            'Is_Intro': is_treated
                        })
                        
        df_errors = pd.DataFrame(error_data)
        
        return df_install, df_production, df_errors

# ==========================================
# 2. Analysis Logic
# ==========================================
class EffectAnalyzer:
    def __init__(self, df_install, df_prod, df_errors):
        self.df_install = df_install
        self.df_prod = df_prod
        self.df_errors = df_errors
        self.processed_data = None
        
    def calculate_utilization_metrics(self):
        """
        [Step 1] Metric Calculation with Effective Denominator
        Instead of 'Time Between Failures', we calculate 'Work (Production) Between Failures'.
        This normalizes the varying utilization rates across tools.
        """
        print("\n[Step 1] Calculating Utilization & WBF (Work Between Failures)...")
        
        # Calculate Global Average Throughput (Units per Hour) for normalization reference
        global_avg_daily_prod = self.df_prod['Production_Count'].mean()
        print(f"  Global Avg Daily Production: {global_avg_daily_prod:.1f} units")
        
        # Sort and calculate intervals
        df_err = self.df_errors.sort_values(['Tool', 'Error_Date']).copy()
        df_err['Prev_Error_Date'] = df_err.groupby('Tool')['Error_Date'].shift(1)
        
        # Calculate raw time (hours) - The naive metric
        df_err['Time_Interval_Hours'] = (df_err['Error_Date'] - df_err['Prev_Error_Date']).dt.total_seconds() / 3600.0
        
        # Calculate "Production between failures" (WBF) - The correct metric
        wbf_list = []
        for idx, row in df_err.iterrows():
            if pd.isna(row['Prev_Error_Date']):
                wbf_list.append(np.nan)
                continue
                
            # Sum production between previous error and current error
            mask = (self.df_prod['Tool'] == row['Tool']) & \
                   (self.df_prod['Date'] >= row['Prev_Error_Date'].floor('D')) & \
                   (self.df_prod['Date'] <= row['Error_Date'].floor('D'))
            prod_sum = self.df_prod.loc[mask, 'Production_Count'].sum()
            wbf_list.append(prod_sum)
            
        df_err['WBF_Units'] = wbf_list
        
        # Calculate Normalized MTBF (Time adjusted by utilization rate)
        # Normalized Time = WBF / Global Avg Throughput
        hourly_throughput = global_avg_daily_prod / 24.0
        df_err['Norm_MTBF_Hours'] = df_err['WBF_Units'] / hourly_throughput
        
        self.processed_data = df_err.dropna(subset=['WBF_Units'])
        print(f"  Processed {len(self.processed_data)} error intervals.")

    def run_survival_analysis(self):
        """
        [Step 2] Survival Analysis (Cox & AFT)
        Uses 'WBF_Units' (Production count) as the duration variable.
        """
        print("\n[Step 2] Running Survival Analysis (Cox PH & AFT) on WBF...")
        
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
        plt.savefig("survival_plot.png")
        print("  -> Saved 'survival_plot.png'")
        
        # 2. Cox Proportional Hazards
        # Event = 1 (Failure occurred)
        df_model = df[['WBF_Units', 'Group']].copy()
        df_model['Event'] = 1 
        df_model['Is_New'] = (df_model['Group'] == 'New_Device').astype(int)
        
        print("\n  --- Cox Proportional Hazards Model Results ---")
        try:
            cph = CoxPHFitter()
            cph.fit(df_model[['WBF_Units', 'Event', 'Is_New']], duration_col='WBF_Units', event_col='Event')
            cph.print_summary()
            
            hr = cph.hazard_ratios_['Is_New']
            print(f"  Hazard Ratio (HR): {hr:.3f}")
            if hr < 1:
                print(f"  Result: The new device reduces failure risk by {(1-hr)*100:.1f}%.")
        except Exception as e:
            print(f"  Cox fitting failed: {e}")

        # 3. AFT (Weibull)
        print("\n  --- Weibull AFT Model Results ---")
        try:
            aft = WeibullAFTFitter()
            # Add small epsilon to avoid zero duration issues
            df_model['WBF_Units'] = df_model['WBF_Units'].clip(lower=0.1)
            aft.fit(df_model[['WBF_Units', 'Event', 'Is_New']], duration_col='WBF_Units', event_col='Event')
            
            # exp(coef) in AFT is the Acceleration Factor. > 1 means life is extended.
            print(aft.summary[['exp(coef)', 'p']])
        except Exception as e:
            print(f"  AFT fitting failed: {e}")

    def run_staggered_did(self):
        """
        [Step 3] Staggered Difference-in-Differences (DiD)
        Uses Generalized Linear Model (Negative Binomial) for Count Data.
        Offsets by log(Production) to account for utilization.
        """
        print("\n[Step 3] Running Staggered DiD Analysis...")
        
        # --- Aggregating Data to Monthly Level ---
        df_daily = self.df_prod.copy()
        df_daily['Month'] = df_daily['Date'].dt.to_period('M').dt.to_timestamp()
        
        # Map installation dates
        df_daily['Install_Date'] = df_daily['Tool'].map(self.df_install.set_index('Tool')['Install_Date'])
        
        # Define Treatment Group (Tools that eventually get the device)
        df_daily['Treated_Group'] = df_daily['Install_Date'].notna().astype(int)
        
        # Define Post Period (Staggered: specific to each tool)
        df_daily['Post'] = 0
        mask_treated = (df_daily['Treated_Group'] == 1) & (df_daily['Date'] >= df_daily['Install_Date'])
        df_daily.loc[mask_treated, 'Post'] = 1
        
        # Merge Error Counts
        error_counts = self.df_errors.groupby(['Tool', 'Error_Date']).size().reset_index(name='Error_Count')
        error_counts['Date'] = error_counts['Error_Date'].dt.floor('D')
        
        df_merged = pd.merge(df_daily, error_counts.groupby(['Tool', 'Date'])['Error_Count'].sum().reset_index(),
                             on=['Tool', 'Date'], how='left').fillna(0)
        
        # Monthly Aggregation
        df_monthly = df_merged.groupby(['Tool', 'Month', 'Treated_Group']).agg({
            'Production_Count': 'sum',
            'Error_Count': 'sum',
            'Post': 'max' # Simplified for monthly granularity
        }).reset_index()
        
        # Filter valid production months
        df_monthly = df_monthly[df_monthly['Production_Count'] > 0]
        
        # *** Key Logic: Effective Denominator ***
        # Using Log(Production) as offset in GLM handles varying utilization rates
        df_monthly['log_production'] = np.log(df_monthly['Production_Count'])
        
        # --- Modeling (GLM Negative Binomial) ---
        # Formula: Error_Count ~ Treated + Post + Treated*Post + Offset(log_prod)
        formula = "Error_Count ~ Treated_Group + Post + Treated_Group:Post"
        
        print("  Fitting GLM (Negative Binomial) with Production Offset...")
        model = smf.glm(formula=formula, data=df_monthly, 
                        offset=df_monthly['log_production'],
                        family=sm.families.NegativeBinomial()).fit()
        
        print(model.summary())
        
        # Extract DiD coefficient (Interaction term)
        did_coeff = model.params['Treated_Group:Post']
        p_value = model.pvalues['Treated_Group:Post']
        effect_ratio = np.exp(did_coeff)
        
        print(f"\n  [DiD Result]")
        print(f"  Interaction Coefficient: {did_coeff:.4f}")
        print(f"  P-value: {p_value:.4f}")
        print(f"  Effect Ratio (Rate Ratio): {effect_ratio:.4f}")
        
        if p_value < 0.05 and effect_ratio < 1.0:
            print("  => CONCLUSION: Significant reduction in Error Rate confirmed.")
        else:
            print("  => CONCLUSION: No significant effect detected.")
            
        # --- Visualization (Parallel Trend Check) ---
        plt.figure(figsize=(10, 6))
        sns.lineplot(data=df_monthly, x='Month', y='Error_Count', hue='Treated_Group', style='Post', estimator='mean', errorbar=None)
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
    # 1. Generate Data
    gen = DummyDataGenerator(n_tools=20, periods=365)
    df_install, df_prod, df_errors = gen.generate_datasets()
    
    # Show sample data
    print("\n--- Installation Data (Sample) ---")
    print(df_install.head())
    print("\n--- Production Data (Sample) ---")
    print(df_prod.head())
    
    # 2. Run Analysis
    analyzer = EffectAnalyzer(df_install, df_prod, df_errors)
    
    # Step 1: Metrics
    analyzer.calculate_utilization_metrics()
    
    # Step 2: Survival Analysis
    analyzer.run_survival_analysis()
    
    # Step 3: DiD Analysis
    analyzer.run_staggered_did()
    
    print("\nAll analysis completed successfully.")
