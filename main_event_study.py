# -*- coding: utf-8 -*-
"""
Event Study Analysis (Dynamic DiD) for Manufacturing Equipment
with Utilization (Wafer Count) Normalization

Author: Go Sato
Description:
    This script performs an Event Study (Dynamic Difference-in-Differences) to visualize 
    the causal impact of an equipment upgrade over time.
    
    It addresses:
    1. Staggered Adoption: Different tools receive upgrades at different times.
    2. Varying Utilization: Normalizes error rates using "Effective Denominator" (Wafer Counts).
    3. Dynamic Effects: Plots coefficients relative to the intervention month (K).

Dependencies:
    pandas, numpy, matplotlib, linearmodels
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings

# Try importing linearmodels for PanelOLS (Required for Event Study)
try:
    from linearmodels.panel import PanelOLS
    LINEARMODELS_AVAILABLE = True
except ImportError:
    LINEARMODELS_AVAILABLE = False
    print("WARNING: 'linearmodels' library not found. Please install it via 'pip install linearmodels'.")

warnings.filterwarnings('ignore')

# ==========================================
# 1. Dummy Data Generator
# ==========================================
class DummyDataGenerator:
    def __init__(self, n_tools=30, start_date='2023-01-01', periods=24):
        """
        n_tools: Number of tools (Higher N is better for Event Study)
        periods: Number of months to simulate
        """
        self.n_tools = n_tools
        self.start_date = pd.to_datetime(start_date)
        self.periods = periods # Months
        self.tools = [f'TOOL_{i:02d}' for i in range(1, n_tools + 1)]
        
    def generate_datasets(self):
        print("Generating Dummy Data (Monthly Aggregated)...")
        
        # 1. Installation Dates (Staggered)
        # 20 tools get Treated, 10 remain Control
        install_map = {}
        treated_tools = self.tools[:20]
        
        for tool in treated_tools:
            # Install scattered between month 6 and month 18
            install_month_offset = np.random.randint(6, 18)
            install_date = self.start_date + pd.DateOffset(months=install_month_offset)
            install_map[tool] = install_date
            
        # 2. Monthly Panel Data (Production & Errors)
        panel_rows = []
        months = pd.date_range(self.start_date, periods=self.periods, freq='MS')
        
        # Base utilization per tool (some are busy, some are idle)
        tool_util_factor = {t: np.random.uniform(0.5, 1.5) for t in self.tools}
        
        for t in self.tools:
            install_dt = install_map.get(t, pd.NaT)
            
            for m in months:
                # -- Production (Wafer Count) --
                # Base 10,000 wafers/month * Tool Factor * Random Fluctuation
                wafers = int(10000 * tool_util_factor[t] * np.random.normal(1.0, 0.1))
                wafers = max(100, wafers)
                
                # -- Errors --
                # Logic: Error count depends on Wafer volume.
                # Before Install: 1 error per 1,000 wafers
                # After Install:  0.2 errors per 1,000 wafers (Improvement)
                
                base_rate = 0.001
                if pd.notna(install_dt) and m >= install_dt:
                    base_rate = 0.0002 # Significant reduction
                
                # Poisson distribution for counts
                expected_errors = wafers * base_rate
                error_count = np.random.poisson(expected_errors)
                
                # MTBF (Mean Time Between Failures) in Hours
                # Simplified: (24h * 30days) / (Error Count). If 0 errors, use max hours.
                uptime_hours = 24 * 30
                if error_count > 0:
                    mtbf = uptime_hours / error_count
                else:
                    mtbf = uptime_hours # No failure
                
                panel_rows.append({
                    'Tool': t,
                    'Month': m,
                    'Wafer_Count': wafers,
                    'Error_Count': error_count,
                    'MTBF_Hours': mtbf,
                    'Install_Date': install_dt
                })
                
        df_panel = pd.DataFrame(panel_rows)
        return df_panel

# ==========================================
# 2. Event Study Logic
# ==========================================
class EventStudyAnalyzer:
    def __init__(self, df_panel):
        self.df = df_panel.copy()
        
    def preprocess_panel(self):
        """
        Calculates:
        1. Effective Denominator (Relative Utilization).
        2. Normalized Metrics (Count Rate per Unit Utilization).
        3. Relative Time 'K' (Month - Event Month).
        """
        print("[Analysis] Preprocessing Panel Data...")
        
        # --- 1. Calculate Relative Utilization ---
        # Average Wafers across all tools per month
        monthly_mean_wafers = self.df.groupby('Month')['Wafer_Count'].transform('mean')
        
        # Relative Utilization = Tool's Wafers / Global Average
        self.df['Relative_Utilization'] = self.df['Wafer_Count'] / monthly_mean_wafers
        
        # --- 2. Normalize Metrics ---
        # Norm_Count_Rate = Raw Count / Relative Utilization
        # (High count due to high utilization -> Lower normalized rate)
        self.df['Norm_Count_Rate'] = self.df['Error_Count'] / self.df['Relative_Utilization']
        
        # Norm_MTBF = Raw MTBF * Relative Utilization
        # (Long MTBF due to low utilization -> Shorter normalized MTBF)
        self.df['Norm_MTBF'] = self.df['MTBF_Hours'] * self.df['Relative_Utilization']
        
        # --- 3. Calculate K (Event Time) ---
        # K = Current Month - Install Month
        def calc_k(row):
            if pd.isna(row['Install_Date']):
                return np.nan
            # Difference in months
            diff = (row['Month'].year - row['Install_Date'].year) * 12 + \
                   (row['Month'].month - row['Install_Date'].month)
            return diff

        self.df['K'] = self.df.apply(calc_k, axis=1)
        
        # Create Dummy Variables for K (Event Study Dummies)
        # We bin K into range [-6, +6] for cleaner plotting, 
        # treating outliers as endpoints.
        self.df['K_binned'] = self.df['K'].clip(lower=-6, upper=6)
        
        print(f"  Data processed. Total rows: {len(self.df)}")

    def run_event_study_model(self, metric='Norm_Count_Rate'):
        """
        Runs PanelOLS regression:
        Metric ~ EntityEffects + TimeEffects + K_Dummies
        """
        if not LINEARMODELS_AVAILABLE:
            print("  Skipping model execution (linearmodels not installed).")
            return
            
        print(f"[Analysis] Running Event Study Model on '{metric}'...")
        
        # Prepare data for linearmodels
        # Index must be [Entity, Time]
        model_df = self.df.set_index(['Tool', 'Month']).copy()
        
        # Filter: Only use rows where K is defined (Treated group) 
        # or use all if we want to include Control group as reference (K=NaN).
        # For Event Study, usually restricted to Treated, or Control handled via 0 dummies.
        # Here, we treat Control group as having 0 effect dummies (reference).
        
        # Create dummies manually to handle Reference period (K = -1)
        # Reference period K=-1 is usually dropped to avoid multicollinearity.
        
        # Get dummies
        dummies = pd.get_dummies(model_df['K_binned'], prefix='K', dtype=int)
        
        # Drop K_-1 (The month before installation) as the reference point
        if 'K_-1.0' in dummies.columns:
            dummies = dummies.drop(columns=['K_-1.0'])
        
        # Combine
        exog_data = dummies
        
        # Formula not strictly needed if we pass exog directly, 
        # but PanelOLS requires defining effects.
        mod = PanelOLS(model_df[metric], exog_data, entity_effects=True, time_effects=True)
        
        # Cluster errors by Entity (Tool)
        res = mod.fit(cov_type='clustered', cluster_entity=True)
        
        print(res.summary)
        return res

    def plot_event_study_coeffs(self, model_result, metric_name):
        """
        Plots the coefficients of K dummies.
        This visualizes the trend before and after the event.
        """
        if model_result is None: return

        print(f"[Visual] Plotting Coefficients for {metric_name}...")
        
        params = model_result.params
        conf_int = model_result.conf_int()
        
        # Extract K values from index strings (e.g., "K_1.0" -> 1.0)
        ks = []
        coefs = []
        errs = []
        
        # Add Reference Point manually (K=-1, Coef=0)
        ks.append(-1)
        coefs.append(0)
        errs.append(0)
        
        for col in params.index:
            try:
                k_val = float(col.replace('K_', ''))
                ks.append(k_val)
                coefs.append(params[col])
                # Error bar length (upper - coef)
                err = conf_int.loc[col, 'upper'] - params[col]
                errs.append(err)
            except ValueError:
                continue
                
        # Sort by K
        plot_data = sorted(zip(ks, coefs, errs))
        ks, coefs, errs = zip(*plot_data)
        
        plt.figure(figsize=(10, 6))
        plt.errorbar(ks, coefs, yerr=errs, fmt='-o', color='b', ecolor='gray', capsize=5, label='Effect Estimate')
        plt.axhline(0, color='red', linestyle='--')
        plt.axvline(-0.5, color='green', linestyle=':', label='Intervention')
        
        plt.title(f"Event Study: Impact on {metric_name}\n(Dynamic Difference-in-Differences)")
        plt.xlabel("Months Relative to Installation (K)")
        plt.ylabel(f"Change in {metric_name}")
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        filename = f"event_study_{metric_name}.png"
        plt.savefig(filename)
        print(f"  -> Saved {filename}")

# ==========================================
# 3. Main Execution
# ==========================================
if __name__ == "__main__":
    # 1. Generate Data
    gen = DummyDataGenerator(n_tools=40, periods=36)
    df_panel = gen.generate_datasets()
    
    # 2. Analyze
    analyzer = EventStudyAnalyzer(df_panel)
    analyzer.preprocess_panel()
    
    # 3. Run Models & Plot
    if LINEARMODELS_AVAILABLE:
        # Model 1: Normalized Count Rate
        res_rate = analyzer.run_event_study_model(metric='Norm_Count_Rate')
        analyzer.plot_event_study_coeffs(res_rate, metric_name='Norm_Count_Rate')
        
        # Model 2: Normalized MTBF
        res_mtbf = analyzer.run_event_study_model(metric='Norm_MTBF')
        analyzer.plot_event_study_coeffs(res_mtbf, metric_name='Norm_MTBF')
    else:
        print("\n[!] Skipping regression analysis due to missing library.")
        print("    Data generation and preprocessing were successful.")
