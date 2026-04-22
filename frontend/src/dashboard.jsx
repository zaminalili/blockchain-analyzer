import { useState, useEffect, useRef, useCallback } from "react";
import * as d3 from "d3";

// ── Demo data (API olmadan işləyir) ──────────────────────────────────────────
const DEMO_DATA = {
  queried_address: "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
  chain: "BTC",
  nodes: [
    { id: "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2", chain: "BTC", risk: 100, label: "1BvBMSEYst...", is_queried: true },
    { id: "1A8JiWcwvpY7tAopUkSnGuwotti7g9kn7g",  chain: "BTC", risk: 40,  label: "1A8JiWcwvp...", is_queried: false },
    { id: "1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF",  chain: "BTC", risk: 60,  label: "1FeexV6bAH...", is_queried: false },
    { id: "1HLoD9E4SDFFPDiYfNYnkBLQ85Y51J3Zb1",  chain: "BTC", risk: 20,  label: "1HLoD9E4SD...", is_queried: false },
    { id: "1dice8EMZmqKvrGE4Qc9bUFngAia8TD9Bs",  chain: "BTC", risk: 75,  label: "1dice8EMZm...", is_queried: false },
    { id: "1ez69SnzzmePmZX3WpEzMKTrcBF2gpNQ55",  chain: "BTC", risk: 55,  label: "1ez69Snzzm...", is_queried: false },
    { id: "15ubicBBWFnvoZLT7GiU2qxjRaKJPdkDMG",  chain: "BTC", risk: 30,  label: "15ubicBBWF...", is_queried: false },
    { id: "1LomaFwStWriz3vVvTmRZrNVZHiYHPbDmF",  chain: "BTC", risk: 15,  label: "1LomaFwStW...", is_queried: false },
    { id: "1GkQmKAmHtNfnD3LHhTkewJxKHVSta4m2A",  chain: "BTC", risk: 80,  label: "1GkQmKAmHt...", is_queried: false },
    { id: "0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe", chain: "ETH", risk: 45, label: "0xde0B2956...", is_queried: false },
    { id: "0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8", chain: "ETH", risk: 35, label: "0xBE0eB53F...", is_queried: false },
  ],
  links: [
    { source: "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2", target: "1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF", value: 2.5, chain: "BTC" },
    { source: "1A8JiWcwvpY7tAopUkSnGuwotti7g9kn7g",  target: "1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF", value: 2.5, chain: "BTC" },
    { source: "1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF",  target: "1dice8EMZmqKvrGE4Qc9bUFngAia8TD9Bs", value: 2.0, chain: "BTC" },
    { source: "1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF",  target: "1ez69SnzzmePmZX3WpEzMKTrcBF2gpNQ55", value: 2.0, chain: "BTC" },
    { source: "1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF",  target: "15ubicBBWFnvoZLT7GiU2qxjRaKJPdkDMG", value: 2.0, chain: "BTC" },
    { source: "1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF",  target: "1LomaFwStWriz3vVvTmRZrNVZHiYHPbDmF", value: 2.0, chain: "BTC" },
    { source: "1dice8EMZmqKvrGE4Qc9bUFngAia8TD9Bs",   target: "1ez69SnzzmePmZX3WpEzMKTrcBF2gpNQ55", value: 1.0, chain: "BTC" },
    { source: "15ubicBBWFnvoZLT7GiU2qxjRaKJPdkDMG",   target: "1ez69SnzzmePmZX3WpEzMKTrcBF2gpNQ55", value: 1.0, chain: "BTC" },
    { source: "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2", target: "1HLoD9E4SDFFPDiYfNYnkBLQ85Y51J3Zb1", value: 2.5, chain: "BTC" },
    { source: "1HLoD9E4SDFFPDiYfNYnkBLQ85Y51J3Zb1",  target: "1GkQmKAmHtNfnD3LHhTkewJxKHVSta4m2A", value: 3.0, chain: "BTC" },
    { source: "0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe", target: "0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8", value: 5.0, chain: "ETH" },
  ],
  risk: { score: 100, level: "HIGH", color: "red" },
  stats: { nodes: 11, edges: 15, density: 0.1026, strongly_connected: 11 },
  alerts: [
    { type: "FAN_OUT",       severity: "MEDIUM", tx: "b2c3d4e5f6a1b2c3...", detail: "6 output aşkarlandı — potensial mixing" },
    { type: "ROUND_NUMBER",  severity: "LOW",    tx: "c3d4e5f6a1b2c3d4...", detail: "Tam ədəd köçürmə: 1.0" },
    { type: "ROUND_NUMBER",  severity: "LOW",    tx: "0xd4e5f6a1b2c3d4...", detail: "Tam ədəd köçürmə: 5.0" },
    { type: "LARGE_CLUSTER", severity: "HIGH",   tx: "1A8JiWcwvpY7tAop...", detail: "Klasterdə 3 ünvan — eyni sahibə aid ola bilər" },
  ],
};

