import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# 1. Seed Catalog: Real Electronics in the Nepali Market with realistic base prices (NPR)
CATALOG = [
    {"brand": "Apple", "model": "iPhone 15 Pro Max 256GB", "base_price": 215000},
    {"brand": "Apple", "model": "MacBook Air M2 8/256GB", "base_price": 165000},
    {"brand": "Samsung", "model": "Galaxy S24 Ultra", "base_price": 199000},
    {"brand": "Samsung", "model": "Galaxy A54 5G", "base_price": 56000},
    {"brand": "Lenovo", "model": "Legion 5 Pro (RTX 4060)", "base_price": 205000},
    {"brand": "Lenovo", "model": "IdeaPad 3 (Core i5)", "base_price": 85000},
    {"brand": "Dell", "model": "XPS 15 (Core i7)", "base_price": 285000},
    {"brand": "Dell", "model": "Inspiron 15 3000", "base_price": 65000},
    {"brand": "Asus", "model": "ROG Zephyrus G14", "base_price": 230000},
    {"brand": "Acer", "model": "Nitro 5 (RTX 3050)", "base_price": 115000},
    {"brand": "OnePlus", "model": "Nord CE 3 Lite", "base_price": 42000},
    {"brand": "Xiaomi", "model": "Redmi Note 13 Pro+", "base_price": 53000},
    {"brand": "Sony", "model": "WH-1000XM5 Headphones", "base_price": 55000},
    {"brand": "HP", "model": "Victus 15", "base_price": 105000}
]

# Promotional text to train your NLP model
DECEPTIVE_TEXTS = [
    "Dashain Dhamaka! 40% OFF!", "Hurry! Only 2 left in stock!", 
    "Flash Sale Ends in 1 Hour!", "Biggest Price Drop of the Year!", 
    "Clearance! Was Rs. {fake_anchor}, Now Rs. {current}!"
]
NORMAL_TEXTS = ["Standard Delivery Available", "In Stock", "1 Year Official Warranty", "Free Shipping"]

def generate_price_history(start_date, days=365):
    dataset = []
    
    # We will create variations of our seed products to hit the ~50,000 row mark
    # 14 products * 10 variations * 365 days = 51,100 rows
    for seed in CATALOG:
        for variation in range(10):
            product_id = f"PROD-{seed['brand'][:3].upper()}-{seed['model'].replace(' ', '')[:5].upper()}-00{variation}"
            current_base = seed["base_price"] * random.uniform(0.95, 1.05) # Slight jitter for different sellers
            
            # State variables for the timeline
            in_deceptive_spike = False
            spike_days_left = 0
            fake_anchor_price = 0
            
            for day in range(days):
                current_date = start_date + timedelta(days=day)
                listed_price = current_base
                is_deceptive = False
                promo_text = random.choice(NORMAL_TEXTS)
                
                # Logic: Inject a deceptive fake anchor spike
                if not in_deceptive_spike and random.random() < 0.02: # 2% chance to start a deceptive cycle
                    in_deceptive_spike = True
                    spike_days_left = random.randint(10, 20) # Spike lasts 10-20 days
                    fake_anchor_price = current_base * random.uniform(1.20, 1.35) # Spike price by 20-35%
                
                if in_deceptive_spike:
                    if spike_days_left > 0:
                        # During the spike, the price is artificially high
                        listed_price = fake_anchor_price
                        spike_days_left -= 1
                    else:
                        # Spike is over, price drops back to normal, but they claim a massive discount
                        in_deceptive_spike = False
                        is_deceptive = True
                        promo_text = random.choice(DECEPTIVE_TEXTS).format(
                            fake_anchor=int(fake_anchor_price), 
                            current=int(current_base)
                        )
                else:
                    # Normal market fluctuation (+/- 1%)
                    listed_price = current_base * random.uniform(0.99, 1.01)

                dataset.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "product_id": product_id,
                    "brand": seed["brand"],
                    "model": seed["model"],
                    "listed_price": round(listed_price, 2),
                    "promotional_text": promo_text,
                    "is_deceptive_anchor": int(is_deceptive) # 1 for True, 0 for False
                })
                
    return dataset

if __name__ == "__main__":
    print("Generating e-commerce timeline data...")
    # Start exactly 1 year ago from today
    start_date = datetime.now() - timedelta(days=365)
    
    # Generate the dataset
    data = generate_price_history(start_date, days=365)
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Save to CSV
    filename = "fact_historical_pricing_dataset_nepal.csv"
    df.to_csv(filename, index=False)
    
    print(f"Success! Generated {len(df)} rows.")
    print(f"File saved as: {filename}")
    
    # Show a quick summary of deceptive vs normal rows
    print("\nDataset Breakdown:")
    print(df['is_deceptive_anchor'].value_counts())