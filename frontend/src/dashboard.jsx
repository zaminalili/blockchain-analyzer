import { useState, useEffect, useRef, useCallback } from "react";
import * as d3 from "d3";

// Demo data
const DEMO_DATA = {
  queried_address: "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
  chain: "BTC",
  nodes: [
    { id: "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2", chain: "BTC", risk: 100, label: "1BvBMSEYst...", is_queried: true },
    { id: "1A8JiWcwvpY7tAopUkSnGuwotti7g9kn7g", chain: "BTC", risk: 40, label: "1A8JiWcwvp...", is_queried: false },
    { id: "1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF", chain: "BTC", risk: 60, label: "1FeexV6bAH...", is_queried: false },
    { id: "1HLoD9E4SDFFPDiYfNYnkBLQ85Y51J3Zb1", chain: "BTC", risk: 20, label: "1HLoD9E4SD...", is_queried: false },
    { id: "1dice8EMZmqKvrGE4Qc9bUFngAia8TD9Bs", chain: "BTC", risk: 75, label: "1dice8EMZm...", is_queried: false },
    { id: "1ez69SnzzmePmZX3WpEzMKTrcBF2gpNQ55", chain: "BTC", risk: 55, label: "1ez69Snzzm...", is_queried: false },
    { id: "15ubicBBWFnvoZLT7GiU2qxjRaKJPdkDMG", chain: "BTC", risk: 30, label: "15ubicBBWF...", is_queried: false },
    { id: "1LomaFwStWriz3vVvTmRZrNVZHiYHPbDmF", chain: "BTC", risk: 15, label: "1LomaFwStW...", is_queried: false },
    { id: "1GkQmKAmHtNfnD3LHhTkewJxKHVSta4m2A", chain: "BTC", risk: 80, label: "1GkQmKAmHt...", is_queried: false },
    { id: "0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe", chain: "ETH", risk: 45, label: "0xde0B2956...", is_queried: false },
    { id: "0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8", chain: "ETH", risk: 35, label: "0xBE0eB53F...", is_queried: false },
  ],
  links: [
    { source: "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2", target: "1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF", value: 2.5, chain: "BTC" },
    { source: "1A8JiWcwvpY7tAopUkSnGuwotti7g9kn7g", target: "1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF", value: 2.5, chain: "BTC" },
    { source: "1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF", target: "1dice8EMZmqKvrGE4Qc9bUFngAia8TD9Bs", value: 2.0, chain: "BTC" },
    { source: "1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF", target: "1ez69SnzzmePmZX3WpEzMKTrcBF2gpNQ55", value: 2.0, chain: "BTC" },
    { source: "1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF", target: "15ubicBBWFnvoZLT7GiU2qxjRaKJPdkDMG", value: 2.0, chain: "BTC" },
    { source: "1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF", target: "1LomaFwStWriz3vVvTmRZrNVZHiYHPbDmF", value: 2.0, chain: "BTC" },
    { source: "1dice8EMZmqKvrGE4Qc9bUFngAia8TD9Bs", target: "1ez69SnzzmePmZX3WpEzMKTrcBF2gpNQ55", value: 1.0, chain: "BTC" },
    { source: "15ubicBBWFnvoZLT7GiU2qxjRaKJPdkDMG", target: "1ez69SnzzmePmZX3WpEzMKTrcBF2gpNQ55", value: 1.0, chain: "BTC" },
    { source: "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2", target: "1HLoD9E4SDFFPDiYfNYnkBLQ85Y51J3Zb1", value: 2.5, chain: "BTC" },
    { source: "1HLoD9E4SDFFPDiYfNYnkBLQ85Y51J3Zb1", target: "1GkQmKAmHtNfnD3LHhTkewJxKHVSta4m2A", value: 3.0, chain: "BTC" },
    { source: "0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe", target: "0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8", value: 5.0, chain: "ETH" },
  ],
  risk: { score: 100, level: "Kritik", color: "red" },
  stats: { nodes: 11, edges: 15, density: 0.1026, strongly_connected: 11 },
  alerts: [
    { type: "FAN_OUT", severity: "MEDIUM", tx: "b2c3d4e5f6a1b2c3...", detail: "6 output aşkarlandı — potensial mixing" },
    { type: "ROUND_NUMBER", severity: "LOW", tx: "c3d4e5f6a1b2c3d4...", detail: "Tam ədəd köçürmə: 1.0" },
    { type: "ROUND_NUMBER", severity: "LOW", tx: "0xd4e5f6a1b2c3d4...", detail: "Tam ədəd köçürmə: 5.0" },
    { type: "LARGE_CLUSTER", severity: "HIGH", tx: "1A8JiWcwvpY7tAop...", detail: "Klasterdə 3 ünvan — eyni sahibə aid ola bilər" },
  ],
};


