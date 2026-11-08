"""
Command Center Dashboard — Streamlit
====================================
Real-time monitoring dashboard for AI Agent Lintas Platform.

Usage:
    pip install streamlit
    streamlit run command_center_dashboard.py

Features:
- System health monitoring
- Job queue tracker
- Approval panel
- Model router visualization
- Cost dashboard
- Node status
"""

import streamlit as st
import httpx
import os
import json
from pathlib import Path
from datetime import datetime

# Load .env
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

# Streamlit Cloud secrets
try:
    for key in ["SUPABASE_URL", "SUPABASE_SECRET_KEY", "CLICKUP_API_TOKEN", "CLICKUP_LIST_ID", "CLICKUP_TEAM_ID", "OPENROUTER_API_KEY"]:
        if key in st.secrets:
            os.environ[key] = st.secrets[key]
except Exception:
    pass

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY", "")
CLICKUP_TOKEN = os.getenv("CLICKUP_API_TOKEN", "")
CLICKUP_LIST_ID = os.getenv("CLICKUP_LIST_ID", "")
CLICKUP_TEAM_ID = os.getenv("CLICKUP_TEAM_ID", "")

st.set_page_config(
    page_title="Command Center — AI Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
with st.sidebar:
    st.title("🤖 Command Center")
    st.caption("AI Agent Lintas Platform")
    st.divider()

    page = st.radio(
        "Navigation",
        ["📊 Dashboard", "📋 Job Queue", "✅ Approvals", "🧠 Model Router", "💰 Cost", "🖥️ Node Status"],
        index=0,
    )

    st.divider()
    st.caption(f"Updated: {datetime.now().strftime('%H:%M:%S')}")
    if st.button("🔄 Refresh"):
        st.rerun()

# ─────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────
def get_supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }

def fetch_jobs(status=None):
    url = f"{SUPABASE_URL}/rest/v1/jobs?select=*&order=created_at.desc&limit=50"
    if status:
        url += f"&status=eq.{status}"
    try:
        r = httpx.get(url, headers=get_supabase_headers(), timeout=10)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []

def fetch_node_status():
    url = f"{SUPABASE_URL}/rest/v1/node_status?select=*"
    try:
        r = httpx.get(url, headers=get_supabase_headers(), timeout=10)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []

def check_health(url):
    try:
        r = httpx.get(url, timeout=5)
        return r.status_code == 200
    except Exception:
        return False

# ─────────────────────────────────────────────
# Page: Dashboard
# ─────────────────────────────────────────────
if page == "📊 Dashboard":
    st.header("📊 System Dashboard")

    # Health metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ollama_ok = check_health("http://127.0.0.1:11434/api/tags")
        st.metric("Ollama (Local LLM)", "✅ Online" if ollama_ok else "❌ Offline", "qwen3.5:4b")
    with col2:
        fastapi_ok = check_health("http://localhost:8000/health")
        st.metric("FastAPI (Backend)", "✅ Running" if fastapi_ok else "❌ Down", "port 8000")
    with col3:
        supabase_ok = check_health(f"{SUPABASE_URL}/rest/v1/")
        st.metric("Supabase (DB)", "✅ Connected" if supabase_ok else "❌ Disconnected", "3 tables")
    with col4:
        tunnel_ok = check_health("http://127.0.0.1:20243/metrics")
        st.metric("Cloudflare Tunnel", "✅ Active" if tunnel_ok else "❌ Inactive", "named tunnel")

    st.divider()

    # Job stats
    jobs = fetch_jobs()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        queued = len([j for j in jobs if j.get("status") == "queued"])
        st.metric("Queued", queued)
    with col2:
        running = len([j for j in jobs if j.get("status") == "running"])
        st.metric("Running", running)
    with col3:
        done = len([j for j in jobs if j.get("status") == "done"])
        st.metric("Done", done)
    with col4:
        failed = len([j for j in jobs if j.get("status") == "failed"])
        st.metric("Failed", failed)

    st.divider()

    # Recent jobs
    st.subheader("Recent Jobs")
    if jobs:
        for job in jobs[:10]:
            status_icon = {"queued": "⏳", "running": "🔄", "done": "✅", "failed": "❌", "cancelled": "🚫"}.get(job.get("status"), "❓")
            st.write(f"{status_icon} **{job.get('source', 'unknown')}** — {job.get('status', 'unknown')} — Tier {job.get('tier', '?')} — {job.get('created_at', '')[:19]}")
    else:
        st.info("No jobs yet. Create a task in ClickUp to get started.")

