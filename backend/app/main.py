from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import sessions, photos, analysis, styles, simulate

app = FastAPI(
    title="HairMaker API",
    description="Hair style recommendation and simulation backend for hair salons",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])
app.include_router(photos.router, prefix="/api/v1/sessions", tags=["photos"])
app.include_router(analysis.router, prefix="/api/v1/sessions", tags=["analysis"])
app.include_router(styles.router, prefix="/api/v1/styles", tags=["styles"])
app.include_router(simulate.router, prefix="/api/v1/simulate", tags=["simulate"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}
