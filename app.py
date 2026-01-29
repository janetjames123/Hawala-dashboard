import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Hawala & Illicit Flow Analytics Dashboard",
    layout="wide"
)

st.title("Hawala & Illicit Financial Flow Detection Dashboard")

# -----------------------------
# LOAD DATA
# -----------------------------
DATA_FILE = "dataset_2_cleaning.xlsx"

df = pd.read_excel(DATA_FILE)

# Basic cleaning
df = df.dropna(subset=[
    "source_code",
    "destination_code",
    "cc1 lcu amount",
    "date"
])

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"])

# -----------------------------
# BUILD TRANSACTION GRAPH
# -----------------------------
G = nx.DiGraph()

for _, row in df.iterrows():
    G.add_edge(
        row["source_code"],
        row["destination_code"],
        amount=row["cc1 lcu amount"]
    )

total_edges = G.number_of_edges()

# -----------------------------
# MULTI-HOP DETECTION
# -----------------------------
multi_hop_pairs = set()

for s in G.nodes():
    for t in G.nodes():
        if s != t:
            try:
                if nx.shortest_path_length(G, s, t) >= 3:
                    multi_hop_pairs.add((s, t))
            except:
                pass

multi_hop_rate = len(multi_hop_pairs) / total_edges if total_edges else 0

# -----------------------------
# CIRCULAR ROUTING DETECTION
# -----------------------------
cycles = list(nx.simple_cycles(G))

cycle_edges = set()
for c in cycles:
    for i in range(len(c)):
        cycle_edges.add((c[i], c[(i + 1) % len(c)]))

circular_rate = len(cycle_edges) / total_edges if total_edges else 0

# -----------------------------
# MIRRORED FLOW DETECTION
# -----------------------------
df["rounded_amount"] = df["cc1 lcu amount"].round(-2)
mirrored_df = df.groupby("rounded_amount").filter(lambda x: len(x) > 3)

mirrored_rate = mirrored_df.shape[0] / df.shape[0]

# -----------------------------
# CORRIDOR ANALYSIS
# -----------------------------
df["corridor"] = df["source_code"] + " → " + df["destination_code"]

corridor_counts = (
    df.groupby("corridor")
    .size()
    .sort_values(ascending=False)
    .head(15)
)

corridor_rate = len(corridor_counts) / df["corridor"].nunique()

# -----------------------------
# TIME EVOLUTION
# -----------------------------
df["month"] = df["date"].dt.to_period("M").astype(str)

monthly_volume = df.groupby("month").size()
monthly_corridors = df.groupby("month")["corridor"].nunique()

# -----------------------------
# FINAL HAWALA RATE
# -----------------------------
hawala_rate = (
    0.35 * multi_hop_rate +
    0.30 * circular_rate +
    0.20 * mirrored_rate +
    0.15 * corridor_rate
)

# -----------------------------
# DASHBOARD METRICS
# -----------------------------
st.subheader("📊 Network Risk Metrics")

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Multi-hop Transfer Rate", f"{multi_hop_rate*100:.2f}%")
c2.metric("Circular Routing Rate", f"{circular_rate*100:.2f}%")
c3.metric("Mirrored Flow Rate", f"{mirrored_rate*100:.2f}%")
c4.metric("High-risk Corridor Share", f"{corridor_rate*100:.2f}%")
c5.metric("Overall Hawala-like Rate", f"{hawala_rate*100:.2f}%")

# -----------------------------
# NETWORK VISUALIZATION
# -----------------------------
st.subheader("🔁 Transaction Network (Circular Routes Highlighted)")

pos = nx.spring_layout(G, seed=42)

plt.figure(figsize=(10, 8))
nx.draw(G, pos, node_size=20, alpha=0.3)
nx.draw_networkx_edges(
    G,
    pos,
    edgelist=list(cycle_edges),
    edge_color="red",
    width=2
)

st.pyplot(plt)

# -----------------------------
# CORRIDOR-WISE BAR CHART
# -----------------------------
st.subheader("🌍 Corridor-wise Transaction Concentration")

plt.figure(figsize=(10, 5))
corridor_counts.plot(kind="bar")
plt.ylabel("Transaction Count")
plt.xlabel("Corridor")
plt.xticks(rotation=45, ha="right")
st.pyplot(plt)

# -----------------------------
# TIME EVOLUTION GRAPHS
# -----------------------------
st.subheader("⏳ Time Evolution Analysis")

colA, colB = st.columns(2)

with colA:
    plt.figure(figsize=(6, 4))
    monthly_volume.plot(marker="o")
    plt.title("Monthly Transaction Volume")
    plt.xlabel("Month")
    plt.ylabel("Transactions")
    plt.xticks(rotation=45)
    st.pyplot(plt)

with colB:
    plt.figure(figsize=(6, 4))
    monthly_corridors.plot(marker="o", color="orange")
    plt.title("Monthly Active Corridors")
    plt.xlabel("Month")
    plt.ylabel("Unique Corridors")
    plt.xticks(rotation=45)
    st.pyplot(plt)

# -----------------------------
# FOOTER
# -----------------------------
st.markdown("""
---
### 📌 Methodology Summary
- Transaction network modeled as a directed graph  
- Hawala-like behavior identified via:
  - multi-hop transfers  
  - circular routing  
  - mirrored flow symmetry  
  - corridor concentration  
  - temporal evolution  

This system provides **deterministic, explainable, and reproducible** analytics suitable for illicit financial flow detection.
""")
