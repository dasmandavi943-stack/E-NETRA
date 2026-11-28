import streamlit as st
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
import requests

st.set_page_config(
    page_title="E-NETRA | MPLADS VigilAI Integrity Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

@st.cache_data(ttl=5)
def load_data():
    return pd.read_csv("data/final_risk_scores.csv")

df = load_data()

qp = st.query_params
embed_mode = str(qp.get("embed", "false")).lower() == "true"
requested_pid = qp.get("project_id", None)

def build_local_subgraph(full_df, row):
    pid = str(row["project_id"])
    vid = str(row["vendor_id"])
    vname = str(row["vendor_name"])
    bid = str(row["bank_account_id"])
    addr = str(row["vendor_address"])[:28]
    mp = str(row["mp_name"])

    nodes = [
        {"id": pid, "label": pid, "type": "PROJECT"},
        {"id": vid, "label": f"{vname} ({vid})", "type": "VENDOR"},
        {"id": bid, "label": bid, "type": "BANK"},
        {"id": f"ADDR_{pid}", "label": addr, "type": "ADDRESS"},
        {"id": f"MP_{pid}", "label": mp, "type": "MP"},
    ]
    edges = [
        {"source": pid, "target": vid},
        {"source": vid, "target": bid},
        {"source": vid, "target": f"ADDR_{pid}"},
        {"source": pid, "target": f"MP_{pid}"},
    ]

    peer_projects = full_df[
        ((full_df["bank_account_id"] == bid) | (full_df["vendor_id"] == vid))
        & (full_df["project_id"] != pid)
    ].head(4)
    for _, pr in peer_projects.iterrows():
        ppid = str(pr["project_id"])
        nodes.append({"id": ppid, "label": ppid, "type": "PROJECT"})
        edges.append({"source": vid, "target": ppid})

    return nodes, edges

def render_network_graph(selected_project, proj, height=340):
    nodes, edges = [], []
    try:
        resp = requests.get(f"http://127.0.0.1:8003/api/v1/graph/project/{selected_project}", timeout=1.0)
        if resp.status_code == 200:
            data = resp.json()
            nodes = data.get("nodes", [])
            edges = data.get("edges", [])
    except Exception:
        pass
    if not nodes:
        nodes, edges = build_local_subgraph(df, proj)

    G = nx.Graph()
    for n in nodes:
        G.add_node(n["id"], label=n.get("label", n["id"]), ntype=n.get("type", "ENTITY"))
    for e in edges:
        G.add_edge(e["source"], e["target"])

    pos = nx.spring_layout(G, seed=42, k=1.25)
    edge_x, edge_y = [], []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=1.8, color="#cbd5e1"), mode="lines")
    color_map = {"PROJECT": "#2563eb", "VENDOR": "#dc2626", "BANK": "#d97706", "ADDRESS": "#7c3aed", "MP": "#059669"}
    node_x, node_y, node_text, node_color = [], [], [], []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        ntype = G.nodes[node]["ntype"]
        node_text.append(f"{ntype}: {G.nodes[node]['label']}")
        node_color.append(color_map.get(ntype, "#475569"))

    node_trace = go.Scatter(
        x=node_x, y=node_y, mode="markers+text",
        text=[G.nodes[n]["label"] for n in G.nodes()],
        textposition="top center",
        textfont=dict(size=10, color="#0f172a"),
        hovertext=node_text, hoverinfo="text",
        marker=dict(size=18, color=node_color, line=dict(width=2, color="#ffffff"))
    )
    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        showlegend=False,
        height=height,
        margin=dict(l=15, r=15, t=15, b=10),
        paper_bgcolor="#f8fafc",
        plot_bgcolor="#f8fafc",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1.4, 1.4]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1.4, 1.4]),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown(
        "<div style='font-size:11px;color:#475569;text-align:center;margin-top:-8px;'>"
        "|| Project &nbsp; || Vendor &nbsp; || Bank &nbsp; || Address &nbsp; || MP</div>",
        unsafe_allow_html=True,
    )

sorted_ids = df.sort_values("composite_risk_index", ascending=False)["project_id"].tolist()

# EMBEDDED MODE (Inside React Frontend Iframe | Clean Light Graph Only)
if embed_mode:
    st.markdown(
        """<style>
        [data-testid="stSidebar"], header, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] {display: none !important;}
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {background-color: #f8fafc !important; color: #0f172a !important;}
        .block-container {padding: 0.25rem 0.5rem 0rem 0.5rem !important; max-width: 100% !important;}
        </style>""",
        unsafe_allow_html=True,
    )
    selected_project = requested_pid if requested_pid in df["project_id"].values else sorted_ids[0]
    proj = df[df["project_id"] == selected_project].iloc[0]
    render_network_graph(selected_project, proj, height=345)
    st.stop()

# STANDALONE ANALYTICAL MODE (Matches React Counts 100%: 25 Projects, 5 High-Risk Alerts)
st.title("E-NETRA | MPLADS VigilAI Integrity Dashboard")
st.caption("Unified Multi-Modal Auditing: ML Expenditure Anomaly + Spatial EXIF GPS + Relational Collusion Graph")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Monitored Projects", len(df))
c2.metric("High-Risk (RED) Alerts", int((df["composite_risk_index"] >= 60).sum()))
c3.metric("Watchlist (YELLOW)", int(((df["composite_risk_index"] >= 35) & (df["composite_risk_index"] < 60)).sum()))
c4.metric("Safe Zone (GREEN)", int((df["composite_risk_index"] < 35).sum()))
st.divider()
default_idx = sorted_ids.index(requested_pid) if requested_pid in sorted_ids else 0
selected_project = st.selectbox("Select Project ID to Inspect:", options=sorted_ids, index=default_idx)
proj = df[df["project_id"] == selected_project].iloc[0]

col_left, col_right = st.columns([1, 1.4])
with col_left:
    st.subheader(f"{selected_project} | {proj['cri_band']} RISK")
    st.write(f"**Work:** {proj['work_category']} ({proj['district']})")
    st.write(f"**Vendor:** {proj['vendor_name']} (`{proj['vendor_id']}`)")
    st.write(f"**Bank Hash:** `{proj['bank_account_id']}`")
    st.write(f"**MP:** {proj['mp_name']}")
    st.write(f"**Composite CRI:** `{proj['composite_risk_index']:.2f}` | **ML:** `{proj['ml_risk_score']:.2f}` | **Graph:** `{proj['relational_graph_risk']:.2f}` | **Spatial:** `{proj['spatial_risk_score']:.2f}`")

with col_right:
    render_network_graph(selected_project, proj, height=380)