const riskColor = (score) => {
  if (score >= 70) return "var(--risk-high)";
  if (score >= 40) return "var(--risk-medium)";
  return "var(--risk-low)";
};
const severityColor = { HIGH: "var(--risk-high)", MEDIUM: "var(--risk-medium)", LOW: "var(--text-mute)" };
const chainColor = { BTC: "#f7931a", ETH: "#627eea" };


function ForceGraph({ data, onNodeClick }) {
  const svgRef = useRef(null);
  const simRef = useRef(null);
  const zoomRef = useRef(null);
  const svgSelectionRef = useRef(null);

  useEffect(() => {
    if (!data || !data.nodes || !data.links || !svgRef.current) return;

    const el = svgRef.current;
    const W = el.clientWidth || 800;
    const H = el.clientHeight || 500;

    d3.select(el).selectAll("*").remove();

    const svg = d3.select(el)
      .attr("viewBox", `0 0 ${W} ${H}`)
      .style("background", "transparent");

    svgSelectionRef.current = svg;

    const g = svg.append("g");

    const zoom = d3.zoom()
      .scaleExtent([0.1, 8])
      .on("zoom", (e) => g.attr("transform", e.transform));

    zoomRef.current = zoom;
    svg.call(zoom);

    const defs = svg.append("defs");
    const filter = defs.append("filter").attr("id", "glow").attr("x", "-50%").attr("y", "-50%").attr("width", "200%").attr("height", "200%");
    filter.append("feGaussianBlur").attr("stdDeviation", "2.5").attr("result", "coloredBlur");
    const feMerge = filter.append("feMerge");
    feMerge.append("feMergeNode").attr("in", "coloredBlur");
    feMerge.append("feMergeNode").attr("in", "SourceGraphic");

    defs.append("marker")
      .attr("id", "arrowhead")
      .attr("viewBox", "0 -4 8 8")
      .attr("refX", 22).attr("refY", 0)
      .attr("markerWidth", 5).attr("markerHeight", 5)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-4L8,0L0,4")
      .attr("fill", "var(--text-mute)");

    const nodes = data.nodes.map(d => ({ ...d }));
    const links = data.links.map(d => ({ ...d }));

    const sim = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id(d => d.id).distance(120).strength(0.5))
      .force("charge", d3.forceManyBody().strength(-400))
      .force("center", d3.forceCenter(W / 2, H / 2))
      .force("collide", d3.forceCollide(40));
    simRef.current = sim;

    const link = g.append("g").selectAll("line").data(links).join("line")
      .attr("stroke", d => chainColor[d.chain] || "var(--border-dim)")
      .attr("stroke-opacity", 0.4)
      .attr("stroke-width", d => Math.max(1.5, Math.log(d.value + 1) * 2))
      .attr("marker-end", "url(#arrowhead)");

    const linkLabel = g.append("g").selectAll("text").data(links).join("text")
      .attr("font-size", 10)
      .attr("font-family", "var(--font-mono)")
      .attr("fill", "var(--text-mute)")
      .attr("text-anchor", "middle")
      .text(d => d.value + (d.chain === "BTC" ? " ₿" : " Ξ"));

    const node = g.append("g").selectAll("g").data(nodes).join("g")
      .style("cursor", "pointer")
      .on("click", (e, d) => { e.stopPropagation(); onNodeClick && onNodeClick(d); });

    node.call(d3.drag()
      .on("start", (e, d) => { if (!e.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
      .on("drag", (e, d) => { d.fx = e.x; d.fy = e.y; })
      .on("end", (e, d) => { if (!e.active) sim.alphaTarget(0); d.fx = null; d.fy = null; })
    );

    node.filter(d => d.is_queried)
      .append("circle")
      .attr("r", 26)
      .attr("fill", "none")
      .attr("stroke", "var(--accent-primary)")
      .attr("stroke-width", 2)
      .attr("stroke-dasharray", "4 2")
      .append("animateTransform")
      .attr("attributeName", "transform")
      .attr("type", "rotate")
      .attr("from", "0 0 0")
      .attr("to", "360 0 0")
      .attr("dur", "10s")
      .attr("repeatCount", "indefinite");

    node.append("circle")
      .attr("r", 18)
      .attr("fill", d => riskColor(d.risk))
      .attr("fill-opacity", 0.1)
      .attr("stroke", d => riskColor(d.risk))
      .attr("stroke-width", 2)
      .attr("filter", d => d.risk > 70 ? "url(#glow)" : null);

    node.append("rect")
      .attr("x", -30)
      .attr("y", 22)
      .attr("width", 60)
      .attr("height", 14)
      .attr("rx", 4)
      .attr("fill", "var(--bg-main)")
      .attr("opacity", 0.9);

    node.append("text")
      .attr("y", 32)
      .attr("text-anchor", "middle")
      .attr("font-size", 10)
      .attr("font-family", "var(--font-mono)")
      .attr("fill", "var(--text-dim)")
      .text(d => d.label);

    node.append("text")
      .attr("text-anchor", "middle")
      .attr("dominant-baseline", "central")
      .attr("font-size", 12)
      .attr("font-weight", "700")
      .attr("fill", d => chainColor[d.chain])
      .text(d => d.chain === "BTC" ? "₿" : "Ξ");

    sim.on("tick", () => {
      link.attr("x1", d => d.source?.x || 0).attr("y1", d => d.source?.y || 0)
        .attr("x2", d => d.target?.x || 0).attr("y2", d => d.target?.y || 0);
      linkLabel.attr("x", d => ((d.source?.x || 0) + (d.target?.x || 0)) / 2)
        .attr("y", d => ((d.source?.y || 0) + (d.target?.y || 0)) / 2 - 8);
      node.attr("transform", d => `translate(${d.x || 0},${d.y || 0})`);
    });

    return () => sim.stop();
  }, [data, onNodeClick]);

  const zoomIn = () => {
    if (svgSelectionRef.current && zoomRef.current) {
      svgSelectionRef.current.transition().duration(400).call(zoomRef.current.scaleBy, 1.5);
    }
  };

  const zoomOut = () => {
    if (svgSelectionRef.current && zoomRef.current) {
      svgSelectionRef.current.transition().duration(400).call(zoomRef.current.scaleBy, 0.6);
    }
  };

  const resetZoom = () => {
    if (svgSelectionRef.current && zoomRef.current) {
      svgSelectionRef.current.transition().duration(600).call(zoomRef.current.transform, d3.zoomIdentity);
    }
  };

  return (
    <div style={{ width: "100%", height: "100%", position: "relative" }}>
      <svg ref={svgRef} style={{ width: "100%", height: "100%" }} />

      {/* Zoom Controls Overlay */}
      <div className="glass-effect" style={{
        position: 'absolute', top: 20, right: 20,
        display: 'flex', flexDirection: 'column', gap: '8px',
        padding: '8px', borderRadius: '12px',
        border: '1px solid var(--border-dim)',
        zIndex: 5
      }}>
        <button onClick={zoomIn} title="Yaxınlaşdır" style={{
          width: 36, height: 36, borderRadius: 8, border: 'none',
          background: 'var(--bg-main)', color: 'var(--text-main)',
          cursor: 'pointer', fontSize: '1.2rem', fontWeight: 600,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
        }}>+</button>
        <button onClick={zoomOut} title="Uzaqlaşdır" style={{
          width: 36, height: 36, borderRadius: 8, border: 'none',
          background: 'var(--bg-main)', color: 'var(--text-main)',
          cursor: 'pointer', fontSize: '1.2rem', fontWeight: 600,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
        }}>−</button>
        <div style={{ height: 1, background: 'var(--border-dim)', margin: '4px 0' }} />
        <button onClick={resetZoom} title="Mərkəzləşdir" style={{
          width: 36, height: 36, borderRadius: 8, border: 'none',
          background: 'var(--bg-main)', color: 'var(--text-main)',
          cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
        }}>⟲</button>
      </div>
    </div>
  );
}


function RiskGauge({ score }) {
  const r = 40, cx = 60, cy = 60;
  const circ = 2 * Math.PI * r;
  const fill = (score / 100) * circ;
  const color = riskColor(score);
  return (
    <div style={{ position: 'relative', width: 120, height: 100, margin: '0 auto' }}>
      <svg width="120" height="120" viewBox="0 0 120 120">
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--border-dim)" strokeWidth="8" />
        <circle cx={cx} cy={cy} r={r} fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={`${fill} ${circ - fill}`}
          strokeDashoffset={circ * 0.25}
          strokeLinecap="round"
          style={{ transition: "stroke-dasharray 1.5s cubic-bezier(0.4, 0, 0.2, 1)" }}
        />
      </svg>
      <div style={{
        position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
        textAlign: 'center'
      }}>
        <div style={{ fontSize: 24, fontWeight: 700, color: color, fontFamily: 'var(--font-heading)' }}>{score}</div>
        <div style={{ fontSize: 10, color: 'var(--text-mute)', marginTop: -4 }}>XAL</div>
      </div>
    </div>
  );
}


export default function Dashboard() {
  const [input, setInput] = useState("1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2");
  const [chain, setChain] = useState("BTC");
  const [data, setData] = useState({ ...DEMO_DATA, is_demo: true });
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState(null);
  const [apiUrl, setApiUrl] = useState(import.meta.env.VITE_API_URL || "http://localhost:8000");
  const [apiStatus, setApiStatus] = useState("demo");

  useEffect(() => {
    fetch(`${apiUrl}/health`, { signal: AbortSignal.timeout(1500) })
      .then(r => r.ok ? setApiStatus("live") : setApiStatus("error"))
      .catch(() => setApiStatus("demo"));
  }, [apiUrl]);

  const analyze = useCallback(async () => {
    setLoading(true);
    setSelected(null);
    try {
      if (apiStatus === "live") {
        const r = await fetch(`${apiUrl}/graph/${chain}/${input}`);
        if (r.status === 429) {
          alert("API limiti aşıldı. Zəhmət olmasa bir qədər sonra yenidən cəhd edin.");
          return;
        }
        if (!r.ok) throw new Error("API request failed");
        const d = await r.json();
        if (!d.nodes || !d.links) throw new Error("Invalid API response format");
        setData(d);
      } else {
        await new Promise(r => setTimeout(r, 800));
        setData({ ...DEMO_DATA, queried_address: input, chain, is_demo: true });
      }
    } catch (e) {
      console.error(e);
      setData({ ...DEMO_DATA, queried_address: input, chain, is_demo: true });
    } finally {
      setLoading(false);
    }
  }, [input, chain, apiUrl, apiStatus]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>

      {/* ── Header ── */}
      <header className="glass-effect" style={{
        padding: "1rem 2rem", display: "flex", alignItems: "center", justifyContent: 'space-between',
        zIndex: 10, borderTop: 'none', borderLeft: 'none', borderRight: 'none',
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: '0.75rem' }}>
          <div style={{
            width: 32, height: 32, background: 'var(--accent-primary)', borderRadius: '8px',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 0 15px var(--accent-glow)'
          }}>

          </div>
          <div>
            <h1 style={{ fontSize: '1.1rem', margin: 0, fontWeight: 700 }} className="text-gradient">
              Blokçeyn analizi
            </h1>
            <p style={{ fontSize: '0.65rem', color: 'var(--text-mute)', margin: 0, letterSpacing: '0.1em' }}>
              prototip layihə
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ display: 'flex', background: 'rgba(255,255,255,0.5)', padding: 4, borderRadius: 8, border: '1px solid var(--border-dim)' }}>
            {["BTC", "ETH"].map(c => (
              <button key={c} onClick={() => setChain(c)} style={{
                padding: "6px 14px", border: "none", cursor: "pointer", fontSize: '0.75rem',
                background: chain === c ? 'var(--accent-primary)' : "transparent",
                color: chain === c ? "#fff" : "var(--text-mute)",
                borderRadius: 6, fontWeight: 600,
              }}>{c}</button>
            ))}
          </div>

          <div style={{
            fontSize: '0.7rem', padding: "4px 12px", borderRadius: 20,
            background: apiStatus === "live" ? "rgba(16, 185, 129, 0.1)" : "rgba(245, 158, 11, 0.1)",
            border: `1px solid ${apiStatus === "live" ? "var(--risk-low)" : "var(--risk-medium)"}`,
            color: apiStatus === "live" ? "var(--risk-low)" : "var(--risk-medium)",
            fontWeight: 500
          }}>
            {apiStatus === "live" ? "API AKTİVDİR" : "DEMO REJİM"}
          </div>
        </div>
      </header>

      {/* ── Main Content Area ── */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>

        {/* ── Left Sidebar ── */}
        <aside className="glass-effect" style={{
          width: 320, flexShrink: 0, padding: '1.5rem', overflowY: 'auto',
          display: 'flex', flexDirection: 'column', gap: '1.5rem',
          borderTop: 'none', borderBottom: 'none', borderLeft: 'none'
        }}>

          {/* Search Box */}
          <div className="glass-effect" style={{ padding: '1rem', borderRadius: 12, border: '1px solid var(--border-bright)' }}>
            <label style={{ fontSize: '0.7rem', color: 'var(--text-mute)', display: 'block', marginBottom: 8 }}>CÜZDAN ÜNVANI</label>
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && analyze()}
              placeholder="0x... or 1Bv..."
              style={{
                width: '100%', background: 'rgba(255,255,255,0.5)', border: '1px solid var(--border-dim)',
                borderRadius: 6, padding: '10px 12px', color: 'var(--text-main)', fontSize: '0.75rem',
                fontFamily: 'var(--font-mono)', marginBottom: 12, outline: 'none'
              }}
            />
            <button onClick={analyze} disabled={loading} style={{
              width: '100%', padding: '10px', borderRadius: 8, border: 'none',
              background: loading ? 'var(--text-mute)' : 'var(--accent-primary)',
              color: '#fff', fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer',
              boxShadow: loading ? 'none' : '0 4px 15px var(--accent-glow)'
            }}>
              {loading ? "ANALİZ EDİLİR..." : "ANALİZƏ BAŞLA"}
            </button>
          </div>

          {/* Risk Summary */}
          <div className="glass-effect" style={{ padding: '1.5rem', borderRadius: 12, textAlign: 'center' }}>
            <h3 style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '1rem' }}>RİSK QİYMƏTLƏNDİRMƏSİ</h3>
            <RiskGauge score={data?.risk?.score || 0} />
            <div style={{
              marginTop: '1rem', padding: '6px 12px', borderRadius: 6,
              background: riskColor(data?.risk?.score) + '11',
              border: `1px solid ${riskColor(data?.risk?.score)}33`,
              color: riskColor(data?.risk?.score), fontWeight: 700, fontSize: '0.9rem'
            }}>
              {data?.risk?.level}
            </div>
          </div>

          {/* Analytics Stats */}
          <div className="glass-effect" style={{ padding: '1.25rem', borderRadius: 12 }}>
            <h3 style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '1rem' }}>ŞƏBƏKƏ GÖSTƏRİCİLƏRİ</h3>
            {[
              { l: "Ümumi qovşaqlar", v: data?.stats?.nodes || data?.nodes?.length },
              { l: "Əlaqələr", v: data?.stats?.edges || data?.links?.length },
              { l: "Sıxlıq xalı", v: data?.stats?.density?.toFixed(4) || "0.0000" },
              { l: "Bağlı qruplar", v: data?.stats?.strongly_connected || "1" }
            ].map((s, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-mute)' }}>{s.l}</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>{s.v}</span>
              </div>
            ))}
          </div>

          {/* Alerts Section */}
          <div>
            <h3 style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '0.75rem', display: 'flex', justifyContent: 'space-between' }}>
              AKTİV BİLDİRİŞLƏR
              <span style={{ color: 'var(--risk-high)' }}>● {data?.alerts?.length || 0}</span>
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {(data?.alerts || []).map((a, i) => (
                <div key={i} style={{
                  padding: '10px', borderRadius: 8, background: 'rgba(0,0,0,0.02)',
                  border: `1px solid ${severityColor[a.severity]}44`
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontSize: '0.65rem', fontWeight: 700, color: severityColor[a.severity] }}>{a.type}</span>
                    <span style={{ fontSize: '0.6rem', color: 'var(--text-mute)' }}>{a.severity}</span>
                  </div>
                  <p style={{ fontSize: '0.7rem', color: 'var(--text-dim)', margin: 0, lineHeight: 1.4 }}>{a.detail}</p>
                </div>
              ))}
            </div>
          </div>

        </aside>

        {/* ── Main Canvas ── */}
        <main style={{ flex: 1, position: 'relative', background: 'radial-gradient(circle at center, #f1f5f9 0%, #f8fafc 100%)' }}>

          <ForceGraph data={data} onNodeClick={setSelected} />

          {/* Demo Data Alert Banner */}
          {data?.is_demo && (
            <div style={{
              position: 'absolute', top: 80, left: '50%', transform: 'translateX(-50%)',
              background: 'rgba(245, 158, 11, 0.95)', color: '#fff',
              padding: '10px 24px', borderRadius: '30px', fontSize: '0.8rem', fontWeight: 700,
              boxShadow: '0 8px 30px rgba(245, 158, 11, 0.3)',
              display: 'flex', alignItems: 'center', gap: '10px',
              zIndex: 100, border: '1px solid rgba(255,255,255,0.2)',
              backdropFilter: 'blur(8px)',
              animation: 'pulse 2s infinite'
            }}>
              <span style={{ fontSize: '1.2rem' }}>⚠️</span>
              DİQQƏT: Hazırda DEMO məlumatlar göstərilir.
            </div>
          )}

          {/* Floating UI: Target Info */}
          <div className="glass-effect" style={{
            position: 'absolute', top: 20, left: 20, padding: '12px 16px', borderRadius: 12,
            maxWidth: 400
          }}>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-mute)', marginBottom: 4, letterSpacing: '0.05em' }}>HƏDƏF OBYEKT</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--accent-primary)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{data?.queried_address}</div>
          </div>

          {/* Legend Overlay */}
          <div className="glass-effect" style={{
            position: 'absolute', bottom: 20, left: 20, padding: '10px 14px', borderRadius: 10,
            display: 'flex', gap: '1rem', fontSize: '0.65rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--risk-high)' }} /> Yüksək Risk
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--risk-medium)' }} /> Orta
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--risk-low)' }} /> Aşağı
            </div>
          </div>

          {/* Interactive Hint */}
          <div style={{ position: 'absolute', bottom: 20, right: 20, fontSize: '0.65rem', color: 'var(--text-mute)' }}>
            QOVŞAQLARI YERDƏYİŞDİRİN · YAXINLAŞDIRIN · DETALLAR ÜÇÜN KLİKLƏYİN
          </div>

          {/* Detail Panel Float */}
          {selected && (
            <div className="glass-effect" style={{
              position: 'absolute', bottom: 20, left: '50%', transform: 'translateX(-50%)',
              width: '90%', maxWidth: 800, padding: '1.5rem', borderRadius: 16,
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              animation: 'slideUp 0.3s ease-out',
              border: `1px solid ${riskColor(selected.risk)}66`
            }}>
              <div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-mute)', marginBottom: 6 }}>SEÇİLMİŞ QOVŞAQ MƏLUMATLARI</div>
                <div style={{ fontSize: '1.1rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--text-main)' }}>{selected.id}</div>
              </div>

              <div style={{ display: 'flex', gap: '2.5rem' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-mute)', marginBottom: 4 }}>ŞƏBƏKƏ</div>
                  <div style={{ fontSize: '1rem', fontWeight: 700, color: chainColor[selected.chain] }}>{selected.chain}</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-mute)', marginBottom: 4 }}>RİSK İNDEKSİ</div>
                  <div style={{ fontSize: '1rem', fontWeight: 700, color: riskColor(selected.risk) }}>{selected.risk}%</div>
                </div>
                <button onClick={() => setSelected(null)} style={{
                  background: 'rgba(0,0,0,0.03)', border: '1px solid var(--border-dim)',
                  width: 32, height: 32, borderRadius: '50%', color: 'var(--text-mute)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer'
                }}>✕</button>
              </div>
            </div>
          )}

        </main>
      </div>

      <style>{`
        @keyframes slideUp {
          from { transform: translate(-50%, 100%); opacity: 0; }
          to { transform: translate(-50%, 0); opacity: 1; }
        }
        @keyframes pulse {
          0% { transform: translateX(-50%) scale(1); }
          50% { transform: translateX(-50%) scale(1.02); }
          100% { transform: translateX(-50%) scale(1); }
        }
      `}</style>
    </div>
  );
}
