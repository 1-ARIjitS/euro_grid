# European Power Grid Forecasting — Day-Ahead Price Forecasting (France, FR)

**Author:** ARIJIT SAMAL  
**Email:** arijit.samal@student-cs.fr  
**Date:** 30 December 2025  
**Primary artifact:** `euro_grid_forecast.ipynb`

---

## Executive Summary

This submission contains an end-to-end pipeline for forecasting **hourly day-ahead electricity prices** using public ENTSO‑E Transparency Platform data for **France (FR)**. The notebook covers ingestion, QA/cleaning, EDA, feature engineering, model training with time-series validation, signal translation (prompt curve), and exports a `submission.csv` for the defined out-of-sample test window.

**Key Results:**
- **Best model (per `outputs/model_comparison_full.csv`)**: **LightGBM** with **MAE = 5.58 €/MWh**, **RMSE = 7.35 €/MWh**, **R² = 0.9283** on the out-of-sample test window.
- **Test window (out-of-sample)**: last **30 days** of the dataset; `submission.csv` contains **720 hourly predictions** from **2025‑11‑30 00:00:00** to **2025‑12‑29 23:00:00**.
- **Programmatic AI component**: LangGraph + LangChain workflow that generates QA rules from schema + sample rows, executes them, and produces a professional QA report with full prompt/output logging.

---

## 1. Pipeline Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Data Ingestion │ ─▶ │  Data Quality   │ ─▶ │       EDA       │ ─▶ │   Forecasting   │
│   (ENTSO-E API) │    │   (QA Checks)   │    │  (Visualization)│    │   (ML Models)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
                                                                              │
                       ┌─────────────────┐    ┌─────────────────┐             ▼
                       │   LLM-Driven    │ ◀─ │  Prompt Curve   │ ◀─ ┌─────────────────┐
                       │   QA Report     │    │   Translation   │    │   Submission    │
                       └─────────────────┘    └─────────────────┘    │   (CSV Export)  │
                                                                     └─────────────────┘
