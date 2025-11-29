# Impact Analysis of Manufacturing Equipment Upgrade (Staggered DiD & Survival Analysis)

## 📖 Overview
This project is a Python-based analytical framework designed to verify the effectiveness of new equipment components in a manufacturing environment. It addresses complex real-world conditions such as **staggered installation dates** and **varying equipment utilization rates**.

To ensure data confidentiality, this project uses a **"Bread Factory" analogy** to demonstrate the analytical logic without exposing sensitive production data.

---

## 🥐 The Analogy: The Bread Factory

### The Context
- **The Factory:** A large factory producing bread with 20 industrial ovens (Tools).
- **The Upgrade:** A new "AI Temperature Controller" was installed to prevent bread from burning (Failures).
- **The Goal:** To statistically prove that the new controller reduces the failure rate and extends the time between failures.

### The Challenges

#### 1. Varying Utilization Rates
- **Problem:** Oven A runs 24 hours a day. Oven B runs only 2 hours a day.
- **Why simple MTBF fails:** If we measure "Time Between Failures" using simple clock hours, Oven B appears to have a very long life simply because it is rarely used. This is unfair.
- **Solution:** We introduced the concept of **"Effective Denominator"**. Instead of measuring time, we measure **"Loaves Baked" (Production Count)**. We calculate the survival rate based on how much work the oven actually performed.

#### 2. Staggered Installation
- **Problem:** The new controllers were not installed on all ovens at once. Some got them in January, some in March, and others in June.
- **Solution:** We use **Staggered Difference-in-Differences (DiD)** analysis. This allows us to compare the "Treatment Group" (Upgraded) vs. "Control Group" (Old) correctly, even when the "After" period starts at different times for each oven.

---

## 🛠 Methodology

### 1. Data Processing with Utilization Weighting
Calculates utilization rates based on daily production logs. Converts "Calendar Time" into "Normalized Operating Hours" or uses "Production Count" directly as the duration metric.

### 2. Survival Analysis (Lifelines)
- **Kaplan-Meier Estimator:** Visualizes the survival curve (probability of running without failure) based on production volume.
- **Cox Proportional Hazards Model:** Quantifies the hazard ratio (risk reduction).
- **Weibull AFT (Accelerated Failure Time) Model:** Estimates the acceleration factor (how much the lifespan is extended).

### 3. Staggered DiD (Statsmodels)
- Uses **Generalized Linear Models (GLM)** with **Negative Binomial Distribution** to handle count data (rare failure events).
- Verifies **Parallel Trends** assumption to ensure causal validity.
- Calculates the pure effect of the upgrade on error rates.

---

## 💻 Usage

### Prerequisites
- Python 3.8+
- Libraries: `pandas`, `numpy`, `matplotlib`, `seaborn`, `lifelines`, `statsmodels`

### Running the Analysis
The script includes a **Dummy Data Generator**, so you can run it immediately without external data.

```bash
python main_analysis.py
````

This will generate:

1.  **Dummy Data:** Installation logs, Production logs, Error logs.
2.  **Analysis Report:** Utilization metrics, Survival Analysis results, and DiD statistics.
3.  **Visualizations:** `survival_plot.png`, `did_trend_plot.png`.

-----

## 👨‍💻 Author

**Go Sato**
Data Analyst | Production Engineering
Specializing in statistical analysis for manufacturing process improvement.

## 🇯🇵 日本語の説明 (Japanese Description Follows)

-----

# 製造装置のアップグレードによる導入効果分析（Staggered DiD および 生存時間分析）

## 📖 概要

本プロジェクトは、製造現場における新規コンポーネントの導入効果を検証するためのPython分析フレームワークです。**導入時期が装置ごとに異なる点**や、**装置ごとの稼働率のばらつき**といった、実世界の複雑な条件に対応しています。

機密保持のため、本プロジェクトでは\*\*「パン工場」のたとえ話\*\*を用いて、実際の製造データを使わずに分析ロジックを実証しています。

-----

## 🥐 たとえ話：パン工場

### 背景

  - **工場:** 20台の工業用オーブン（装置）を持つ大規模なパン工場。
  - **アップグレード:** パンが焦げる（故障）のを防ぐため、新しい「AI温度制御器」を導入。
  - **目的:** 新しい制御器が故障率を下げ、故障間隔を延ばしていることを統計的に証明すること。

### 課題

#### 1\. 稼働率のばらつき

  - **問題点:** オーブンAは24時間フル稼働ですが、オーブンBは1日2時間しか稼働しません。
  - **単純なMTBFの失敗:** 単純な「時間」で故障間隔を測ると、滅多に使われないオーブンBが長寿命であるかのように見えてしまいます。これは不公平です。
  - **解決策:** \*\*「実効分母 (Effective Denominator)」**の概念を導入しました。時間ではなく**「焼いたパンの数（生産数）」\*\*を基準にします。オーブンが実際にどれだけの仕事をしたかに基づいて生存率を計算します。

#### 2\. 導入時期のずれ (Staggered Installation)

  - **問題点:** 新しい制御器は一斉に導入されたわけではありません。1月に導入されたものもあれば、3月、6月のものもあります。
  - **解決策:** \*\*Staggered DiD（時期不一致の差分の差分法）\*\*を使用しました。これにより、各オーブンで「導入後」の開始時期が異なっていても、処置群（導入済み）と対照群（未導入）を正しく比較することができます。

-----

## 🛠 分析手法

### 1\. 稼働率による重み付けデータ処理

日々の生産ログに基づいて稼働率を算出します。「カレンダー時間」を「正規化された稼働時間」に変換するか、あるいは「生産数」そのものを期間の指標として使用します。

### 2\. 生存時間分析 (Lifelines)

  - **カプラン・マイヤー推定:** 生産量に基づく生存曲線（故障せずに稼働し続ける確率）を可視化。
  - **Cox比例ハザードモデル:** ハザード比（リスク低減率）を定量化。
  - **Weibull AFT（加速寿命）モデル:** 加速係数（寿命がどれだけ延びたか）を推定。

### 3\. Staggered DiD (Statsmodels)

  - **負の二項分布**を用いた\*\*一般化線形モデル（GLM）\*\*を使用し、カウントデータ（稀な故障イベント）を適切に扱います。
  - \*\*平行トレンド（Parallel Trends）\*\*の仮定を検証し、因果推論の妥当性を担保します。
  - アップグレードによるエラー率への純粋な効果を算出します。

-----

## 💻 使用方法

### 必須環境

  - Python 3.8以上
  - ライブラリ: `pandas`, `numpy`, `matplotlib`, `seaborn`, `lifelines`, `statsmodels`

### 実行

スクリプトには**ダミーデータ生成機能**が含まれているため、外部データなしですぐに実行可能です。

```bash
python main_analysis.py
```

実行すると以下が生成されます：

1.  **ダミーデータ:** 導入ログ、生産ログ、エラーログ。
2.  **分析レポート:** 稼働率指標、生存時間分析結果、DiD統計量。
3.  **可視化グラフ:** `survival_plot.png`, `did_trend_plot.png`。

-----

## 👨‍💻 著者

**佐藤剛**
データアナリスト | 生産技術
製造プロセスの改善に向けた統計分析を専門としています。
