from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
from app.core.config import settings
from typing import Optional, Union, List

router = APIRouter()

class GeocodeRequest(BaseModel):
    address: str

class GeocodeResponse(BaseModel):
    location: str
    formatted_address: str
    district: Optional[str] = ""
    city: Optional[str] = ""
    province: Optional[str] = ""

def safe_get_str(data: dict, key: str, default: str = "") -> str:
    """安全地获取字符串值，处理空列表和None的情况"""
    value = data.get(key, default)
    if isinstance(value, list):
        return default
    return str(value) if value is not None else default

@router.post("/geocode", response_model=GeocodeResponse)
async def get_geocode(request: GeocodeRequest):
    try:
        params = {
            "address": request.address,
            "output": "json",
            "key": settings.AMAP_API_KEY
        }
        
        response = requests.get(f"{settings.AMAP_API_BASE_URL}/geocode/geo", params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "1" and "geocodes" in data and len(data["geocodes"]) > 0:
            geocode = data["geocodes"][0]
            return GeocodeResponse(
                location=safe_get_str(geocode, "location"),
                formatted_address=safe_get_str(geocode, "formatted_address"),
                district=safe_get_str(geocode, "district"),
                city=safe_get_str(geocode, "city"),
                province=safe_get_str(geocode, "province")
            )
        else:
            raise HTTPException(status_code=400, detail="Address not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 