# ─────────────────────────────────────────────
# Page: Job Queue
# ─────────────────────────────────────────────
elif page == "📋 Job Queue":
    st.header("📋 Job Queue")

    status_filter = st.selectbox("Filter by status", ["All", "queued", "running", "done", "failed", "cancelled"])
    jobs = fetch_jobs(status_filter if status_filter != "All" else None)

    if jobs:
        for job in jobs:
            with st.expander(f"{job.get('source', 'unknown')} — {job.get('status', 'unknown')} — {job.get('created_at', '')[:19]}"):
                st.json(job)
    else:
        st.info("No jobs found.")

# ─────────────────────────────────────────────
# Page: Approvals
# ─────────────────────────────────────────────
elif page == "✅ Approvals":
    st.header("✅ Approval Panel")

    st.info("Ubah status task di ClickUp dari 'to do' → 'complete' (approve) atau 'cancelled' (reject).")
    st.markdown(f"[Buka ClickUp →](https://app.clickup.com/{CLICKUP_TEAM_ID})")

    # Fetch tasks from ClickUp
    try:
        r = httpx.get(
            f"https://api.clickup.com/api/v2/list/{CLICKUP_LIST_ID}/task",
            headers={"Authorization": CLICKUP_TOKEN},
            timeout=10,
        )
        tasks = r.json().get("tasks", [])
        pending = [t for t in tasks if t.get("status", {}).get("status", "").lower() in ["to do", "open"]]
        if pending:
            for task in pending:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"**{task.get('name', 'Unnamed')}**")
                        st.caption(task.get("description", "")[:100])
                    with col2:
                        if st.button("✅ Approve", key=f"approve_{task['id']}"):
                            httpx.put(
                                f"https://api.clickup.com/api/v2/task/{task['id']}",
                                headers={"Authorization": CLICKUP_TOKEN, "Content-Type": "application/json"},
                                json={"status": "complete"},
                            )
                            st.success("Approved!")
                            st.rerun()
                    with col3:
                        if st.button("❌ Reject", key=f"reject_{task['id']}"):
                            httpx.put(
                                f"https://api.clickup.com/api/v2/task/{task['id']}",
                                headers={"Authorization": CLICKUP_TOKEN, "Content-Type": "application/json"},
                                json={"status": "cancelled"},
                            )
                            st.error("Rejected!")
                            st.rerun()
                    st.divider()
        else:
            st.success("No pending approvals. All clear! ✅")
    except Exception as e:
        st.error(f"Error fetching tasks: {e}")

