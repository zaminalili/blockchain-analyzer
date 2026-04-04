"""
AZ Blockchain Transaction Analyzer
Azərbaycan Hüquq-Mühafizə Orqanları üçün Prototip
────────────────────────────────────────────────────
İstifadə:
  python main.py --btc <bitcoin_address>
  python main.py --eth <ethereum_address>
  python main.py --demo          (test ünvanları ilə)
"""

import argparse
import json
import sys
from datetime import datetime
from colorama import init, Fore, Style

from fetcher import (
    fetch_btc_address, fetch_eth_address,
    parse_btc_transactions, parse_eth_transactions,
)
from graph import (
    build_transaction_graph, get_graph_stats,
    cluster_by_common_input, detect_patterns, calculate_risk_score,
)

init(autoreset=True)  # colorama Windows uyğunluğu

# ── Demo ünvanlar (ictimai blockchain, real məlumat) ──────────────────────────
# Bunlar əvvəllər şübhəli fəaliyyətlə əlaqəli olduğu bilinən ünvanlardır
# (arxivləşdirilmiş, artıq aktiv deyil)
DEMO_BTC = "1A1zP1eP5QGefi2DMPTfTL5SLmv7Divf Na"   # genesis block (nümunə)
DEMO_BTC_REAL = "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"
DEMO_ETH = "0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe"  # Ethereum Foundation


def print_header():
    print(f"\n{Fore.CYAN}{'═'*60}")
    print(f"  AZ Blockchain Analyzer — Kriminalistik Prototip")
    print(f"  Azərbaycan Hüquq-Mühafizə Orqanları üçün")
    print(f"{'═'*60}{Style.RESET_ALL}\n")


def print_section(title: str):
    print(f"\n{Fore.YELLOW}── {title} {'─'*(50-len(title))}{Style.RESET_ALL}")