// ── Risk helpers ─────────────────────────────────────────────────────────────
const riskColor = (score) => {
  if (score >= 70) return "#ef4444";
  if (score >= 40) return "#f59e0b";
  return "#22c55e";
};
const severityColor = { HIGH: "#ef4444", MEDIUM: "#f59e0b", LOW: "#6b7280" };
const chainColor = { BTC: "#f7931a", ETH: "#627eea" };

// ── D3 Force Graph ────────────────────────────────────────────────────────────
function ForceGraph({ data, onNodeClick }) {
  const svgRef = useRef(null);
  const simRef = useRef(null);

  useEffect(() => {
    if (!data || !svgRef.current) return;

    const el  = svgRef.current;
    const W   = el.clientWidth  || 700;
    const H   = el.clientHeight || 440;

    d3.select(el).selectAll("*").remove();

    const svg = d3.select(el)
      .attr("viewBox", `0 0 ${W} ${H}`)
      .style("background", "transparent");

    // Zoom
    const g = svg.append("g");
    svg.call(d3.zoom().scaleExtent([0.3, 3]).on("zoom", e => g.attr("transform", e.transform)));

    // Defs: arrow marker
    svg.append("defs").append("marker")
      .attr("id", "arrowhead")
      .attr("viewBox", "0 -4 8 8")
      .attr("refX", 18).attr("refY", 0)
      .attr("markerWidth", 6).attr("markerHeight", 6)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-4L8,0L0,4")
      .attr("fill", "#475569");

    // Deep copy nodes/links for simulation
    const nodes = data.nodes.map(d => ({ ...d }));
    const links = data.links.map(d => ({ ...d }));

    // Simulation
    const sim = d3.forceSimulation(nodes)
      .force("link",   d3.forceLink(links).id(d => d.id).distance(90).strength(0.6))
      .force("charge", d3.forceManyBody().strength(-280))
      .force("center", d3.forceCenter(W / 2, H / 2))
      .force("collide", d3.forceCollide(28));
    simRef.current = sim;

    // Links
    const link = g.append("g").selectAll("line").data(links).join("line")
      .attr("stroke", d => chainColor[d.chain] || "#475569")
      .attr("stroke-opacity", 0.35)
      .attr("stroke-width", d => Math.max(1, Math.log(d.value + 1) * 1.5))
      .attr("marker-end", "url(#arrowhead)");

    // Link value labels
    const linkLabel = g.append("g").selectAll("text").data(links).join("text")
      .attr("font-size", 9)
      .attr("fill", "#64748b")
      .attr("text-anchor", "middle")
      .text(d => d.value + (d.chain === "BTC" ? "₿" : "Ξ"));

    // Node groups
    const node = g.append("g").selectAll("g").data(nodes).join("g")
      .style("cursor", "pointer")
      .call(d3.drag()
        .on("start", (e, d) => { if (!e.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
        .on("drag",  (e, d) => { d.fx = e.x; d.fy = e.y; })
        .on("end",   (e, d) => { if (!e.active) sim.alphaTarget(0); d.fx = null; d.fy = null; })
      )
      .on("click", (e, d) => { e.stopPropagation(); onNodeClick && onNodeClick(d); });

    // Outer glow ring for queried node
    node.filter(d => d.is_queried)
      .append("circle")
      .attr("r", 22)
      .attr("fill", "none")
      .attr("stroke", "#f59e0b")
      .attr("stroke-width", 2)
      .attr("stroke-dasharray", "4 2")
      .attr("opacity", 0.7);

    // Risk ring
    node.append("circle")
      .attr("r", 16)
      .attr("fill", d => riskColor(d.risk) + "22")
      .attr("stroke", d => riskColor(d.risk))
      .attr("stroke-width", d => d.is_queried ? 2.5 : 1.5);

    // Chain icon
    node.append("text")
      .attr("text-anchor", "middle")
      .attr("dominant-baseline", "central")
      .attr("font-size", 11)
      .attr("font-weight", "600")
      .attr("fill", d => chainColor[d.chain] || "#94a3b8")
      .text(d => d.chain === "BTC" ? "₿" : "Ξ");

    // Label
    node.append("text")
      .attr("y", 26)
      .attr("text-anchor", "middle")
      .attr("font-size", 9)
      .attr("fill", "#94a3b8")
      .text(d => d.label);

    // Tick
    sim.on("tick", () => {
      link
        .attr("x1", d => d.source.x).attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
      linkLabel
        .attr("x", d => (d.source.x + d.target.x) / 2)
        .attr("y", d => (d.source.y + d.target.y) / 2 - 5);
      node.attr("transform", d => `translate(${d.x},${d.y})`);
    });

    return () => sim.stop();
  }, [data]);

  return (
    <svg ref={svgRef} style={{ width: "100%", height: "100%", display: "block" }} />
  );
}

// ── Risk Gauge ────────────────────────────────────────────────────────────────
function RiskGauge({ score }) {
  const r = 48, cx = 64, cy = 64;
  const circ = 2 * Math.PI * r;
  const fill  = (score / 100) * circ;
  const color = riskColor(score);
  return (
    <svg width="128" height="80" viewBox="0 0 128 80">
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="#1e293b" strokeWidth="10"/>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke={color} strokeWidth="10"
        strokeDasharray={`${fill} ${circ - fill}`}
        strokeDashoffset={circ * 0.25}
        strokeLinecap="round"
        style={{ transition: "stroke-dasharray 1s ease" }}
      />
      <text x={cx} y={cy - 2} textAnchor="middle" dominantBaseline="central"
        fontSize="22" fontWeight="700" fill={color}>{score}</text>
      <text x={cx} y={cx + 18} textAnchor="middle" fontSize="10" fill="#64748b">/ 100</text>
    </svg>
  );
}

// ── Main Dashboard ────────────────────────────────────────────────────────────
export default function Dashboard() {
  const [input,     setInput]     = useState("1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2");
  const [chain,     setChain]     = useState("BTC");
  const [data,      setData]      = useState(DEMO_DATA);
  const [loading,   setLoading]   = useState(false);
  const [selected,  setSelected]  = useState(null);
  const [apiUrl,    setApiUrl]    = useState("http://localhost:8000");
  const [apiStatus, setApiStatus] = useState("demo"); // "demo" | "live" | "error"

  // API health yoxla
  useEffect(() => {
    fetch(`${apiUrl}/health`, { signal: AbortSignal.timeout(2000) })
      .then(r => r.ok ? setApiStatus("live") : setApiStatus("error"))
      .catch(() => setApiStatus("demo"));
  }, [apiUrl]);

  const analyze = useCallback(async () => {
    setLoading(true);
    setSelected(null);
    try {
      if (apiStatus === "live") {
        const r = await fetch(`${apiUrl}/graph/${chain}/${input}`);
        const d = await r.json();
        setData(d);
      } else {
        // Demo mode — offline data
        await new Promise(r => setTimeout(r, 600));
        setData({ ...DEMO_DATA, queried_address: input, chain });
      }
    } catch {
      setData({ ...DEMO_DATA, queried_address: input, chain });
    } finally {
      setLoading(false);
    }
  }, [input, chain, apiUrl, apiStatus]);

  const riskLevel = data?.risk?.level || "LOW";
  const riskScore = data?.risk?.score || 0;

  return (
    <div style={{
      minHeight: "100vh",
      background: "#020c14",
      color: "#e2e8f0",
      fontFamily: "'IBM Plex Mono', 'Courier New', monospace",
      padding: "0",
    }}>

      {/* ── Header ── */}
      <header style={{
        borderBottom: "1px solid #0f2744",
        padding: "14px 24px",
        display: "flex",
        alignItems: "center",
        gap: 16,
        background: "#040f1c",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <svg width="28" height="28" viewBox="0 0 28 28">
            <polygon points="14,2 26,8 26,20 14,26 2,20 2,8" fill="none" stroke="#f59e0b" strokeWidth="1.5"/>
            <polygon points="14,7 21,11 21,17 14,21 7,17 7,11" fill="#f59e0b22" stroke="#f59e0b" strokeWidth="1"/>
            <circle cx="14" cy="14" r="3" fill="#f59e0b"/>
          </svg>
          <span style={{ fontSize: 15, fontWeight: 700, color: "#f8fafc", letterSpacing: "0.05em" }}>
            AZ BLOCKCHAIN ANALYZER
          </span>
        </div>
        <span style={{ fontSize: 10, color: "#334155", marginLeft: 4 }}>
          KRİMİNALİSTİK PROTOTİP v1.0
        </span>
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{
            fontSize: 10, padding: "3px 10px", borderRadius: 20,
            background: apiStatus === "live" ? "#14532d44" : "#1e1e2e",
            border: `1px solid ${apiStatus === "live" ? "#22c55e" : "#334155"}`,
            color: apiStatus === "live" ? "#22c55e" : "#64748b",
          }}>
            {apiStatus === "live" ? "● API CANLI" : "● DEMO REJIM"}
          </span>
        </div>
      </header>

      {/* ── Search bar ── */}
      <div style={{
        padding: "16px 24px",
        background: "#040f1c",
        borderBottom: "1px solid #0f2744",
        display: "flex", gap: 10, flexWrap: "wrap",
      }}>
        {/* Chain selector */}
        <div style={{ display: "flex", borderRadius: 6, overflow: "hidden", border: "1px solid #1e3a5f" }}>
          {["BTC", "ETH"].map(c => (
            <button key={c} onClick={() => setChain(c)} style={{
              padding: "8px 16px", border: "none", cursor: "pointer", fontSize: 12,
              background: chain === c ? chainColor[c] + "33" : "transparent",
              color: chain === c ? chainColor[c] : "#64748b",
              fontFamily: "inherit", fontWeight: 700,
              borderRight: c === "BTC" ? "1px solid #1e3a5f" : "none",
            }}>{c}</button>
          ))}
        </div>

        {/* Address input */}
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && analyze()}
          placeholder="Wallet ünvanı daxil edin..."
          style={{
            flex: 1, minWidth: 260,
            background: "#0a1929", border: "1px solid #1e3a5f",
            borderRadius: 6, padding: "8px 14px",
            color: "#e2e8f0", fontSize: 12, fontFamily: "inherit",
            outline: "none",
          }}
        />

        <button onClick={analyze} disabled={loading} style={{
          padding: "8px 20px", borderRadius: 6, border: "none",
          background: loading ? "#1e3a5f" : "#1d4ed8",
          color: "#fff", cursor: loading ? "not-allowed" : "pointer",
          fontSize: 12, fontFamily: "inherit", fontWeight: 700,
          letterSpacing: "0.05em",
        }}>
          {loading ? "ANALİZ EDİLİR..." : "ANALİZ ET"}
        </button>

        {/* API URL (collapsible) */}
        <input
          value={apiUrl}
          onChange={e => setApiUrl(e.target.value)}
          placeholder="API URL"
          style={{
            width: 180, background: "#0a1929", border: "1px solid #0f2744",
            borderRadius: 6, padding: "8px 10px",
            color: "#475569", fontSize: 11, fontFamily: "inherit", outline: "none",
          }}
        />
      </div>

      {/* ── Main content ── */}
      <div style={{ display: "flex", height: "calc(100vh - 140px)", overflow: "hidden" }}>

        {/* ── Left sidebar ── */}
        <aside style={{
          width: 260, flexShrink: 0,
          background: "#040f1c",
          borderRight: "1px solid #0f2744",
          overflowY: "auto", padding: 16,
          display: "flex", flexDirection: "column", gap: 16,
        }}>

          {/* Risk Card */}
          <div style={{
            background: "#0a1929",
            border: `1px solid ${riskColor(riskScore)}44`,
            borderRadius: 10, padding: 16, textAlign: "center",
          }}>
            <div style={{ fontSize: 10, color: "#64748b", marginBottom: 8, letterSpacing: "0.1em" }}>
              RİSK QİYMƏTLƏNDİRMƏSİ
            </div>
            <RiskGauge score={riskScore} />
            <div style={{
              marginTop: 8, fontSize: 13, fontWeight: 700,
              color: riskColor(riskScore), letterSpacing: "0.1em",
            }}>
              {riskLevel}
            </div>
            <div style={{ fontSize: 10, color: "#475569", marginTop: 4 }}>
              {riskLevel === "HIGH"   && "Dərhal istintaq açılsın"}
              {riskLevel === "MEDIUM" && "Əlavə araşdırma lazımdır"}
              {riskLevel === "LOW"    && "Adi monitorinq kifayətdir"}
            </div>
          </div>

          {/* Stats */}
          <div style={{ background: "#0a1929", borderRadius: 10, padding: 14, border: "1px solid #0f2744" }}>
            <div style={{ fontSize: 10, color: "#64748b", marginBottom: 10, letterSpacing: "0.1em" }}>
              QRAF STATİSTİKASI
            </div>
            {[
              ["Node",       data?.stats?.nodes || data?.nodes?.length || 0],
              ["Edge",       data?.stats?.edges || data?.links?.length || 0],
              ["Sıxlıq",    data?.stats?.density?.toFixed(4) || "—"],
              ["Komponent", data?.stats?.strongly_connected || "—"],
            ].map(([k, v]) => (
              <div key={k} style={{ display: "flex", justifyContent: "space-between", marginBottom: 7 }}>
                <span style={{ fontSize: 11, color: "#64748b" }}>{k}</span>
                <span style={{ fontSize: 11, color: "#94a3b8", fontWeight: 600 }}>{v}</span>
              </div>
            ))}
          </div>

          {/* Alerts */}
          <div style={{ background: "#0a1929", borderRadius: 10, padding: 14, border: "1px solid #0f2744" }}>
            <div style={{ fontSize: 10, color: "#64748b", marginBottom: 10, letterSpacing: "0.1em" }}>
              XƏBƏRDARLIQLAR ({data?.alerts?.length || 0})
            </div>
            {(data?.alerts || []).map((a, i) => (
              <div key={i} style={{
                marginBottom: 8, padding: "8px 10px",
                background: severityColor[a.severity] + "11",
                border: `1px solid ${severityColor[a.severity]}33`,
                borderRadius: 6,
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                  <span style={{ fontSize: 10, fontWeight: 700, color: severityColor[a.severity] }}>
                    {a.type}
                  </span>
                  <span style={{ fontSize: 9, color: severityColor[a.severity], opacity: 0.7 }}>
                    {a.severity}
                  </span>
                </div>
                <div style={{ fontSize: 10, color: "#94a3b8", lineHeight: 1.4 }}>{a.detail}</div>
              </div>
            ))}
          </div>

          {/* Chain legend */}
          <div style={{ background: "#0a1929", borderRadius: 10, padding: 14, border: "1px solid #0f2744" }}>
            <div style={{ fontSize: 10, color: "#64748b", marginBottom: 10, letterSpacing: "0.1em" }}>RƏNG CƏDVƏLİ</div>
            {[["#ef4444","Yüksək risk (70+)"],["#f59e0b","Orta risk (40–69)"],["#22c55e","Aşağı risk (0–39)"],
              ["#f7931a","Bitcoin şəbəkəsi"],["#627eea","Ethereum şəbəkəsi"]].map(([c, l]) => (
              <div key={l} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                <div style={{ width: 10, height: 10, borderRadius: 2, background: c, flexShrink: 0 }} />
                <span style={{ fontSize: 10, color: "#64748b" }}>{l}</span>
              </div>
            ))}
          </div>
        </aside>

        {/* ── Graph + detail ── */}
        <main style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>

          {/* Graph canvas */}
          <div style={{ flex: 1, position: "relative", background: "#020c14" }}>
            <ForceGraph data={data} onNodeClick={setSelected} />

            {/* Overlay: queried address */}
            <div style={{
              position: "absolute", top: 14, left: 14,
              background: "#040f1ccc", backdropFilter: "blur(6px)",
              border: "1px solid #1e3a5f", borderRadius: 8,
              padding: "8px 12px", maxWidth: 340,
            }}>
              <div style={{ fontSize: 9, color: "#475569", marginBottom: 3 }}>SORĞULANAN ÜNVAN</div>
              <div style={{ fontSize: 11, color: "#f59e0b", wordBreak: "break-all" }}>
                {data?.queried_address}
              </div>
            </div>

            {/* Zoom hint */}
            <div style={{
              position: "absolute", bottom: 14, right: 14,
              fontSize: 10, color: "#1e3a5f",
            }}>
              Scroll: zoom · Sürüklə: hərəkət · Node: klik
            </div>
          </div>

          {/* ── Node detail panel ── */}
          {selected && (
            <div style={{
              height: 140, background: "#040f1c",
              borderTop: `1px solid ${riskColor(selected.risk)}55`,
              padding: "14px 20px",
              display: "flex", gap: 24, alignItems: "center",
            }}>
              <div>
                <div style={{ fontSize: 9, color: "#475569", marginBottom: 4 }}>SEÇİLMİŞ NODE</div>
                <div style={{ fontSize: 12, color: "#e2e8f0", wordBreak: "break-all", maxWidth: 420 }}>
                  {selected.id}
                </div>
              </div>
              <div style={{ display: "flex", gap: 24, marginLeft: "auto" }}>
                {[
                  ["Şəbəkə",     selected.chain, chainColor[selected.chain]],
                  ["Risk Skoru", selected.risk + "/100", riskColor(selected.risk)],
                  ["Sorğulanan", selected.is_queried ? "Bəli" : "Xeyr", selected.is_queried ? "#f59e0b" : "#475569"],
                ].map(([k, v, c]) => (
                  <div key={k} style={{ textAlign: "center" }}>
                    <div style={{ fontSize: 9, color: "#475569", marginBottom: 4 }}>{k}</div>
                    <div style={{ fontSize: 14, fontWeight: 700, color: c }}>{v}</div>
                  </div>
                ))}
                <button onClick={() => setSelected(null)} style={{
                  background: "transparent", border: "1px solid #1e3a5f",
                  color: "#475569", borderRadius: 6, padding: "4px 12px",
                  cursor: "pointer", fontSize: 11, fontFamily: "inherit",
                }}>✕</button>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
