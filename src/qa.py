import pandas as pd
import matplotlib.pyplot as plt

def run_qa():
    print("\n🔍 Starting Data Quality Assurance (QA)...")
    
    # Load Data
    try:
        df = pd.read_csv('data/training_data.csv', index_col=0, parse_dates=True)
    except FileNotFoundError:
        print("❌ Data file not found. Run ingestion.py first.")
        return

    # 1. Missing Values Check
    print("1. Missing Values Report:")
    missing = df.isnull().sum()
    print(missing[missing > 0])
    if missing.sum() == 0:
        print("   -> No missing values found (Clean!).")

    # 2. Duplicate Check
    duplicates = df.index.duplicated().sum()
    print(f"\n2. Duplicate Timestamp Check: {duplicates} duplicates found.")
    
    # 3. Negative Price Check (Outlier/Reality Check)
    # Negative prices are possible in Germany, but we want to know about them.
    neg_prices = df[df['price_da'] < 0]
    print(f"\n3. Negative Prices: {len(neg_prices)} hours found.")
    
    # 4. Visualization (Requirement: "At least 2 figures")
    print("\n4. Generating QA Plots...")
    
    plt.figure(figsize=(15, 5))
    plt.plot(df.index, df['price_da'], label='Price', linewidth=0.5, alpha=0.8)
    plt.title("Data QA: Price History (Check for spikes/gaps)")
    plt.ylabel("EUR/MWh")
    plt.legend()
    plt.savefig('data/qa_price_history.png')
    
    plt.figure(figsize=(15, 5))
    plt.plot(df.index, df['solar'], label='Solar', alpha=0.6)
    plt.plot(df.index, df['wind_onshore'], label='Wind On', alpha=0.6)
    plt.title("Data QA: Renewables Availability")
    plt.ylabel("MW")
    plt.legend()
    plt.savefig('data/qa_renewables.png')
    
    print("✅ QA Complete. Plots saved to 'data/'.")

if __name__ == "__main__":
    run_qa()