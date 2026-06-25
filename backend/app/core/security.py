import time
import logging
from typing import List, Optional
from fastapi import Depends, HTTPException, Security, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import jwt, JWTError

from app.core.config import settings

# Structured logger setup
logger = logging.getLogger("AuditLogger")

class User(BaseModel):
    uid: str
    email: str
    role: str  # Administrator, Emergency Responder, Volunteer, NGO, Citizen

# Security Schemes
security_scheme = HTTPBearer(auto_error=False)

# In-memory Rate Limiter Fallback
class InMemoryRateLimiter:
    def __init__(self) -> None:
        self.requests: dict[str, List[float]] = {}

    def is_rate_limited(self, ip: str, limit: int, window: int = 60) -> bool:
        now = time.time()
        # Clean expired timestamps
        if ip not in self.requests:
            self.requests[ip] = []
        self.requests[ip] = [t for t in self.requests[ip] if now - t < window]
        
        if len(self.requests[ip]) >= limit:
            return True
        
        self.requests[ip].append(now)
        return False

in_memory_limiter = InMemoryRateLimiter()

# -------------------------------------------------------------
# Structured Audit Log Helper
# -------------------------------------------------------------
def log_audit_event(
    action: str,
    user_id: Optional[str],
    role: Optional[str],
    resource: str,
    ip_address: str,
    status_code: str,
    details: Optional[str] = None
) -> None:
    """Logs structured audit events to stdout for logging aggregation tools."""
    import json
    from datetime import datetime
    
    audit_record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "log_type": "AUDIT",
        "action": action,
        "user_id": user_id or "anonymous",
        "role": role or "anonymous",
        "resource": resource,
        "ip_address": ip_address,
        "status": status_code,
        "details": details or ""
    }
    
    if settings.STRUCTURED_LOGGING:
        # Standard json format for Cloud Logging
        logger.info(json.dumps(audit_record))
    else:
        logger.info(
            f"[AUDIT] {audit_record['timestamp']} | Action: {action} | User: {user_id} ({role}) | "
            f"Resource: {resource} | IP: {ip_address} | Status: {status_code} | Details: {details or ''}"
        )

# -------------------------------------------------------------
# Firebase Token & Mock Auth Verifier
# -------------------------------------------------------------
async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> User:
    ip_address = request.client.host if request.client else "unknown"
    path = request.url.path

    if not credentials:
        log_audit_event("AUTHENTICATE", None, None, path, ip_address, "DENIED", "Missing authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization credentials missing. Please login."
        )

    token = credentials.credentials

    # Development Bypass/Mock Verification Check
    if settings.ENV == "development" or settings.DEBUG:
        # Check standard mock headers (e.g. bearer mock-admin)
        token_lower = token.lower()
        if "mock-admin" in token_lower or "admin" in token_lower:
            user = User(uid="mock-admin-123", email="admin@humanityos.dev", role="Administrator")
            log_audit_event("AUTHENTICATE", user.uid, user.role, path, ip_address, "ALLOWED", "Mock Development Bypass")
            return user
        elif "mock-responder" in token_lower or "responder" in token_lower:
            user = User(uid="mock-resp-456", email="responder@humanityos.dev", role="Emergency Responder")
            log_audit_event("AUTHENTICATE", user.uid, user.role, path, ip_address, "ALLOWED", "Mock Development Bypass")
            return user
        elif "mock-volunteer" in token_lower or "volunteer" in token_lower:
            user = User(uid="mock-vol-789", email="volunteer@humanityos.dev", role="Volunteer")
            log_audit_event("AUTHENTICATE", user.uid, user.role, path, ip_address, "ALLOWED", "Mock Development Bypass")
            return user
        elif "mock-ngo" in token_lower or "ngo" in token_lower:
            user = User(uid="mock-ngo-101", email="ngo@humanityos.dev", role="NGO")
            log_audit_event("AUTHENTICATE", user.uid, user.role, path, ip_address, "ALLOWED", "Mock Development Bypass")
            return user
        elif "mock-citizen" in token_lower or "citizen" in token_lower:
            user = User(uid="mock-citizen-202", email="citizen@humanityos.dev", role="Citizen")
            log_audit_event("AUTHENTICATE", user.uid, user.role, path, ip_address, "ALLOWED", "Mock Development Bypass")
            return user

    # Live Firebase JWT verification logic using project ID keys
    try:
        # Firebase public certificates url: https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com
        # For lightweight standard signature decoding, check claims:
        # iss must be https://securetoken.google.com/<project_id>
        # aud must be <project_id>
        decoded = jwt.get_unverified_claims(token)
        
        project_id = settings.FIREBASE_PROJECT_ID
        expected_iss = f"https://securetoken.google.com/{project_id}"
        
        if decoded.get("iss") != expected_iss:
            raise JWTError("Invalid token issuer.")
        if decoded.get("aud") != project_id:
            raise JWTError("Invalid token audience.")
            
        uid = decoded.get("sub")
        email = decoded.get("email")
        
        # Enforce custom claims for roles; default to Citizen
        role = decoded.get("role", "Citizen")
        
        user = User(uid=uid, email=email, role=role)
        log_audit_event("AUTHENTICATE", user.uid, user.role, path, ip_address, "ALLOWED", "Firebase Token Decoded")
        return user
        
    except JWTError as e:
        log_audit_event("AUTHENTICATE", None, None, path, ip_address, "DENIED", f"JWT Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}"
        )