# ─────────────────────────────────────────────
# Page: Model Router
# ─────────────────────────────────────────────
elif page == "🧠 Model Router":
    st.header("🧠 Model Router — Tier Visualization")

    tiers = [
        {"tier": 0, "name": "Local", "model": "Ollama + Hermes", "use": "Data sensitif, massal, draft murah", "color": "#4CAF50"},
        {"tier": 1, "name": "Cheap", "model": "DeepSeek / Gemini Flash", "use": "Klasifikasi, ringkasan, ekstraksi", "color": "#2196F3"},
        {"tier": 2, "name": "Quality", "model": "Claude / ChatGPT / Gemini Pro", "use": "Penulisan, coding, analisis", "color": "#FF9800"},
        {"tier": 3, "name": "Special", "model": "Grok / Gemini", "use": "Riset real-time, dokumen besar", "color": "#9C27B0"},
    ]

    for t in tiers:
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 3])
            with col1:
                st.markdown(f"### Tier {t['tier']}")
            with col2:
                st.markdown(f"**{t['name']}**")
                st.caption(t["model"])
            with col3:
                st.caption(t["use"])
            st.divider()

    st.subheader("Routing Rules")
    st.markdown("""
    - **sensitivity=high** → Tier 0 (Local only, cannot leave)
    - **Tier 0 fails** → Fallback to Tier 1
    - **Tier 1 fails** → Fallback to Tier 2
    - **Tier 2 fails** → Fallback to Tier 3
    - **Tier 3 fails** → Fallback to Tier 2
    """)

    # Test pick_model
    st.subheader("Test Model Selection")
    test_payload = st.text_input("Enter test payload", "Summarize this article about AI")
    test_sensitivity = st.selectbox("Sensitivity", ["low", "high"])
    test_tier = st.slider("Tier", 0, 3, 1)
    if st.button("Pick Model"):
        from model_router import pick_model
        model = pick_model({"sensitivity": test_sensitivity, "tier": test_tier, "payload": test_payload})
        st.success(f"Selected: {model.model}")

# ─────────────────────────────────────────────
# Page: Cost Dashboard
# ─────────────────────────────────────────────
elif page == "💰 Cost":
    st.header("💰 Cost Dashboard")

    jobs = fetch_jobs()
    total_cost = sum(j.get("cost_usd", 0) or 0 for j in jobs)
    total_tokens = sum(j.get("tokens", 0) or 0 for j in jobs)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Cost", f"${total_cost:.4f}")
    with col2:
        st.metric("Total Tokens", f"{total_tokens:,}")
    with col3:
        st.metric("Total Jobs", len(jobs))

    st.divider()

    # Cost by tier
    st.subheader("Cost by Tier")
    tier_costs = {}
    for job in jobs:
        tier = job.get("tier", 0)
        cost = job.get("cost_usd", 0) or 0
        tier_costs[tier] = tier_costs.get(tier, 0) + cost

    if tier_costs:
        for tier, cost in sorted(tier_costs.items()):
            st.write(f"Tier {tier}: ${cost:.4f}")
    else:
        st.info("No cost data yet.")

# ─────────────────────────────────────────────
# Page: Node Status
# ─────────────────────────────────────────────
elif page == "🖥️ Node Status":
    st.header("🖥️ Node Status — Local AI Node")

    nodes = fetch_node_status()
    if nodes:
        for node in nodes:
            col1, col2, col3 = st.columns(3)
            with col1:
                state = node.get("state", "unknown")
                state_icon = {"on": "🟢", "off": "🔴", "waking": "🟡"}.get(state, "⚪")
                st.metric("State", f"{state_icon} {state.upper()}")
            with col2:
                st.write(f"**Node:** {node.get('node', 'unknown')}")
                st.caption(f"Last job: {node.get('last_job_at', 'N/A')}")
            with col3:
                st.write(f"Wake requested: {node.get('wake_requested', False)}")
                st.caption(f"Last seen: {node.get('last_seen', 'N/A')}")
            st.divider()
    else:
        st.warning("No node status found. Insert default node in Supabase.")

    # Wake button
    if st.button("🔔 Wake Node"):
        try:
            httpx.patch(
                f"{SUPABASE_URL}/rest/v1/node_status?node=eq.local-ai-node",
                headers=get_supabase_headers(),
                json={"wake_requested": True, "state": "waking"},
            )
            st.success("Wake request sent!")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

    # Shutdown button
    if st.button("⏻ Shutdown Node"):
        try:
            httpx.patch(
                f"{SUPABASE_URL}/rest/v1/node_status?node=eq.local-ai-node",
                headers=get_supabase_headers(),
                json={"state": "off", "wake_requested": False},
            )
            st.warning("Shutdown request sent!")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
