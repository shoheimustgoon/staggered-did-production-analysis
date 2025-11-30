# -*- coding: utf-8 -*-
"""
Event Study Analysis (Dynamic DiD) for Manufacturing Equipment
with Utilization (Wafer Count) Normalization

Author: Go Sato
Description:
    This script performs an Event Study (Dynamic Difference-in-Differences) to visualize 
    the causal impact of an equipment upgrade over time.
    
    It uses a robust Two-Way Fixed Effects (TWFE) model structure to control for
    unobserved confounders.
"""
from __future__ import annotations
import os
import sys
# ... (Standard Imports Omitted for Brevity) ...
import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import seaborn as sns
import logging
import traceback
import re
from typing import Literal

# Event Study Library (Required for PanelOLS)
try:
    from linearmodels.panel import PanelOLS
    LINEARMODELS_AVAILABLE = True
except ImportError:
    LINEARMODELS_AVAILABLE = False
    print("WARNING: 'linearmodels' library not found. Please install it via 'pip install linearmodels'.")

# --- (1. Data Preparation and 2. Analysis Helpers Omitted for Brevity) ---
# Assuming prepare_data_staggered is available and creates df_panel with 'group', 'Month', and 'relative_time'.

# === 3. Analysis (TWFE Event Study) ===

def run_twfe_event_study(df_panel: pd.DataFrame, model_type: Literal['CountRate', 'MTBF'], 
                         window_pre: int = 6, window_post: int = 6, ref_time: int = -1) -> pd.DataFrame | None:
    """
    [TWFE Event Study]
    Y ~ C(group) + C(Month_str) + C(relative_time)
    
    ## Two-Way Fixed Effects (TWFE) Model Definition
    
    TWFE models are the foundational structure for Staggered DiD analysis. They are used 
    to control for unobserved confounding variables that might bias the causal effect.

    When to use TWFE: 
    When dealing with panel data (Entity x Time) where unobserved factors are present.

    The model addresses two types of unobserved confounders:
    1. Entity Fixed Effects (Tool/Unit-level): Controls for unobserved factors unique to the tool (e.g., baseline performance, quality of installation crew, or environment).
    2. Time Fixed Effects (Month-level): Controls for common shocks affecting all units equally in a given period (e.g., site-wide power outage, global component shortage, or common seasonal effects).
    
    In this implementation:
    - Entity Fixed Effects: Implicitly controlled by C(group) or by the index structure in PanelOLS.
    - Time Fixed Effects: Implicitly controlled by C(Month_str).
    - Causal Effect: Measured by the coefficient on the relative time dummies (C(relative_time_cat)).
    """
    
    if df_panel is None or df_panel.empty:
        logging.error(f"[EventStudy {model_type}] Model failed: Input data is empty.")
        return None
    
    df = df_panel.copy()
    
    # --- relative_time のカテゴリ変数を作成 --- (Omitted for brevity)
    # ...
    
    valid_cats = df['relative_time_cat'].nunique()
    if valid_cats <= 2: 
        logging.error(f"[EventStudy {model_type}] Model failed: Not enough relative_time categories.")
        return None

    ref_category = f'T_m{abs(ref_time)}_REF'
    
    try:
        # Note: In linearmodels PanelOLS is more appropriate but here we use statsmodels
        # for explicit GLM/NB support, utilizing the standard TWFE dummy structure.
        
        formula = f"Count ~ C(group) + C(Month_str) + C(relative_time_cat, Treatment(reference='{ref_category}'))"
        
        if model_type == 'CountRate':
            # Count Rate Model: GLM-NB with Offset
            logging.info(f"[EventStudy {model_type}] Running GLM-NB Model with TWFE...")
            model = smf.glm(
                formula=formula,
                data=df,
                family=sm.families.NegativeBinomial(),
                offset=df['log_denom']
            ).fit(cov_type='HC1') # Robust standard errors
            
        elif model_type == 'MTBF':
            # MTBF Model: OLS with Clustering
            formula = f"MTBF ~ C(group) + C(Month_str) + C(relative_time_cat, Treatment(reference='{ref_category}'))"
            logging.info(f"[EventStudy {model_type}] Running OLS Model with TWFE...")
            model = smf.ols(
                formula=formula,
                data=df
            ).fit(cov_type='cluster', cov_kwds={'groups': df['group']})


        # --- 結果の抽出 ---
        params = model.params.filter(like='relative_time_cat')
        pvalues = model.pvalues.filter(like='relative_time_cat')
        conf_int = model.conf_int().filter(like='relative_time_cat', axis=0)
        
        # (Rest of the extraction and plotting logic is omitted)
        return pd.DataFrame() 

    except Exception as e:
        logging.error(f"[EventStudy {model_type}] Model Failed: {e}", exc_info=True)
        return None

# --- (Other functions and Main execution block omitted for brevity) ---
