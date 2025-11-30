# Impact Analysis of Manufacturing Equipment Upgrade (Survival, Staggered DiD & Event Study)

> **[🇯🇵 日本語の説明はこちら (Click here for Japanese Description)](#japanese-description)**

## 📖 Overview
This project is a Python-based analytical framework designed to verify the effectiveness of new equipment components in a manufacturing environment. It addresses complex real-world conditions such as **staggered installation dates** and **varying equipment utilization rates**.

It includes three complementary analytical approaches:
1.  **Survival Analysis:** KMF, Cox PH, and AFT models using **MTBF** corrected for utilization.
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
1.  **Varying Utilization:** Oven A runs 24/7, while Oven B runs only 2 hours. Simple "Time Between Failures" is unfair.
    - *Solution:* We derive **Normalized MTBF** using **Production Count**. We normalize metrics using **"Effective Denominator"** (Production Count / Production Volume).
2.  **Staggered Installation:** Controllers were installed at different times (Jan, Mar, Jun...).
    - *Solution:* We align data using **Relative Time ($K$)** and use Staggered DiD / Event Study models.

---

## 🛠 Included Scripts & Methodology

### 1. `main_survival_analysis.py` (Survival Analysis)
Focuses on the duration metric and risk modeling. This script uses **MTBF (Mean Time Between Failures)** corrected for utilization as the primary duration metric.

#### 右打ち切り（Right-Censoring）の考慮
分析では、**右打ち切り**のデータを考慮しています。右打ち切りとは、観測終了時点までに故障（イベント）が発生しなかった場合を指します。これらのデータも `Event = 0` として組み込むことで、母集団のリスクを正確に推定し、バイアスを防いでいます。

| Model | Goal (English) | Role in this Project (Japanese) |
| :--- | :--- | :--- |
| **KMF** (Kaplan-Meier) | Estimates the **Survival Function** (non-parametric). | **視覚的な比較:** 新旧デバイス間の**MTBF**（故障間隔）の分布をグラフで示します。 |
| **Cox PH** (Proportional Hazards) | Estimates the **Hazard Ratio** (risk ratio, semi-parametric). | **リスク低減の定量化:** 新デバイス導入による**故障リスクの減少率**を推定します。 |
| **Weibull AFT** (Accelerated Failure Time) | Estimates the **Acceleration Factor** (lifespan ratio, parametric). | **寿命の定量化:** 新デバイス導入による**MTBF**の延長率を推定します。 |

### 2. `main_analysis.py` (Static DiD Analysis)
Focuses on quantifying the overall Average Treatment Effect (ATT) using the standard TWFE structure.
- **Staggered DiD Implementation:** The core staggered logic (unit-specific `Post` variable timing) is applied to both OLS and GLM.
- **Continuous Outcomes (MTBF):** Uses **OLS** regression.
- **Count Outcomes (Rate):** Uses **Negative Binomial GLM** with the `log(Production)` offset for utilization normalization.

### 3. `main_event_study.py` (Dynamic Analysis)
Focuses on visualizing the timing of the effect and checking the Parallel Trend assumption.
- **Event Study (PanelOLS):** Visualizes the causal impact trend before and after installation.
- **Parallel Trend Check:** Verifies if the pre-installation trend ($K < 0$) is flat (validating the causal assumption).
- **Dynamics:** Shows whether the improvement is immediate or gradual ($K \ge 0$).

---

## 💻 Usage
... (Unchanged English Usage) ...

---

## 👨‍💻 Author
**Go Sato**
Data Scientist | AI Department, Semiconductor Equipment Manufacturer
Specializing in Causal Inference, Survival Analysis, and Reliability Engineering.

<br>
<br>
<br>

---
## Japanese Description
---

# 製造装置の導入効果分析（生存分析、Staggered DiD & イベントスタディ）

## 📖 概要
本プロジェクトは、製造現場における新規コンポーネントの導入効果を検証するためのPython分析フレームワークです。**導入時期が装置ごとに異なる点**や、**装置ごとの稼働率のばらつき**といった、実世界の複雑な条件に対応しています。

**この生存分析の核となる手法（Cox PH/AFT）は、薬効の分析や患者の生存期間推定など、医療・製薬分野（Time-to-Event）にも直接応用可能なスキルです。**

以下の3つの補完的な分析アプローチを含みます：
1.  **生存時間分析:** KMF、Cox PH、AFTモデルを稼働率補正された指標で実行。
2.  **静的DiD分析:** 標準的なDiD（OLS/GLM）による全体効果の定量化。
3.  **動的DiD分析:** イベントスタディによるトレンドの視覚化。

機密保持のため、本プロジェクトでは**「パン工場」のたとえ話**を用いて、実際の製造データを使わずに分析ロジックを実証しています。

---

## 🥐 たとえ話：パン工場

### 背景と課題
パンが焦げる（故障）のを防ぐため、オーブンに「AI温度制御器」を導入しました。しかし、以下の課題により単純な比較ができません。

1.  **稼働率のばらつき:** フル稼働のオーブンと、たまにしか使わないオーブンを「時間」で比較するのは不公平です。
    - *解決策:* **Normalized MTBF**を導出します。**「実効分母（Effective Denominator）」**（生産数/生産数）を用いてMTBFを正規化します。
2.  **導入時期のずれ:** 1月導入、3月導入などバラバラです。
    - *解決策:* **相対時間 ($K$)** を用いた Staggered DiD モデルで評価します。

---

## 🛠 収録スクリプトと分析手法

### 1. `main_survival_analysis.py`（生存時間分析）
期間指標とリスクモデルの推定に焦点を当てています。このスクリプトは、稼働率補正済みの期間指標である **MTBF（平均故障間隔）**を算出します。

#### 右打ち切り（Right-Censoring）の考慮
分析では、**右打ち切り**のデータを考慮しています。右打ち切りとは、観測終了時点までに故障（イベント）が発生しなかった場合を指します。これらのデータも `Event = 0` として組み込むことで、母集団のリスクを正確に推定し、バイアスを防いでいます。

| Model | Goal (English) | Role in this Project (Japanese) |
| :--- | :--- | :--- |
| **KMF** (Kaplan-Meier) | Estimates the **Survival Function** (non-parametric). | **視覚的な比較:** 新旧デバイス間の**MTBF**（故障間隔）の分布をグラフで示します。 |
| **Cox PH** (Proportional Hazards) | Estimates the **Hazard Ratio** (risk ratio, semi-parametric). | **リスク低減の定量化:** 新デバイス導入による**故障リスクの減少率**を推定します。 |
| **Weibull AFT** (Accelerated Failure Time) | Estimates the **Acceleration Factor** (lifespan ratio, parametric). | **寿命の定量化:** 新デバイス導入による**MTBF**の延長率を推定します。 |

### 2. `main_analysis.py`（静的DiD分析）
標準的なTWFE構造を用い、全体的な平均治療効果（ATT）の定量化に焦点を当てています。
- **Staggered DiDの実装:** 個体固有の導入時期に合わせた `Post` 変数のタイミング設定が、OLSとGLMの両方に適用されます。
- **連続値の結果（MTBF）:** OLS回帰を実行します。
- **カウント値の結果（Rate）:** 負の二項分布GLMを実行し、稼働率の正規化のために `log(生産量)` のオフセットを利用します。

### 3. `main_event_study.py`（動的分析）
効果のタイミングとトレンドの可視化に焦点を当てています。
- **イベントスタディ (PanelOLS):** 導入前後における効果の推移を可視化します。
- **平行トレンドの検証:** 導入前 ($K < 0$) の係数が0付近であれば、比較が妥当であると判断できます。

---

## 💻 Usage
... (Unchanged Japanese Usage) ...

---

## 👨‍💻 Author
**佐藤 剛 (Go Sato)**
データサイエンティスト | 外資系半導体装置メーカー AI部
因果推論、生存時間分析、および信頼性工学を専門としています。
