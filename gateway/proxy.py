import httpx

async def forward_request(upstream_url, payload, headers):
    """
    Forwards a request to an upstream service.
    """
    try:
        async with httpx.AsyncClient() as client:            
            response = await client.post(upstream_url, json=payload, headers=headers, timeout=1.0)
            return response.json()
    except Exception as e:
        print(f"Error forwarding request: {e}")
        return  None