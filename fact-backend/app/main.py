from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import analysis

app = FastAPI(title="FACT Core Engine APIs", version="1.0.0")

# Enable Cross-Origin Resource Sharing so your extension can talk to it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Includes your route under the /api/v1 pathing structure
app.include_router(analysis.router, prefix="/api/v1", tags=["Analysis Engine"])

@app.get("/health")
def health_check():
    return {"status": "healthy"}