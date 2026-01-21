from fastapi import Header, HTTPException
from app.core.config import settings

def api_key_auth(x_api_key: str = Header(..., alias="X-API-KEY")):
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
