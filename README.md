# OmniGuard

A Zero-Trust MCP Governance Gateway and Agentic SOC for enterprise AI agents. OmniGuard sits between your AI agents and the tools they call - enforcing identity, policy, and security on every single request.

**Live at: https://prismbrain.co**
**Admin Dashboard: https://admin.prismbrain.co**

## What It Does

Every time an AI agent tries to call a tool (GitHub, database, API), the request passes through OmniGuard first. No exceptions.

- **Identity Verification** - JWT-based authentication on every request. No valid token, no access.
- **Policy Enforcement** - Open Policy Agent (OPA) enforces RBAC rules. Junior devs cannot commit to production. Contractors cannot access databases. Rules are defined in policy files, not hardcoded.
- **Prompt Injection Detection** - Pinecone vector similarity matching against 60+ known jailbreak and injection patterns. Threshold tunable per deployment.
- **PII Redaction** - Microsoft Presidio strips emails, SSNs, credit cards, phone numbers, names, IP addresses, passport numbers, addresses, and bank account numbers before any payload reaches an upstream service.
- **Rate Limiting** - Redis token bucket enforces per-user request limits. Precise enforcement validated at exactly 60 req/min.
- **Audit Logging** - Every request logged to PostgreSQL with user identity, tool called, action taken, blocked status, and block reason. Append-only, immutable.
- **Agentic SOC** - Three LangGraph agents (Triage, Enrichment, Containment) run in a Docker container 24/7. Every 30 seconds they read audit logs, detect suspicious patterns, and automatically add compromised users to the Redis blocklist. No human needed.
- **Automated Red Team** - Offensive LangGraph swarm you run on demand. Attacks OmniGuard across 103 vectors and outputs a full security benchmark report.
- **Admin Dashboard** - Live security dashboard at admin.prismbrain.co showing total requests, block rate, top blocked users, and real-time audit logs.

## Benchmark Results

Validated in production at prismbrain.co:

- Prompt Injection Block Rate: 100% (30/30 vectors)
- JWT Attack Prevention: 100% (3/3 vectors)
- OPA Policy Bypass Prevention: 100% (3/3 vectors)
- Rate Limit Enforcement: precise at 60 req/min (10/70 correctly blocked)
- PII Redaction Accuracy: 100% across 10 entity types (email, SSN, credit card, phone, name, IP address, date of birth, passport, address, bank account)

## Stack

- FastAPI + httpx (async reverse proxy)
- Open Policy Agent (OPA) - RBAC policy enforcement
- Microsoft Presidio - PII redaction
- Pinecone - prompt injection vector store
- Redis - token bucket rate limiting + SOC blocklist
- PostgreSQL - append-only audit logs
- LangGraph - Agentic SOC and Red Team swarm
- Docker

## Operational Scenarios

**Scenario A - Policy Enforcement:** Junior dev AI agent tries to commit to production repo. OPA blocks it based on role. Zero code changes needed to update the policy.

**Scenario B - Agentic SOC:** Prompt injection tricks an AI agent into attempting a data dump. Pinecone blocks the request. Triage Agent detects the anomaly spike in audit logs every 30 seconds. Containment Agent adds the user to Redis blocklist. All subsequent requests from that user are blocked instantly.

**Scenario C - Red Team:** Run `python red-team/attacker.py` to launch the offensive swarm. It attacks the gateway across 103 vectors and outputs a full benchmark report.

## What Gets Blocked

- Invalid or expired JWT returns `401`
- Policy violation (wrong role for tool) returns `403`
- Prompt injection detected returns `400 {"detail": "Prompt injection detected"}`
- Rate limit exceeded returns `429`
- SOC-blocklisted user returns `403 {"detail": "User blocked by SOC"}`

## Roles Available (Default)

- `admin` - full access to all tools
- `senior-dev` - access to all tools except delete operations
- `junior-dev` - read-only access (read_repo only)
- `contractor` - restricted access

---

## Using the Hosted Version (prismbrain.co)

