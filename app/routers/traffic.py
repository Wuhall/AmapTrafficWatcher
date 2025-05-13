from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
from datetime import datetime
import json
import os
from app.core.config import settings

router = APIRouter()

class TrafficRequest(BaseModel):
    origin: str = settings.DEFAULT_ORIGIN
    destination: str = settings.DEFAULT_DESTINATION
    strategy: int = 10  # 默认使用速度优先策略

class TrafficResponse(BaseModel):
    duration: float
    distance: float
    timestamp: str

@router.post("/traffic/duration", response_model=TrafficResponse)
async def get_traffic_duration(request: TrafficRequest):
    try:
        params = {
            "origin": request.origin,
            "destination": request.destination,
            "extensions": "base",
            "strategy": request.strategy,
            "output": "json",
            "key": settings.AMAP_API_KEY
        }
        
        print(f"Requesting Amap API with params: {params}")  # 添加日志
        response = requests.get(f"{settings.AMAP_API_BASE_URL}/direction/driving", params=params)
        response.raise_for_status()
        data = response.json()
        print(f"Amap API response: {data}")  # 添加日志

        if data.get("status") == "1" and "route" in data and "paths" in data["route"]:
            path = data["route"]["paths"][0]
            return TrafficResponse(
                duration=round(float(path["duration"]) / 3600, 2),  # 转换为小时
                distance=round(float(path["distance"]) / 1000, 2),  # 转换为公里
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        else:
            error_msg = f"Invalid response from Amap API: {data}"
            print(error_msg)  # 添加日志
            raise HTTPException(status_code=400, detail=error_msg)
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Request to Amap API failed: {str(e)}"
        print(error_msg)  # 添加日志
        raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg)  # 添加日志
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/traffic/history")
async def get_traffic_history():
    try:
        data_file = "hourly_durations.json"
        if not os.path.exists(data_file):
            return []
            
        with open(data_file, "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        error_msg = f"Error reading history data: {str(e)}"
        print(error_msg)  # 添加日志
        raise HTTPException(status_code=500, detail=error_msg) 