from fastapi import APIRouter, HTTPException
from app.schemas.analysis import AnalysisPayload, AnalysisResponse
from app.pipeline.pipeline_manager import execute_analysis_pipeline

router = APIRouter()

@router.post("/analysis")
async def analyze_product(payload: AnalysisPayload):
    try:
        return await execute_analysis_pipeline(payload)
    except Exception as e:
        import traceback
        print("\n=== CRITICAL PIPELINE BREAKDOWN ===")
        traceback.print_exc()
        print("===================================\n")
        raise e