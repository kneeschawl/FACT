from fastapi import APIRouter, HTTPException
from app.schemas.analysis import AnalysisPayload, AnalysisResponse
from app.pipeline.pipeline_manager import execute_analysis_pipeline

router = APIRouter()

@router.post("/analysis", response_model=AnalysisResponse)
async def analyze_product(payload: AnalysisPayload):
    try:
        # Passes the payload directly into your orchestration pipeline manager
        result = await execute_analysis_pipeline(payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))