"""
AZ Blockchain Analyzer PDF hesabat generatoru

Azərbaycan hüquq-mühafizə orqanları üçün rəsmi istintaq sənədi.

İstifadə:
    from report import generate_report
    path = generate_report(analyze_result, output_dir="reports/")
"""

import os
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether,
)
from reportlab.graphics.shapes import Drawing, Rect, Circle, String, Line
from reportlab.graphics import renderPDF
from reportlab.graphics.charts.piecharts import Pie


C_BG        = colors.HexColor("#020c14")
C_NAVY      = colors.HexColor("#040f1c")
C_PANEL     = colors.HexColor("#0a1929")
C_BORDER    = colors.HexColor("#0f2744")
C_ACCENT    = colors.HexColor("#1d4ed8")
C_GOLD      = colors.HexColor("#f59e0b")
C_RED       = colors.HexColor("#ef4444")
C_YELLOW    = colors.HexColor("#f59e0b")
C_GREEN     = colors.HexColor("#22c55e")
C_MUTED     = colors.HexColor("#64748b")
C_TEXT      = colors.HexColor("#e2e8f0")
C_SUBTEXT   = colors.HexColor("#94a3b8")
C_BTC       = colors.HexColor("#f7931a")
C_ETH       = colors.HexColor("#627eea")
C_WHITE     = colors.white
C_BLACK     = colors.HexColor("#0f172a")

PAGE_W, PAGE_H = A4
MARGIN = 2 * cm


def risk_color(score: int):
    if score >= 70: return C_RED
    if score >= 40: return C_YELLOW
    return C_GREEN


def risk_bg(score: int):
    if score >= 70: return colors.HexColor("#3f0f0f")
    if score >= 40: return colors.HexColor("#3f2f0f")
    return colors.HexColor("#0f2f0f")



def make_styles():
    base = getSampleStyleSheet()

    def s(name, **kw):
        return ParagraphStyle(name, **kw)

    return {
        "cover_title": s("cover_title",
            fontSize=26, fontName="Helvetica-Bold",
            textColor=C_WHITE, alignment=TA_CENTER, spaceAfter=6),

        "cover_sub": s("cover_sub",
            fontSize=12, fontName="Helvetica",
            textColor=C_GOLD, alignment=TA_CENTER, spaceAfter=4),

        "cover_meta": s("cover_meta",
            fontSize=9, fontName="Helvetica",
            textColor=C_MUTED, alignment=TA_CENTER, spaceAfter=2),

        "section_title": s("section_title",
            fontSize=13, fontName="Helvetica-Bold",
            textColor=C_WHITE, spaceBefore=14, spaceAfter=6,
            borderPad=4),

        "body": s("body",
            fontSize=9, fontName="Helvetica",
            textColor=C_SUBTEXT, spaceAfter=4, leading=14,
            alignment=TA_JUSTIFY),

        "label": s("label",
            fontSize=8, fontName="Helvetica-Bold",
            textColor=C_MUTED, spaceAfter=2, leading=11),

        "value": s("value",
            fontSize=10, fontName="Helvetica-Bold",
            textColor=C_TEXT, spaceAfter=4, leading=14),

        "mono": s("mono",
            fontSize=8, fontName="Courier",
            textColor=C_SUBTEXT, spaceAfter=2, leading=12),

        "mono_address": s("mono_address",
            fontSize=8, fontName="Courier-Bold",
            textColor=C_GOLD, spaceAfter=4, leading=12),

        "alert_high": s("alert_high",
            fontSize=9, fontName="Helvetica",
            textColor=C_RED, spaceAfter=2, leading=13),

        "alert_med": s("alert_med",
            fontSize=9, fontName="Helvetica",
            textColor=C_YELLOW, spaceAfter=2, leading=13),

        "alert_low": s("alert_low",
            fontSize=9, fontName="Helvetica",
            textColor=C_MUTED, spaceAfter=2, leading=13),

        "footer": s("footer",
            fontSize=7, fontName="Helvetica",
            textColor=C_MUTED, alignment=TA_CENTER),

        "toc_item": s("toc_item",
            fontSize=10, fontName="Helvetica",
            textColor=C_SUBTEXT, spaceAfter=4, leading=14),
    }



