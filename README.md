# OmniGuard

A Zero-Trust MCP Governance Gateway and Agentic SOC for enterprise AI agents. OmniGuard sits between your AI agents and the tools they call - enforcing identity, policy, and security on every single request.

## What It Does

Every time an AI agent tries to call a tool (GitHub, database, API), the request passes through OmniGuard first. No exceptions.

- **Identity Verification** - JWT-based authentication on every request. No valid token, no access.
- **Policy Enforcement** - Open Policy Agent (OPA) enforces RBAC rules. Junior devs cannot commit to production. Contractors cannot access databases. Rules are defined in policy files, not hardcoded.
- **Prompt Injection Detection** - Pinecone vector similarity matching against 60+ known jailbreak and injection patterns. Threshold tunable per deployment.
- **PII Redaction** - Microsoft Presidio strips emails, SSNs, credit cards, phone numbers, and names before any payload reaches an upstream service.
- **Rate Limiting** - Redis token bucket enforces per-user request limits. Precise enforcement validated at exactly 60 req/min.
- **Audit Logging** - Every request logged to PostgreSQL with user identity, tool called, action taken, blocked status, and block reason. Append-only, immutable.
- **Agentic SOC** - LangGraph-powered Triage, Enrichment, and Containment agents monitor audit logs in real time and automatically revoke compromised sessions.
- **Automated Red Team** - Offensive LangGraph swarm continuously attacks the gateway and outputs security benchmark scores.

## Benchmark Results

Validated against 103 automated attack vectors:

- Prompt Injection Block Rate: 100% (30/30 vectors)
- JWT Attack Prevention: 100% (3/3 vectors)
- OPA Policy Bypass Prevention: 100% (3/3 vectors)
- Rate Limit Enforcement: precise at 60 req/min (10/70 correctly blocked)

## How to Use

Point your AI agent at OmniGuard instead of your upstream service:

```python
import httpx

response = httpx.post(
    "https://prismbrain.co/call_tool",
    headers={"Authorization": "Bearer your-jwt-token"},
    json={
        "upstream_url": "https://your-mcp-server.com",
        "payload": {"content": "your request"},
        "tool": "read_repo"
    }
)
```

Get a token first:

```
POST /token
{"user_id": "john", "role": "junior-dev"}
```

## Stack

- FastAPI + httpx (async reverse proxy)
- Open Policy Agent (OPA) - RBAC policy enforcement
- Microsoft Presidio - PII redaction
- Pinecone - prompt injection vector store
- Redis - token bucket rate limiting
- PostgreSQL - append-only audit logs
- LangGraph - Agentic SOC and Red Team swarm
- Docker

## Operational Scenarios

**Scenario A - Policy Enforcement:** Junior dev AI agent tries to commit to production repo. OPA blocks it based on role. Zero code changes needed to update the policy.

**Scenario B - Agentic SOC:** Prompt injection tricks an AI agent into attempting a data dump. Pinecone blocks the request. Triage Agent detects the anomaly spike. Containment Agent revokes the JWT and updates OPA policy in under 5 seconds.

**Scenario C - Red Team:** Offensive LangGraph swarm runs nightly, generating attack benchmarks. Ensures no new deployment introduced a security regression.

## Self-Hosting Setup

1. Create a Pinecone index:
   - Name: `prompt-injections`
   - Dimensions: `384`
   - Metric: `cosine`

2. Create `.env`:

```
JWT_SECRET=your_secret_key
DATABASE_URL=postgresql://postgres:password@localhost:5432/omniguard
REDIS_URL=redis://localhost:6379
PINECONE_API_KEY=your_pinecone_key
OPENAI_API_KEY=your_openai_key
GATEWAY_URL=http://localhost:8000
UPSTREAM_URL=https://your-mcp-server.com
```

3. Install dependencies:

```bash
pip install -r gateway/requirements.txt
python -m spacy download en_core_web_lg
```

4. Seed jailbreak vectors:

```bash
python seed_pinecone.py
```

5. Start OPA:

```bash
./opa run --server --addr localhost:8181 gateway/policy.rego
```

6. Run with Docker:

```bash
docker-compose up --build -d
```

## Endpoints

- `POST /call_tool` - Main proxy endpoint
- `POST /token` - Get a JWT token
- `GET /docs` - API documentation

## Port

- 8011

## GitHub

github.com/MSaiRam10/OmniGuard