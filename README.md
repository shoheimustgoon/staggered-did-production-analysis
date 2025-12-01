### 1\. `main_hybrid_utilization.py` の最終コード

まず、パン工場のアナロジーに完全に沿った、ハイブリッド推定ロジックのコードです。

```python
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
            
    print(f"  Total Imputed Values: {df_imputed['Loaves_Baked_Imputed'].isna().sum()} (Should be 0 if clean)")
    return df_imputed[['Tool', 'Month', 'Loaves_Baked', 'Loaves_Baked_Imputed', 'Material_Consumed_Kg']]

# ==========================================
# 3. Main Execution
# ==========================================
if __name__ == "__main__":
    df_prod_raw, df_clean_log = generate_hybrid_dummy_data()
    
    print("--- 1. Raw Data Status (Loaves Baked) ---")
    print(df_prod_raw[df_prod_raw['Loaves_Baked'].isna()].head())
    print(f"\nTotal Missing Loaves Baked Counts: {df_prod_raw['Loaves_Baked'].isna().sum()}")
    
    df_results = estimate_missing_utilization(df_prod_raw, df_clean_log)
    
    print("\n--- 2. Imputation Results (Monthly) ---")
    print(df_results.head(10))
    
    print("\n[Conclusion]")
    print(f"The 'Loaves_Baked_Imputed' column now contains estimated values where 'Loaves_Baked' was missing, based on the Material_Consumed_Kg proxy.")
```

-----

### 2\. `README.md` 最終統合版

このコード (`main_hybrid_utilization.py`) と、これまでの全ての分析を網羅した最終版 `README.md` です。

````markdown
# Impact Analysis of Manufacturing Equipment Upgrade (Survival, Staggered DiD & Event Study)