def make_risk_gauge(score: int, width=160, height=100) -> Drawing:
    d   = Drawing(width, height)
    cx  = width / 2
    cy  = 20
    r   = 55

    from reportlab.graphics.shapes import Wedge
    d.add(Wedge(cx, cy, r, 0, 180, fillColor=colors.HexColor("#1e293b"),
                strokeColor=None, strokeWidth=0))
    d.add(Wedge(cx, cy, r - 14, 0, 180, fillColor=C_NAVY,
                strokeColor=None, strokeWidth=0))

    angle = score * 1.8  # 0–100 → 0–180
    rc    = risk_color(score)
    d.add(Wedge(cx, cy, r, 0, angle, fillColor=rc,
                strokeColor=None, strokeWidth=0))
    d.add(Wedge(cx, cy, r - 14, 0, angle, fillColor=C_NAVY,
                strokeColor=None, strokeWidth=0))

    d.add(Circle(cx, cy, 16, fillColor=C_PANEL, strokeColor=rc, strokeWidth=1.5))

    
    d.add(String(cx, cy + 4, str(score),
                 fontSize=15, fontName="Helvetica-Bold",
                 fillColor=rc, textAnchor="middle"))
    d.add(String(cx, cy - 9, "/100",
                 fontSize=7, fontName="Helvetica",
                 fillColor=C_MUTED, textAnchor="middle"))

    d.add(String(8, cy - 2, "0",   fontSize=7, fontName="Helvetica", fillColor=C_MUTED, textAnchor="middle"))
    d.add(String(width - 8, cy - 2, "100", fontSize=7, fontName="Helvetica", fillColor=C_MUTED, textAnchor="middle"))

    return d



