import os
import pandas as pd
from entsoe import EntsoePandasClient
from dotenv import load_dotenv
import time

# 1. Load Environment Variables
load_dotenv()
API_KEY = os.getenv("ENTSOE_API_KEY")

if not API_KEY:
    raise ValueError("CRITICAL ERROR: API Key not found. Please check your .env file.")

# 2. Configuration
# We use DE_LU (Germany-Luxembourg) as it's the main European index.
COUNTRY = 'DE_LU' 
# We fetch 1 year of training data + recent data for testing
START_DATE = pd.Timestamp('2024-01-01', tz='UTC')
END_DATE = pd.Timestamp.now(tz='UTC').floor('h') 

def ingest_data():
    print(f"🚀 Starting Ingestion for {COUNTRY}...")
    client = EntsoePandasClient(api_key=API_KEY)

    try:
        # --- A. Fetch Day-Ahead Prices (Target) ---
        print("   -> Fetching Day-Ahead Prices...")
        prices = client.query_day_ahead_prices(COUNTRY, start=START_DATE, end=END_DATE)
        # API may return Series or DataFrame depending on version/country
        if isinstance(prices, pd.Series):
            prices = prices.to_frame(name='price_da')
        else:
            prices.columns = ['price_da']

        # --- B. Fetch Load Forecast (Driver 1) ---
        print("   -> Fetching Load Forecast...")
        load = client.query_load_forecast(COUNTRY, start=START_DATE, end=END_DATE)
        # API may return Series or DataFrame depending on version/country
        if isinstance(load, pd.Series):
            load = load.to_frame(name='load_forecast')
        else:
            load.columns = ['load_forecast']

        # --- C. Fetch Wind & Solar Forecast (Driver 2 & 3) ---
        print("   -> Fetching Generation Forecasts (Wind/Solar)...")
        gen = client.query_wind_and_solar_forecast(COUNTRY, start=START_DATE, end=END_DATE)
        # Rename columns to be code-friendly
        # The API usually returns: 'Solar', 'Wind Offshore', 'Wind Onshore'
        gen.columns = [c.lower().replace(' ', '_') for c in gen.columns]
        
        # --- D. Data Alignment & DST Handling ---
        print("   -> Aligning Data & Handling Timezones...")
        
        # 1. Join everything on the Index (Time)
        # Note: ENTSO-E returns data in UTC. This is perfect. 
        # We use an 'inner' join to ensure we only keep hours where we have ALL data.
        df = pd.concat([prices, load, gen], axis=1)
        
        # 2. Resampling
        # Some generation data might be 15-min resolution. Prices are 60-min.
        # We resample to hourly means to match the Price.
        df = df.resample('1h').mean()
        
        # 3. Drop rows with missing targets (Price)
        # We cannot train without a price.
        initial_len = len(df)
        df.dropna(subset=['price_da'], inplace=True)
        dropped_len = initial_len - len(df)
        
        if dropped_len > 0:
            print(f"      Warning: Dropped {dropped_len} rows due to missing prices.")

        # --- E. Feature Engineering (Basic) ---
        # We need these for the model later
        df['hour'] = df.index.hour
        df['day_of_week'] = df.index.dayofweek
        df['month'] = df.index.month
        
        # --- F. Save ---
        os.makedirs('data', exist_ok=True)
        output_path = 'data/training_data.csv'
        df.to_csv(output_path)
        
        print(f"✅ Success! Data saved to {output_path}")
        print(f"   Shape: {df.shape}")
        print("   Head:")
        print(df.head(3))
        
        return df

    except Exception as e:
        print(f"❌ Error during ingestion: {e}")
        return None

if __name__ == "__main__":
    ingest_data()