> **[🇯🇵 日本語の説明はこちら (Click here for Japanese Description)](#japanese-description)**

## 📖 Overview
This project is a Python-based analytical framework designed to verify the effectiveness of new equipment components in a manufacturing environment. It addresses complex real-world conditions such as **staggered installation dates** and **varying equipment utilization rates**.

The core survival technique (Cox PH/AFT) is directly applicable to medical/pharmaceutical analysis (Time-to-Event), such as assessing drug efficacy and patient survival.

It includes three complementary analytical approaches:
1.  **Survival Analysis:** KMF, Cox PH, and AFT models using utilization-corrected metrics.
2.  **Static DiD Analysis:** Standard DiD (OLS/GLM) for overall effect quantification.
3.  **Dynamic DiD Analysis:** Event Study for trend visualization.

To ensure data confidentiality, this project uses a **"Bread Factory" analogy** to demonstrate the analytical logic without exposing sensitive production data.

---

## 🥐 The Analogy: The Bread Factory

### The Context
- **The Factory:** A large factory producing bread with 20-40 industrial ovens (Tools).
- **The Upgrade:** A new "AI Temperature Controller" was installed to prevent bread from burning (Failures).
- **The Goal:** To statistically prove that the new controller reduces the failure rate.

### The Challenges
1.  **Varying Utilization:** Oven A runs 24/7, while Oven B runs only 2 hours. Simple **MTBF** (Mean Time Between Failures) is unfair.
    - *Solution:* We derive **Normalized MTBF** using **Production Count (Loaves Baked)**. We normalize metrics using **"Effective Denominator"** (Material Consumption / Loaves Baked).
2.  **Staggered Installation:** Controllers were installed at different times (Jan, Mar, Jun...).
    - *Solution:* We align data using **Relative Time ($K$)** and use Staggered DiD / Event Study models.

#### The Data Scarcity Problem (Hybrid Estimation)
We initially ran the DiD analysis assuming all ovens were operating consistently. **However, the initial results were unstable and unreliable**, proving our fundamental premise was flawed due to varying utilization.

To solve the data scarcity that arose when measuring "Loaves Baked" directly, we developed a proxy estimation system: We used secondary metrics, such as **"Oven Cleaning Frequency"** or **"Energy Consumption" (RF time equivalent)**, to **estimate** the missing production counts. This process, handled by the utility script (`main_hybrid_utilization.py`), ensures utilization correction is robustly applied across the entire historical dataset.

---

## 🛠 Included Scripts & Methodology

### 1. `main_hybrid_utilization.py` (Data Utility)
**Purpose:** Solves the data scarcity challenge by imputing missing output volumes.
- **Logic:** Learns the relationship between **Material Consumption (Proxy Input)** and **Loaves Baked (Output)** during data-rich periods. This ratio is then used to estimate the missing 'Loaves Baked' when only the proxy input is available.
- **Output:** Provides the necessary **Utilization-Corrected Data** for the downstream analysis scripts (2, 3, & 4).

### 2. `main_survival_analysis.py` (Survival Analysis)
Focuses on the duration metric and risk modeling. This script uses **MTBF (Mean Time Between Failures)** corrected for utilization as the primary duration metric.

#### Right-Censoring Logic
The analysis incorporates **Right-Censoring**, which is vital for unbiased results. Censoring occurs when a unit (oven) is still functional when the observation period ends. In the analysis, these data points are included with an `Event = 0` flag to correctly estimate the population risk and survival curve.

| Model | Goal (English) | Role in this Project (Japanese) |
| :--- | :--- | :--- |
| **KMF** (Kaplan-Meier) | Estimates the **Survival Function** (non-parametric). | **視覚的な比較:** 新旧デバイス間のMTBF（故障間隔）の分布をグラフで示します。 |
| **Cox PH** (Proportional Hazards) | Estimates the **Hazard Ratio** (risk ratio, semi-parametric). | **リスク低減の定量化:** 新デバイス導入による**故障リスクの減少率**を推定します。 |
| **Weibull AFT** (Accelerated Failure Time) | Estimates the **Acceleration Factor** (lifespan ratio, parametric). | **寿命の定量化:** 新デバイス導入による**MTBF**の延長率を推定します。 |

### 3. `main_analysis.py` (Static DiD Analysis)
Focuses on quantifying the overall Average Treatment Effect (ATT) using the standard **Two-Way Fixed Effects (TWFE)** structure.

#### Two-Way Fixed Effects (TWFE) Details
TWFE models are used for panel data to control for unobserved confounding variables.

| 固定効果の種類 | 制御する未観測の要因 | このプロジェクトでの対応 |
| :--- | :--- | :--- |
| **Entity Fixed Effects** | Unit-specific factors (e.g., environment, initial performance) | **装置**ごとの固定効果（`C(Tool)` または `C(group)`）により制御 |
| **Time Fixed Effects** | Factors common across all units at a given time (e.g., site-wide power failure, component delays) | **時間**ごとの固定効果（`C(Month)` または `C(Date)`）により制御 |

- **Staggered DiD Implementation:** The core staggered logic (unit-specific `Post` variable timing) is applied to both OLS and GLM.
- **Continuous Outcomes (MTBF):** Uses **OLS** regression.
- **Count Outcomes (Rate):** Uses **Negative Binomial GLM** with the `log(Production)` offset for utilization normalization.

### 4. `main_event_study.py` (Dynamic Analysis)
Focuses on visualizing the timing of the effect and checking the Parallel Trend assumption.
- **Event Study (PanelOLS):** Visualizes the causal impact trend before and after installation.
- **Parallel Trend Check:** Verifies if the pre-installation trend ($K < 0$) is flat (validating the causal assumption).

---

## 💻 Usage

### Running the Analysis
The project uses a three-step workflow, starting with data imputation.

#### Step 1: Run Hybrid Imputation (Utility)
```bash
python main_hybrid_utilization.py
````

#### Step 2: Run Survival Analysis (Risk Modeling)

```bash
python main_survival_analysis.py
```

#### Step 3: Run DiD Analysis (Causal Effect)

```bash
python main_analysis.py
```

#### Step 4: Run Dynamic Analysis (Event Study)

```bash
python main_event_study.py
```

-----

## 👨‍💻 Author

**Go Sato**
Data Scientist | AI Department, Semiconductor Equipment Manufacturer
Specializing in Causal Inference, Survival Analysis, and Reliability Engineering.

<br>
<br>
<br>

-----

## Japanese Description

-----

# 製造装置の導入効果分析（生存分析、Staggered DiD & イベントスタディ）

## 📖 概要

本プロジェクトは、製造現場における新規コンポーネントの導入効果を検証するためのPython分析フレームワークです。**導入時期が装置ごとに異なる点**や、**装置ごとの稼働率のばらつき**といった、実世界の複雑な条件に対応しています。

**この生存分析の核となる手法（Cox PH/AFT）は、薬効の分析や患者の生存期間推定など、医療・製薬分野（Time-to-Event）にも直接応用可能なスキルです。**

以下の4つの補完的な分析アプローチを含みます：

1.  **データユーティリティ:** 欠損した稼働率データを推定し、補完する。
2.  **生存時間分析:** KMF、Cox PH、AFTモデルを稼働率補正された指標で実行。
3.  **静的DiD分析:** 標準的なDiD（OLS/GLM）による全体効果の定量化。
4.  **動的DiD分析:** イベントスタディによるトレンドの視覚化。

機密保持のため、本プロジェクトでは\*\*「パン工場」のたとえ話\*\*を用いて、実際の製造データを使わずに分析ロジックを実証しています。

-----

## 🥐 たとえ話：パン工場

### 背景と課題

パンが焦げる（故障）のを防ぐため、オーブンに「AI温度制御器」を導入しました。しかし、以下の課題により単純な比較ができません。

1.  **稼働率のばらつき:** フル稼働のオーブンと、たまにしか使わないオーブンを「時間」で比較するのは不公平です。
      - *解決策:* **Normalized MTBF**を導出します。**「実効分母（Effective Denominator）」**（材料消費量/パンの製造数）を用いてMTBFを正規化します。
2.  **導入時期のずれ:** 1月導入、3月導入などバラバラです。
      - *解決策:* **相対時間 ($K$)** を用いた Staggered DiD モデルで評価します。

#### 誤った仮定と解決への経緯：データ欠損への対応

当初、すべてのオーブンが常に稼働していると仮定してDiD分析を行ったところ、**結果が不安定でおかしいことに気づきました。これは、すべての装置が等しく稼働しているという前提（稼働率）が間違っていた**ためです。

**データ欠損という課題**：そこで必要な「パンの製造数」データが、古い期間や一部のオーブンで欠損していることが分かりました。

この課題を克服するため、私たちは補助データを利用する手法を開発しました。**「データがある期間の電力消費量（RF時間相当）」と「製造数」の関係を学習**し、**オーブンの洗浄履歴**などの二次データから欠損期間の製造数を**推定**することで、稼働率補正を全期間にわたり強固に適用することを可能にしました。

-----

## 🛠 収録スクリプトと分析手法

### 1\. `main_hybrid_utilization.py`（データユーティリティ）

**目的:** データ欠損の課題を解決し、欠損した製造数（パンの数）を推定して埋めるためのユーティリティです。

  - **ロジック:** データ豊富な期間で\*\*材料消費量（Proxy Input）**と**パンの製造数（Output）\*\*の比率を学習します。この学習した比率を使い、Proxyデータしかない期間の製造数を推定し、分析用のデータセット（`Production_Imputed`）を準備します。

### 2\. `main_survival_analysis.py`（生存時間分析）

期間指標とリスクモデルの推定に焦点を当てています。このスクリプトは、稼働率補正済みの期間指標である \*\*MTBF（平均故障間隔）\*\*を算出します。

#### 右打ち切り（Right-Censoring）の考慮

分析では、**右打ち切り**のデータを考慮しています。右打ち切りとは、観測終了時点までに故障（イベント）が発生しなかった場合を指します。これらのデータも `Event = 0` として組み込むことで、母集団のリスクを正確に推定し、バイアスを防いでいます。

| Model | Goal (English) | Role in this Project (Japanese) |
| :--- | :--- | :--- |
| **KMF** (Kaplan-Meier) | Estimates the **Survival Function** (non-parametric). | **視覚的な比較:** 新旧デバイス間のMTBF（故障間隔）の分布をグラフで示します。 |
| **Cox PH** (Proportional Hazards) | Estimates the **Hazard Ratio** (risk ratio, semi-parametric). | **リスク低減の定量化:** 新デバイス導入による**故障リスクの減少率**を推定します。 |
| **Weibull AFT** (Accelerated Failure Time) | Estimates the **Acceleration Factor** (lifespan ratio, parametric). | **寿命の定量化:** 新デバイス導入による**MTBF**の延長率を推定します。 |

### 3\. `main_analysis.py`（静的DiD分析）

標準的なTWFE構造を用い、全体的な平均治療効果（ATT）の定量化に焦点を当てています。

#### Two-Way Fixed Effects (TWFE) の役割

TWFEモデルは、パネルデータ（装置×時間）における**未観測の交絡因子**をコントロールするために、固定効果（ダミー変数）を導入します。

| 固定効果の種類 | 制御する未観測の要因 | このプロジェクトでの対応 |
| :--- | :--- | :--- |
| **Entity Fixed Effects** | 装置固有の要因（例：設置場所の環境、初期性能など） | **装置**ごとの固定効果（`C(Tool)` または `C(group)`）により制御 |
| **Time Fixed Effects** | 全装置に共通する要因（例：サイト全体での停電、コンポーネント供給遅延など） | **時間**ごとの固定効果（`C(Month)` または `C(Date)`）により制御 |

  - **Staggered DiDの実装:** 個体固有の導入時期に合わせた `Post` 変数のタイミング設定が、OLSとGLMの両方に適用されます。
  - **連続値の結果（MTBF）:** OLS回帰を実行します。
  - **カウント値の結果（Rate）:** 負の二項分布GLMを実行し、稼働率の正規化のために `log(生産量)` のオフセットを利用します。

### 4\. `main_event_study.py`（動的分析）

効果のタイミングとトレンドの可視化に焦点を当てています。

  - **Event Study (PanelOLS):** 導入前後における効果の推移を可視化します。
  - **平行トレンドの検証:** 導入前 ($K < 0$) の係数が0付近であれば、比較が妥当であると判断できます。

-----

## 💻 Usage

### 実行

プロジェクトは、データユーティリティから実行する4ステップのワークフローをとります。

```bash
# ステップ 1: ハイブリッド推定（欠損データの補完）
python main_hybrid_utilization.py

# ステップ 2: 生存分析（リスクモデリング）の実行
python main_survival_analysis.py

# ステップ 3: 静的DiD分析（因果効果の定量化）の実行
python main_analysis.py

# ステップ 4: 動的分析（イベントスタディ）の実行
python main_event_study.py
```

-----

## 👨‍💻 Author

**佐藤 剛 (Go Sato)**
データサイエンティスト | 外資系半導体装置メーカー AI部
因果推論、生存時間分析、および信頼性工学を専門としています。
