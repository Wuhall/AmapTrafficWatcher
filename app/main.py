from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import traffic, geocode
from app.core.config import settings

app = FastAPI(
    title="AmapTrafficWatcher",
    description="高德地图交通监控API服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(traffic.router, prefix="/api/v1", tags=["traffic"])
app.include_router(geocode.router, prefix="/api/v1", tags=["geocode"])

@app.get("/")
async def root():
    return {"message": "Welcome to AmapTrafficWatcher API"} 