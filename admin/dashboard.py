import streamlit as st
import requests
import pandas as pd

GATEWAY_URL = "https://prismbrain.co"

st.set_page_config(page_title="OmniGuard Admin", layout="wide")
st.title("OmniGuard Security Dashboard")

if st.button("Refresh"):
    st.rerun()

try:
    data = requests.get(f"{GATEWAY_URL}/admin/stats").json()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Requests", data["total_requests"])
    col2.metric("Blocked", data["blocked_requests"])
    col3.metric("Allowed", data["allowed_requests"])
    col4.metric("Block Rate", data["block_rate"])

    st.subheader("Top Blocked Users")
    if data["top_blocked_users"]:
        df_users = pd.DataFrame(data["top_blocked_users"])
        st.bar_chart(df_users.set_index("user_id"))
    else:
        st.info("No blocked users yet")

    st.subheader("Recent Audit Logs")
    if data["recent_logs"]:
        df_logs = pd.DataFrame(data["recent_logs"])
        df_logs["blocked"] = df_logs["blocked"].map({True: "BLOCKED", False: "ALLOWED"})
        st.dataframe(df_logs, use_container_width=True)
    else:
        st.info("No logs yet")

except Exception as e:
    st.error(f"Could not connect to OmniGuard: {e}")