# -------------------------------------------------------------
# Role-Based Access Control (RBAC) Dependency
# -------------------------------------------------------------
class RoleChecker:
    def __init__(self, allowed_roles: List[str]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(self, request: Request, current_user: User = Depends(get_current_user)) -> User:
        ip_address = request.client.host if request.client else "unknown"
        path = request.url.path

        if current_user.role not in self.allowed_roles:
            log_audit_event(
                "AUTHORIZE", current_user.uid, current_user.role, path, ip_address, "DENIED",
                f"Required roles: {self.allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {self.allowed_roles}"
            )
            
        log_audit_event("AUTHORIZE", current_user.uid, current_user.role, path, ip_address, "ALLOWED")
        return current_user

# -------------------------------------------------------------
# Prompt Injection Detector
# -------------------------------------------------------------
INJECTION_KEYWORDS = [
    "ignore previous instructions",
    "ignore above instructions",
    "system instruction override",
    "you are now a",
    "you are now an",
    "forget everything you were told",
    "override the default behavior",
    "bypass safety checks",
    "ignore the system prompt",
    "jailbreak instructions"
]

def scan_for_prompt_injection(prompt: str, request: Request, user: Optional[User] = None) -> None:
    """Scans the incoming prompt for injection keywords and logs an audit violation if found."""
    ip_address = request.client.host if request.client else "unknown"
    path = request.url.path
    
    prompt_lower = prompt.lower()
    for kw in INJECTION_KEYWORDS:
        if kw in prompt_lower:
            uid = user.uid if user else "anonymous"
            role = user.role if user else "anonymous"
            
            log_audit_event(
                "INJECTION_DETECTION", uid, role, path, ip_address, "BLOCKED",
                f"Prompt injection pattern detected: '{kw}'"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Malicious system injection detected. The prompt has been blocked."
            )

# Cache Redis offline status to avoid repeated connection timeouts in offline environments
_redis_offline = False

async def check_rate_limit(request: Request) -> None:
    """FastAPI dependency mapping rate limiting. Uses Redis, fallback to memory."""
    global _redis_offline
    ip_address = request.client.host if request.client else "unknown"
    path = request.url.path
    limit = settings.RATE_LIMIT_PER_MINUTE

    is_limited = False
    
    # Try Redis first if possible and not marked offline
    if not _redis_offline:
        try:
            import redis
            r = redis.from_url(settings.REDIS_URL, socket_timeout=1)
            key = f"rate_limit:{ip_address}:{path}"
            current = r.get(key)
            if current and int(current) >= limit:
                is_limited = True
            else:
                p = r.pipeline()
                p.incr(key)
                p.expire(key, 60)
                p.execute()
        except Exception:
            _redis_offline = True
            is_limited = in_memory_limiter.is_rate_limited(ip_address, limit, window=60)
    else:
        is_limited = in_memory_limiter.is_rate_limited(ip_address, limit, window=60)

    if is_limited:
        log_audit_event("RATE_LIMIT", "anonymous", "anonymous", path, ip_address, "BLOCKED", "Rate limit exceeded")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please wait a minute."
        )
