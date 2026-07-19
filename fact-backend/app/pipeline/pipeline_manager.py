import sys
import os
import datetime
import mysql.connector
from app.schemas.analysis import AnalysisPayload, AnalysisResponse

# --- Hardcoded Absolute Path to DPD Engine ---
# This ensures Python can explicitly find your DistilBERT model code
DPD_ENGINE_PATH = r"E:\FYP_FACT\DPD-Engine"
if DPD_ENGINE_PATH not in sys.path:
    sys.path.append(DPD_ENGINE_PATH)

try:
    from inference import score_many
except ImportError as e:
    print(f"--- [CRITICAL] Failed to import DPD Engine from {DPD_ENGINE_PATH}: {e} ---")
    # Fallback placeholder if path mismatch occurs during spin-up
    def score_many(texts):
        return [{"deceptive_score": 1.0, "verdict": "Neutral"} for _ in texts]

# Database Configuration (Port 3307)
DB_CONFIG = {
    'host': 'localhost',
    'port': 3307,
    'user': 'root',
    'password': '',
    'database': 'fiscal_db'
}

def safe_float(value) -> float:
    if value is None or str(value).strip() == "":
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def log_current_page_visit(payload: AnalysisPayload, current_date: str):
    data = payload.model_dump() if hasattr(payload, 'model_dump') else payload.dict()
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    insert_query = """
        INSERT INTO scraped_products (
            product_id, source_url, product_name, actual_price, 
            discount_percentage, discounted_price, claimed_anchor, scraped_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    values = (
        str(data.get('productId', data.get('product_id', ''))),
        data.get('url', ''),
        data.get('productName', data.get('product_name', data.get('name', data.get('title', 'Unknown Product')))),
        safe_float(data.get('actualPrice', data.get('actual_price', 0.0))),
        safe_float(data.get('discountPercentage', data.get('discount_percentage', 0.0))),
        safe_float(data.get('discountedPrice', data.get('discounted_price', 0.0))),
        safe_float(data.get('anchorPrice', data.get('anchor_price', 0.0))),
        current_date
    )
    
    cursor.execute(insert_query, values)
    conn.commit()
    cursor.close()
    conn.close()

def fetch_recent_history(product_id: str):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT actual_price, discounted_price, claimed_anchor, scraped_at 
        FROM scraped_products 
        WHERE product_id = %s 
        ORDER BY scraped_at DESC
    """
    cursor.execute(query, (product_id,))
    records = cursor.fetchall()
    cursor.close()
    conn.close()
    return records

def analyze_pricing_deception(current_price: float, current_anchor: float, history: list) -> float:
    """[FISCAL Engine Component] Computes historical price manipulation factor (scaled 0 to 10)."""
    if len(history) <= 1:
        return 0.0

    lookback_records = history[1:4]
    highest_past_price = max(safe_float(r.get('discounted_price')) for r in lookback_records)
    lowest_past_price = min(safe_float(r.get('discounted_price')) for r in lookback_records)
    
    score = 0.0
    # Pattern 1: Artificial Price Gouging prior to markdown (adds up to 4.0 points)
    if highest_past_price > lowest_past_price and lowest_past_price > 0:
        hike_percentage = ((highest_past_price - lowest_past_price) / lowest_past_price)
        if hike_percentage > 0.10:
            score += 4.0

    # Pattern 2: Inflated / Illusionary Anchor Baseline (adds up to 6.0 points)
    if current_anchor > highest_past_price * 1.25 and highest_past_price > 0:
        score += 6.0
        
    return min(score, 10.0)

