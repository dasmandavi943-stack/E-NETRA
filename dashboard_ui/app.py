import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
import requests
from pathlib import Path

st.set_page_config(
    page_title="E-NETRA | MPLADS VigilAI Dashboard",
    page_icon="🛡️",
    layout="wide"
)

st.markdown("""
    <style>
    .main-header {font-size: 2.2rem; font-weight: 700; color: #1E293B; margin-bottom: 0;}
    .sub-header {font-size: 1rem; color: #64748B; margin-bottom: 1.5rem;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🛡️ E-NETRA — MPLADS VigilAI Integrity Dashboard</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">AI-Powered Expenditure Anomaly, Spatial EXIF Verification & Vendor Cartel Detection</p>', unsafe_allow_html=True)

@st.cache_data
def load_data():
    csv_path = Path(__file__).resolve().parent.parent / "data" / "final_risk_scores.csv"
    df = pd.read_csv(csv_path)
    df["graph_flags"] = df["graph_flags"].fillna("None").replace("", "None")
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Could not load data/final_risk_scores.csv: {e}")
    st.stop()

st.sidebar.header("🔍 Audit Filters")
selected_bands = st.sidebar.multiselect(
    "CRI Risk Band",
    options=["RED", "YELLOW", "GREEN"],
    default=["RED", "YELLOW", "GREEN"]
)

districts = sorted(df["district"].dropna().unique().tolist())
selected_districts = st.sidebar.multiselect(
    "District",
    options=districts,
    default=districts
)

filtered_df = df[
    (df["cri_band"].isin(selected_bands)) &
    (df["district"].isin(selected_districts))
]

col1, col2, col3, col4 = st.columns(4)
red_df = filtered_df[filtered_df["cri_band"] == "RED"]
yellow_df = filtered_df[filtered_df["cri_band"] == "YELLOW"]
funds_at_risk = red_df["sanctioned_amount"].sum() / 1e5

col1.metric("Total Projects Audited", f"{len(filtered_df):,}")
col2.metric("🔴 High-Risk (RED) Alerts", f"{len(red_df):,}", delta=f"{len(yellow_df)} Yellow", delta_color="inverse")
col3.metric("Sanctioned Funds at High Risk", f"₹{funds_at_risk:,.2f} L")
col4.metric("Cartel / Shared Bank Flags", f"{(filtered_df['vendors_per_bank'] > 1).sum():,}")

st.divider()

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("Risk Distribution by CRI Band")
    band_counts = filtered_df["cri_band"].value_counts().reset_index()
    band_counts.columns = ["CRI Band", "Projects"]
    fig_pie = px.pie(
        band_counts,
        names="CRI Band",
        values="Projects",
        color="CRI Band",
        color_discrete_map={"RED": "#EF4444", "YELLOW": "#F59E0B", "GREEN": "#10B981"},
        hole=0.45
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with chart_col2:
    st.subheader("Top 10 Highest Composite Risk Projects")
    top10 = filtered_df.sort_values("composite_risk_index", ascending=False).head(10)
    fig_bar = px.bar(
        top10,
        x="composite_risk_index",
        y="project_id",
        color="cri_band",
        orientation="h",
        color_discrete_map={"RED": "#EF4444", "YELLOW": "#F59E0B", "GREEN": "#10B981"},
        hover_data=["mp_name", "district", "vendor_name", "sanctioned_amount"]
    )
    fig_bar.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_bar, use_container_width=True)

st.subheader("📋 Prioritized Audit Queue (Sorted by Composite Risk Index)")
display_cols = [
    "project_id", "cri_band", "composite_risk_index", "ml_risk_score",
    "relational_graph_risk", "spatial_risk_score", "district", "mp_name",
    "vendor_name", "sanctioned_amount", "gps_mismatch_km", "graph_flags"
]
st.dataframe(
    filtered_df[display_cols].sort_values("composite_risk_index", ascending=False),
    use_container_width=True,
    height=320
)

st.divider()

st.subheader("🕵️ Project Forensic & Collusion Network Inspector")
sorted_ids = df.sort_values("composite_risk_index", ascending=False)["project_id"].tolist()
selected_project = st.selectbox("Select Project ID to Inspect:", options=sorted_ids, index=0)

proj = df[df["project_id"] == selected_project].iloc[0]

def build_local_subgraph(full_df, row):
    nodes, edges = [], []
    seen = set()

    def add_n(nid, label, ntype):
        if nid not in seen:
            nodes.append({"id": nid, "label": label, "type": ntype})
            seen.add(nid)

    pid = row["project_id"]
    vid = row["vendor_id"]
    bid = row["bank_account_id"]
    mp = row["mp_name"]
    addr = str(row["vendor_address"])[:28] + "..."

    add_n(pid, pid, "PROJECT")
    add_n(mp, mp, "MP")
    add_n(vid, f"{row['vendor_name']} ({vid})", "VENDOR")
    add_n(bid, bid, "BANK")
    add_n(addr, addr, "ADDRESS")

    edges.append({"source": mp, "target": pid})
    edges.append({"source": pid, "target": vid})
    edges.append({"source": vid, "target": bid})
    edges.append({"source": vid, "target": addr})

    # Add linked vendors/projects sharing the same bank account or MP-vendor cartel cluster
    shared_bank = full_df[(full_df["bank_account_id"] == bid) & (full_df["project_id"] != pid)].head(6)
    for _, r in shared_bank.iterrows():
        other_vid = r["vendor_id"]
        other_pid = r["project_id"]
        add_n(other_vid, f"{r['vendor_name']} ({other_vid})", "VENDOR")
        add_n(other_pid, other_pid, "PROJECT")
        edges.append({"source": other_vid, "target": bid})
        edges.append({"source": other_pid, "target": other_vid})

    same_vendor = full_df[(full_df["vendor_id"] == vid) & (full_df["project_id"] != pid)].head(5)
    for _, r in same_vendor.iterrows():
        other_pid = r["project_id"]
        add_n(other_pid, other_pid, "PROJECT")
        edges.append({"source": other_pid, "target": vid})

    return nodes, edges

det_col1, det_col2 = st.columns([1, 1.4])

with det_col1:
    st.markdown(f"### `{proj['project_id']}` — **{proj['cri_band']} RISK** (CRI: `{proj['composite_risk_index']}`)")
    st.write(f"**MP Name:** {proj['mp_name']} | **District:** {proj['district']}")
    st.write(f"**Work:** {proj['work_category']} (`{proj['status']}`)")
    st.write(f"**Sanctioned Amount:** ₹{proj['sanctioned_amount']:,.0f} (Released: ₹{proj['amount_released']:,.0f})")
    st.write(f"**Vendor:** {proj['vendor_name']} (`{proj['vendor_id']}`)")
    st.write(f"**Bank Account Hash:** `{proj['bank_account_id']}` (Vendors sharing bank: **{proj['vendors_per_bank']}**)")
    st.write(f"**GPS Site vs Photo Mismatch:** `{proj['gps_mismatch_km']} km`")
    st.write(f"**Graph Collusion Flags:** `{proj['graph_flags']}`")

    scores_df = pd.DataFrame({
        "Module": ["ML Anomaly", "Graph Collusion", "Spatial EXIF", "Composite CRI"],
        "Score": [proj["ml_risk_score"], proj["relational_graph_risk"], proj["spatial_risk_score"], proj["composite_risk_index"]]
    })
    fig_scores = px.bar(scores_df, x="Module", y="Score", range_y=[0, 100], color="Module", text="Score")
    fig_scores.update_layout(showlegend=False, height=280)
    st.plotly_chart(fig_scores, use_container_width=True)

with det_col2:
    st.markdown("### 🕸️ Vendor–Bank–Address Collusion Network")
    nodes, edges = [], []
    source_label = "Dataset Relational Subgraph"

    try:
        resp = requests.get(f"http://127.0.0.1:8003/api/v1/graph/project/{selected_project}", timeout=1.5)
        if resp.status_code == 200:
            graph_data = resp.json()
            nodes = graph_data.get("nodes", [])
            edges = graph_data.get("edges", [])
            source_label = "Live Graph API (Port 8003)"
    except Exception:
        pass

    if not nodes:
        nodes, edges = build_local_subgraph(df, proj)

    G = nx.Graph()
    for n in nodes:
        G.add_node(n["id"], label=n.get("label", n["id"]), ntype=n.get("type", "ENTITY"))
    for e in edges:
        G.add_edge(e["source"], e["target"])

    pos = nx.spring_layout(G, seed=42, k=0.9)
    edge_x, edge_y = [], []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=1.8, color="#94A3B8"), mode="lines")

    color_map = {"PROJECT": "#3B82F6", "VENDOR": "#EF4444", "BANK": "#F59E0B", "ADDRESS": "#8B5CF6", "MP": "#10B981"}
    node_x, node_y, node_text, node_color = [], [], [], []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        ntype = G.nodes[node]["ntype"]
        node_text.append(f"{ntype}: {G.nodes[node]['label']}")
        node_color.append(color_map.get(ntype, "#64748B"))

    node_trace = go.Scatter(
        x=node_x, y=node_y, mode="markers+text",
        text=[G.nodes[n]["label"] for n in G.nodes()],
        textposition="top center", hovertext=node_text, hoverinfo="text",
        marker=dict(size=22, color=node_color, line=dict(width=2, color="white"))
    )

    fig_net = go.Figure(data=[edge_trace, node_trace])
    fig_net.update_layout(
        showlegend=False, height=430, margin=dict(l=10, r=10, t=20, b=10),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
    )
    st.plotly_chart(fig_net, use_container_width=True)
    st.caption(f"Source: {source_label} | 🔵 Project  🔴 Vendor  🟡 Bank Account  🟣 Address  🟢 MP")
