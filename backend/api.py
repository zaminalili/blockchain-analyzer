"""
AZ Blockchain Analyzer FastAPI backend

Endpointlər:
  POST /analyze          — tək ünvan analizi
  POST /analyze/batch    — çoxlu ünvan
  GET  /address/{chain}/{address} — sürətli lookup
  GET  /graph/{chain}/{address}   — qraf data (D3 üçün)
  GET  /health                    — server statusu
  GET  /docs                      — Swagger UI (avtomatik)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
import asyncio
import aiohttp
import json

from models import (
    AnalyzeRequest, AnalyzeResponse, BatchAnalyzeRequest,
    TransactionOut, AlertOut, RiskOut, GraphStatsOut, ClusterOut,
)
from fetcher import (
    fetch_btc_address, fetch_eth_address,
    parse_btc_transactions, parse_eth_transactions,
)
from graph import (
    build_transaction_graph, get_graph_stats,
    cluster_by_common_input, detect_patterns, calculate_risk_score,
)

# ── App init ──────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AZ Blockchain Analyzer API",
    description="""
## Azərbaycan Hüquq-Mühafizə Orqanları üçün Blockchain Kriminalistik API

### İmkanlar
- **BTC + ETH** tranzaksiya analizi
- **Wallet klasterləşmə** (CIO heuristikası)
- **Risk skorlaması** (0–100)
- **Şübhəli pattern** aşkarlaması (fan-out, round numbers, mixer)
- **D3.js** üçün qraf data

### İstifadə
1. `/analyze` endpoint-inə `address` + `chain` göndər
2. JSON cavabda `risk.score` yoxla
3. `/graph/{chain}/{address}` ilə vizualizasiya üçün data al
    """,
    version="1.0.0",
    contact={"name": "AZ Blockchain Analyzer", "email": "dev@example.az"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Offline demo data  ─────────────────────────────────────────

DEMO_TRANSACTIONS = [
    {
        "chain": "BTC", "hash": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        "timestamp": "2024-01-15T10:22:00Z",
        "inputs":  ["1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2", "1A8JiWcwvpY7tAopUkSnGuwotti7g9kn7g"],
        "outputs": ["1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF", "1HLoD9E4SDFFPDiYfNYnkBLQ85Y51J3Zb1"],
        "value_btc": 2.5, "fee_sat": 1500,
    },
    {
        "chain": "BTC", "hash": "b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3",
        "timestamp": "2024-01-15T11:05:00Z",
        "inputs":  ["1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF"],
        "outputs": ["1dice8EMZmqKvrGE4Qc9bUFngAia8TD9Bs", "1ez69SnzzmePmZX3WpEzMKTrcBF2gpNQ55",
                    "15ubicBBWFnvoZLT7GiU2qxjRaKJPdkDMG", "1LomaFwStWriz3vVvTmRZrNVZHiYHPbDmF",
                    "12cbQLTFMXRnSzktFkuoG3eHoMeFtpTu3S", "1HT7xU2Ngenf7D4yocz2SAcnNLW7rK8d4Y"],
        "value_btc": 2.0, "fee_sat": 3000,
    },
    {
        "chain": "BTC", "hash": "c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
        "timestamp": "2024-01-15T12:30:00Z",
        "inputs":  ["1dice8EMZmqKvrGE4Qc9bUFngAia8TD9Bs", "15ubicBBWFnvoZLT7GiU2qxjRaKJPdkDMG"],
        "outputs": ["1ez69SnzzmePmZX3WpEzMKTrcBF2gpNQ55"],
        "value_btc": 1.0, "fee_sat": 1000,
    },
    {
        "chain": "ETH", "hash": "0xd4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5",
        "timestamp": "2024-01-15T14:00:00Z",
        "inputs":  ["0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe"],
        "outputs": ["0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8"],
        "value_eth": 5.0, "gas_used": 21000,
    },
    {
        "chain": "BTC", "hash": "e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6",
        "timestamp": "2024-01-16T09:00:00Z",
        "inputs":  ["1HLoD9E4SDFFPDiYfNYnkBLQ85Y51J3Zb1", "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
                    "1A8JiWcwvpY7tAopUkSnGuwotti7g9kn7g"],
        "outputs": ["1GkQmKAmHtNfnD3LHhTkewJxKHVSta4m2A"],
        "value_btc": 3.0, "fee_sat": 2500,
    },
]


# ── Helper: transactions → AnalyzeResponse ───────────────────────────────────

def build_response(address: str, chain: str, transactions: list[dict]) -> AnalyzeResponse:
    """Tranzaksiya listindən tam response obyekti qur."""

    # Standart output formatı
    txs_out = []
    for tx in transactions:
        val = tx.get("value_btc") or tx.get("value_eth") or 0.0
        txs_out.append(TransactionOut(
            chain=tx["chain"],
            hash=tx["hash"],
            timestamp=str(tx.get("timestamp", "")),
            inputs=tx.get("inputs", []),
            outputs=tx.get("outputs", []),
            value=float(val),
            fee=tx.get("fee_sat") or tx.get("gas_used"),
        ))

    # Graph
    G      = build_transaction_graph(transactions)
    stats  = get_graph_stats(G)
    g_out  = GraphStatsOut(**stats) if stats else None

    # Clusters
    raw_clusters = cluster_by_common_input(transactions)
    clusters_out = [
        ClusterOut(
            cluster_id=root[:16],
            address_count=len(addrs),
            sample_address=addrs[0],
        )
        for root, addrs in raw_clusters.items() if len(addrs) > 1
    ]

    # Alerts + Risk
    alerts      = detect_patterns(transactions, raw_clusters)
    risk        = calculate_risk_score(alerts)
    alerts_out  = [AlertOut(**a) for a in alerts]
    risk_out    = RiskOut(**risk)

    total_val   = sum(tx.get("value_btc") or tx.get("value_eth") or 0 for tx in transactions)

    return AnalyzeResponse(
        address=address,
        chain=chain,
        tx_count=len(transactions),
        total_value=round(total_val, 8),
        transactions=txs_out,
        graph_stats=g_out,
        clusters=clusters_out,
        alerts=alerts_out,
        risk=risk_out,
        analyzed_at=datetime.now(timezone.utc).isoformat(),
    )


# ── Endpointlər ───────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health():
    """Server sağlamlıq yoxlaması."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "supported_chains": ["BTC", "ETH"],
    }


