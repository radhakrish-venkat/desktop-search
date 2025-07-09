"""
Authentication router for API key management
"""

from fastapi import APIRouter, HTTPException, Depends, status, Header
from typing import List, Optional
import secrets
import hashlib
import json
import os
from datetime import datetime, timedelta

from api.models import APIResponse, APIKeyCreate, APIKeyInfo, APIKeyList
from api.config import settings
from api.middleware.auth import create_access_token, verify_token

router = APIRouter()

# API keys storage file
API_KEYS_FILE = os.path.join(settings.DEFAULT_DATA_PATH, "api_keys.json")

def load_api_keys() -> List[dict]:
    """Load API keys from file"""
    if not os.path.exists(API_KEYS_FILE):
        return []
    
    try:
        with open(API_KEYS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading API keys: {e}")
        return []

def save_api_keys(keys: List[dict]):
    """Save API keys to file"""
    os.makedirs(os.path.dirname(API_KEYS_FILE), exist_ok=True)
    try:
        with open(API_KEYS_FILE, 'w') as f:
            json.dump(keys, f, indent=2)
        # Set restrictive permissions
        os.chmod(API_KEYS_FILE, 0o600)
    except Exception as e:
        print(f"Error saving API keys: {e}")

def generate_api_key() -> str:
    """Generate a new API key"""
    return f"ds_{secrets.token_urlsafe(32)}"

def hash_api_key(api_key: str) -> str:
    """Hash API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()

@router.post("/create-key", response_model=APIResponse)
async def create_api_key(request: APIKeyCreate, x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key")):
    """Create a new API key"""
    try:
        # Validate admin key from header
        if settings.API_KEY and (not x_admin_key or x_admin_key != settings.API_KEY):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid admin key"
            )
        
        # Generate new API key
        api_key = generate_api_key()
        key_hash = hash_api_key(api_key)
        
        # Create key info
        key_info = {
            "id": secrets.token_urlsafe(16),
            "name": request.name,
            "description": request.description,
            "key_hash": key_hash,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=request.expires_days)).isoformat() if request.expires_days else None,
            "permissions": request.permissions or ["read", "search"],
            "is_active": True
        }
        
        # Save to file
        keys = load_api_keys()
        keys.append(key_info)
        save_api_keys(keys)
        
        return APIResponse(
            success=True,
            message="API key created successfully",
            data={
                "api_key": api_key,  # Only returned once
                "key_info": {
                    "id": key_info["id"],
                    "name": key_info["name"],
                    "description": key_info["description"],
                    "created_at": key_info["created_at"],
                    "expires_at": key_info["expires_at"],
                    "permissions": key_info["permissions"]
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create API key: {str(e)}")

@router.get("/list-keys", response_model=APIKeyList)
async def list_api_keys(x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key")):
    """List all API keys (admin only)"""
    try:
        # Validate admin key
        if settings.API_KEY and (not x_admin_key or x_admin_key != settings.API_KEY):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin key required"
            )
        
        keys = load_api_keys()
        
        # Return key info without hashes
        key_list = []
        for key in keys:
            key_list.append(APIKeyInfo(
                id=key["id"],
                name=key["name"],
                description=key["description"],
                created_at=key["created_at"],
                expires_at=key["expires_at"],
                permissions=key["permissions"],
                is_active=key["is_active"]
            ))
        
        return APIKeyList(keys=key_list)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list API keys: {str(e)}")

@router.delete("/revoke-key/{key_id}", response_model=APIResponse)
async def revoke_api_key(key_id: str, x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key")):
    """Revoke an API key (admin only)"""
    try:
        # Validate admin key
        if settings.API_KEY and (not x_admin_key or x_admin_key != settings.API_KEY):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin key required"
            )
        
        keys = load_api_keys()
        
        # Find and remove key
        for i, key in enumerate(keys):
            if key["id"] == key_id:
                revoked_key = keys.pop(i)
                save_api_keys(keys)
                
                return APIResponse(
                    success=True,
                    message=f"API key '{revoked_key['name']}' revoked successfully"
                )
        
        raise HTTPException(status_code=404, detail="API key not found")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to revoke API key: {str(e)}")

@router.post("/validate-key", response_model=APIResponse)
async def validate_api_key(api_key: str):
    """Validate an API key"""
    try:
        keys = load_api_keys()
        key_hash = hash_api_key(api_key)
        
        for key in keys:
            if key["key_hash"] == key_hash and key["is_active"]:
                # Check expiration
                if key["expires_at"]:
                    expires_at = datetime.fromisoformat(key["expires_at"])
                    if datetime.now() > expires_at:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="API key has expired"
                        )
                
                return APIResponse(
                    success=True,
                    message="API key is valid",
                    data={
                        "key_info": {
                            "id": key["id"],
                            "name": key["name"],
                            "permissions": key["permissions"]
                        }
                    }
                )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate API key: {str(e)}")

@router.post("/login", response_model=APIResponse)
async def login_with_api_key(api_key: str):
    """Login with API key and get JWT token"""
    try:
        keys = load_api_keys()
        key_hash = hash_api_key(api_key)
        
        for key in keys:
            if key["key_hash"] == key_hash and key["is_active"]:
                # Check expiration
                if key["expires_at"]:
                    expires_at = datetime.fromisoformat(key["expires_at"])
                    if datetime.now() > expires_at:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="API key has expired"
                        )
                
                # Create JWT token
                token_data = {
                    "sub": key["name"],
                    "key_id": key["id"],
                    "permissions": key["permissions"]
                }
                access_token = create_access_token(token_data)
                
                return APIResponse(
                    success=True,
                    message="Login successful",
                    data={
                        "access_token": access_token,
                        "token_type": "bearer",
                        "key_info": {
                            "id": key["id"],
                            "name": key["name"],
                            "permissions": key["permissions"]
                        }
                    }
                )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}") 