def make_cover(story, st, data: dict):
    now = datetime.now(timezone.utc).strftime("%d.%m.%Y  %H:%M UTC")

    story.append(HRFlowable(width="100%", thickness=3, color=C_ACCENT, spaceAfter=0))
    story.append(Spacer(1, 1.2 * cm))

    logo_d = Drawing(PAGE_W - 2 * MARGIN, 60)
    pts = []
    cx2, cy2, r2 = 30, 30, 28
    import math
    for i in range(6):
        a = math.pi / 6 + i * math.pi / 3
        pts += [cx2 + r2 * math.cos(a), cy2 + r2 * math.sin(a)]
    from reportlab.graphics.shapes import Polygon
    logo_d.add(Polygon(pts, fillColor=colors.HexColor("#f59e0b22"),
                       strokeColor=C_GOLD, strokeWidth=1.5))
    logo_d.add(Circle(cx2, cy2, 8, fillColor=C_GOLD, strokeColor=None))
    logo_d.add(String(72, 22, "AZ BLOCKCHAIN ANALYZER",
                      fontSize=20, fontName="Helvetica-Bold",
                      fillColor=C_WHITE, textAnchor="start"))
    logo_d.add(String(72, 8, "KRİMİNALİSTİK ANALİZ SİSTEMİ — PROTOTİP v1.0",
                      fontSize=9, fontName="Helvetica",
                      fillColor=C_GOLD, textAnchor="start"))
    story.append(logo_d)
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER))
    story.append(Spacer(1, 1.5 * cm))

    story.append(Paragraph("BLOCKCHAIN TRANZAKSİYA<br/>ANALİZ HESABATI", st["cover_title"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("Rəsmi İstintaq Sənədi", st["cover_sub"]))
    story.append(Spacer(1, 1.5 * cm))
    score   = data.get("risk", {}).get("score", 0)
    level   = data.get("risk", {}).get("level", "LOW")
    rc      = risk_color(score)
    rbg     = risk_bg(score)

    badge_d = Drawing(PAGE_W - 2 * MARGIN, 90)
    bw      = 220
    bx      = (PAGE_W - 2 * MARGIN - bw) / 2
    badge_d.add(Rect(bx, 5, bw, 80, rx=10,
                     fillColor=rbg, strokeColor=rc, strokeWidth=1.5))
    badge_d.add(String(bx + bw / 2, 62, "RİSK SƏVİYYƏSİ",
                       fontSize=8, fontName="Helvetica",
                       fillColor=C_MUTED, textAnchor="middle"))
    badge_d.add(String(bx + bw / 2, 38, level,
                       fontSize=26, fontName="Helvetica-Bold",
                       fillColor=rc, textAnchor="middle"))
    badge_d.add(String(bx + bw / 2, 16, f"Skor: {score} / 100",
                       fontSize=10, fontName="Helvetica",
                       fillColor=rc, textAnchor="middle"))
    story.append(badge_d)
    story.append(Spacer(1, 1.2 * cm))

    chain   = data.get("chain", "—")
    address = data.get("address", "—")
    tx_cnt  = data.get("tx_count", 0)
    val     = data.get("total_value", 0)
    unit    = "BTC" if chain == "BTC" else "ETH"

    meta_rows = [
        ["Sorğulanan Ünvan", address],
        ["Şəbəkə",           chain],
        ["Tranzaksiya sayı", str(tx_cnt)],
        [f"Cəm dəyər ({unit})", f"{val:.8f}"],
        ["Analiz tarixi",    now],
        ["Tərtib edən",      "AZ Blockchain Analyzer v1.0"],
    ]
    meta_t = Table(meta_rows, colWidths=[4.5 * cm, PAGE_W - 2 * MARGIN - 4.5 * cm])
    meta_t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (0, -1), C_PANEL),
        ("BACKGROUND",  (1, 0), (1, -1), C_NAVY),
        ("TEXTCOLOR",   (0, 0), (0, -1), C_MUTED),
        ("TEXTCOLOR",   (1, 0), (1, -1), C_TEXT),
        ("FONTNAME",    (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",    (1, 0), (1, -1), "Courier"),
        ("FONTSIZE",    (0, 0), (-1, -1), 8.5),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [C_PANEL, C_NAVY]),
        ("GRID",        (0, 0), (-1, -1), 0.5, C_BORDER),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING",   (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 7),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(meta_t)
    story.append(Spacer(1, 1.5 * cm))

    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER))
    story.append(Spacer(1, 0.3 * cm))

    conf_d = Drawing(PAGE_W - 2 * MARGIN, 24)
    conf_d.add(Rect(0, 0, PAGE_W - 2 * MARGIN, 24, rx=4,
                    fillColor=colors.HexColor("#1a0a0a"),
                    strokeColor=C_RED, strokeWidth=1))
    conf_d.add(String((PAGE_W - 2 * MARGIN) / 2, 8,
                      "GİZLİ — YALNIZ SƏLAHİYYƏTLİ ŞƏXSLƏR ÜÇÜN",
                      fontSize=9, fontName="Helvetica-Bold",
                      fillColor=C_RED, textAnchor="middle"))
    story.append(conf_d)

    story.append(PageBreak())



def section_header(story, st, title: str, number: str):
    d = Drawing(PAGE_W - 2 * MARGIN, 28)
    d.add(Rect(0, 0, PAGE_W - 2 * MARGIN, 28, rx=5,
               fillColor=C_PANEL, strokeColor=C_ACCENT, strokeWidth=1))
    d.add(Rect(0, 0, 4, 28, rx=0, fillColor=C_ACCENT, strokeColor=None))
    d.add(String(14, 9, f"{number}  {title}",
                 fontSize=12, fontName="Helvetica-Bold",
                 fillColor=C_WHITE, textAnchor="start"))
    story.append(d)
    story.append(Spacer(1, 0.3 * cm))


