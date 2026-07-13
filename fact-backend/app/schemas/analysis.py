from pydantic import BaseModel
from typing import List, Optional

# This handles the "API Request Layout" sent by the extension
class AnalysisPayload(BaseModel):
    product_id: str
    product_name: str
    anchor_price: float
    discount_percentage: float
    discounted_price: float
    urgency_text: str
    
    # Extra fields used by the spaCy NER microservice
    full_text: Optional[str] = ""
    title: Optional[str] = ""
    price_hints: Optional[List[str]] = []
    discount_hints: Optional[List[str]] = []
    brand_hints: Optional[List[str]] = []
    urgency_hints: Optional[List[str]] = []
    image_alts: Optional[List[str]] = []
    url: Optional[str] = ""

# This defines the structural response format returned to the extension
class AnalysisResponse(BaseModel):
    status: str
    deceptive_score: float
    urgency_score: float
    inflation_score: float
    price_history: List[float]
    complaint_template: str