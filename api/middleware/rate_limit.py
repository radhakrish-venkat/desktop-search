"""
Rate limiting middleware for the Desktop Search API
"""

from fastapi import HTTPException, Request, status
from typing import Dict, Tuple
import time
import asyncio
from collections import defaultdict
import os

# Rate limiting settings
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "10000"))  # requests per window
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))    # seconds (1 hour)
RATE_LIMIT_BURST = int(os.getenv("RATE_LIMIT_BURST", "1000"))     # burst requests

class RateLimiter:
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = asyncio.Lock()
    
    async def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed based on rate limits"""
        async with self.lock:
            now = time.time()
            window_start = now - RATE_LIMIT_WINDOW
            
            # Clean old requests
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id] 
                if req_time > window_start
            ]
            
            # Check burst limit
            if len(self.requests[client_id]) >= RATE_LIMIT_BURST:
                return False
            
            # Check rate limit
            if len(self.requests[client_id]) >= RATE_LIMIT_REQUESTS:
                return False
            
            # Add current request
            self.requests[client_id].append(now)
            return True
    
    def get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Use X-Forwarded-For if behind proxy, otherwise use client host
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

# Global rate limiter instance
rate_limiter = RateLimiter()

async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    # Skip rate limiting if disabled
    if not RATE_LIMIT_ENABLED:
        response = await call_next(request)
        return response
    
    client_id = rate_limiter.get_client_id(request)
    
    if not await rate_limiter.is_allowed(client_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": str(RATE_LIMIT_WINDOW)}
        )
    
    response = await call_next(request)
    return response 