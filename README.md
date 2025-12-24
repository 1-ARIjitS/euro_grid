# Euro Grid

European power grid price forecasting using ENTSO-E data.

## Overview

This project fetches day-ahead electricity price data and generation forecasts from the ENTSO-E Transparency Platform for the Germany-Luxembourg (DE_LU) market zone.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API key:**
   
   Create a `.env` file in the project root:
   ```
   ENTSOE_API_KEY=your_api_key_here
   ```
   
   Get your API key from: https://transparency.entsoe.eu/

## Usage

### Data Ingestion
```bash
python src/ingest.py
```
Fetches day-ahead prices, load forecasts, and wind/solar generation data from ENTSO-E.

### Quality Assurance
```bash
python src/qa.py
```
Runs data quality checks and generates visualization plots.

## Project Structure

```
├── src/
│   ├── ingest.py    # Data fetching from ENTSO-E API
│   └── qa.py        # Data quality assurance & visualization
├── data/            # Generated data files (gitignored)
├── requirements.txt
└── README.md
```

## Data Sources

- **ENTSO-E Transparency Platform** - Day-ahead prices, load forecasts, wind & solar generation forecasts