def print_risk(risk: dict):
    colors = {"HIGH": Fore.RED, "MEDIUM": Fore.YELLOW, "LOW": Fore.GREEN}
    c = colors.get(risk["level"], Fore.WHITE)
    bar_filled = "█" * (risk["score"] // 5)
    bar_empty  = "░" * (20 - risk["score"] // 5)
    print(f"\n  Risk Skoru: {c}{risk['score']}/100  [{bar_filled}{bar_empty}]  {risk['level']}{Style.RESET_ALL}")


def analyze(transactions: list[dict], address: str, chain: str):
    """Tam analiz pipeline-ı."""

    if not transactions:
        print(f"{Fore.RED}  Tranzaksiya tapılmadı.{Style.RESET_ALL}")
        return

    # ── Ünvan xülasəsi ────────────────────────────────────────────────────
    print_section("Ünvan Xülasəsi")
    print(f"  Ünvan  : {Fore.CYAN}{address}{Style.RESET_ALL}")
    print(f"  Şəbəkə : {chain}")
    print(f"  Tx say : {len(transactions)}")

    total_val = sum(tx.get("value_btc") or tx.get("value_eth") or 0 for tx in transactions)
    unit = "BTC" if chain == "BTC" else "ETH"
    print(f"  Cəm    : {total_val:.6f} {unit}")

    # ── Son tranzaksiyalar ────────────────────────────────────────────────
    print_section("Son 5 Tranzaksiya")
    for tx in transactions[:5]:
        val  = tx.get("value_btc") or tx.get("value_eth") or 0
        ts   = tx.get("timestamp", "")[:10]
        h    = tx["hash"][:20] + "..."
        inp  = tx["inputs"][0][:18]  + "..." if tx["inputs"]  else "?"
        out  = tx["outputs"][0][:18] + "..." if tx["outputs"] else "?"
        print(f"  {Fore.WHITE}{h}{Style.RESET_ALL}  {ts}  {inp} → {out}  [{val:.6f} {unit}]")

    # ── Qraf analizi ─────────────────────────────────────────────────────
    print_section("Tranzaksiya Qraf Analizi")
    G = build_transaction_graph(transactions)
    stats = get_graph_stats(G)

    if stats:
        print(f"  Node (unikal ünvan) : {stats['nodes']}")
        print(f"  Edge (əlaqə)        : {stats['edges']}")
        print(f"  Qraf sıxlığı        : {stats['density']}")
        print(f"  Güclü komponent     : {stats['strongly_connected']}")

        print(f"\n  {Fore.CYAN}Ən çox göndərən ünvanlar:{Style.RESET_ALL}")
        for addr, deg in stats["top_senders"][:3]:
            print(f"    {addr[:30]}...  →  {deg} tx")

    # ── Klasterləşmə ─────────────────────────────────────────────────────
    print_section("Wallet Klasterləşmə (CIO Heuristikası)")
    clusters = cluster_by_common_input(transactions)
    multi = {k: v for k, v in clusters.items() if len(v) > 1}

    if multi:
        print(f"  {len(multi)} klaster aşkarlandı (2+ ünvan eyni sahibə aid ola bilər):")
        for root, addrs in list(multi.items())[:3]:
            print(f"    Klaster: {len(addrs)} ünvan  (nümunə: {addrs[0][:25]}...)")
    else:
        print("  Çox ünvanlı klaster aşkarlanmadı.")

    # ── Şübhəli patternlər ───────────────────────────────────────────────
    print_section("Şübhəli Pattern Analizi")
    alerts = detect_patterns(transactions, clusters)

    sev_colors = {"HIGH": Fore.RED, "MEDIUM": Fore.YELLOW, "LOW": Fore.CYAN}
    if alerts:
        for a in alerts[:8]:
            c = sev_colors.get(a["severity"], Fore.WHITE)
            print(f"  {c}[{a['severity']:6}]{Style.RESET_ALL}  {a['type']:15}  {a['detail']}")
    else:
        print(f"  {Fore.GREEN}Şübhəli pattern aşkarlanmadı.{Style.RESET_ALL}")

    # ── Risk skoru ───────────────────────────────────────────────────────
    print_section("Risk Qiymətləndirməsi")
    risk = calculate_risk_score(alerts)
    print_risk(risk)

    risk_labels = {
        "LOW":    "Adi monitorinq kifayətdir.",
        "MEDIUM": "Əlavə araşdırma tövsiyə olunur.",
        "HIGH":   "DƏRHAl istintaq açılması tövsiyə olunur!",
    }
    print(f"  Tövsiyə: {risk_labels[risk['level']]}")

    # ── JSON export ──────────────────────────────────────────────────────
    result = {
        "meta": {
            "address": address,
            "chain": chain,
            "analyzed_at": datetime.utcnow().isoformat() + "Z",
            "tx_count": len(transactions),
        },
        "graph_stats": stats,
        "clusters_found": len(multi),
        "alerts": alerts,
        "risk": risk,
    }

    outfile = f"report_{address[:12]}_{chain}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n  {Fore.GREEN}✓ Hesabat saxlanıldı: {outfile}{Style.RESET_ALL}")
    print(f"\n{'═'*60}\n")

    return result


def run_demo():
    """Demo mode — Ethereum Foundation ünvanı ilə test."""
    print(f"{Fore.CYAN}  Demo rejimi: Ethereum Foundation ünvanı test edilir...{Style.RESET_ALL}")

    raw = fetch_eth_address(DEMO_ETH, limit=15)
    if raw:
        txs = parse_eth_transactions(raw, DEMO_ETH)
        analyze(txs, DEMO_ETH, "ETH")
    else:
        # API çatışmazsa offline demo data istifadə et
        print(f"{Fore.YELLOW}  API əlçatmaz — offline demo data ilə davam edilir...{Style.RESET_ALL}")
        run_offline_demo()


def run_offline_demo():
    """Offline demo — API olmadan konsepti göstər."""
    # Süni tranzaksiya datası (realistic struktur)
    fake_txs = [
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
                        "12cbQLTFMXRnSzktFkuoG3eHoMeFtpTu3S", "1HT7xU2Ngenf7D4yocz2SAcnNLW7rK8d4Y"],  # fan-out!
            "value_btc": 2.0, "fee_sat": 3000,
        },
        {
            "chain": "BTC", "hash": "c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
            "timestamp": "2024-01-15T12:30:00Z",
            "inputs":  ["1dice8EMZmqKvrGE4Qc9bUFngAia8TD9Bs", "15ubicBBWFnvoZLT7GiU2qxjRaKJPdkDMG"],
            "outputs": ["1ez69SnzzmePmZX3WpEzMKTrcBF2gpNQ55"],
            "value_btc": 1.0,  # round number!
            "fee_sat": 1000,
        },
        {
            "chain": "ETH", "hash": "0xd4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5",
            "timestamp": "1705316400",
            "inputs":  ["0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe"],
            "outputs": ["0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8"],
            "value_eth": 5.0,  # round number!
            "gas_used": 21000,
        },
        {
            "chain": "BTC", "hash": "e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6",
            "timestamp": "2024-01-16T09:00:00Z",
            "inputs":  ["1HLoD9E4SDFFPDiYfNYnkBLQ85Y51J3Zb1", "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
                        "1A8JiWcwvpY7tAopUkSnGuwotti7g9kn7g"],
            "outputs": ["1GkQmKAmHtNfnD3LHhTkewJxKHVSta4m2A"],
            "value_btc": 3.0,
            "fee_sat": 2500,
        },
    ]

    analyze(fake_txs, "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2", "BTC+ETH")


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print_header()

    parser = argparse.ArgumentParser(description="AZ Blockchain Analyzer")
    parser.add_argument("--btc",  type=str, help="Bitcoin ünvanı")
    parser.add_argument("--eth",  type=str, help="Ethereum ünvanı")
    parser.add_argument("--demo", action="store_true", help="Demo rejimi")
    args = parser.parse_args()

    if args.demo or (not args.btc and not args.eth):
        run_demo()

    if args.btc:
        print(f"  BTC ünvanı analiz edilir: {args.btc}")
        raw = fetch_btc_address(args.btc)
        if raw:
            txs = parse_btc_transactions(raw)
            analyze(txs, args.btc, "BTC")

    if args.eth:
        print(f"  ETH ünvanı analiz edilir: {args.eth}")
        raw = fetch_eth_address(args.eth)
        if raw:
            txs = parse_eth_transactions(raw, args.eth)
            analyze(txs, args.eth, "ETH")
