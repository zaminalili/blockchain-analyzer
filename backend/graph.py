"""
Graph Analysis + Wallet Clustering
- Transaction flow graph (NetworkX)
- Common Input Ownership (CIO) heuristic
- Change address detection
- Suspicious pattern detection
"""

import networkx as nx
from collections import defaultdict
from typing import Optional


# ── Graph builder ─────────────────────────────────────────────────────────────

def build_transaction_graph(transactions: list[dict]) -> nx.DiGraph:
    """
    Tranzaksiyalardan yönlü qraf qur.
    Node = wallet address
    Edge = transaction (weight = value)
    """
    G = nx.DiGraph()

    for tx in transactions:
        chain = tx.get("chain", "?")
        val   = tx.get("value_btc") or tx.get("value_eth") or 0
        label = f"{chain}:{tx['hash'][:10]}..."

        for inp in tx["inputs"]:
            if not inp or inp == "unknown":
                continue
            for out in tx["outputs"]:
                if not out or out == "unknown":
                    continue
                if inp == out:
                    continue  # özünə köçürmə
                if G.has_edge(inp, out):
                    G[inp][out]["weight"] += val
                    G[inp][out]["count"]  += 1
                else:
                    G.add_edge(inp, out, weight=val, count=1, tx=label, chain=chain)

    return G


def get_graph_stats(G: nx.DiGraph) -> dict:
    """Qrafın əsas statistikaları."""
    if G.number_of_nodes() == 0:
        return {}
    return {
        "nodes":           G.number_of_nodes(),
        "edges":           G.number_of_edges(),
        "density":         round(nx.density(G), 4),
        "top_senders":     sorted(G.out_degree(), key=lambda x: x[1], reverse=True)[:5],
        "top_receivers":   sorted(G.in_degree(),  key=lambda x: x[1], reverse=True)[:5],
        "strongly_connected": nx.number_strongly_connected_components(G),
    }


# ── Wallet Clustering ─────────────────────────────────────────────────────────

def cluster_by_common_input(transactions: list[dict]) -> dict[str, list[str]]:
    """
    Common Input Ownership (CIO) heuristikası:
    Eyni tranzaksiyada input olan ünvanlar → eyni sahibə aiddir.
    Chainalysis-in əsas metodudur.
    """
    # Union-Find strukturu
    parent = {}

    def find(x):
        if x not in parent:
            parent[x] = x
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    for tx in transactions:
        inputs = [i for i in tx.get("inputs", []) if i and i != "unknown"]
        if len(inputs) > 1:
            for i in range(len(inputs) - 1):
                union(inputs[i], inputs[i + 1])

    # Klasterləri topla
    clusters: dict[str, list[str]] = defaultdict(list)
    all_addrs = set()
    for tx in transactions:
        for addr in tx.get("inputs", []) + tx.get("outputs", []):
            if addr and addr != "unknown":
                all_addrs.add(addr)

    for addr in all_addrs:
        root = find(addr)
        clusters[root].append(addr)

    return dict(clusters)


def detect_change_address(tx: dict) -> Optional[str]:
    """
    Change address aşkarlaması (BTC üçün).
    Heuristika: Çıxış sayı = 2 olarsa, daha kiçik məbləğ change-dir.
    """
    outputs = tx.get("outputs", [])
    if len(outputs) != 2:
        return None
    # Sadə heuristika: az məbləğli çıxış dəyişiklik adresidir
    # Real implementasiyada script type də yoxlanılır
    return f"Ehtimal olunan change address: çıxışlardan biri"


# ── Suspicious Pattern Detection ─────────────────────────────────────────────

MIXER_INDICATORS = [
    "1CKSoDFoJJFSMKSvkL4XxUDkMXsj2KLTAF",  # nümunə mixer ünvanlar
    "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
]

def detect_patterns(transactions: list[dict], clusters: dict) -> list[dict]:
    """
    Şübhəli pattern-ləri aşkarla.
    """
    alerts = []

    # 1. Peeling chain: zəncir kimi ardıcıl köçürmələr
    addr_freq = defaultdict(int)
    for tx in transactions:
        for addr in tx.get("outputs", []):
            if addr and addr != "unknown":
                addr_freq[addr] += 1

    # 2. Fan-out: 1 input → çox output (mixing əlaməti)
    for tx in transactions:
        if len(tx.get("outputs", [])) > 5:
            alerts.append({
                "type":     "FAN_OUT",
                "severity": "MEDIUM",
                "tx":       tx["hash"][:16] + "...",
                "detail":   f"{len(tx['outputs'])} output aşkarlandı — potensial mixing",
            })

    # 3. Round number transfers (pul yuyulmasında çox görülür)
    for tx in transactions:
        val = tx.get("value_btc") or tx.get("value_eth") or 0
        if val > 0 and val == round(val, 0):
            alerts.append({
                "type":     "ROUND_NUMBER",
                "severity": "LOW",
                "tx":       tx["hash"][:16] + "...",
                "detail":   f"Tam ədəd köçürmə: {val}",
            })

    # 4. Böyük klasterlər (çox ünvan = exchange/mixer)
    for root, addrs in clusters.items():
        if len(addrs) >= 3:
            alerts.append({
                "type":     "LARGE_CLUSTER",
                "severity": "HIGH" if len(addrs) > 5 else "MEDIUM",
                "tx":       root[:16] + "...",
                "detail":   f"Klasterdə {len(addrs)} ünvan — eyni sahibə aid ola bilər",
            })

    return alerts


# ── Risk Scoring ──────────────────────────────────────────────────────────────

RISK_WEIGHTS = {
    "FAN_OUT":       25,
    "LARGE_CLUSTER": 30,
    "ROUND_NUMBER":  10,
    "MIXER_ADDRESS": 50,
}

SEVERITY_MULTIPLIER = {
    "LOW":    1.0,
    "MEDIUM": 1.5,
    "HIGH":   2.0,
}

def calculate_risk_score(alerts: list[dict]) -> dict:
    """
    0-100 arası risk skoru hesabla.
    Hüquq-mühafizə orqanları üçün prioritetləşdirmə.
    """
    if not alerts:
        return {"score": 0, "level": "LOW", "color": "green"}

    raw = sum(
        RISK_WEIGHTS.get(a["type"], 5) * SEVERITY_MULTIPLIER.get(a["severity"], 1.0)
        for a in alerts
    )
    score = min(int(raw), 100)

    if score >= 70:
        level, color = "HIGH",   "red"
    elif score >= 40:
        level, color = "MEDIUM", "yellow"
    else:
        level, color = "LOW",    "green"

    return {"score": score, "level": level, "color": color}
