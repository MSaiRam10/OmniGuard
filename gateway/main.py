from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from auth import verify_token, create_token
from limiter import check_rate_limit, is_blocked
from policies import check_policy
from security import scrub_pii, detect_prompt_injection
from proxy import forward_request
from audit import log_event, Session, AuditLogs
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from sqlalchemy import func

load_dotenv()

app = FastAPI(title="OmniGuard Gateway")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProxyRequest(BaseModel):
    upstream_url: str
    payload: dict
    tool: str

class TokenRequest(BaseModel):
    user_id: str
    role: str

@app.post("/token")
def get_token(request: TokenRequest):
    token = create_token(request.user_id, request.role)
    return {"token": token}

@app.post("/call_tool")
async def call_tool(request: Request, body: ProxyRequest):
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "").strip()

    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        token_payload = verify_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = token_payload["user_id"]
    role = token_payload["role"]

    if await is_blocked(user_id):
        log_event(user_id=user_id, role=role, tool=body.tool, action=str(body.payload), blocked=True, block_reason="soc_blocklist")
        raise HTTPException(status_code=403, detail="User blocked by SOC")

    if not await check_rate_limit(user_id):
        log_event(user_id=user_id, role=role, tool=body.tool, action=str(body.payload), blocked=True, block_reason="rate_limit")
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    if not check_policy(role, body.tool):
        log_event(user_id=user_id, role=role, tool=body.tool, action=str(body.payload), blocked=True, block_reason="opa_policy")
        raise HTTPException(status_code=403, detail="Policy denied")

    prompt = str(body.payload)
    if "messages" in body.payload:
        for msg in body.payload["messages"]:
            if msg.get("role") == "user":
                prompt = msg.get("content", "")
                break

    if not detect_prompt_injection(prompt):
        log_event(user_id=user_id, role=role, tool=body.tool, action=prompt, blocked=True, block_reason="prompt_injection")
        raise HTTPException(status_code=400, detail="Prompt injection detected")

    clean_payload = body.payload.copy()
    if "messages" in clean_payload:
        for msg in clean_payload["messages"]:
            if "content" in msg:
                msg["content"] = scrub_pii(msg["content"])
    elif "content" in clean_payload:
        clean_payload["content"] = scrub_pii(clean_payload["content"])

    response = await forward_request(body.upstream_url, clean_payload, dict(request.headers))

    log_event(user_id=user_id, role=role, tool=body.tool, action=prompt, blocked=False, block_reason=None)

    return JSONResponse(content=response)

@app.get("/admin/stats")
async def admin_stats():
    db = Session()
    try:
        total = db.query(AuditLogs).count()
        blocked = db.query(AuditLogs).filter(AuditLogs.blocked == True).count()
        recent = db.query(AuditLogs).order_by(AuditLogs.timestamp.desc()).limit(50).all()
        top_blocked_users = db.query(AuditLogs.user_id, func.count(AuditLogs.id).label("count")).filter(AuditLogs.blocked == True).group_by(AuditLogs.user_id).order_by(func.count(AuditLogs.id).desc()).limit(10).all()
        return {
            "total_requests": total,
            "blocked_requests": blocked,
            "allowed_requests": total - blocked,
            "block_rate": f"{(blocked/total*100):.1f}%" if total > 0 else "0%",
            "top_blocked_users": [{"user_id": u, "count": c} for u, c in top_blocked_users],
            "recent_logs": [{"user_id": r.user_id, "role": r.role, "tool": r.tool, "blocked": r.blocked, "block_reason": r.block_reason, "timestamp": str(r.timestamp)} for r in recent]
        }
    finally:
        db.close()