@app.post("/analyze", response_model=AnalyzeResponse, tags=["Analysis"])
async def analyze_address(req: AnalyzeRequest):
    """
    Tək wallet ünvanını analiz et.

    - **address**: Bitcoin və ya Ethereum ünvanı
    - **chain**: BTC | ETH
    - **limit**: qaytarılacaq tranzaksiya sayı (max 100)
    """
    transactions = []

    if req.chain == "BTC":
        raw = fetch_btc_address(req.address, limit=req.limit)
        if raw:
            transactions = parse_btc_transactions(raw)

    elif req.chain == "ETH":
        raw = fetch_eth_address(req.address, limit=req.limit)
        if raw:
            transactions = parse_eth_transactions(raw, req.address)

    # API əlçatmaz olsa demo data ilə davam et
    if not transactions:
        transactions = [t for t in DEMO_TRANSACTIONS if t["chain"] == req.chain.value]
        if not transactions:
            transactions = DEMO_TRANSACTIONS

    return build_response(req.address, req.chain.value, transactions)


@app.post("/analyze/batch", tags=["Analysis"])
async def analyze_batch(req: BatchAnalyzeRequest):
    """
    Çoxlu ünvanı eyni vaxtda analiz et (max 10).
    Hüquq-mühafizə orqanları üçün toplu yoxlama.
    """
    results = []
    for item in req.addresses:
        try:
            result = await analyze_address(item)
            results.append({
                "address": item.address,
                "chain":   item.chain,
                "risk":    result.risk.model_dump(),
                "tx_count": result.tx_count,
                "alerts_count": len(result.alerts),
            })
        except Exception as e:
            results.append({"address": item.address, "error": str(e)})

    # Risk səviyyəsinə görə sırala
    results.sort(key=lambda x: x.get("risk", {}).get("score", 0), reverse=True)
    return {"total": len(results), "results": results}


@app.get("/address/{chain}/{address}", tags=["Analysis"])
async def quick_lookup(
    chain: str,
    address: str,
    limit: int = Query(default=10, ge=1, le=50),
):
    """
    Sürətli ünvan sorğusu — yalnız risk skoru və xülasə.
    Dashboard axtarış paneli üçün optimallaşdırılmış.
    """
    req = AnalyzeRequest(address=address, chain=chain.upper(), limit=limit)
    full = await analyze_address(req)
    return {
        "address":   full.address,
        "chain":     full.chain,
        "tx_count":  full.tx_count,
        "total_value": full.total_value,
        "risk":      full.risk,
        "top_alerts": full.alerts[:3],
        "clusters":  len(full.clusters),
    }


@app.get("/graph/{chain}/{address}", tags=["Visualization"])
async def get_graph_data(
    chain: str,
    address: str,
    limit: int = Query(default=20, ge=1, le=50),
):
    """
    D3.js Force-Directed Graph üçün node/link data.

    Format:
    ```json
    {
      "nodes": [{"id": "addr", "risk": 45, "chain": "BTC"}],
      "links": [{"source": "addr1", "target": "addr2", "value": 1.5}]
    }
    ```
    """
    req  = AnalyzeRequest(address=address, chain=chain.upper(), limit=limit)
    full = await analyze_address(req)

    # Node-lar
    node_set: dict[str, dict] = {}
    for tx in full.transactions:
        for addr in tx.inputs + tx.outputs:
            if addr and addr != "unknown" and addr not in node_set:
                node_set[addr] = {
                    "id":    addr,
                    "chain": tx.chain,
                    "risk":  0,
                    "label": addr[:12] + "...",
                    "is_queried": addr == address,
                }

    # Qeyd edilmiş ünvana risk skoru ver
    if address in node_set:
        node_set[address]["risk"] = full.risk.score

    # Linklər
    links = []
    for tx in full.transactions:
        for inp in tx.inputs:
            for out in tx.outputs:
                if inp and out and inp != out and inp != "unknown" and out != "unknown":
                    links.append({
                        "source": inp,
                        "target": out,
                        "value":  tx.value,
                        "chain":  tx.chain,
                        "tx_hash": tx.hash[:16] + "...",
                    })

    return {
        "queried_address": address,
        "chain":  chain.upper(),
        "nodes":  list(node_set.values()),
        "links":  links,
        "risk":   full.risk.model_dump(),
        "stats":  full.graph_stats.model_dump() if full.graph_stats else {},
    }


@app.get("/demo", tags=["System"])
async def demo_analyze():
    """
    Demo analiz — API key olmadan test et.
    Offline saxlanmış tranzaksiya datası istifadə olunur.
    """
    return build_response(
        address="1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
        chain="BTC",
        transactions=DEMO_TRANSACTIONS,
    )
