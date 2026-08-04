# OmniGuard

A Zero-Trust MCP Governance Gateway and Agentic SOC for enterprise AI agents. OmniGuard sits between your AI agents and the tools they call - enforcing identity, policy, and security on every single request.

**Live at: https://prismbrain.co**

## What It Does

Every time an AI agent tries to call a tool (GitHub, database, API), the request passes through OmniGuard first. No exceptions.

- **Identity Verification** - JWT-based authentication on every request. No valid token, no access.
- **Policy Enforcement** - Open Policy Agent (OPA) enforces RBAC rules. Junior devs cannot commit to production. Contractors cannot access databases. Rules are defined in policy files, not hardcoded.
- **Prompt Injection Detection** - Pinecone vector similarity matching against 60+ known jailbreak and injection patterns. Threshold tunable per deployment.
- **PII Redaction** - Microsoft Presidio strips emails, SSNs, credit cards, phone numbers, and names before any payload reaches an upstream service.
- **Rate Limiting** - Redis token bucket enforces per-user request limits. Precise enforcement validated at exactly 60 req/min.
- **Audit Logging** - Every request logged to PostgreSQL with user identity, tool called, action taken, blocked status, and block reason. Append-only, immutable.
- **Agentic SOC** - LangGraph-powered Triage, Enrichment, and Containment agents monitor audit logs in real time and automatically revoke compromised sessions.
- **Automated Red Team** - Offensive LangGraph swarm that attacks the gateway on demand and outputs security benchmark scores across 103 attack vectors.

## Benchmark Results

Validated against 103 automated attack vectors:

- Prompt Injection Block Rate: 100% (30/30 vectors)
- JWT Attack Prevention: 100% (3/3 vectors)
- OPA Policy Bypass Prevention: 100% (3/3 vectors)
- Rate Limit Enforcement: precise at 60 req/min (10/70 correctly blocked)

## How to Use (Hosted Version at prismbrain.co)

No setup required. Just use the hosted version directly.

**Step 1 - Get a token:**

```bash
curl -X POST https://prismbrain.co/token \
  -H "Content-Type: application/json" \
  -d '{"user_id": "john", "role": "junior-dev"}'
```

Returns:
```json
{"token": "eyJhbGci..."}
```

**Step 2 - Call a tool through OmniGuard:**

The hosted version at prismbrain.co is currently pointed at our GitHub MCP Server (mcp.glassbrain.dev).

Available tools on this upstream:
- `list_repos` - list all repos for a GitHub user
- `get_repo` - get details of a specific repo
- `list_issues` - list open issues on a repo
- `create_issue` - create a new issue
- `list_prs` - list open pull requests
- `get_file` - read a file from a repo

Since the upstream is a GitHub MCP server, you also need to pass your GitHub Personal Access Token as an additional header:

```bash
curl -X POST https://prismbrain.co/call_tool \
  -H "Authorization: Bearer your-omniguard-token" \
  -H "X-GitHub-Token: your-github-personal-access-token" \
  -H "Content-Type: application/json" \
  -d '{
    "upstream_url": "https://mcp.glassbrain.dev/mcp",
    "payload": {"content": "MSaiRam10"},
    "tool": "list_repos"
  }'
```

To point OmniGuard at your own MCP server instead, self-host using the setup instructions below and set `UPSTREAM_URL` in your `.env`.

**Step 3 - That is it.** OmniGuard handles identity verification, policy enforcement, prompt injection detection, PII redaction, rate limiting, and audit logging automatically on every request.

## Roles Available (Default)

- `admin` - full access to all tools
- `senior-dev` - access to all tools except delete operations
- `junior-dev` - read-only access (read_repo only)
- `contractor` - restricted access

Add your own roles and rules in `gateway/policy.rego`.

## What Gets Blocked

- Invalid or expired JWT returns `401`
- Policy violation (wrong role for tool) returns `403`
- Prompt injection detected returns `400 {"detail": "Prompt injection detected"}`
- Rate limit exceeded returns `429`

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

**Scenario C - Red Team:** Run `python red-team/attacker.py` to launch the offensive swarm. It attacks the gateway across 103 vectors and outputs a full benchmark report.

---

## Self-Hosting Setup

Only follow these steps if you want to run your own instance. Skip if using prismbrain.co.

**1. Create a Pinecone account at pinecone.io and create an index with these exact settings:**

- Name: `prompt-injections`
- Dimensions: `384`
- Metric: `cosine`
- Cloud: AWS
- Region: us-east-1

**2. Create `.env` in the root folder:**

```
JWT_SECRET=any_random_secret_string_here
DATABASE_URL=postgresql://postgres:password@db:5432/omniguard
REDIS_URL=redis://172.17.0.1:6379
PINECONE_API_KEY=your_pinecone_api_key
OPENAI_API_KEY=your_openai_api_key
GATEWAY_URL=https://prismbrain.co
UPSTREAM_URL=https://your-mcp-server.com
```

**3. Edit `gateway/policy.rego` to define your own roles and tools:**

```rego
package omniguard

default allow = false

allow {
    input.role == "admin"
}

allow {
    input.role == "senior-dev"
    input.tool != "delete_database"
}

allow {
    input.role == "junior-dev"
    input.tool == "read_repo"
}
```

**4. Install dependencies:**

```bash
pip install -r gateway/requirements.txt
python -m spacy download en_core_web_lg
```

**5. Seed jailbreak vectors into Pinecone:**

```bash
python seed_pinecone.py
```

**6. Run with Docker:**

```bash
docker-compose up --build -d
```

**7. Run the red team benchmark (optional):**

```bash
python red-team/attacker.py
```

## Endpoints

- `POST /token` - Get a JWT token
- `POST /call_tool` - Main proxy endpoint
- `GET /docs` - API documentation

## Port

- 8011

## GitHub

github.com/MSaiRam10/OmniGuard
