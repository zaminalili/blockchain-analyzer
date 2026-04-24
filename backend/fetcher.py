"""
Blockchain Transaction Fetcher
Bitcoin (BlockCypher) + Ethereum (Etherscan) - free tier APIs
"""

import requests
import time
from typing import Optional

# ── Free-tier API endpoints ──────────────────────
BTC_API  = "https://api.blockcypher.com/v1/btc/main"
ETH_API  = "https://api.etherscan.io/api"

# Etherscan demo key (public test key - rate limited)
ETHERSCAN_KEY = "YourApiKeyToken"   


def fetch_btc_address(address: str, limit: int = 20) -> Optional[dict]:
    """Bitcoin ünvanının tranzaksiyalarını çək."""
    url = f"{BTC_API}/addrs/{address}/full"
    params = {"limit": limit, "includeHex": False}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        print(f"[BTC] Fetch xətası: {e}")
        return None


def fetch_eth_address(address: str, limit: int = 20) -> Optional[dict]:
    """Ethereum ünvanının tranzaksiyalarını çək."""
    params = {
        "module":  "account",
        "action":  "txlist",
        "address": address,
        "startblock": 0,
        "endblock": 99999999,
        "page":    1,
        "offset":  limit,
        "sort":    "desc",
        "apikey":  ETHERSCAN_KEY,
    }
    try:
        r = requests.get(ETH_API, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data.get("status") == "1":
            return data
        else:
            print(f"[ETH] API cavabı: {data.get('message', 'Unknown error')}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"[ETH] Fetch xətası: {e}")
        return None


def fetch_btc_tx(txid: str) -> Optional[dict]:
    """Konkret BTC tranzaksiyasının detalları."""
    url = f"{BTC_API}/txs/{txid}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except:
        return None


def parse_btc_transactions(raw: dict) -> list[dict]:
    """BTC raw data-nı standart formata çevir."""
    txs = []
    for tx in raw.get("txs", []):
        inputs  = [(i.get("addresses") or ["unknown"])[0] for i in tx.get("inputs", [])]
        outputs = [(o.get("addresses") or ["unknown"])[0] for o in tx.get("outputs", [])]
        value   = sum(o.get("value", 0) for o in tx.get("outputs", [])) / 1e8  # satoshi → BTC

        txs.append({
            "chain":     "BTC",
            "hash":      tx.get("hash", ""),
            "timestamp": tx.get("confirmed", tx.get("received", "")),
            "inputs":    inputs,
            "outputs":   outputs,
            "value_btc": round(value, 8),
            "fee_sat":   tx.get("fees", 0),
        })
    return txs


def parse_eth_transactions(raw: dict, queried_address: str) -> list[dict]:
    """ETH raw data-nı standart formata çevir."""
    txs = []
    for tx in raw.get("result", []):
        value_eth = int(tx.get("value", 0)) / 1e18  # wei → ETH
        txs.append({
            "chain":     "ETH",
            "hash":      tx.get("hash", ""),
            "timestamp": tx.get("timeStamp", ""),
            "inputs":    [tx.get("from", "unknown")],
            "outputs":   [tx.get("to",   "unknown")],
            "value_eth": round(value_eth, 6),
            "gas_used":  tx.get("gasUsed", 0),
        })
    return txs