def kv_table(rows, col_w=(4 * cm,)):
    right_w = PAGE_W - 2 * MARGIN - col_w[0]
    t = Table(rows, colWidths=[col_w[0], right_w])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (0, -1), C_PANEL),
        ("BACKGROUND",  (1, 0), (1, -1), C_NAVY),
        ("TEXTCOLOR",   (0, 0), (0, -1), C_MUTED),
        ("TEXTCOLOR",   (1, 0), (1, -1), C_TEXT),
        ("FONTNAME",    (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",    (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 0), (-1, -1), 8.5),
        ("GRID",        (0, 0), (-1, -1), 0.5, C_BORDER),
        ("LEFTPADDING",  (0, 0), (-1, -1), 9),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [C_PANEL, C_NAVY]),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


class ReportTemplate(SimpleDocTemplate):
    def __init__(self, filename, data, **kw):
        super().__init__(filename, **kw)
        self.report_data = data

    def handle_pageBegin(self):
        super().handle_pageBegin()

    def afterPage(self):
        c    = self.canv
        data = self.report_data
        now  = datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")

        c.setStrokeColor(C_BORDER)
        c.setLineWidth(0.5)
        c.line(MARGIN, PAGE_H - 1.3 * cm, PAGE_W - MARGIN, PAGE_H - 1.3 * cm)
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(C_MUTED)
        c.drawString(MARGIN, PAGE_H - 1.1 * cm, "AZ BLOCKCHAIN ANALYZER")
        c.setFont("Helvetica", 7)
        c.drawRightString(PAGE_W - MARGIN, PAGE_H - 1.1 * cm,
                          f"GİZLİ  |  {now}")

        c.line(MARGIN, 1.4 * cm, PAGE_W - MARGIN, 1.4 * cm)
        c.setFont("Helvetica", 7)
        c.setFillColor(C_MUTED)
        addr = data.get("address", "")
        c.drawString(MARGIN, 0.9 * cm, f"Ünvan: {addr[:40]}...")
        c.drawRightString(PAGE_W - MARGIN, 0.9 * cm,
                          f"Səhifə {self.canv.getPageNumber()}")


def generate_report(data: dict, output_dir: str = ".") -> str:
    os.makedirs(output_dir, exist_ok=True)
    ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
    addr_s  = data.get("address", "unknown")[:12].replace("/", "_")
    fname   = f"report_{addr_s}_{ts}.pdf"
    fpath   = os.path.join(output_dir, fname)

    doc = ReportTemplate(
        fpath, data,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=1.8 * cm, bottomMargin=1.8 * cm,
    )
    st    = make_styles()
    story = []

    make_cover(story, st, data)

    section_header(story, st, "İCMAL", "1.")
    score   = data.get("risk", {}).get("score", 0)
    level   = data.get("risk", {}).get("level", "LOW")
    chain   = data.get("chain", "—")
    address = data.get("address", "—")

    gauge   = make_risk_gauge(score, 180, 110)
    summary_text = (
        f"Bu hesabat <b>{chain}</b> şəbəkəsindəki "
        f"<font color='#f59e0b'>{address[:20]}...</font> "
        f"ünvanının avtomatlaşdırılmış blockchain kriminalistik analizinin nəticəsini əks etdirir. "
        f"Analiz zamanı {data.get('tx_count', 0)} tranzaksiya, "
        f"{len(data.get('alerts', []))} xəbərdarlıq və "
        f"{len(data.get('clusters', []))} wallet klasteri aşkarlanmışdır. "
        f"Ümumi risk skoru <b>{score}/100</b> olaraq qiymətləndirilmişdir."
    )

    sum_t = Table(
        [[gauge, Paragraph(summary_text, st["body"])]],
        colWidths=[5 * cm, PAGE_W - 2 * MARGIN - 5 * cm],
    )
    sum_t.setStyle(TableStyle([
        ("VALIGN",  (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ("BACKGROUND",   (0, 0), (-1, -1), C_PANEL),
        ("GRID",         (0, 0), (-1, -1), 0.5, C_BORDER),
        ("LEFTPADDING",  (1, 0), (1, 0), 14),
    ]))
    story.append(KeepTogether([sum_t]))
    story.append(Spacer(1, 0.5 * cm))

    section_header(story, st, "QRAF STATİSTİKASI", "2.")
    gs   = data.get("graph_stats") or data.get("stats") or {}
    rows = [
        ["Node (unikal ünvan)", str(gs.get("nodes", data.get("nodes", []).__len__() if isinstance(data.get("nodes"), list) else "—"))],
        ["Edge (əlaqə sayı)",   str(gs.get("edges", data.get("links", []).__len__() if isinstance(data.get("links"), list) else "—"))],
        ["Qraf sıxlığı",        str(gs.get("density", "—"))],
        ["Güclü komponent",     str(gs.get("strongly_connected", "—"))],
    ]
    story.append(kv_table(rows, col_w=(5.5 * cm,)))
    story.append(Spacer(1, 0.5 * cm))

    section_header(story, st, "TRANZAKSİYALAR", "3.")

    txs = data.get("transactions", [])
    if txs:
        hdr = ["#", "Şəbəkə", "Hash (qısa)", "Zaman", "Dəyər", "Giriş → Çıxış"]
        tx_rows = [hdr]
        unit = "BTC" if chain == "BTC" else "ETH"
        for i, tx in enumerate(txs[:20], 1):
            if isinstance(tx, dict):
                h   = tx.get("hash", "")[:18] + "..."
                ts2 = str(tx.get("timestamp", ""))[:16]
                val = tx.get("value_btc") or tx.get("value_eth") or tx.get("value", 0)
                inp = (tx.get("inputs", ["?"])[0] or "?")[:14] + "..."
                out = (tx.get("outputs", ["?"])[0] or "?")[:14] + "..."
                ch  = tx.get("chain", chain)
            else:
                h   = tx.hash[:18] + "..."
                ts2 = str(tx.timestamp)[:16]
                val = tx.value
                inp = (tx.inputs[0] if tx.inputs else "?")[:14] + "..."
                out = (tx.outputs[0] if tx.outputs else "?")[:14] + "..."
                ch  = tx.chain

            tx_rows.append([str(i), ch, h, ts2, f"{val:.4f}", f"{inp} → {out}"])

        col_w2 = [0.6*cm, 1.2*cm, 3.8*cm, 2.8*cm, 2.2*cm,
                  PAGE_W - 2*MARGIN - 0.6 - 1.2 - 3.8 - 2.8 - 2.2 - 0.5]
        tx_t = Table(tx_rows, colWidths=[c * cm for c in
               [0.6, 1.2, 3.8, 2.8, 2.2, PAGE_W/cm - 2*2 - 0.6 - 1.2 - 3.8 - 2.8 - 2.2]])
        tx_t.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, 0), C_ACCENT),
            ("TEXTCOLOR",   (0, 0), (-1, 0), C_WHITE),
            ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1, -1), 7.5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_NAVY, C_PANEL]),
            ("TEXTCOLOR",   (0, 1), (-1, -1), C_SUBTEXT),
            ("FONTNAME",    (0, 1), (-1, -1), "Courier"),
            ("GRID",        (0, 0), (-1, -1), 0.5, C_BORDER),
            ("LEFTPADDING",  (0, 0), (-1, -1), 6),
            ("TOPPADDING",   (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
            ("ALIGN",        (0, 0), (-1, -1), "LEFT"),
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(tx_t)
        if len(txs) > 20:
            story.append(Spacer(1, 0.2*cm))
            story.append(Paragraph(f"* {len(txs) - 20} əlavə tranzaksiya göstərilmir.",
                                   st["label"]))
    else:
        story.append(Paragraph("Tranzaksiya məlumatı tapılmadı.", st["body"]))

    story.append(Spacer(1, 0.5 * cm))

    clusters = data.get("clusters", [])
    if clusters:
        section_header(story, st, "WALLET KLASTERLƏŞMƏSİ", "4.")
        story.append(Paragraph(
            "Aşağıdakı klasterlər Common Input Ownership (CIO) heuristikası əsasında müəyyən edilmişdir. "
            "Eyni klasterdəki ünvanlar eyni şəxsə və ya quruma aid ola bilər.",
            st["body"]
        ))
        story.append(Spacer(1, 0.2 * cm))

        cl_hdr  = [["#", "Klaster ID", "Ünvan sayı", "Nümunə ünvan"]]
        cl_rows = []
        for i, cl in enumerate(clusters[:10], 1):
            if isinstance(cl, dict):
                cl_rows.append([
                    str(i),
                    str(cl.get("cluster_id", ""))[:16] + "...",
                    str(cl.get("address_count", "")),
                    str(cl.get("sample_address", ""))[:30] + "...",
                ])
        cl_t = Table(cl_hdr + cl_rows,
                     colWidths=[0.7*cm, 3.5*cm, 2.2*cm,
                                PAGE_W/cm*cm - 2*MARGIN - 0.7*cm - 3.5*cm - 2.2*cm])
        cl_t.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#0f2744")),
            ("TEXTCOLOR",   (0, 0), (-1, 0), C_GOLD),
            ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_NAVY, C_PANEL]),
            ("TEXTCOLOR",   (0, 1), (-1, -1), C_SUBTEXT),
            ("FONTNAME",    (0, 1), (-1, -1), "Courier"),
            ("GRID",        (0, 0), (-1, -1), 0.5, C_BORDER),
            ("LEFTPADDING",  (0, 0), (-1, -1), 7),
            ("TOPPADDING",   (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(cl_t)
        story.append(Spacer(1, 0.5 * cm))

    section_header(story, st, "ŞÜBHƏLİ PATTERN ANALİZİ", "5.")
    alerts = data.get("alerts", [])
    if alerts:
        sev_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        sorted_alerts = sorted(alerts, key=lambda a: sev_order.get(
            a.get("severity") if isinstance(a, dict) else a.severity, 3))

        for al in sorted_alerts:
            if isinstance(al, dict):
                sev    = al.get("severity", "LOW")
                atype  = al.get("type", "")
                detail = al.get("detail", "")
                tx     = al.get("tx", "")
            else:
                sev    = al.severity
                atype  = al.type
                detail = al.detail
                tx     = al.tx

            sc  = {  "HIGH": C_RED, "MEDIUM": C_YELLOW, "LOW": C_MUTED  }.get(sev, C_MUTED)
            sbg = { "HIGH": "#3f0f0f", "MEDIUM": "#3f2f0f", "LOW": "#1a1a2e" }.get(sev, "#1a1a2e")

            al_d = Drawing(PAGE_W - 2 * MARGIN, 36)
            al_d.add(Rect(0, 0, PAGE_W - 2 * MARGIN, 36, rx=5,
                          fillColor=colors.HexColor(sbg),
                          strokeColor=sc, strokeWidth=0.8))
            al_d.add(Rect(0, 0, 5, 36, fillColor=sc, strokeColor=None))
            al_d.add(String(14, 22, f"[{sev}]  {atype}",
                            fontSize=9, fontName="Helvetica-Bold",
                            fillColor=sc, textAnchor="start"))
            al_d.add(String(14, 9, detail,
                            fontSize=8, fontName="Helvetica",
                            fillColor=C_SUBTEXT, textAnchor="start"))
            al_d.add(String(PAGE_W - 2 * MARGIN - 8, 9, tx,
                            fontSize=7, fontName="Courier",
                            fillColor=C_MUTED, textAnchor="end"))
            story.append(al_d)
            story.append(Spacer(1, 0.15 * cm))
    else:
        story.append(Paragraph("Heç bir şübhəli pattern aşkarlanmadı.", st["body"]))

    story.append(Spacer(1, 0.5 * cm))

    section_header(story, st, "TÖVSİYƏLƏR VƏ NƏTİCƏ", "6.")

    rec_map = {
        "HIGH": [
            "Dərhal rəsmi istintaq başladılsın.",
            "FIMSA-ya (Maliyyə Monitorinqi Xidməti) məlumat verilsin.",
            "Əlaqəli bütün ünvanlar dondurulsun.",
            "Beynəlxalq kanallar vasitəsilə (INTERPOL, Egmont) əməkdaşlıq tələb oluna bilər.",
            "Chainalysis və ya Elliptic kimi peşəkar alətlərlə dərin analiz aparılsın.",
        ],
        "MEDIUM": [
            "Əlavə tranzaksiya monitorinqi başladılsın.",
            "Müvafiq birja (exchange) platforma sorğusu göndərilsin.",
            "30 gün müddətində yenidən qiymətləndirilsin.",
            "FATF Seyahət Qaydası (Travel Rule) çərçivəsində məlumat tələb olunsun.",
        ],
        "LOW": [
            "Adi monitorinq prosesi davam etdirilsin.",
            "Növbəti yoxlama 90 gün sonra aparılsın.",
        ],
    }

    for i, rec in enumerate(rec_map.get(level, rec_map["LOW"]), 1):
        story.append(Paragraph(f"  {i}.  {rec}", st["body"]))

    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "Bu hesabat AZ Blockchain Analyzer Prototip v1.0 sistemi tərəfindən avtomatik yaradılmışdır. "
        "Hesabat hüquqi sənəd qüvvəsi daşımır; yalnız ilkin kriminalistik qiymətləndirmə məqsədilə nəzərdə tutulmuşdur. "
        "Rəsmi istintaq prosesi üçün sertifikatlı ekspert rəyi tələb olunur.",
        st["footer"]
    ))

    doc.build(story)
    return fpath


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from graph import (build_transaction_graph, get_graph_stats,
                       cluster_by_common_input, detect_patterns, calculate_risk_score)

    DEMO = [
        {"chain":"BTC","hash":"a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
         "timestamp":"2024-01-15T10:22:00Z",
         "inputs":["1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2","1A8JiWcwvpY7tAopUkSnGuwotti7g9kn7g"],
         "outputs":["1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF","1HLoD9E4SDFFPDiYfNYnkBLQ85Y51J3Zb1"],
         "value_btc":2.5,"fee_sat":1500},
        {"chain":"BTC","hash":"b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3",
         "timestamp":"2024-01-15T11:05:00Z",
         "inputs":["1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF"],
         "outputs":["1dice8EMZmqKvrGE4Qc9bUFngAia8TD9Bs","1ez69SnzzmePmZX3WpEzMKTrcBF2gpNQ55",
                    "15ubicBBWFnvoZLT7GiU2qxjRaKJPdkDMG","1LomaFwStWriz3vVvTmRZrNVZHiYHPbDmF",
                    "12cbQLTFMXRnSzktFkuoG3eHoMeFtpTu3S","1HT7xU2Ngenf7D4yocz2SAcnNLW7rK8d4Y"],
         "value_btc":2.0,"fee_sat":3000},
        {"chain":"BTC","hash":"c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
         "timestamp":"2024-01-15T12:30:00Z",
         "inputs":["1dice8EMZmqKvrGE4Qc9bUFngAia8TD9Bs","15ubicBBWFnvoZLT7GiU2qxjRaKJPdkDMG"],
         "outputs":["1ez69SnzzmePmZX3WpEzMKTrcBF2gpNQ55"],
         "value_btc":1.0,"fee_sat":1000},
        {"chain":"ETH","hash":"0xd4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5",
         "timestamp":"2024-01-15T14:00:00Z",
         "inputs":["0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe"],
         "outputs":["0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8"],
         "value_eth":5.0,"gas_used":21000},
        {"chain":"BTC","hash":"e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6",
         "timestamp":"2024-01-16T09:00:00Z",
         "inputs":["1HLoD9E4SDFFPDiYfNYnkBLQ85Y51J3Zb1","1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
                   "1A8JiWcwvpY7tAopUkSnGuwotti7g9kn7g"],
         "outputs":["1GkQmKAmHtNfnD3LHhTkewJxKHVSta4m2A"],
         "value_btc":3.0,"fee_sat":2500},
    ]

    G        = build_transaction_graph(DEMO)
    stats    = get_graph_stats(G)
    clusters_raw = cluster_by_common_input(DEMO)
    multi    = {k: v for k, v in clusters_raw.items() if len(v) > 1}
    alerts   = detect_patterns(DEMO, clusters_raw)
    risk     = calculate_risk_score(alerts)

    clusters_out = [
        {"cluster_id": k[:16], "address_count": len(v), "sample_address": v[0]}
        for k, v in multi.items()
    ]

    report_data = {
        "address":     "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
        "chain":       "BTC",
        "tx_count":    len(DEMO),
        "total_value": sum(t.get("value_btc", 0) or t.get("value_eth", 0) for t in DEMO),
        "transactions": DEMO,
        "graph_stats": stats,
        "clusters":    clusters_out,
        "alerts":      alerts,
        "risk":        risk,
    }

    path = generate_report(report_data, output_dir="/tmp/az_reports")
    print(f"PDF yaradıldı: {path}")
