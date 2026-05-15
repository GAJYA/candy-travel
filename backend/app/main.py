from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import (
    ai_import,
    auth,
    checklist,
    health,
    inspirations,
    me,
    trip_events,
    trip_invites,
    trips,
)

app = FastAPI(title="CandyTravel Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 健康检查（无前缀 + /api/v1）
app.include_router(health.router, tags=["health"])
app.include_router(health.router, prefix="/api/v1")

# 业务接口
api_v1 = "/api/v1"
app.include_router(auth.router, prefix=api_v1)
app.include_router(me.router, prefix=api_v1)
app.include_router(trips.router, prefix=api_v1)
app.include_router(trip_events.router, prefix=api_v1)
app.include_router(ai_import.router, prefix=api_v1)
app.include_router(trip_invites.router, prefix=api_v1)
app.include_router(checklist.router, prefix=api_v1)
app.include_router(inspirations.router, prefix=api_v1)
