from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import requests

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def dashboard():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>OmniGuard Admin</title>
    <style>
        body { background: #0e1117; color: white; font-family: sans-serif; padding: 40px; }
        h1 { margin-bottom: 30px; }
        .metrics { display: flex; gap: 40px; margin-bottom: 40px; }
        .metric { background: #1e2130; padding: 20px 30px; border-radius: 8px; min-width: 150px; }
        .metric-label { font-size: 14px; color: #aaa; margin-bottom: 8px; }
        .metric-value { font-size: 32px; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; background: #1e2130; border-radius: 8px; overflow: hidden; }
        th { background: #2a2d3e; padding: 12px 16px; text-align: left; font-size: 13px; color: #aaa; }
        td { padding: 12px 16px; border-top: 1px solid #2a2d3e; font-size: 13px; }
        .blocked { color: #ff4b4b; font-weight: bold; }
        .allowed { color: #21c55d; font-weight: bold; }
        button { background: #ff4b4b; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-bottom: 30px; }
    </style>
    <script>
        async function loadData() {
            const res = await fetch('https://prismbrain.co/admin/stats');
            const data = await res.json();
            document.getElementById('total').innerText = data.total_requests;
            document.getElementById('blocked').innerText = data.blocked_requests;
            document.getElementById('allowed').innerText = data.allowed_requests;
            document.getElementById('rate').innerText = data.block_rate;
            const tbody = document.getElementById('logs');
            tbody.innerHTML = '';
            data.recent_logs.forEach(log => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${log.user_id}</td>
                    <td>${log.role}</td>
                    <td>${log.tool}</td>
                    <td class="${log.blocked ? 'blocked' : 'allowed'}">${log.blocked ? 'BLOCKED' : 'ALLOWED'}</td>
                    <td>${log.block_reason || 'None'}</td>
                    <td>${log.timestamp}</td>
                `;
                tbody.appendChild(tr);
            });
        }
        loadData();
        setInterval(loadData, 5000);
    </script>
</head>
<body>
    <h1>OmniGuard Security Dashboard</h1>
    <button onclick="loadData()">Refresh</button>
    <div class="metrics">
        <div class="metric"><div class="metric-label">Total Requests</div><div class="metric-value" id="total">-</div></div>
        <div class="metric"><div class="metric-label">Blocked</div><div class="metric-value" id="blocked">-</div></div>
        <div class="metric"><div class="metric-label">Allowed</div><div class="metric-value" id="allowed">-</div></div>
        <div class="metric"><div class="metric-label">Block Rate</div><div class="metric-value" id="rate">-</div></div>
    </div>
    <h2>Recent Audit Logs</h2>
    <table>
        <thead><tr><th>User ID</th><th>Role</th><th>Tool</th><th>Status</th><th>Block Reason</th><th>Timestamp</th></tr></thead>
        <tbody id="logs"></tbody>
    </table>
</body>
</html>
"""