async def execute_analysis_pipeline(payload: AnalysisPayload) -> AnalysisResponse:
    """Orchestrates combined DistilBERT Model + FISCAL Engine metrics on a 0-10 UI Scale."""
    data = payload.model_dump() if hasattr(payload, 'model_dump') else payload.dict()
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # 1. Store tracking data
    log_current_page_visit(payload, current_date)
    
    # 2. Extract context dimensions
    prod_id = str(data.get('productId', data.get('product_id', '')))
    history = fetch_recent_history(prod_id)
    
    current_discounted = safe_float(data.get('discountedPrice', data.get('discounted_price', 0.0)))
    current_anchor = safe_float(data.get('anchorPrice', data.get('anchor_price', 0.0)))
    
    # 3. Component A: Compute FISCAL Price Score (0.0 to 10.0)
    fiscal_score = analyze_pricing_deception(current_discounted, current_anchor, history)
    
    # --- DIAGNOSTIC LOG START ---
    print("\n" + "="*50)
    print("DEBUG: INCOMING PAYLOAD TEXT DIAGNOSTICS")
    print(f"urgency_hints content : {data.get('urgency_hints')}")
    print(f"urgency_text content  : {data.get('urgency_text')}")
    print(f"full_text content     : {data.get('full_text')}")
    print("="*50 + "\n")
    # --- DIAGNOSTIC LOG END ---

    # 4. Component B: Compute DistilBERT Text Urgency Score (1.0 to 10.0)
    extracted_text = data.get('urgency_hints', [])
    
    # If urgency_hints is empty or contains empty strings, evaluate alternative text fields
    if not extracted_text or (isinstance(extracted_text, list) and len(extracted_text) == 0):
        single_text = data.get('urgency_text', data.get('full_text', ''))
        if single_text and str(single_text).strip():
            extracted_text = [str(single_text).strip()]
    
    dpd_urgency_score = 0.0
    # Clean up empty strings or placeholders out of the text array
    if isinstance(extracted_text, list):
        extracted_text = [t for t in extracted_text if t and str(t).strip() not in ["", "string"]]

    if extracted_text:
        try:
            # Run batch evaluation via DistilBERT
            inference_results = score_many(extracted_text)
            
            # Extract scores safely whether it's returning dictionaries or direct values
            raw_scores = []
            for res in inference_results:
                if isinstance(res, dict):
                    raw_scores.append(safe_float(res.get('deceptive_score', 0.0)))
                elif isinstance(res, (int, float)):
                    raw_scores.append(float(res))
            
            if raw_scores:
                dpd_urgency_score = max(raw_scores)
        except Exception as e:
            print(f"--- [DPD INFERENCE WARNING] Processing fallback: {e} ---")
            dpd_urgency_score = 0.0

    # 5. Hybrid Data Fusion Matrix -> Ultimate Deception Score (0 to 10 Scale)
    if fiscal_score > 0:
        ultimate_score = (fiscal_score * 0.6) + (dpd_urgency_score * 0.4)
    else:
        ultimate_score = dpd_urgency_score

    # Clip and clean to the strict 0 - 10 bounds
    ultimate_score = round(max(0.0, min(ultimate_score, 10.0)), 2)
    dpd_urgency_score = round(dpd_urgency_score, 2)
    fiscal_score = round(fiscal_score, 2)
    
    # 6. Context-Aware Hybrid Diagnostics
    if ultimate_score >= 7.0:
        analysis_remarks = "Highly Deceptive: Artificial pricing fraud corroborated by coercive dark patterns."
    elif ultimate_score >= 3.0:
        analysis_remarks = "Moderately Deceptive: Hybrid metrics flagged synthetic urgency or questionable markdown variations."
    else:
        analysis_remarks = "Less Deceptive: Normal pricing history and compliant textual copy verified."

    flat_price_history = [safe_float(r.get('discounted_price')) for r in history]

    return AnalysisResponse(
        status="success",
        deceptive_score=ultimate_score,         
        urgency_score=dpd_urgency_score,        
        inflation_score=fiscal_score,           
        dark_pattern_analysis=analysis_remarks,
        price_history=flat_price_history,
        total_historical_records=len(history),
        complaint_template=f"Official Notice: Multi-layered pattern deception confirmed for asset target ID {prod_id}."
    )