No setup required. The hosted version at prismbrain.co is pointed at OpenAI's API. You bring your own OpenAI key and pass it on every request.

**Step 1 - Get a token:**

```bash
curl -X POST https://prismbrain.co/token \
  -H "Content-Type: application/json" \
  -d '{"user_id": "john", "role": "senior-dev"}'
```

Returns:
```json
{"token": "eyJhbGci..."}
```

**Step 2 - Call OpenAI through OmniGuard:**

```bash
curl -X POST https://prismbrain.co/call_tool \
  -H "Authorization: Bearer your-omniguard-token" \
  -H "X-Upstream-Key: your-openai-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "upstream_url": "https://api.openai.com/v1/chat/completions",
    "payload": {
      "model": "gpt-4o-mini",
      "messages": [{"role": "user", "content": "What is 2+2?"}]
    },
    "tool": "chat_completion"
  }'
```

**Step 3 - That is it.** Every request is automatically checked for prompt injection, PII redacted, rate limited, and logged.

---

## Self-Hosting Setup

Follow these steps to run OmniGuard on your own infrastructure and point it at any upstream - OpenAI, Anthropic, your own MCP servers, or any internal API.

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
GATEWAY_URL=https://your-domain.com
UPSTREAM_URL=https://your-domain.com
```

**3. Edit `gateway/policy.rego` to define your own roles and tools:**

```rego
package omniguard

default allow := false

allow if {
    input.role == "admin"
}

allow if {
    input.role == "senior-dev"
    input.tool != "delete_database"
}

allow if {
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

---

## Using OmniGuard in Your Application (Self-Hosted)

Once deployed, use OmniGuard from any language. Replace `https://your-domain.com` with your own deployment URL.

OmniGuard works with any upstream that accepts HTTP - not just OpenAI:

| Upstream | upstream_url | X-Upstream-Key |
|----------|-------------|----------------|
| OpenAI | `https://api.openai.com/v1/chat/completions` | Your OpenAI API key |
| Anthropic | `https://api.anthropic.com/v1/messages` | Your Anthropic API key |
| GitHub MCP | `https://your-github-mcp.com/call_tool` | Your GitHub PAT |
| Any MCP server | `https://your-mcp-server.com` | Whatever key that server needs |

**Python:**

```python
import httpx

# Get a token once and reuse until expiry
token_res = httpx.post("https://prismbrain.co/token", json={
    "user_id": "john",
    "role": "senior-dev"
})
token = token_res.json()["token"]

# Call any upstream through OmniGuard
response = httpx.post(
    "https://prismbrain.co/call_tool",
    headers={
        "Authorization": f"Bearer {token}",
        "X-Upstream-Key": "your-upstream-api-key"
    },
    json={
        "upstream_url": "https://api.openai.com/v1/chat/completions",
        "payload": {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "What is 2+2?"}]
        },
        "tool": "chat_completion"
    }
)
print(response.json())
```

**Node.js:**

```javascript
const axios = require('axios');

const tokenRes = await axios.post('https://prismbrain.co/token', {
    user_id: 'john',
    role: 'senior-dev'
});
const token = tokenRes.data.token;

const response = await axios.post(
    'https://prismbrain.co/call_tool',
    {
        upstream_url: 'https://api.openai.com/v1/chat/completions',
        payload: {
            model: 'gpt-4o-mini',
            messages: [{ role: 'user', content: 'What is 2+2?' }]
        },
        tool: 'chat_completion'
    },
    {
        headers: {
            'Authorization': `Bearer ${token}`,
            'X-Upstream-Key': 'your-upstream-api-key'
        }
    }
);
console.log(response.data);
```

## Endpoints

- `POST /token` - Get a JWT token
- `POST /call_tool` - Main proxy endpoint
- `GET /admin/stats` - Security statistics JSON
- `GET /docs` - API documentation

## Ports

- 8011 - Gateway API
- 8512 - Admin Dashboard

## GitHub

github.com/MSaiRam10/OmniGuard
