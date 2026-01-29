import pandas as pd
import networkx as nx
from typing import Dict, List, Tuple

# -------------------------------------------------
# CONFIG (INTERNAL)
# -------------------------------------------------
MIN_HOP_LENGTH = 3          # Minimum nodes in path (A→B→C)
TIME_WINDOW_DAYS = 7        # Temporal constraint


# -------------------------------------------------
# CORE BACKEND FUNCTION
# -------------------------------------------------
def detect_suspicious_multihop_transfers(
    dataset_path: str
) -> Dict[str, object]:
    """
    Silent backend function.
    No prints, no files, no UI, no JSON.
    Returns results only for internal backend use.
    """

    # -----------------------------
    # LOAD DATA
    # -----------------------------
    df = pd.read_excel(dataset_path)

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

    for _, r in df.iterrows():
        G.add_edge(
            r["source_code"],
            r["destination_code"],
            amount=r["cc1 lcu amount"],
            date=r["date"]
        )

    # -----------------------------
    # MULTI-HOP DETECTION
    # -----------------------------
    suspicious_paths: List[List[str]] = []

    nodes = list(G.nodes())

    for src in nodes:
        for dst in nodes:
            if src == dst:
                continue

            try:
                path = nx.shortest_path(G, src, dst)
            except nx.NetworkXNoPath:
                continue

            # hop length check
            if len(path) < MIN_HOP_LENGTH:
                continue

            # temporal consistency check
            edge_dates = []
            for i in range(len(path) - 1):
                edge_data = G.get_edge_data(path[i], path[i + 1])
                if edge_data and "date" in edge_data:
                    edge_dates.append(edge_data["date"])

            if edge_dates:
                if (max(edge_dates) - min(edge_dates)).days <= TIME_WINDOW_DAYS:
                    suspicious_paths.append(path)

    # -----------------------------
    # AGGREGATION (INTERNAL)
    # -----------------------------
    unique_suspicious_pairs: List[Tuple[str, str]] = list(
        set((p[0], p[-1]) for p in suspicious_paths)
    )

    total_transactions = G.number_of_edges()

    suspicious_rate = (
        len(unique_suspicious_pairs) / total_transactions
        if total_transactions > 0 else 0.0
    )

    # -----------------------------
    # SILENT RETURN (BACKEND ONLY)
    # -----------------------------
    return {
        "total_transactions": total_transactions,
        "suspicious_multihop_paths": suspicious_paths,
        "unique_suspicious_pairs": unique_suspicious_pairs,
        "multihop_suspicion_rate": suspicious_rate
    }