```

---

## 2. Data Ingestion (Section 2)

### Data Sources
| Data Type | ENTSO-E Code | Granularity | Role |
|-----------|--------------|-------------|------|
| Day-Ahead Prices | A44 | Hourly | **TARGET** |
| Load Forecast | A65 | Hourly | Driver 1 |
| Wind Forecast | A69 | Hourly | Driver 2 |
| Solar Forecast | A69 | Hourly | Driver 3 |

### Implementation
- **API Client:** `entsoe-py` library
- **Market:** France (FR) bidding zone
- **Period:** rolling 1-year window (configured in notebook `Config`; end date is run-time dependent)
- **Timezone:** Europe/Paris (handles DST automatically)

### Output Dataset (core columns)
The ingestion step produces an hourly DataFrame with:
- `price_da` (target, €/MWh)
- `load_forecast` (MW)
- `wind_forecast` (MW)
- `solar_forecast` (MW)

---

## 3. Data Quality & Cleaning (Section 3)

### Quality Assessment Framework
Comprehensive checks for:
- Missing values per column
- Duplicate timestamps
- Value range validation
- Statistical outlier detection
- Temporal coverage gaps

### Cleaning Operations
- Forward/backward fill for small gaps
- Outlier capping using IQR method
- Timezone normalization

---

## 4. Exploratory Data Analysis (Section 4)

### Key Visualizations
1. **Time Series Analysis** - Price evolution over study period
2. **Distribution Analysis** - Price and driver histograms
3. **Scatter Analysis** - Price vs fundamental drivers
4. **Correlation Matrix** - Feature relationships
5. **Seasonality Decomposition** - Trend, seasonal, residual components

### Key Findings
- Strong negative correlation between renewable generation and prices
- Clear hourly and weekly seasonality patterns
- Price volatility increases during low-wind/low-solar periods

---

## 5. Forecasting Models (Section 5)

### Feature Engineering
The notebook builds features via `create_features(df_clean)` (see Section 5.1). Below is the **complete** engineered feature set (in addition to the raw driver columns).

| Feature Category | Features created in the notebook |
|-----------------|----------------------------------|
| **Raw drivers (inputs)** | `load_forecast`, `wind_forecast`, `solar_forecast` |
| **Temporal (calendar/flags)** | `hour`, `day_of_week`, `day_of_month`, `month`, `is_weekend`, `is_peak`, `is_night`, `is_solar_hour` |
| **Cyclical encoding** | `hour_sin`, `hour_cos`, `dow_sin`, `dow_cos`, `month_sin`, `month_cos` |
| **Price lag features** | `price_lag_1h`, `price_lag_2h`, `price_lag_3h`, `price_lag_24h`, `price_lag_48h`, `price_lag_72h`, `price_lag_168h` |
| **Driver lag features (24h)** | `load_forecast_lag_24h`, `wind_forecast_lag_24h`, `solar_forecast_lag_24h` |
| **Rolling price statistics (24h)** | `price_roll_mean_24h`, `price_roll_std_24h`, `price_roll_min_24h`, `price_roll_max_24h` |
| **Rolling price statistics (168h)** | `price_roll_mean_168h`, `price_roll_std_168h`, `price_roll_min_168h`, `price_roll_max_168h` |
| **Domain features** | `residual_demand`, `renewable_gen`, `renewable_share`, `load_factor` |
| **Interaction features** | `load_x_peak`, `solar_x_hour`, `wind_x_night`, `residual_x_peak` |
| **Price momentum** | `price_momentum_24h`, `price_momentum_168h` |

**Target (not a feature):** `price_da` (day-ahead price, €/MWh).  
**Note:** after feature creation, rows with missing lag/rolling values are dropped (`df_feat = df_feat.dropna()`), ensuring models train on fully-defined feature vectors.

### Models Evaluated
| Model | Type | Hyperparameter Tuning |
|-------|------|----------------------|
| Seasonal Naive (t-24h) | Baseline | - |
| Last-Week-Same-Day (t-168h) | Baseline | - |
| Linear Regression | Baseline | - |
| Ridge/Lasso/ElasticNet | Regularized | GridSearchCV |
| Random Forest | Ensemble | GridSearchCV |
| Gradient Boosting | Ensemble | GridSearchCV |
| LightGBM | Gradient Boosting | GridSearchCV |
| XGBoost | Gradient Boosting | GridSearchCV |

### Validation Strategy
- **Walk-Forward Validation:** 5-fold TimeSeriesSplit
- **Train/Test split:** `split_date = df_features.index.max() - pd.Timedelta(days=30)`; train ≤ split_date, test > split_date
- **Test Period:** last 30 days (out-of-sample)
- **Metrics:** MAE, RMSE, R², MAPE, P95 Error

### Best Model (from notebook outputs)
Per `outputs/model_comparison_full.csv`, the best overall model is:
- **Model:** 11. LightGBM
- **Test MAE:** 5.58 €/MWh
- **Test RMSE:** 7.35 €/MWh
- **Test R²:** 0.9283
- **Best params:** `{'learning_rate': 0.1, 'max_depth': 5, 'n_estimators': 200}`

---

## 6. Prompt Curve Translation (Section 6)

### Trading Signal Generation
Converts hourly forecasts into actionable trading views:

| Signal | Condition | Action |
|--------|-----------|--------|
| LONG | Fair Value > Market + Band | Buy futures |
| SHORT | Fair Value < Market - Band | Sell futures |
| NO TRADE | Within confidence band | Wait |

### Backtesting Results
- Simulated P&L using 1 MWh position per signal
- Coverage calibration (95% target vs actual)
- Sharpe ratio and maximum drawdown analysis

---

## 7. LLM-Driven Data Quality Assurance (Section 7)

### AI as Engineering Multiplier
This section demonstrates **programmatic AI integration using LangGraph** to reduce manual QA work: given a schema and sample rows, an LLM proposes validation rules, the pipeline executes them, and another LLM call generates a professional QA report.

### Workflow
```
analyze_schema → generate_rules (LLM) → run_checks → create_report (LLM)
```

### Implementation Details
| Requirement | Implementation |
|-------------|----------------|
| LLM called from code | `ChatOpenAI` via LangChain |
| Prompts logged | `llm_log` in notebook + persisted log file |
| Outputs logged | `llm_log` in notebook + persisted log file |
| Failure modes logged | Error handling with fallbacks |
| No secrets committed | `os.getenv('OPENAI_API_KEY')` |
| Workflow orchestration | LangGraph `StateGraph` |

### LangGraph Nodes
1. **analyze_schema** - Extract DataFrame schema + 20 random sample rows
2. **generate_rules** - LLM proposes validation rules as `(pandas_code, explanation)` tuples
3. **run_checks** - Execute pandas code, collect results
4. **create_report** - LLM generates professional QA report

### Output Files
- `reports/llm_qa_report.json` - Complete QA artifact (rules, results, report, audit log)
- `reports/llm_qa_report.md` - Rendered QA report (Markdown)
- `logs/llm_qa_pipeline.log` - LLM interaction audit trail (prompts, outputs, errors)

### LLM Configuration (as implemented in notebook)
- **Environment variable:** `OPENAI_API_KEY`
- **LLM wrapper:** `langchain_openai.ChatOpenAI`
- **Configured model (see Section 7 code):** `gpt-5-mini` (model string is configurable in one place)

---

## 8. Submission File (Section 8)

### File: `submission.csv`
| Column | Description | Format |
|--------|-------------|--------|
| `id` | Timestamp identifier | `YYYY-MM-DD HH:MM:SS` |
| `y_pred` | Predicted price | Float (€/MWh) |

### Test Window
- **Period:** Last 30 days of data
- **Granularity:** Hourly predictions
- **Total Rows:** 720 (30 days × 24 hours)
- **ID range:** 2025‑11‑30 00:00:00 → 2025‑12‑29 23:00:00

---

## Repository Structure

```
euro_grid/
├── .gitignore                  # Git ignore rules (keeps logs/data/secrets out of commits)
├── .env                        # Local environment variables (NOT committed; contains API keys)
├── euro_grid_forecast.ipynb    # Main notebook
├── LICENSE                     # License file
├── submission.csv              # Out-of-sample predictions
├── requirements.txt            # Dependencies
├── README.md                   # Project documentation
├── SUBMISSION.md               # This document
├── data/                       # Raw/intermediate data (generated/downloaded by notebook)
├── models/                     # Saved model artifacts (if persisted)
├── outputs/                    # Saved charts + model comparison CSV (generated by notebook)
├── reports/                    # QA report artifacts (generated by notebook)
└── logs/                       # Pipeline + LLM logs (generated by notebook; typically gitignored)
```

---

## Conclusion

This pipeline demonstrates:
1. **End-to-end ML workflow** from data ingestion to deployment-ready predictions
2. **Rigorous validation** with walk-forward cross-validation
3. **AI augmentation** using LLMs to automate data quality assessment
4. **Production-ready outputs** with clear submission format

The LangGraph QA component is explicitly engineered as an “AI multiplier”: it produces rules from schema + samples, executes them deterministically, and logs prompts/outputs/errors for auditability reducing manual QA effort while preserving reproducibility.