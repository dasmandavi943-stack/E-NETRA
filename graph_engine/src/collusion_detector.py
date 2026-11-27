import os
import json
import pandas as pd
import networkx as nx
from collections import Counter

def build_vendor_graph(df: pd.DataFrame) -> nx.Graph:
    """Builds a relationship graph linking Contractors, BankAccounts, Addresses, and Tenders."""
    G = nx.Graph()

    for _, row in df.iterrows():
        c_id = row["contractor_id"]
        t_id = row["tender_id"]
        b_hash = f"BANK_{row['bank_account_hash']}"
        addr = f"ADDR_{row['registered_address']}"

        G.add_node(c_id, type="Contractor", name=row["contractor_name"], gstin=row["gstin"])
        G.add_node(t_id, type="Tender", project_id=row["project_id"], amount=row["sanctioned_amount"])
        G.add_node(b_hash, type="BankAccount")
        G.add_node(addr, type="Address")

        G.add_edge(c_id, t_id, relation="BID_ON", bid_amount=row["bid_amount"], is_winner=row["is_winner"])
        G.add_edge(c_id, b_hash, relation="USES_ACCOUNT")
        G.add_edge(c_id, addr, relation="LOCATED_AT")

    return G

def detect_collusion_and_score(csv_path="graph_engine/data/sample_vendors.csv"):
    df = pd.read_csv(csv_path)
    G = build_vendor_graph(df)

    # Precompute shared bank accounts and shared addresses across contractors
    bank_to_contractors = df.groupby("bank_account_hash")["contractor_id"].nunique().to_dict()
    addr_to_contractors = df.groupby("registered_address")["contractor_id"].nunique().to_dict()

    # Precompute co-bidding pairs (contractors bidding together on the same tender)
    pair_counts = Counter()
    for _, group in df.groupby("tender_id"):
        bidders = sorted(group["contractor_id"].unique())
        for i in range(len(bidders)):
            for j in range(i + 1, len(bidders)):
                pair_counts[(bidders[i], bidders[j])] += 1

    # Precompute split-tendering counts (multiple wins under 10 Lakh by same contractor in same district)
    under_threshold = df[(df["is_winner"] == True) & (df["sanctioned_amount"] < 1000000)]
    split_counts = under_threshold.groupby(["contractor_id", "district"]).size().to_dict()

    project_results = []

    for proj_id, proj_df in df.groupby("project_id"):
        risk_score = 0
        reasons = []
        involved_vendors = proj_df["contractor_name"].unique().tolist()

        # Check 1: Shared Bank Account among bidders
        for b_hash in proj_df["bank_account_hash"].unique():
            shared_cnt = bank_to_contractors.get(b_hash, 1)
            if shared_cnt > 1:
                risk_score += 45
                reasons.append(f"Shared Bank Account detected across {shared_cnt} competing vendors")
                break

        # Check 2: Shared Registered Address among bidders
        for addr in proj_df["registered_address"].unique():
            shared_cnt = addr_to_contractors.get(addr, 1)
            if shared_cnt > 1:
                risk_score += 30
                reasons.append(f"Shared Physical Address detected across {shared_cnt} vendors")
                break

        # Check 3: Repeat Co-Bidding Ring (same pair bidding together >= 3 times)
        bidders = sorted(proj_df["contractor_id"].unique())
        for i in range(len(bidders)):
            for j in range(i + 1, len(bidders)):
                co_bids = pair_counts.get((bidders[i], bidders[j]), 0)
                if co_bids >= 3:
                    risk_score += 20
                    reasons.append(f"Bidding Cartel Pattern: Vendors co-bid together on {co_bids} tenders")
                    break

        # Check 4: Split Tendering (< 10 Lakh repeated wins in same district)
        winners = proj_df[proj_df["is_winner"] == True]
        for _, w_row in winners.iterrows():
            s_cnt = split_counts.get((w_row["contractor_id"], w_row["district"]), 0)
            if s_cnt >= 3:
                risk_score += 65
                reasons.append(f"Split-Tendering Alert: {w_row['contractor_name']} won {s_cnt} projects under ?10L in {w_row['district']}")
                break

        # Cap score between 0 and 100
        final_score = min(100, risk_score)
        risk_level = "HIGH" if final_score >= 70 else ("MEDIUM" if final_score >= 35 else "LOW")

        project_results.append({
            "project_id": proj_id,
            "district": proj_df["district"].iloc[0],
            "work_category": proj_df["work_category"].iloc[0],
            "sanctioned_amount": int(proj_df["sanctioned_amount"].iloc[0]),
            "relational_graph_risk": final_score,
            "risk_level": risk_level,
            "involved_vendors": involved_vendors,
            "flags": reasons if reasons else ["No collusion anomalies detected"]
        })

    results_df = pd.DataFrame(project_results)
    os.makedirs("graph_engine/data", exist_ok=True)
    results_df.to_json("graph_engine/data/graph_risk_scores.json", orient="records", indent=2)

    flagged = results_df[results_df["relational_graph_risk"] > 0]
    print(f"Graph built with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    print(f"Analyzed {len(results_df)} projects -> Flagged {len(flagged)} suspicious projects!\n")
    print("Sample Flagged Projects:")
    print(flagged[["project_id", "district", "relational_graph_risk", "risk_level", "flags"]].to_string(index=False))

if __name__ == "__main__":
    detect_collusion_and_score()
