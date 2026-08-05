from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from typing import TypedDict
import os
import asyncio
import redis.asyncio as aioredis
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
engine = create_engine(DB_URL)
llm = ChatOpenAI(model="gpt-4o-mini")

class AgentState(TypedDict):
    user_id: str
    threat_detected: bool
    threat_summary: str
    action_taken: str

def triage_node(state: AgentState):
    db = engine.connect()
    logs = db.execute(text("SELECT * FROM audit_logs WHERE blocked = true ORDER BY timestamp DESC LIMIT 50")).fetchall()
    logs_str = "\n".join([str(row) for row in logs])
    db.close()
    response = llm.invoke([
        SystemMessage(content="You are a threat detection agent. Analyze the following audit logs. If you detect a threat such as repeated blocked requests from the same user, start your response with 'THREAT:'. If no threat, start with 'SAFE:'. Also extract the most suspicious user_id if THREAT."),
        HumanMessage(content=f"Audit Logs:\n{logs_str}")
    ])
    is_threat = response.content.startswith("THREAT")
    user_id = state.get("user_id", "unknown")
    if is_threat and "user_id:" in response.content.lower():
        for line in response.content.split("\n"):
            if "user_id:" in line.lower():
                user_id = line.split(":")[-1].strip()
                break
    return {"threat_detected": is_threat, "threat_summary": response.content, "user_id": user_id}

def enrichment_node(state: AgentState):
    user_id = state["user_id"]
    db = engine.connect()
    logs = db.execute(text("SELECT tool, action, block_reason, timestamp FROM audit_logs WHERE user_id = :user_id ORDER BY timestamp DESC LIMIT 100"), {"user_id": user_id}).fetchall()
    logs_str = "\n".join([str(row) for row in logs])
    db.close()
    response = llm.invoke([
        SystemMessage(content="You are a threat enrichment agent. Analyze this user's activity and provide a detailed threat assessment. Recommend one of: REVOKE_JWT, BLOCK_USER, MONITOR_ONLY, NO_ACTION."),
        HumanMessage(content=f"User ID: {user_id}\nThreat Summary: {state['threat_summary']}\nFull Activity:\n{logs_str}")
    ])
    return {"threat_summary": response.content}

def containment_node(state: AgentState):
    user_id = state["user_id"]
    response = llm.invoke([
        SystemMessage(content="You are a containment agent. Return only one of: REVOKE_JWT, BLOCK_USER, MONITOR_ONLY, NO_ACTION."),
        HumanMessage(content=f"User ID: {user_id}\nThreat Assessment: {state['threat_summary']}")
    ])
    action = response.content.strip()
    db = engine.connect()
    db.execute(text("INSERT INTO audit_logs (user_id, role, tool, action, blocked, block_reason) VALUES (:user_id, 'system', 'containment', :action, true, 'agentic_soc')"), {"user_id": user_id, "action": action})
    db.commit()
    db.close()
    return {"action_taken": action}

def should_contain(state: AgentState):
    if state["threat_detected"]:
        return "enrichment"
    return END

graph = StateGraph(AgentState)
graph.add_node("triage", triage_node)
graph.add_node("enrichment", enrichment_node)
graph.add_node("containment", containment_node)
graph.set_entry_point("triage")
graph.add_conditional_edges("triage", should_contain)
graph.add_edge("enrichment", "containment")
graph.add_edge("containment", END)
soc = graph.compile()

async def run_soc():
    redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
    while True:
        try:
            result = soc.invoke({
                "user_id": "unknown",
                "threat_detected": False,
                "threat_summary": "",
                "action_taken": ""
            })
            action = result.get("action_taken", "")
            user_id = result.get("user_id", "unknown")
            if "REVOKE" in action or "BLOCK" in action:
                await redis_client.set(f"blocklist:{user_id}", "blocked")
                print(f"SOC: Blocked user {user_id} -- action: {action}")
        except Exception as e:
            print(f"SOC error: {e}")
        await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(run_soc())
