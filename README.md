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
    - *Solution:* We normalize metrics using **"Effective Denominator"** (Production Count / Wafer Count).
2.  **Staggered Installation:** Controllers were installed at different times (Jan, Mar, Jun...).
    - *Solution:* We align data using **Relative Time ($K$)** and use Staggered DiD / Event Study models.

---

## 🛠 Included Scripts & Methodology

### 1. `main_analysis.py` (Static Analysis)
Focuses on quantifying the overall effect and survival probability.
- **Survival Analysis (Lifelines):**
    - Kaplan-Meier curves based on production volume.
    - Cox Proportional Hazards & Weibull AFT models to estimate risk reduction.
- **Staggered DiD (GLM-NB):**
    - Negative Binomial Regression to estimate the overall Rate Ratio (RR).

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
Data Analyst | Production Engineering
Specializing in Causal Inference, Survival Analysis, and Reliability Engineering.

<br>
<br>
<br>

-----

## Japanese Description

## *(以下、日本語の説明)*

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
      - *解決策:* **「実効分母（Effective Denominator）」**（生産数/Wafer枚数）を用いて指標を正規化します。
2.  **導入時期のずれ:** 1月導入、3月導入などバラバラです。
      - *解決策:* **相対時間 ($K$)** を用いた Staggered DiD モデルで評価します。

-----

## 🛠 収録スクリプトと分析手法

### 1\. `main_analysis.py`（静的分析）

全体的な効果量と生存確率の推定に焦点を当てています。

  - **生存時間分析:** 生産量ベースのカプラン・マイヤー曲線、Cox比例ハザードモデルによるリスク低減率の算出。
  - **Staggered DiD:** 負の二項分布モデルを用いた、導入による全体的な改善率（Rate Ratio）の推定。

### 2\. `main_event_study.py`（動的分析）

効果のタイミングとトレンドの可視化に焦点を当てています。

  - **イベントスタディ (PanelOLS):** 導入前後における効果の推移を可視化します。
  - **平行トレンドの検証:** 導入前 ($K < 0$) の係数が0付近であれば、比較が妥当であると判断できます。
  - **効果の持続性:** 導入後 ($K \ge 0$)、効果が即座に出るか、徐々に出るかを確認できます。

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

## 👨‍💻 著者

**佐藤 剛 (Go Sato)**
データアナリスト | 生産技術
因果推論、生存時間分析、および信頼性工学を専門としています。
