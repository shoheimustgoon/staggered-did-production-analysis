# Impact Analysis of Manufacturing Equipment Upgrade (Staggered DiD & Event Study)

> **[🇯🇵 日本語の説明はこちら (Click here for Japanese Description)](#japanese-description)**

## 📖 Overview
This project is a Python-based analytical framework designed to verify the effectiveness of new equipment components in a manufacturing environment. It addresses complex real-world conditions such as **staggered installation dates** and **varying equipment utilization rates**.

It includes two complementary analytical approaches:
1.  **Static Analysis:** Survival Analysis & Standard Staggered DiD.
2.  **Dynamic Analysis:** Event Study (Dynamic DiD) to visualize trends over time.

To ensure data confidentiality, this project uses a **"Bread Factory" analogy** to demonstrate the analytical logic without exposing sensitive production data.

---

## 🥐 The Analogy: The Bread Factory

### The Context
- **The Factory:** A large factory producing bread with 20-40 industrial ovens (Tools).
- **The Upgrade:** A new "AI Temperature Controller" was installed to prevent bread from burning (Failures).
- **The Goal:** To statistically prove that the new controller reduces the failure rate.

### The Challenges
1.  **Varying Utilization:** Oven A runs 24/7, while Oven B runs only 2 hours. Simple "Time Between Failures" is unfair.
    - *Solution:* We normalize metrics using **"Effective Denominator"** (Production Count / Production Volume).
2.  **Staggered Installation:** Controllers were installed at different times (Jan, Mar, Jun...).
    - *Solution:* We align data using **Relative Time ($K$)** and use Staggered DiD / Event Study models.

---

## 🛠 Included Scripts & Methodology

### 1. `main_analysis.py` (Static Analysis)
Focuses on quantifying the overall effect and survival probability. このスクリプトは、連続値（WBF/MTBF）およびカウント（Rate）の両方の結果に適用可能な**Staggered Difference-in-Differences (DiD)**手法を実装しています。

#### Staggered DiD Implementation (TWFE Structure)
The core of the staggered implementation is defining the treatment indicator variable, `Post`, based on the individual unit's installation date. This establishes the necessary **Two-Way Fixed Effects (TWFE) DiD structure** to estimate the Average Treatment Effect (ATT) across all units.

* **Logic:** The `Post` variable is set to `1` only when the current date is **greater than or equal to the unit’s `Install_Date`**. This ensures the "After" period starts at the correct, staggered time for each unit.
* **Continuous Outcomes (WBF/MTBF):** Uses **OLS** regression with the TWFE structure. $$Y = \beta_0 + \beta_1 \cdot \text{Treated} + \beta_2 \cdot \text{Post} + \beta_3 \cdot (\text{Treated} \times \text{Post}) + \epsilon$$
* **Count Outcomes (Rate):** Uses **Negative Binomial GLM** with the same TWFE structure, utilizing the `log(Production)` offset for utilization normalization.

#### Other Analysis in `main_analysis.py`
- **Survival Analysis (WBF/Lifelines):** Uses WBF (**Production Volume**) as the duration metric to measure risk reduction (Cox PH) and lifespan extension (Weibull AFT).

### 2. `main_event_study.py` (Dynamic Analysis)
Focuses on visualizing the timing of the effect.
- **Event Study (PanelOLS):**
    - Visualizes the causal impact trend before and after installation.
    - **Parallel Trend Check:** Verifies if the pre-installation trend ($K < 0$) is flat (validating the causal assumption).
    - **Dynamics:** Shows whether the improvement is immediate or gradual ($K \ge 0$).

---

## 💻 Usage

### Prerequisites
- Python 3.8+
- Libraries: `pandas`, `numpy`, `matplotlib`, `seaborn`, `lifelines`, `statsmodels`, `linearmodels`

### Running the Analysis
Both scripts contain a **Dummy Data Generator**, so they can be executed immediately.

#### Run Static Analysis (Survival & DiD)
```bash
python main_analysis.py
````

*Outputs: `survival_plot.png`, `did_trend_plot.png`, Statistical Summaries*

#### Run Dynamic Analysis (Event Study)

```bash
python main_event_study.py
```

*Outputs: `event_study_Norm_Count_Rate.png`, `event_study_Norm_MTBF.png`*

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

# 製造装置のアップグレードによる導入効果分析（Staggered DiD および Event Study）

## 📖 概要

本プロジェクトは、製造現場における新規コンポーネントの導入効果を検証するためのPython分析フレームワークです。**導入時期が装置ごとに異なる点**や、**装置ごとの稼働率のばらつき**といった、実世界の複雑な条件に対応しています。

以下の2つの補完的な分析アプローチを含みます：

1.  **静的分析:** 生存時間分析 および 通常の Staggered DiD。
2.  **動的分析:** 効果の時系列変化を可視化する Event Study（動的DiD）。

機密保持のため、本プロジェクトでは\*\*「パン工場」のたとえ話\*\*を用いて、実際の製造データを使わずに分析ロジックを実証しています。

-----

## 🥐 たとえ話：パン工場

### 背景と課題

パンが焦げる（故障）のを防ぐため、オーブンに「AI温度制御器」を導入しました。しかし、以下の課題により単純な比較ができません。

1.  **稼働率のばらつき:** フル稼働のオーブンと、たまにしか使わないオーブンを「時間」で比較するのは不公平です。
      - *解決策:* **「実効分母（Effective Denominator）」**（生産数/生産数）を用いて指標を正規化します。
2.  **導入時期のずれ:** 1月導入、3月導入などバラバラです。
      - *解決策:* **相対時間 ($K$)** を用いた Staggered DiD モデルで評価します。

-----

## 🛠 収録スクリプトと分析手法

### 1\. `main_analysis.py`（静的分析）

全体的な効果量と生存確率の推定に焦点を当てています。このスクリプトは、連続値（WBF/MTBF）およびカウント（Rate）の両方の結果に適用可能な\*\*Staggered Difference-in-Differences (DiD)\*\*手法を実装しています。

#### Staggered DiDの実装方法 (TWFE構造)

Staggered実装の核は、介入を示す `Post` 変数（介入後を示す）の定義にあります。この変数は、各ユニットの固有の導入日（`Install_Date`）に基づいて個別に定義されます。

  * **ロジック:** `Post` 変数は、現在の月日が**ユニットの `Install_Date` 以降**である場合にのみ `1` に設定されます。これにより、すべてのStaggered設定における平均的な治療効果（ATT）を推定するための**Two-Way Fixed Effects (TWFE) DiD構造**が確立されます。
  * **連続値の結果（WBF/MTBF）:** **OLS**回帰をTWFE構造で実行します。 $$Y = \beta_0 + \beta_1 \cdot \text{Treated} + \beta_2 \cdot \text{Post} + \beta_3 \cdot (\text{Treated} \times \text{Post}) + \epsilon$$
  * **カウント値の結果（Rate）:** 同じTWFE構造で**負の二項分布GLM**を実行し、稼働率の正規化のために `log(生産量)` のオフセットを利用します。

#### その他の分析 (`main_analysis.py`内)

  - **生存時間分析:** WBF（生産数）を期間の指標として使用し、リスク低減（Cox PH）および寿命延長（Weibull AFT）を測定します。

### 2\. `main_event_study.py`（動的分析）

効果のタイミングとトレンドの可視化に焦点を当てています。

  - **イベントスタディ (PanelOLS):** 導入前後における効果の推移を可視化します。
  - **平行トレンドの検証:** 導入前 ($K < 0$) の係数が0付近であれば、比較が妥当であると判断できます。
  - **効果の持続性:** 導入後 ($K \ge 0$)、効果が即座に出るか、徐々に増えるかを確認できます。

-----

## 💻 使用方法

### 実行

どちらのスクリプトも**ダミーデータ生成機能**を含んでいるため、外部データなしですぐに実行可能です。

```bash
# 静的分析（生存分析・DiD）の実行
python main_analysis.py

# 動的分析（イベントスタディ）の実行
python main_event_study.py
```

-----

## 👨‍💻 Author

**佐藤 剛 (Go Sato)**
データサイエンティスト | 外資系半導体装置メーカー AI部
因果推論、生存時間分析、および信頼性工学を専門としています。
