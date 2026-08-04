import httpx
import os

OPA_URL = os.getenv("OPA_URL", "http://opa:8181")

def check_policy(role: str, tool: str) -> bool:
    """
    Checks if a user with a given role can access a specific tool.
    """
    try:
        response = httpx.post(f"{OPA_URL}/v1/data/omniguard/allow", json={"input": {"role": role, "tool": tool}})
        return response.json().get("result", False)
    except Exception as e:
        print(f"Error checking policy: {e}")
        return False
