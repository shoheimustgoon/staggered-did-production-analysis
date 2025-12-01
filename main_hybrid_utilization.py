# -*- coding: utf-8 -*-
"""
Hybrid Utilization Estimation (Proxy-based Imputation)
Logic: Learns relationship between Oven Usage/Cleaning Time and Loaves Baked (Production)
to estimate utilization during data-scarce periods.

Author: Go Sato
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# ==========================================
# 1. Dummy Data Generator (Simulates Missing Data)
# ==========================================
def generate_hybrid_dummy_data(n_tools=3, start_date='2024-01-01', months=6):
    """Generates Loaves Baked Data with Gaps and Oven Usage Log (Proxy Data)."""
    tools = [f'OVEN_{i:02d}' for i in range(1, n_tools + 1)]  # ツールをオーブンに変更
    end_date = pd.to_datetime(start_date) + pd.DateOffset(months=months)
    date_range = pd.date_range(start_date, end_date, freq='D')
    
    prod_rows = []
    clean_rows = [] # Proxy/Consumption Log用

    for t in tools:
        util_factor = np.random.uniform(0.5, 1.2)
        base_production = 500 * util_factor
        
        # --- 1. Output Data (Loaves Baked: パンの製造数) ---
        for d in date_range:
            daily_loaves = int(np.random.normal(base_production, 20))
            if np.random.rand() < 0.3 and d < pd.to_datetime('2024-03-01'):
                # 早期の期間でデータ欠損をシミュレート
                prod_rows.append({'Date': d, 'Tool': t, 'Loaves_Baked': np.nan})
            else:
                prod_rows.append({'Date': d, 'Tool': t, 'Loaves_Baked': max(0, daily_loaves)})

        # --- 2. Proxy Data (Material Consumption Log: 材料消費量) ---
        # 材料消費量が月次で記録されると仮定
        monthly_dates = pd.date_range(start_date, end_date, freq='MS')
        for md in monthly_dates:
            # Proxyとなる材料消費量（使用時間ではない）
            material_consumed = 500 * util_factor * np.random.uniform(0.9, 1.1)
            clean_rows.append({'Date': md + timedelta(hours=1), 'Tool': t, 'Material_Consumed_Kg': material_consumed}) # RF_Time_Hrs -> Material_Consumed_Kg

    df_prod = pd.DataFrame(prod_rows)
    df_clean = pd.DataFrame(clean_rows)
    return df_prod, df_clean

# ==========================================
# 2. Hybrid Estimation Logic
# ==========================================
def estimate_missing_utilization(df_prod, df_clean):
    print("\n[Step 1] Learning Production Coefficient from Proxy Data...")
    
    # 1. 月次集計 (Material Consumption & Loaves)
    df_prod['Month'] = df_prod['Date'].dt.to_period('M').dt.to_timestamp()
    df_clean['Month'] = df_clean['Date'].dt.to_period('M').dt.to_timestamp()
    
    df_monthly_prod = df_prod.groupby(['Tool', 'Month'])['Loaves_Baked'].sum().reset_index()
    df_monthly_clean = df_clean.groupby(['Tool', 'Month'])['Material_Consumed_Kg'].sum().reset_index()
    
    df_merged = pd.merge(df_monthly_prod, df_monthly_clean, on=['Tool', 'Month'], how='outer')
    
    # 2. 係数学習 (Coefficient = Material / Loaves) - データが揃っている期間で学習
    # Coeff: 1 Loaf (Unit) 生産するのに必要な材料消費量 (Proxy)
    df_merged['Coefficient'] = df_merged['Material_Consumed_Kg'] / df_merged['Loaves_Baked'].replace(0, np.nan)
    
    # Toolごとの平均係数 (学習データ)
    tool_coeffs = df_merged.dropna(subset=['Coefficient']).groupby('Tool')['Coefficient'].mean().to_dict()
    global_coeff = pd.Series(tool_coeffs).median()
    
    print(f"  Learned Global Coefficient (Median Kg/Loaf): {global_coeff:.4f}") 

    # 3. 欠損期間の推定 (Imputation)
    df_imputed = df_merged.copy()
    
    for index, row in df_imputed.iterrows():
        # 推定条件: Loaves_Bakedが欠損 (NaN) かつ Material_Consumed_Kgがある場合
        if pd.isna(row['Loaves_Baked']) and pd.notna(row['Material_Consumed_Kg']):
            tool = row['Tool']
            material_consumed = row['Material_Consumed_Kg']
            coeff = tool_coeffs.get(tool, global_coeff)
            
            # Estimated Production = Material Consumed / Coefficient
            if coeff > 0:
                estimated_loaves = material_consumed / coeff
                df_imputed.loc[index, 'Loaves_Baked_Imputed'] = estimated_loaves
            else:
                df_imputed.loc[index, 'Loaves_Baked_Imputed'] = 0
        else:
            # 欠損していない期間は実測値を使用
            df_imputed.loc[index, 'Loaves_Baked_Imputed'] = row['Loaves_Baked']
            
    print(f"  Total Imputed Values: {df_imputed['Loaves_Baked_
