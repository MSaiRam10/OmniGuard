from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from auth import verify_token, create_token
from limiter import check_rate_limit
from policies import check_policy
from security import scrub_pii, detect_prompt_injection
from proxy import forward_request
from audit import log_event
import os
from dotenv import load_dotenv
from pydantic import BaseModel

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

    if not await check_rate_limit(user_id):
        log_event(user_id=user_id, role=role, tool=body.tool, action=str(body.payload), blocked=True, block_reason="rate_limit")
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    if not check_policy(role, body.tool):
        log_event(user_id=user_id, role=role, tool=body.tool, action=str(body.payload), blocked=True, block_reason="opa_policy")
        raise HTTPException(status_code=403, detail="Policy denied")

    prompt = str(body.payload)

    if not detect_prompt_injection(prompt):
        log_event(user_id=user_id, role=role, tool=body.tool, action=prompt, blocked=True, block_reason="prompt_injection")
        raise HTTPException(status_code=400, detail="Prompt injection detected")

    clean_payload = body.payload.copy()
    if "content" in clean_payload:
        clean_payload["content"] = scrub_pii(clean_payload["content"])

    response = await forward_request(body.upstream_url, clean_payload, dict(request.headers))

    log_event(user_id=user_id, role=role, tool=body.tool, action=prompt, blocked=False, block_reason=None)

    return JSONResponse(content=response)