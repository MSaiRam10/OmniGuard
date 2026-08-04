import httpx

async def forward_request(upstream_url, payload, headers):
    """
    Forwards a request to an upstream service.
    Pass your upstream API key via X-Upstream-Key header.
    """
    forward_headers = {"Content-Type": "application/json"}
    if "x-upstream-key" in headers:
        forward_headers["Authorization"] = f"Bearer {headers['x-upstream-key']}"
    async with httpx.AsyncClient() as client:
        response = await client.post(upstream_url, json=payload, headers=forward_headers, timeout=30.0)
        return response.json()
