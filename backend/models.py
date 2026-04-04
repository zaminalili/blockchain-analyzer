"""
Pydantic modellər — Request/response sxemləri
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class ChainType(str, Enum):
    BTC = "BTC"
    ETH = "ETH"


class RiskLevel(str, Enum):
    LOW    = "LOW"
    MEDIUM = "MEDIUM"
    HIGH   = "HIGH"


# ── Request modellər ──────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    address: str = Field(..., min_length=10, description="Wallet ünvanı")
    chain:   ChainType = Field(..., description="BTC və ya ETH")
    limit:   int = Field(default=20, ge=1, le=100, description="Tx limiti")

    model_config = {"json_schema_extra": {
        "example": {
            "address": "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
            "chain":   "BTC",
            "limit":   20,
        }
    }}


class BatchAnalyzeRequest(BaseModel):
    addresses: list[AnalyzeRequest] = Field(..., max_length=10)


# ── Response modellər ─────────────────────────────────────────────────────────

class TransactionOut(BaseModel):
    chain:     str
    hash:      str
    timestamp: str
    inputs:    list[str]
    outputs:   list[str]
    value:     float
    fee:       Optional[int] = None


class AlertOut(BaseModel):
    type:     str
    severity: str
    tx:       str
    detail:   str


class RiskOut(BaseModel):
    score: int
    level: RiskLevel
    color: str


class GraphStatsOut(BaseModel):
    nodes:               int
    edges:               int
    density:             float
    strongly_connected:  int
    top_senders:         list
    top_receivers:       list


class ClusterOut(BaseModel):
    cluster_id:    str
    address_count: int
    sample_address: str


class AnalyzeResponse(BaseModel):
    address:        str
    chain:          str
    tx_count:       int
    total_value:    float
    transactions:   list[TransactionOut]
    graph_stats:    Optional[GraphStatsOut]
    clusters:       list[ClusterOut]
    alerts:         list[AlertOut]
    risk:           RiskOut
    analyzed_at:    str
