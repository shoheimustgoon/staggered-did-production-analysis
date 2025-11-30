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
... (Unchanged English Analogy) ...

---

## 🛠 Included Scripts & Methodology

### 1. `main_survival_analysis.py` (Survival Analysis)
Focuses on the duration metric and risk modeling. This script calculates the **WBF (Work Between Failures)**, which is the utilization-corrected duration metric.

| Model | Goal (English) | Role in this Project (Japanese) |
| :--- | :--- | :--- |
| **KMF** (Kaplan-Meier) | Estimates the **Survival Function** (non-parametric). | **視覚的な比較:** 新旧デバイス間のWBF（故障間隔）の分布をグラフで示します。 |
| **Cox PH** (Proportional Hazards) | Estimates the **Hazard Ratio** (risk ratio, semi-parametric). | **リスク低減の定量化:** 新デバイス導入による**故障リスクの減少率**を推定します。 |
| **Weibull AFT** (Accelerated Failure Time) | Estimates the **Acceleration Factor** (lifespan ratio, parametric). | **寿命の定量化:** 新デバイス導入による**WBFの延長率**を推定します。 |

### 2. `main_analysis.py` (Static DiD Analysis)
Focuses on quantifying the overall Average Treatment Effect (ATT) using the standard **Two-Way Fixed Effects (TWFE)** structure.

#### Two-Way Fixed Effects (TWFE) の役割
TWFEモデルは、パネルデータ（装置×時間）における**未観測の交絡因子**をコントロールするために、固定効果（ダミー変数）を導入します。

| 固定効果の種類 | 制御する未観測の要因 | このプロジェクトでの対応 |
| :--- | :--- | :--- |
| **Entity Fixed Effects** | 装置固有の要因（例：設置場所の環境、初期性能、担当チームの習熟度など） | **装置**ごとの固定効果（`C(Tool)` または `C(group)`）により制御 |
| **Time Fixed Effects** | 全装置に共通する要因（例：サイト全体での停電、全社的なコンポーネント供給遅延、季節性） | **時間**ごとの固定効果（`C(Month)` または `C(Date)`）により制御 |

**利用場面:** ユニット（装置）間でベースラインが異なり、かつ時間を通じて全ユニットに共通の影響（ショック）がある場合に、因果効果（ATT）をより頑健に推定するために利用されます。

- **Staggered DiD Implementation:** The core staggered logic (unit-specific `Post` variable timing) is applied to both OLS and GLM.
- **Continuous Outcomes (WBF/MTBF):** Uses **OLS** regression.
- **Count Outcomes (Rate):** Uses **Negative Binomial GLM** with the `log(Production)` offset for utilization normalization.

### 3. `main_event_study.py` (Dynamic Analysis)
Focuses on visualizing the timing of the effect and checking the Parallel Trend assumption.

#### Event Study (動的DiD) の役割
Event Studyは、**TWFEモデルの構造**を利用しつつ、介入（アップグレード）からの**相対時間 ($K$)**をダミー変数として投入することで、効果の推移を時間軸で可視化する手法です。

- **Event Study (PanelOLS):** Visualizes the causal impact trend before and after installation.
- **Parallel Trend Check:** Verifies if the pre-installation trend ($K < 0$) is flat (validating the causal assumption, which is the key assumption of DiD models).
- **Dynamics:** Shows whether the improvement is immediate or gradual ($K \ge 0$).

---

## 💻 Usage

### Prerequisites
- Python 3.8+
- Libraries: `pandas`, `numpy`, `matplotlib`, `seaborn`, `lifelines`, `statsmodels`, `linearmodels`

### Running the Analysis
Both scripts contain a **Dummy Data Generator**, so they can be executed immediately.

#### Run Survival Analysis (KMF, Cox, AFT)
```bash
python main_survival_analysis.py
