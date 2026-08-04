import httpx

async def forward_request(upstream_url, payload, headers):
    """
    Forwards a request to an upstream service.
    Extracts X-OpenAI-Key header and uses it as Authorization for the upstream.
    """
    forward_headers = {"Content-Type": "application/json"}
    if "x-openai-key" in headers:
        forward_headers["Authorization"] = f"Bearer {headers['x-openai-key']}"
    async with httpx.AsyncClient() as client:
        response = await client.post(upstream_url, json=payload, headers=forward_headers, timeout=30.0)
        return response.json()
