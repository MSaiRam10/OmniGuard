from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from typing import TypedDict
import sys
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
engine = create_engine(DB_URL)
llm = ChatOpenAI(model="gpt-4o-mini")

class AgentState(TypedDict):
    user_id: str
    threat_detected: bool
    threat_summary: str
    action_taken: str

def triage_node(state: AgentState):
    user_id = state["user_id"]
    db = engine.connect()
    logs = db.execute(text("SELECT * FROM audit_logs WHERE blocked = true ORDER BY timestamp DESC LIMIT 50")).fetchall()
    logs_str = "\n".join([str(row) for row in logs])
    response = llm.invoke([
        SystemMessage(content="You are a threat detection agent. Analyze the following audit logs and determine if there is a potential security threat."),
        HumanMessage(content=f"User ID: {user_id}\nAudit Logs:\n{logs_str}")
    ])
    db.close()
    return {"threat_detected": response.content.startswith("THREAT"), "threat_summary": response.content}

def enrichment_node(state: AgentState):
    user_id = state["user_id"]
    db = engine.connect()
    logs = db.execute(text("SELECT tool, action, block_reason, timestamp FROM audit_logs WHERE user_id = :user_id ORDER BY timestamp DESC LIMIT 100"), {"user_id": user_id}).fetchall()
    logs_str = "\n".join([str(row) for row in logs])
    db.close()
    response = llm.invoke([
        SystemMessage(content="You are a threat enrichment agent. Given a user's full activity history, provide a detailed threat assessment including patterns, severity, and recommended action."),
        HumanMessage(content=f"User ID: {user_id}\nThreat Summary: {state['threat_summary']}\nFull Activity:\n{logs_str}")
    ])
    return {"threat_summary": response.content}

def containment_node(state: AgentState):
    user_id = state["user_id"]
    response = llm.invoke([
        SystemMessage(content="You are a containment agent. Based on the threat assessment, decide what action to take. Options: REVOKE_JWT, BLOCK_USER, MONITOR_ONLY, NO_ACTION. Return only the action and a one line reason."),
        HumanMessage(content=f"User ID: {user_id}\nThreat Assessment: {state['threat_summary']}")
    ])
    action = response.content
    db = engine.connect()
    db.execute(text("INSERT INTO audit_logs (user_id, role, tool, action, blocked, block_reason) VALUES (:user_id, 'system', 'containment', :action, true, 'agentic_soc')"), {"user_id": user_id, "action": action})
    db.commit()
    db.close()
    return {"action_taken": action}

graph = StateGraph(AgentState)
graph.add_node("triage", triage_node)
graph.add_node("enrichment", enrichment_node)
graph.add_node("containment", containment_node)
graph.set_entry_point("triage")
graph.add_edge("triage", "enrichment")
graph.add_edge("enrichment", "containment")
graph.add_edge("containment", END)

soc = graph.compile()
