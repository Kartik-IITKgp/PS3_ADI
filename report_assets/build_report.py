#!/usr/bin/env python3
"""Build the PS3 report PDF (Times New Roman 12pt, themed layout).

Theme colours are centralised in THEME so the palette can be re-matched to the
reference PDF (2025112.pdf) by editing a few hex values and re-running.
Structure:
  1  Executive Summary
  2  The Business Problem
  3  Dataset and Data Quality
  4  Exploratory Analysis of Field-Visit Evidence
  5  Commercial Baseline Geocoder Evaluation
  6  Model Architecture and Detailed Design
  7  Model Evaluation
  8  Key Insights and Interpretation
  9  Evaluation Framework and Reproducibility
  10 Security, RBAC and Compliance
  11 Deployment Plan
  12 Known Limitations and Next Engineering Work
  13 Deliverables and Submission
  14 Conclusion
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, Image, Table, TableStyle, PageBreak,
                                NextPageTemplate, KeepTogether, HRFlowable)
from reportlab.platypus.tableofcontents import TableOfContents
from PIL import Image as PILImage
import hashlib

# --------------------------------------------------------------------------- theme
THEME = {
    'primary': '#1F3864',   # dark navy  : cover band, H1, table headers
    'accent':  '#2E74B5',   # medium blue: H2, rules, accents
    'light':   '#DEEAF6',   # light blue : code background
    'zebra':   '#F2F6FB',   # alt table rows
    'text':    '#1A1A1A',
    'muted':   '#595959',
    'rule':    '#BFBFBF',
}
PRIMARY = colors.HexColor(THEME['primary'])
ACCENT = colors.HexColor(THEME['accent'])
LIGHT = colors.HexColor(THEME['light'])
ZEBRA = colors.HexColor(THEME['zebra'])
TEXT = colors.HexColor(THEME['text'])
MUTED = colors.HexColor(THEME['muted'])
RULE = colors.HexColor(THEME['rule'])

PAGE_W, PAGE_H = A4
ML = MR = 25 * mm
MT = 24 * mm
MB = 22 * mm
BODY_W = PAGE_W - ML - MR
IN = mm / 25.4

FIG = '/home/user/PS3_ADI/report_assets/figures'
OUT = '/home/user/PS3_ADI/PS3_Report.pdf'

# --------------------------------------------------------------------------- styles
def S(name, **kw):
    base = dict(fontName='Times-Roman', fontSize=12, leading=16.5,
                textColor=TEXT, alignment=TA_JUSTIFY)
    base.update(kw)
    return ParagraphStyle(name, **base)

st = {
    'body':    S('body'),
    'bodyc':   S('bodyc', alignment=TA_CENTER),
    'bullet':  S('bullet', leftIndent=16, firstLineIndent=-10, spaceBefore=2, spaceAfter=2),
    'numitem': S('numitem', leftIndent=18, firstLineIndent=-14, spaceBefore=3, spaceAfter=3),
    'h1':      S('h1', fontName='Times-Bold', fontSize=15, leading=19,
                 textColor=PRIMARY, spaceBefore=14, spaceAfter=4, alignment=TA_LEFT,
                 keepWithNext=1),
    'h2':      S('h2', fontName='Times-Bold', fontSize=12.5, leading=16,
                 textColor=ACCENT, spaceBefore=10, spaceAfter=3, alignment=TA_LEFT,
                 keepWithNext=1),
    'h3':      S('h3', fontName='Times-Bold', fontSize=12, leading=15,
                 textColor=PRIMARY, spaceBefore=8, spaceAfter=2, alignment=TA_LEFT,
                 keepWithNext=1),
    'cap':     S('cap', fontName='Times-Italic', fontSize=10, leading=13,
                 textColor=MUTED, alignment=TA_CENTER, spaceBefore=3, spaceAfter=10),
    'tcap':    S('tcap', fontName='Times-Italic', fontSize=10, leading=13,
                 textColor=MUTED, alignment=TA_CENTER, spaceBefore=10, spaceAfter=3,
                 keepWithNext=1),
    'code':    S('code', fontName='Courier', fontSize=8.5, leading=11.5,
                 alignment=TA_LEFT, textColor=TEXT, leftIndent=8, rightIndent=8),
    'cover_inst': S('cover_inst', fontName='Times-Bold', fontSize=21, leading=26,
                    textColor=colors.white, alignment=TA_CENTER),
    'cover_kicker': S('cover_kicker', fontName='Times-Bold', fontSize=14, leading=18,
                      textColor=ACCENT, alignment=TA_CENTER),
    'cover_title': S('cover_title', fontName='Times-Bold', fontSize=23, leading=29,
                     textColor=PRIMARY, alignment=TA_CENTER),
    'cover_sub': S('cover_sub', fontSize=14, leading=19, textColor=TEXT,
                   alignment=TA_CENTER),
    'meta_k':  S('meta_k', fontName='Times-Bold', fontSize=12, leading=17,
                 textColor=PRIMARY, alignment=TA_LEFT),
    'meta_v':  S('meta_v', fontSize=12, leading=17, alignment=TA_LEFT),
    'toc_h':   S('toc_h', fontName='Times-Bold', fontSize=15, leading=19,
                 textColor=PRIMARY, alignment=TA_LEFT, spaceAfter=12),
    'toc0':    S('toc0', fontName='Times-Bold', fontSize=12, leading=19,
                 textColor=TEXT, leftIndent=0),
    'toc1':    S('toc1', fontSize=11, leading=16.5, leftIndent=18, textColor=TEXT),
}

# --------------------------------------------------------------------------- helpers
# Characters outside WinAnsi (the encoding of the base-14 Times fonts)
_WINANSI_FIX = {
    '\u2192': '->',
    '\u2212': '-',
    '\u2264': '<=',
    '\u2265': '>=',
    '\u2248': '~',
}

def _safe(s):
    for a, b in _WINANSI_FIX.items():
        s = s.replace(a, b)
    return s

def P(text, style='body'):
    return Paragraph(_safe(text), st[style])

def B(text):
    return Paragraph(_safe(text), st['bullet'], bulletText='\u2022')

def H1(num, title):
    return Paragraph(_safe(f'{num}.&nbsp;&nbsp;{title}'), st['h1'])

def H2(num, title):
    return Paragraph(_safe(f'{num}&nbsp;&nbsp;{title}'), st['h2'])

def H3(title):
    return Paragraph(_safe(title), st['h3'])

def rule_under():
    return HRFlowable(width='100%', thickness=1.1, color=ACCENT,
                      spaceBefore=0, spaceAfter=8)

def h1block(num, title):
    return [H1(num, title), rule_under()]

def fig_image(path, width=None, cap=None):
    im = PILImage.open(path)
    w, h = im.size
    width = width or BODY_W
    height = width * h / w
    parts = [Image(path, width=width, height=height)]
    if cap:
        parts.append(Paragraph(_safe(cap), st['cap']))
    return KeepTogether(parts)

def table(data, colw, header=True, fontsize=9.5, align_right_cols=(), zebra=True,
          span=None):
    total = sum(colw)
    assert total <= BODY_W + 2, f'table wider than frame: {total / mm:.1f}mm'
    def cell_style(bold, white, right):
        return S(f'tc_{bold}_{white}_{right}', fontName='Times-Bold' if bold else 'Times-Roman',
                 fontSize=fontsize, leading=fontsize + 3.2,
                 textColor=colors.white if white else TEXT,
                 alignment=TA_RIGHT if right else TA_LEFT, spaceAfter=0)
    styles = {
        (0, 0): cell_style(True, True, False),
        (0, 1): cell_style(True, True, True),
        (1, 0): cell_style(False, False, False),
        (1, 1): cell_style(False, False, True),
    }
    rows = []
    for ri, row in enumerate(data):
        r = []
        for ci, val in enumerate(row):
            is_hdr = header and ri == 0
            if is_hdr:
                key = (0, 1 if ci in align_right_cols else 0)
            else:
                key = (1, 1 if ci in align_right_cols else 0)
            r.append(Paragraph(_safe(str(val)), styles[key]))
        rows.append(r)
    t = Table(rows, colWidths=colw, repeatRows=1 if header else 0)
    cmds = [
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, RULE),
    ]
    body0 = 1 if header else 0
    if header:
        cmds += [
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ]
    if zebra:
        cmds.append(('ROWBACKGROUNDS', (0, body0), (-1, -1), [colors.white, ZEBRA]))
    for c in align_right_cols:
        cmds.append(('ALIGN', (c, 0), (c, -1), 'RIGHT'))
    if span:
        cmds += span
    t.setStyle(TableStyle(cmds))
    return t

def tcap(text):
    return Paragraph(_safe(text), st['tcap'])

def codeblock(lines):
    body = '<br/>'.join(l.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        if l else '&nbsp;' for l in lines)
    t = Table([[Paragraph(body, st['code'])]], colWidths=[BODY_W])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.6, RULE),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return KeepTogether([Spacer(1, 4), t, Spacer(1, 6)])

# --------------------------------------------------------------------------- canvas
def draw_cover(canv, doc):
    canv.saveState()
    band_h = 120
    canv.setFillColor(PRIMARY)
    canv.rect(0, PAGE_H - band_h, PAGE_W, band_h, fill=1, stroke=0)
    canv.setFillColor(ACCENT)
    canv.rect(0, PAGE_H - band_h - 5, PAGE_W, 5, fill=1, stroke=0)
    canv.setFont('Times-Bold', 21)
    canv.setFillColor(colors.white)
    canv.drawCentredString(PAGE_W / 2, PAGE_H - 58, 'Indian Institute of Technology Kharagpur')
    canv.setFont('Times-Roman', 12.5)
    canv.drawCentredString(PAGE_W / 2, PAGE_H - 82, 'Applied Data Intelligence (ADI)  \u2022  Problem Set 3')
    canv.setFillColor(PRIMARY)
    canv.rect(0, 0, PAGE_W, 34, fill=1, stroke=0)
    canv.setFillColor(ACCENT)
    canv.rect(0, 34, PAGE_W, 4, fill=1, stroke=0)
    canv.setFont('Times-Roman', 10)
    canv.setFillColor(colors.white)
    canv.drawCentredString(PAGE_W / 2, 14, 'Exploratory Data Analysis, Model Architecture, Evaluation and Delivery Report  \u2022  October 2026')
    canv.restoreState()

def draw_body(canv, doc):
    canv.saveState()
    y = PAGE_H - 16 * mm
    canv.setStrokeColor(PRIMARY)
    canv.setLineWidth(1.0)
    canv.line(ML, y, PAGE_W - MR, y)
    canv.setFont('Times-Italic', 8.5)
    canv.setFillColor(MUTED)
    canv.drawString(ML, y + 4, 'PS3 \u2014 AI-Native Field Address Geocoder')
    canv.drawRightString(PAGE_W - MR, y + 4, 'Exploratory Analysis, Model Design, Evaluation and Delivery')
    y2 = 15 * mm
    canv.setStrokeColor(RULE)
    canv.setLineWidth(0.6)
    canv.line(ML, y2, PAGE_W - MR, y2)
    canv.setFont('Times-Roman', 9)
    canv.setFillColor(MUTED)
    canv.drawCentredString(PAGE_W / 2, y2 - 12, f'Page {canv.getPageNumber()}')
    canv.restoreState()

class Doc(BaseDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            name = flowable.style.name
            if name in ('h1', 'h2'):
                text = flowable.getPlainText()
                key = hashlib.sha1(text.encode()).hexdigest()[:12]
                level = 0 if name == 'h1' else 1
                self.canv.bookmarkPage(key)
                self.canv.addOutlineEntry(text, key, level, 0)
                self.notify('TOCEntry', (level, text, self.page, key))

# --------------------------------------------------------------------------- story
story = []

# ---- cover (page 1)
story.append(Spacer(1, 46 * mm))
story.append(Paragraph('PROBLEM SET 3', st['cover_kicker']))
story.append(Spacer(1, 8))
story.append(Paragraph('AI-Native Field Address Geocoder', st['cover_title']))
story.append(Spacer(1, 5))
story.append(Paragraph('Exploratory Data Analysis, Model Architecture,<br/>Evaluation and Delivery Report', st['cover_sub']))
story.append(Spacer(1, 26))
meta = [
    ['Course:', 'Applied Data Intelligence (ADI) \u2014 PS3'],
    ['Project:', 'Address-intelligence geocoder with uncertainty and evidence trails'],
    ['Name:', 'Kartik'],
    ['Roll No.:', '2025112'],
    ['Date:', 'October 2026'],
]
mt = Table([[Paragraph(k, st['meta_k']), Paragraph(v, st['meta_v'])] for k, v in meta],
           colWidths=[34 * mm, 92 * mm])
mt.setStyle(TableStyle([
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('TOPPADDING', (0, 0), (-1, -1), 4),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ('LINEABOVE', (0, 0), (-1, 0), 0.8, RULE),
    ('LINEBELOW', (0, -1), (-1, -1), 0.8, RULE),
    ('LEFTPADDING', (0, 0), (-1, -1), 2),
]))
story.append(mt)
story.append(NextPageTemplate('Body'))
story.append(PageBreak())

# ---- TOC
story.append(Paragraph('Table of Contents', st['toc_h']))
toc = TableOfContents()
toc.levelStyles = [st['toc0'], st['toc1']]
toc.dotsMinLevel = 0
story.append(toc)
story.append(PageBreak())

# ---- list of figures / tables
story.append(Paragraph('List of Figures', st['toc_h']))
lof = [
    ['Fig. 1', 'Field-visit outcome distribution (n = 3,896)', '4.1'],
    ['Fig. 2', 'Visit evidence quality: GPS accuracy and dwell time by outcome', '4.2'],
    ['Fig. 3', 'Commercial baseline geocoder error distribution (projected metres)', '5.3'],
    ['Fig. 4', 'End-to-end model architecture', '6.1'],
    ['Fig. 5', 'Ranker feature importance (LightGBM, 150 trees)', '6.5'],
    ['Fig. 6', 'Head-to-head: commercial baseline vs weighted visit centroid', '7.2'],
    ['Fig. 7', 'Confidence calibration (predicted vs empirical accuracy)', '7.4'],
]
story.append(table([['Figure', 'Title', 'Section']] + lof, [22 * mm, 114 * mm, 20 * mm],
                   align_right_cols=(2,)))
story.append(Spacer(1, 14))
story.append(Paragraph('List of Tables', st['toc_h']))
lot = [
    ['Table 1', 'Fully-loaded contact-channel costs', '2.1'],
    ['Table 2', 'Product requirements mapped to implemented behaviour', '2.4'],
    ['Table 3', 'PS3 dataset inventory (train split)', '3.1'],
    ['Table 4', 'Coordinate ranges by table (projected metres)', '3.2'],
    ['Table 5', 'Data quality summary: nulls and duplicate keys', '3.3'],
    ['Table 6', 'Referential-integrity (orphan) checks', '3.3'],
    ['Table 7', 'Address type and source distribution', '3.4'],
    ['Table 8', 'Town-level address and landmark coverage', '3.4'],
    ['Table 9', 'Field-visit outcome distribution', '4.1'],
    ['Table 10', 'GPS accuracy and dwell-time statistics', '4.2'],
    ['Table 11', 'Evidence quality by visit outcome', '4.3'],
    ['Table 12', 'Agent visit concentration (top 9 of 30 agents)', '4.4'],
    ['Table 13', 'Commercial baseline geocoder evaluation (n = 66)', '5.2'],
    ['Table 14', 'Town-level baseline error', '5.3'],
    ['Table 15', 'Model pipeline: stage-by-stage inputs and outputs', '6.1'],
    ['Table 16', 'Candidate-generation sources', '6.3'],
    ['Table 17', 'Ranker feature contract (21 features) with training ranges', '6.5'],
    ['Table 18', 'Ranker training configuration', '6.5'],
    ['Table 19', 'Ranker feature importance (non-zero gain)', '6.5'],
    ['Table 20', 'Head-to-head evaluation results', '7.2'],
    ['Table 21', 'Confidence calibration bins (non-empty)', '7.4'],
    ['Table 22', 'PS3 deliverables and evidence', '13.1'],
    ['Table 23', 'Pre-pilot acceptance checklist', '13.2'],
]
story.append(table([['Table', 'Title', 'Section']] + lot, [22 * mm, 114 * mm, 20 * mm],
                   align_right_cols=(2,)))
story.append(PageBreak())

# ===========================================================================
# 1. Executive summary
# ===========================================================================
story += h1block(1, 'Executive Summary')
story.append(P(
    "CreditNirvana\u2019s field-collections teams must find borrowers whose addresses are often "
    "written as descriptions rather than postal locations. A commercial geocoder may return a "
    "locality centre even when the useful operational answer is \u201cbehind the ration shop, two "
    "lanes after the temple.\u201d The resulting search time is expensive, productive visits are "
    "lost, and an account can be marked address-not-traceable even though the borrower is present."))
story.append(P(
    "This project implements an address-intelligence service for that problem. It combines address "
    "text, landmarks, localities, historical visit evidence, GPS quality, dwell time, visit outcomes, "
    "remarks, integrity signals and shared-place evidence. The model is a 150-tree LightGBM "
    "classifier over a 21-feature evidence contract, fronted by a deterministic reliability-weighted "
    "aggregator that works even where the learned model has no support. The service returns a "
    "predicted location, an uncertainty radius, an explainable evidence trail and an operational "
    "recommendation. Reliable successful visits improve future predictions, while confirmed and "
    "predicted locations remain separate so that a weak prediction cannot overwrite a strong "
    "observation."))
story.append(P(
    "On the supplied train split (2,175 addresses, 3,896 visits, 66 surveyed ground-truth "
    "addresses), the evidence-weighted geocoder achieves a median location error of "
    "<b>204.4 m</b> compared with <b>380.8 m</b> for the commercial baseline geocoder \u2014 a 46.3% "
    "reduction in median error \u2014 and places 53.0% of addresses within 250 m versus 28.8% for the "
    "baseline. The uncertainty radius covers the true location for 72.7% of predictions, the expected "
    "calibration error is 0.155, and each prediction takes about 3.3 ms. The service is deliberately "
    "conservative: it uses projected PS3 coordinates as metres during evaluation, does not treat every "
    "check-in as ground truth, and refuses to report causal treatment effects because the supplied "
    "data lacks treatment assignment and an independent recovery outcome. Every reproducible "
    "evaluation run is recorded with a run ID, artifact version, configuration, source-file SHA-256 "
    "hashes, metrics and explicit limitations."))
story.append(Spacer(1, 4))

# ===========================================================================
# 2. Business problem
# ===========================================================================
story += h1block(2, 'The Business Problem')
story.append(H2('2.1', 'Operational setting'))
story.append(P(
    "The platform serves secured and unsecured retail, MSME and microfinance portfolios. A lender may "
    "hold millions of accounts across delinquency buckets, and field work is far more expensive than "
    "digital contact. The fully-loaded cost of the available channels is summarised in Table 1."))
story.append(tcap('Table 1. Typical fully-loaded cost per contact channel.'))
story.append(table([
    ['Channel', 'Typical fully-loaded cost'],
    ['SMS / WhatsApp', 'Fraction of a rupee'],
    ['AI voice', 'Approximately INR 1\u20133 per call'],
    ['Human tele-caller', 'Approximately INR 15\u201330 per connect'],
    ['Productive field visit', 'Approximately INR 150\u2013400'],
], [62 * mm, 96 * mm]))
story.append(P(
    "The correct objective is therefore recovery <i>net of contact cost, customer goodwill and "
    "compliance risk</i>. A geocoder is useful only if it increases the probability that a field visit "
    "is productive, without encouraging unlawful or excessive contact."))

story.append(H2('2.2', 'Why ordinary geocoding fails'))
story.append(P("Indian collection addresses frequently contain:"))
for b in [
    "mixed Devanagari, Roman, Kannada, Hindi and English text;",
    "transliteration differences such as <i>mandir</i> and <i>temple</i> for the same landmark;",
    "abbreviations, spelling errors and inconsistent house numbers;",
    "relational descriptions such as \u201cbehind\u201d, \u201cnear\u201d, \u201copposite\u201d and \u201cnext lane\u201d;",
    "informal landmarks that are not represented in any global geocoder;",
    "locality names shared by several towns;",
    "an address that identifies a shop, workplace or landmark rather than a precise residence.",
]:
    story.append(B(b))
story.append(P(
    "Returning the pincode centroid is technically a geocode but operationally unhelpful: in a dense "
    "or rural area the error can be hundreds of metres or several kilometres."))

story.append(H2('2.3', 'Why visit GPS is valuable but imperfect'))
story.append(P(
    "The answer is often already present in the platform: a prior agent may have met the borrower. "
    "However, a check-in is evidence, not unquestionable truth. The borrower may have been met at work "
    "or on a road; GPS accuracy may be poor; a device may have checked in at a tea stall or the "
    "agent\u2019s home; a failed search may be near the address without being at it; and a successful "
    "outcome can still be recorded with a misleading location. The solution must therefore combine "
    "evidence with reliability weights and uncertainty, not copy the latest latitude and longitude."))

story.append(H2('2.4', 'Product requirements mapped to system behaviour'))
story.append(tcap('Table 2. Requirements from the PS3 problem statement and the behaviour that implements them.'))
reqs = [
    ['Location pin', 'Canonical account location plus separate predicted and confirmed fields'],
    ['Honest uncertainty', 'Radius in metres, calibration metrics and fallback states'],
    ['Landmark directions', 'Address entities and operational evidence returned to the UI'],
    ['Noisy evidence', 'GPS accuracy, dwell, outcome and integrity influence evidence weights'],
    ['Multilingual addresses', 'Unicode normalisation, transliteration and entity pipeline'],
    ['Shared places', 'Cluster enrichment with guarded propagation'],
    ['Fake-visit resistance', 'Integrity and reliability scores reduce low-quality evidence'],
    ['Offline field use', 'Service-worker caching and queued visit synchronisation'],
    ['Planner integration', 'Explainable visit_directly / verify_first / skip actions'],
    ['PS2 integration', 'Location-confidence RPC contract for right-party-contact models'],
    ['Auditability', 'Authenticated routes, source fields, timestamps and persisted evidence'],
    ['Compliance boundary', 'Collections purpose, access controls and explicit deployment limits'],
    ['Evaluation', 'Versioned JSON artifacts with baselines, ablations and split metadata'],
]
story.append(table([['Requirement', 'Implemented behaviour']] + reqs, [44 * mm, 114 * mm]))
story.append(Spacer(1, 4))

# ===========================================================================
# 3. Dataset and data quality
# ===========================================================================
story += h1block(3, 'Dataset and Data Quality')
story.append(H2('3.1', 'Source tables'))
story.append(P(
    "The PS3 dataset is assembled from shared account/address/visit tables and PS3-specific evidence "
    "tables. All analysis in this report uses the <b>train</b> split, matching the project\u2019s "
    "real-data evaluation path; validation and test files are not mixed into the reported values. "
    "Table 3 lists the inventory as discovered by the notebook."))
story.append(tcap('Table 3. PS3 dataset inventory, train split.'))
inv = [
    ['towns', 'PS_3/towns', '3', '4', '139 B'],
    ['localities', 'PS_3/localities', '36', '6', '1.7 KB'],
    ['landmarks_poi', 'PS_3/landmarks_poi', '240', '6', '11.3 KB'],
    ['visit_gps_points', 'PS_3/visit_gps_points', '112,080', '6', '5.1 MB'],
    ['baseline_geocodes', 'PS_3/baseline_geocodes', '2,010', '4', '64.6 KB'],
    ['surveyed_addresses', 'PS_3/surveyed_addresses', '66', '3', '1.6 KB'],
    ['accounts', 'Shared/accounts', '1,680', '20', '220.8 KB'],
    ['addresses', 'Shared/addresses', '2,175', '7', '278.3 KB'],
    ['field_visits', 'Shared/field_visits', '3,896', '15', '658.3 KB'],
    ['agents', 'Shared/agents', '30', '6', '1.0 KB'],
]
story.append(table([['Table', 'Dataset family', 'Rows', 'Columns', 'File size']] + inv,
                   [40 * mm, 52 * mm, 18 * mm, 18 * mm, 26 * mm], align_right_cols=(2, 3, 4)))
story.append(P(
    "The evaluator validates the required files before running and records SHA-256 hashes of the "
    "addresses, visits, surveyed and baseline files in every artifact, so a result can be reproduced "
    "against exactly the same inputs."))

story.append(H2('3.2', 'Coordinate system: projected metres, not WGS84'))
story.append(P(
    "PS3 <i>x</i> and <i>y</i> values are projected local coordinates measured in <b>metres</b>. They "
    "are not WGS84 latitude and longitude. Evaluation therefore uses Euclidean distance:"))
story.append(codeblock([
    'error_m = sqrt((predicted_x - surveyed_x)^2 + (predicted_y - surveyed_y)^2)',
]))
story.append(P(
    "This distinction is critical. Sending projected coordinates to Google Maps, or computing a "
    "Haversine distance from them, produces a plausible-looking but invalid result. The frontend keeps "
    "projected PS3 scatter plots separate from the optional Google Maps panel, which accepts WGS84 "
    "coordinates only. Table 4 shows the observed ranges, which are clearly local metre values and not "
    "degrees."))
story.append(tcap('Table 4. Coordinate ranges by table (projected metres).'))
coords = [
    ['surveyed', '\u22124,039.0', '4,177.6', '\u22124,013.1', '3,273.5'],
    ['baseline geocodes', '\u22124,061.5', '4,053.1', '\u22124,088.6', '3,403.4'],
    ['visit check-ins', '\u22124,410.0', '4,311.0', '\u22124,122.6', '3,422.1'],
    ['landmarks / POI', '\u22124,072.0', '3,788.5', '\u22124,085.8', '3,568.5'],
    ['locality centroids', '\u22123,766.2', '3,653.7', '\u22123,613.0', '3,208.9'],
]
story.append(table([['Table', 'x min', 'x max', 'y min', 'y max']] + coords,
                   [42 * mm, 29 * mm, 29 * mm, 29 * mm, 29 * mm], align_right_cols=(1, 2, 3, 4)))

story.append(H2('3.3', 'Data quality and relational checks'))
story.append(P(
    "A geocoder must know whether its evidence is joinable. Table 5 summarises null cells and duplicate "
    "keys; Table 6 reports orphan references across the core joins. The null cells are concentrated in "
    "optional attribute columns of <i>accounts</i> and <i>visits</i>; no join key contains nulls, and "
    "there are no duplicate primary keys in any table."))
story.append(tcap('Table 5. Data quality summary (train split).'))
qual = [
    ['accounts', '1,680', '1,651', '0'],
    ['addresses', '2,175', '0', '0'],
    ['field_visits', '3,896', '3,471', '0'],
    ['surveyed_addresses', '66', '0', '0'],
    ['baseline_geocodes', '2,010', '0', '0'],
    ['landmarks_poi', '240', '0', '0'],
    ['visit_gps_points', '112,080', '0', '\u2014'],
    ['towns', '3', '0', '0'],
    ['localities', '36', '0', '0'],
]
story.append(table([['Table', 'Rows', 'Null cells', 'Duplicate IDs']] + qual,
                   [56 * mm, 32 * mm, 34 * mm, 36 * mm], align_right_cols=(1, 2, 3)))
story.append(tcap('Table 6. Referential-integrity checks: orphan rows in each relationship.'))
orph = [
    ['addresses -> accounts', '0'],
    ['visits -> accounts', '0'],
    ['visits -> addresses', '0'],
    ['surveyed -> addresses', '0'],
    ['baseline -> addresses', '0'],
]
story.append(table([['Relationship', 'Orphan rows']] + orph, [110 * mm, 40 * mm],
                   align_right_cols=(1,)))
story.append(P(
    "The relational structure is therefore clean: every surveyed address and every baseline geocode "
    "joins to an account address, and every visit joins to both its account and its address. The "
    "evaluation joins used in Section 5 and Section 7 lose no rows."))

story.append(H2('3.4', 'Address and landmark coverage'))
story.append(P(
    "Addresses are dominated by residences, with a meaningful office share, and almost all originate "
    "from KYC origination. The 19 <i>skip_trace</i> addresses are exactly the hard cases the geocoder "
    "is built for. Table 8 shows town-level coverage: the three towns use different address styles "
    "(Kannataka, Hindi, metro), which is why the pipeline normalises and transliterates rather than "
    "pattern-matching one script."))
story.append(tcap('Table 7. Address type and source distribution (n = 2,175).'))
story.append(table([
    ['Field', 'Value', 'Count'],
    ['address_type', 'residence', '1,699'],
    ['address_type', 'office', '320'],
    ['address_type', 'permanent_native', '156'],
    ['source', 'kyc_origination', '2,156'],
    ['source', 'skip_trace', '19'],
], [44 * mm, 62 * mm, 44 * mm], align_right_cols=(2,)))
story.append(tcap('Table 8. Town-level address and landmark coverage.'))
story.append(table([
    ['Town ID', 'Town name', 'Address style', 'Approx. radius (m)', 'Addresses', 'Landmarks'],
    ['T1', 'Kaveripura', 'karnataka', '4,200', '664', '82'],
    ['T2', 'Devgarh Nagar', 'hindi', '3,800', '639', '77'],
    ['T3', 'Navanagara East', 'metro', '4,800', '707', '81'],
], [18 * mm, 36 * mm, 28 * mm, 30 * mm, 22 * mm, 24 * mm], align_right_cols=(3, 4, 5)))
story.append(Spacer(1, 4))

# ===========================================================================
# 4. EDA of field visits
# ===========================================================================
story += h1block(4, 'Exploratory Analysis of Field-Visit Evidence')
story.append(P(
    "Successful visits are clues, not unquestionable ground truth. Before visits are used as learning "
    "evidence, their outcomes, GPS accuracy, dwell time, trajectories and agent concentration are "
    "audited (notebook Section 4)."))

story.append(H2('4.1', 'Outcome distribution'))
story.append(P(
    "Of the 3,896 recorded field visits, 1,555 (39.9%) are successful contacts \u2014 the borrower was "
    "met, a family member was met, or cash was collected. The remaining visits are still informative "
    "search evidence: they tell the model where the agent looked and failed to find anyone, which is "
    "precisely the signal behind the \u201caddress-not-traceable\u201d problem."))
story.append(tcap('Table 9. Field-visit outcome distribution (train split).'))
outc = [
    ['address_not_traceable', '957', '24.6%'],
    ['locked_premises', '901', '23.1%'],
    ['met_borrower', '766', '19.7%'],
    ['met_family', '730', '18.7%'],
    ['neighbour_says_shifted', '332', '8.5%'],
    ['no_such_person', '151', '3.9%'],
    ['cash_collected', '59', '1.5%'],
    ['Total', '3,896', '100%'],
]
story.append(table([['Outcome', 'Visits', 'Share']] + outc, [78 * mm, 40 * mm, 40 * mm],
                   align_right_cols=(1, 2)))
story.append(fig_image(f'{FIG}/fig_outcomes.png', BODY_W,
    'Figure 1. Field-visit outcome distribution. Orange bars mark successful-contact outcomes used '
    'as positive geolocation evidence.'))

story.append(H2('4.2', 'GPS accuracy and dwell time'))
story.append(P(
    "GPS accuracy is good on the whole \u2014 median 9.9 m, 90th percentile 18.7 m \u2014 so check-in "
    "coordinates are a reliable <i>carrier</i> of evidence; the question is which check-ins actually "
    "mark the borrower\u2019s location. Dwell time is the discriminating signal: median dwell on "
    "<i>met_borrower</i> visits is 876 s, against 78 s on <i>address_not_traceable</i> visits. A "
    "long, accurate dwell at a check-in is strong location evidence; a short pass-by is not. Both "
    "quantities enter the evidence weights of Section 6.4."))
story.append(tcap('Table 10. GPS accuracy and dwell-time statistics (all 3,896 visits).'))
story.append(table([
    ['Metric', 'Mean', 'Median', 'P90', 'Max'],
    ['GPS accuracy (m)', '11.28', '9.9', '18.7', '54.0'],
    ['Dwell time (s)', '339.8', '203.0', '908.0', '1,495.0'],
], [48 * mm, 27 * mm, 27 * mm, 27 * mm, 25 * mm], align_right_cols=(1, 2, 3, 4)))
story.append(fig_image(f'{FIG}/fig_01_cell10.png', BODY_W,
    'Figure 2. Visit evidence quality (notebook Section 4): GPS-accuracy distribution (left) and dwell '
    'time by outcome (right). Successful contacts show distinctly longer dwells.'))

story.append(H2('4.3', 'Evidence quality by outcome'))
story.append(tcap('Table 11. Median GPS accuracy, median dwell and GPS-trail availability by outcome.'))
byout = [
    ['address_not_traceable', '957', '10.00', '78.0', '100%'],
    ['locked_premises', '901', '10.10', '150.0', '100%'],
    ['met_borrower', '766', '9.75', '876.0', '100%'],
    ['met_family', '730', '9.70', '393.5', '100%'],
    ['neighbour_says_shifted', '332', '9.10', '257.5', '100%'],
    ['no_such_person', '151', '10.90', '198.0', '100%'],
    ['cash_collected', '59', '9.80', '785.0', '100%'],
]
story.append(table([['Outcome', 'Visits', 'Median accuracy (m)', 'Median dwell (s)', 'Trail share']] + byout,
                   [48 * mm, 20 * mm, 31 * mm, 31 * mm, 24 * mm], align_right_cols=(1, 2, 3, 4)))
story.append(P(
    "GPS accuracy is comparable across outcomes, so accuracy alone cannot separate a true meeting "
    "point from a wrong check-in; dwell and outcome jointly carry the discrimination. All visits carry "
    "a GPS trail in this split, enabling trajectory-shape features (searching vs direct approach)."))

story.append(H2('4.4', 'Agent concentration and integrity'))
story.append(P(
    "Visit volume is spread across the 30-agent fleet (fleet average 130 visits), with the top agents "
    "each carrying roughly a third more than average. Concentration is not itself fraud, but it is why "
    "the model includes an <i>agent-independence</i> feature: repeated evidence from a single agent is "
    "prevented from dominating a cluster, which is the core fake-visit resistance control "
    "(Section 6.7)."))
story.append(tcap('Table 12. Agent visit concentration, top 9 of 30 agents.'))
agents = [['FA003', '470'], ['FA001', '451'], ['FA008', '447'], ['FA002', '446'],
          ['FA007', '445'], ['FA009', '431'], ['FA004', '421'], ['FA005', '398'],
          ['FA006', '387']]
story.append(table([['Agent', 'Visits']] + agents, [60 * mm, 40 * mm], align_right_cols=(1,)))
story.append(Spacer(1, 4))

# ===========================================================================
# 5. Baseline evaluation
# ===========================================================================
story += h1block(5, 'Commercial Baseline Geocoder Evaluation')
story.append(H2('5.1', 'Protocol'))
story.append(P(
    "The supplied commercial baseline geocode for each address is joined to the surveyed ground truth "
    "by <i>address_id</i>. Sixty-six addresses have both, and all errors are computed in projected "
    "metres with the Euclidean formula of Section 3.2. The baseline is the measured comparison point "
    "for every geocoder built in this project: an improvement must be demonstrated against it."))

story.append(H2('5.2', 'Results'))
story.append(tcap('Table 13. Commercial baseline geocoder error against surveyed truth (n = 66).'))
story.append(table([
    ['Metric', 'Value'],
    ['Evaluated addresses', '66'],
    ['Median error (m)', '380.8'],
    ['P90 error (m)', '745.6'],
    ['P95 error (m)', '1,176.9'],
    ['Within 50 m', '4.5%'],
    ['Within 100 m', '9.1%'],
    ['Within 250 m', '28.8%'],
    ['Within 500 m', '71.2%'],
], [90 * mm, 60 * mm], align_right_cols=(1,)))
story.append(P(
    "Only 28.8% of surveyed addresses fall within 250 m of the commercial geocode, and the right tail "
    "extends to roughly 2.2 km. For a field agent walking a lane, that is the difference between a "
    "productive visit and a lost half-day \u2014 and it quantifies the headroom the evidence-based "
    "geocoder must fill."))

story.append(H2('5.3', 'Error distribution and town-level behaviour'))
story.append(fig_image(f'{FIG}/fig_02_cell12.png', BODY_W * 0.72,
    'Figure 3. Commercial baseline geocoder error distribution, projected metres (n = 66). A tight core '
    'around 400\u2013600 m plus a heavy tail beyond 1 km.'))
story.append(tcap('Table 14. Town-level commercial baseline error (descriptive; measured, not a controlled pilot).'))
story.append(table([
    ['Town', 'Evaluated', 'Median error (m)', 'P90 error (m)', 'Within 250 m', 'Address style'],
    ['T2 \u2014 Devgarh Nagar', '18', '359.3', '875.8', '33.3%', 'hindi'],
    ['T3 \u2014 Navanagara East', '28', '369.3', '644.0', '28.6%', 'metro'],
    ['T1 \u2014 Kaveripura', '20', '420.2', '790.0', '25.0%', 'karnataka'],
], [38 * mm, 18 * mm, 28 * mm, 26 * mm, 22 * mm, 24 * mm], align_right_cols=(1, 2, 3, 4)))
story.append(P(
    "The Kannataka-style town (T1) is the weakest for the commercial baseline, consistent with "
    "transliteration and script diversity degrading global geocoders. Address style, landmark density "
    "and search behaviour therefore vary by territory, and the system is designed per evidence type "
    "rather than tuned to one town\u2019s conventions."))
story.append(Spacer(1, 4))

# ===========================================================================
# 6. Model architecture and detailed design
# ===========================================================================
story += h1block(6, 'Model Architecture and Detailed Design')
story.append(H2('6.1', 'Architecture overview'))
story.append(P(
    "The service is an evidence-fusion geocoder, not an address lookup. Figure 4 shows the end-to-end "
    "architecture; Table 15 gives the stage-by-stage contract. The important output is not a point but "
    "a <b>location plus a radius plus an evidence trail</b>, and the architecture is deliberately "
    "layered: the deterministic evidence aggregator (stage 4) works even where the learned ranker "
    "(stage 5) has no support, and every downstream consumer sees the same uncertainty-annotated "
    "result."))
story.append(fig_image(f'{FIG}/fig_architecture.png', BODY_W,
    'Figure 4. End-to-end model architecture: inputs, pipeline stages, uncertainty and action decision, '
    'and operational consumers.'))
story.append(tcap('Table 15. Model pipeline: stage-by-stage inputs and outputs.'))
stages = [
    ['1. Ingestion & CRS validation', 'Ten PS3/Shared CSV files',
     'Existence checks, SHA-256 hashes, projected-coordinate declaration',
     'Clean tables + artifact metadata'],
    ['2. Address normalisation', 'Raw multilingual address text',
     'Unicode cleanup, whitespace, abbreviations, transliteration-aware tokenisation',
     'Normalised string; original retained for audit'],
    ['3. Entity & relation extraction', 'Normalised address',
     'House/plot, roads, village/town/locality, landmarks, direction relations, pincodes',
     'Searchable entity and relation set'],
    ['4. Candidate generation', 'Entities + five evidence sources (Table 16)',
     'Resolution against landmarks, localities, visit history, confirmed accounts, remarks',
     'Alternative coordinate candidates'],
    ['5. Evidence weighting', 'Visit check-ins + quality signals',
     'w = (1/accuracy) x dwell/300; integrity, recency, agent-independence controls',
     'Reliability-weighted evidence per candidate'],
    ['6. Candidate ranking', '21-feature vector per candidate',
     'LightGBM classifier, 150 trees (Tables 17\u201319)',
     'Candidate accept probabilities'],
    ['7. Uncertainty & action', 'Winning candidate + evidence spread',
     'radius = max(50 m, weighted RMS); confidence = 1 - radius/1000; calibrated thresholds',
     'Pin + radius + visit_directly / verify_first / skip'],
    ['8. Persistence & serving', 'Prediction + confirmed observations',
     'Confirmed/predicted field separation; RBAC-scoped authenticated routes',
     'Field app, planner API, PS2 RPC, dashboards'],
]
story.append(table([['Stage', 'Input', 'Processing', 'Output']] + stages,
                   [34 * mm, 34 * mm, 50 * mm, 40 * mm], fontsize=9))

story.append(H2('6.2', 'Address understanding: normalisation and entities'))
story.append(P(
    "The normalizer applies Unicode cleanup, whitespace normalisation, common abbreviation handling, "
    "transliteration-aware processing and robust tokenisation. Normalisation is used for matching and "
    "candidate generation; the original text is retained for audit and agent display. Entity and "
    "relation extraction then identifies the searchable components of an address: house and plot "
    "numbers; roads, cross-roads and lanes; villages, towns and localities; temples, schools, shops "
    "and other landmarks; directional relations such as behind, opposite, beside and near; and "
    "pincodes with administrative hints. The output is a set of searchable entities and relations that "
    "can be resolved against known landmarks and prior account evidence. Remarks are retained for "
    "audit; recognised correction phrases are captured conservatively, and the system does not claim "
    "that every free-form multilingual remark becomes a precise geometric offset \u2014 an intentional "
    "safety boundary, because a wrong offset moves a field agent <i>farther</i> from the borrower."))

story.append(H2('6.3', 'Candidate generation'))
story.append(P(
    "Candidate generation intentionally produces alternatives from five sources; ranking and "
    "uncertainty estimation then decide whether the alternatives are sufficiently consistent for a "
    "direct visit (Table 16)."))
story.append(tcap('Table 16. Candidate-generation sources and their role.'))
cands = [
    ['Commercial / open geocoder', 'Supplied baseline pin for every address',
     'Prior and fallback when no usable visit evidence exists'],
    ['Historical successful visits', 'Weighted centroid of met_borrower / met_family / cash_collected check-ins',
     'Strongest single evidence source where it exists'],
    ['Nearby confirmed accounts & shared-place clusters', 'Confirmed locations of neighbouring accounts at the same building or landmark',
     'Guarded corroboration with source and reliability thresholds'],
    ['Landmarks & locality centroids', 'Resolved named entities matched against landmarks_poi and localities',
     'Anchor for descriptive addresses (\u201cbehind the temple\u201d)'],
    ['Agent-remarks corrections', 'Conservative, recognised offset phrases from visit remarks',
     'Small, high-precision corrections; never speculative'],
]
story.append(table([['Source', 'What it contributes', 'Role in the model']] + cands,
                   [40 * mm, 60 * mm, 58 * mm], fontsize=9))

story.append(H2('6.4', 'Evidence aggregation and reliability weighting'))
story.append(P(
    "Successful-visit evidence is weighted by GPS accuracy, dwell time, outcome, trajectory and search "
    "shape, visit-integrity checks, recency and repeated independent support, agent-influence controls "
    "and shared-place corroboration. The transparent reference implementation in the evaluation bridge "
    "(notebook Section 6) aggregates successful visits with the weights below, falls back to the "
    "commercial geocode when an address has no usable successful visit, and derives the uncertainty "
    "radius from the weighted spread of the evidence:"))
story.append(codeblock([
    'SUCCESSFUL = {met_borrower, met_family, cash_collected}',
    'weight     = (1 / gps_accuracy) * (clip(dwell, 1, 600) / 300)',
    'predicted  = weighted average of successful-visit check-in coordinates',
    'radius     = max(50 m, weighted RMS spread of check-ins about the prediction)',
    'confidence = clip(1 - radius / 1000, 0, 1)',
]))
story.append(P(
    "When multiple accounts share a building or landmark, one reliable confirmed visit can enrich the "
    "cluster; propagation is guarded by source and reliability thresholds. Cluster enrichment is not "
    "unconditional copying and must be monitored at lender scale before broad write-back."))

story.append(H2('6.5', 'Candidate ranker: the LightGBM model'))
story.append(P(
    "The production ranker scores each candidate with a 21-feature evidence contract (Table 17), "
    "trained as a LightGBM binary classifier (Table 18). For submission portability the trained model "
    "is embedded in the notebook as a base64 artifact, so evaluation does not depend on an external "
    "model file. The feature ranges in Table 17 are taken from the model\u2019s own training metadata "
    "(<i>feature_infos</i>); several distance features held constant default values (999999) during "
    "training, which the importance analysis in Figure 5 confirms \u2014 those features contribute no "
    "gain, and the model\u2019s decisions are driven by text similarity and evidence quality instead."))
story.append(tcap('Table 17. Ranker feature contract (21 features) with observed training ranges.'))
feats = [
    ['Text similarity', 'address_similarity', '0.10 \u2013 0.60'],
    ['Text similarity', 'landmark_similarity', '0.00 \u2013 0.40'],
    ['Text similarity', 'locality_similarity', '0.30 \u2013 0.80'],
    ['Visit evidence', 'distance_to_successful_visits', 'constant 999999 (default)'],
    ['Visit evidence', 'distance_to_failed_visits', 'constant 999999 (default)'],
    ['Visit evidence', 'number_of_supporting_visits', '0 \u2013 7'],
    ['Visit evidence', 'weighted_successful_visit_count', '0 \u2013 7'],
    ['Evidence quality', 'visit_integrity', '0.80 \u2013 1.00'],
    ['Evidence quality', 'gps_accuracy', '4.1 \u2013 1,000 m'],
    ['Evidence quality', 'dwell_time', '0 \u2013 1,475 s'],
    ['Evidence quality', 'trajectory_quality', '0.20 \u2013 0.70'],
    ['Corroboration', 'nearby_account_support', 'default (none observed)'],
    ['Corroboration', 'place_cluster_support', 'default (none observed)'],
    ['Commercial reference', 'commercial_geocoder_distance', 'default (none observed)'],
    ['Adversarial control', 'agent_independence', '0 \u2013 1'],
    ['Source flags (one-hot)', 'source_historical', '0 \u2013 1'],
    ['Source flags (one-hot)', 'source_nearby', '0 \u2013 1'],
    ['Source flags (one-hot)', 'source_geocoder', '0 \u2013 1'],
    ['Source flags (one-hot)', 'source_landmark', '0 \u2013 1'],
    ['Source flags (one-hot)', 'source_locality', '0 \u2013 1'],
    ['Source flags (one-hot)', 'source_pincode', '0 \u2013 1'],
]
story.append(table([['Group', 'Feature', 'Training range']] + feats,
                   [38 * mm, 60 * mm, 58 * mm], fontsize=9))
story.append(tcap('Table 18. Ranker training configuration (from the embedded model artifact).'))
train = [
    ['Framework', 'LightGBM binary classifier (sigmoid objective), text artifact v4'],
    ['Boosting iterations', '150 trees retained (cap 200, early stopping)'],
    ['Learning rate', '0.05'],
    ['Max leaves per tree', '31 (observed trees 452\u2013885 nodes, mean \u2248 612)'],
    ['Bagging', '0.8 fraction, every 5 iterations (seed 400)'],
    ['Min data in leaf', '3'],
    ['Boost from average', 'enabled'],
    ['Features', '21 (contract in Table 17)'],
    ['Train / eval split', 'Deterministic account-level 80/20 partition; disjoint-ID assertion before fitting'],
    ['Deterministic check', 'P(accept | zero vector) = 0.6927'],
    ['Portability', 'Embedded as base64 in the notebook \u2014 no external model file at submission time'],
]
story.append(table([['Parameter', 'Value']] + train, [44 * mm, 114 * mm], fontsize=9))
story.append(tcap('Table 19. Ranker feature importance \u2014 non-zero gain (of 21 features).'))
fi = [
    ['address_similarity', '816.8', '181'],
    ['gps_accuracy', '404.0', '74'],
    ['visit_integrity', '365.1', '38'],
    ['number_of_supporting_visits', '346.1', '39'],
    ['locality_similarity', '129.5', '105'],
    ['landmark_similarity', '109.3', '26'],
    ['weighted_successful_visit_count', '82.5', '14'],
    ['source_locality', '36.1', '12'],
    ['source_geocoder', '4.3', '13'],
    ['agent_independence', '2.4', '4'],
    ['source_pincode', '1.1', '4'],
    ['trajectory_quality', '0.067', '2'],
]
story.append(table([['Feature', 'Gain', 'Splits']] + fi, [74 * mm, 40 * mm, 40 * mm],
                   align_right_cols=(1, 2)))
story.append(fig_image(f'{FIG}/fig_importance.png', BODY_W,
    'Figure 5. Ranker feature importance by gain (log scale). Text similarity, GPS accuracy, '
    'visit-integrity and supporting-visit count dominate; nine features contribute no gain.'))
story.append(P(
    "The ranking is explainable: the top drivers are address text similarity and the quality of the "
    "supporting visits, not opaque representations. Zero-gain features (distance to failed visits, "
    "nearby-account support, place-cluster support and several source flags) remain in the contract so "
    "that future evidence sources can be added without changing the interface."))

story.append(H2('6.6', 'Uncertainty and operational decisions'))
story.append(P(
    "The output contains a location candidate and a radius rather than a naked point. The radius is "
    "used by the planner and displayed to the agent, and the service returns one of three actions: "
    "<b>visit_directly</b> when evidence and confidence are sufficient; <b>verify_first</b> when the "
    "location is plausible but uncertain; and <b>skip_until_geocoded</b> when no usable coordinate "
    "candidate exists. The frontend handles null predictions explicitly \u2014 an unresolved account "
    "shows \u201cNo location candidate found\u201d rather than crashing on a null value, because an "
    "unresolved result is a valid model state, not a frontend exception."))
story.append(P(
    "Calibration is treated as an evaluation metric, not an afterthought: a confidence score that is "
    "not calibrated makes the planner over-spend on false certainty, so the system must prefer an "
    "honest verification action over a precise-looking guess."))

story.append(H2('6.7', 'Integrity and adversarial evidence controls'))
story.append(P("The system treats fake or low-quality visits as a model-risk problem:"))
for b in [
    "GPS accuracy is incorporated into every evidence weight;",
    "very short or implausible dwell is down-weighted;",
    "outcomes are considered with the location rather than treated as proof of it;",
    "trajectories help distinguish searching from a direct approach;",
    "repeated evidence from one agent cannot dominate a cluster (agent-independence);",
    "failed visits remain useful as search evidence but are never treated as borrower locations;",
    "visit validation and integrity signals are fully auditable.",
]:
    story.append(B(b))
story.append(P(
    "These controls reduce, but do not eliminate, manipulation risk. Production deployment should "
    "monitor unusual agent-location concentration, repeated identical coordinates and implausible "
    "travel patterns under the applicable employment and monitoring framework."))

story.append(H2('6.8', 'Interfaces and workflow integration'))
story.append(P(
    "<b>Field app.</b> The agent receives the corrected pin, radius, evidence summary and landmark "
    "directions. Static assets and selected GET responses are cached for poor-connectivity areas; "
    "visit submissions are queued in IndexedDB when the network is unavailable and synchronised later "
    "with the current bearer token; five failed retries move to a local dead-letter store. Conflict "
    "resolution and complete offline planner data remain deployment work."))
story.append(P(
    "<b>Visit planner.</b> <i>GET /api/planner/visits</i> exposes coordinates, confidence, radius, "
    "source and a recommended action for an origin and a maximum-distance budget. It is an "
    "explainable prioritiser, not a full road-network route optimiser; future cost-aware routing "
    "should include channel cost, distance, contact-hour rules, visit capacity and productive-visit "
    "probability."))
story.append(P(
    "<b>PS2 / right-party-contact contract.</b> <i>GET /api/rpc/location-features/{account_id}</i> "
    "exposes confidence, radius, source, successful visits, failed searches and confirmed status, so "
    "the PS2 model can distinguish a borrower who may have moved from one whose address is valid but "
    "hard to find. This is an integration contract, not a claim that the PS2 model itself has been "
    "trained or causally validated by this repository."))
story.append(P(
    "<b>Dashboards.</b> The dashboard and benchmark consume live evaluation responses and show "
    "measured values rather than hard-coded scores; rendering is null-safe, and backend 503s were "
    "addressed by making real-data evaluation and metrics paths tolerate missing data while surfacing "
    "explicit unavailable statuses."))
story.append(P(
    "<b>Administration and account discovery.</b> Operational use is separated from privileged "
    "administration. All authenticated users can use the account workflow, while the Admin route is "
    "shown only to users identified as <i>admin</i> by the login response; the retraining endpoint is "
    "additionally protected by the backend RBAC dependency, so hiding the navigation item is not the "
    "security boundary. Account discovery is server-side: <i>GET /api/real/accounts</i> accepts "
    "<i>search</i>, <i>limit</i> and <i>offset</i>, with case-insensitive matching across account ID, "
    "town, preferred language and all associated address text, letting a supervisor find an account by "
    "a local address fragment before opening address intelligence."))
story.append(Spacer(1, 4))

# ===========================================================================
# 7. Model evaluation
# ===========================================================================
story += h1block(7, 'Model Evaluation')
story.append(H2('7.1', 'Protocol'))
story.append(P(
    "The embedded backend evaluator (notebook Section 6) predicts a location for each of the 66 "
    "surveyed addresses on the train split using the weighted-visit evidence of Section 6.4 with "
    "commercial-geocode fallback, measures error in projected metres, and records coverage, "
    "calibration and latency. No future-dated evidence is used, and no metric is fabricated: missing "
    "inputs are reported explicitly."))

story.append(H2('7.2', 'Head-to-head results'))
story.append(tcap('Table 20. Commercial baseline vs embedded weighted-visit geocoder (n = 66 surveyed addresses).'))
story.append(table([
    ['Metric', 'Commercial baseline', 'Weighted visit centroid', 'Change'],
    ['Median error (m)', '380.8', '204.4', '\u221246.3%'],
    ['Mean error (m)', '\u2014', '319.7', '\u2014'],
    ['P90 error (m)', '745.6', '639.2', '\u221214.3%'],
    ['P95 error (m)', '1,176.9', '797.1', '\u221232.3%'],
    ['Max error (m)', '\u2014', '2,201.7', '\u2014'],
    ['Within 50 m', '4.5%', '27.3%', '+22.7 pts'],
    ['Within 100 m', '9.1%', '37.9%', '+28.8 pts'],
    ['Within 250 m', '28.8%', '53.0%', '+24.2 pts'],
    ['Within 500 m', '71.2%', '78.8%', '+7.6 pts'],
    ['Radius coverage (error \u2264 radius)', '\u2014', '72.7%', '\u2014'],
    ['Radius-coverage agreement error', '\u2014', '0.398', '\u2014'],
    ['Latency (ms / prediction)', '\u2014', '3.31', '\u2014'],
], [54 * mm, 36 * mm, 40 * mm, 26 * mm], align_right_cols=(1, 2, 3)))
story.append(fig_image(f'{FIG}/fig_comparison.png', BODY_W,
    'Figure 6. Head-to-head on the 66 surveyed train addresses: error percentiles (left) and share '
    'within each threshold (right). The weighted-visit geocoder improves the median by 46.3% and more '
    'than doubles the within-250 m share.'))
story.append(P(
    "The median error falls from 380.8 m to 204.4 m (\u221246.3%), the P95 from 1,176.9 m to 797.1 m "
    "(\u221232.3%), and the within-250 m share more than doubles (28.8% \u2192 53.0%). The P90 improves "
    "by a smaller 14.3%: the largest remaining errors are the addresses where the historical evidence "
    "itself is wrong or absent, and the system answers them with a larger radius and a "
    "<i>verify_first</i> action rather than a false-precision pin. The 72.7% coverage figure reflects "
    "the 48 of 66 addresses with usable successful-visit evidence; the remaining 18 fall back to the "
    "commercial geocode, which keeps coverage total at 100% of evaluated addresses."))

story.append(H2('7.3', 'Uncertainty coverage'))
story.append(P(
    "The radius contains the true surveyed location for 72.7% of predictions (calibration error of the "
    "covered-vs-confidence agreement: 0.398). Coverage is deliberately reported alongside accuracy: a "
    "geocoder that is very accurate on the easy addresses and silent on the hard ones would look better "
    "on error metrics while failing the field. The fallback state is itself part of the contract."))

story.append(H2('7.4', 'Confidence calibration'))
story.append(P(
    "Confidence is derived from the uncertainty radius (<i>confidence = 1 \u2212 radius/1000</i>, "
    "clipped to [0, 1]) and is checked against empirical within-250 m accuracy. The expected "
    "calibration error (ECE) is <b>0.155</b> on 66 predictions. Table 21 lists the non-empty "
    "decile bins; Figure 7 shows the calibration curve."))
story.append(tcap('Table 21. Calibration bins with predictions (deciles of confidence).'))
story.append(table([
    ['Bin', 'Mean predicted confidence', 'Empirical within-250 m', 'Count'],
    ['0.5 \u2013 0.6', '0.500', '0.302', '43'],
    ['0.8 \u2013 0.9', '0.880', '0.667', '3'],
    ['0.9 \u2013 1.0', '0.946', '1.000', '20'],
], [34 * mm, 48 * mm, 46 * mm, 26 * mm], align_right_cols=(1, 2, 3)))
story.append(fig_image(f'{FIG}/fig_03_cell15.png', BODY_W * 0.62,
    'Figure 7. Confidence calibration: mean predicted confidence against empirical within-250 m '
    'accuracy, with the perfect-calibration diagonal.'))
story.append(P(
    "The interpretation is honest, not flattering: high-confidence predictions (radius \u2264 100 m, "
    "confidence bin 0.9\u20131.0) are nearly always correct (20/20 within 250 m), but the large middle bin "
    "predicted 0.50 against an observed 0.30. With 66 ground-truth addresses the decile estimate is "
    "noisy, and the production system recalibrates on held-out data before thresholds drive planner "
    "budgets. Until then, the conservative default for this bin is <i>verify_first</i>."))

story.append(H2('7.5', 'Latency'))
story.append(P(
    "The embedded evaluator predicts all 66 addresses at <b>3.31 ms per prediction</b> end to end "
    "(evidence lookup, weighting, radius and metrics). That is comfortably below any field-app "
    "interactivity budget and leaves headroom for the full ranker with text-similarity features."))
story.append(Spacer(1, 4))

# ===========================================================================
# 8. Key insights
# ===========================================================================
story += h1block(8, 'Key Insights and Interpretation')
story.append(P(
    "The following insights are drawn directly from the measured data in Sections 4\u20137. They are "
    "descriptive \u2014 each is tied to a number the artifact reproduces \u2014 and together they "
    "explain <i>why</i> the architecture of Section 6 is shaped the way it is."))

insights = [
    ('The commercial baseline fails for linguistic, not geographic, reasons.',
     "Only 28.8% of surveyed addresses fall within 250 m of the commercial geocode, and the weakest "
     "town is the Kannataka-style town T1 (median 420.2 m, within-250 m 25.0%) while the metro-style "
     "town T3 is strongest (median 369.3 m, 28.6%). The spread across towns tracks address style, "
     "which is why the pipeline invests in normalisation, transliteration and entity resolution "
     "rather than expecting any single external geocoder to be locale-complete."),
    ('Dwell time is the evidence discriminator; GPS accuracy is the filter.',
     "Median dwell on met_borrower visits is 876 s, eleven times the 78 s on address_not_traceable "
     "visits, while median GPS accuracy moves only from 9.1 m to 10.9 m across outcomes (Table 11). "
     "Accuracy tells us the coordinate is trustworthy; dwell and outcome tell us whether the "
     "coordinate marks the borrower. The weighting formula of Section 6.4 encodes exactly this "
     "separation: (1/accuracy) is a filter, dwell/300 is the discriminator."),
    ('Visit history already contains the location the geocoder is missing.',
     "A single deterministic aggregator \u2014 the weighted centroid of successful visits, no learned "
     "model \u2014 cuts median error by 46.3% against the commercial baseline (204.4 m vs 380.8 m). "
     "That result validates the core design thesis: the platform\u2019s own field evidence is a "
     "stronger location signal than a global geocoder for this population, and the value of the full "
     "ranker is to use that signal more precisely, not to replace it."),
    ('The hard 27% define the fallback contract.',
     "18 of 66 surveyed addresses (27.3%) have no usable successful-visit evidence and fall back to "
     "the commercial geocode with a 500 m radius. Coverage is therefore reported alongside accuracy "
     "at every level: a geocoder that is precise on the easy 73% and silent on the hard 27% would "
     "look better on error metrics while failing exactly the accounts that produced the "
     "address-not-traceable problem this project exists to solve."),
    ('Confidence is bimodal: near-perfect at the top, over-confident in the middle.',
     "Predictions in the 0.9\u20131.0 confidence bin were correct within 250 m in 20 of 20 cases, while the "
     "large middle bin (43 predictions) is predicted at 0.50 against an observed 0.30. The practical "
     "consequence is governance of thresholds: the planner should auto-route only above a calibrated "
     "high-confidence bar and default the middle band to verify_first, and decile calibration must "
     "be re-estimated on a larger ground-truth set before the pilot (Section 7.4)."),
    ('The ranker is evidence-driven, not proximity-driven.',
     "Feature importance ranks address_similarity (816.8 gain), gps_accuracy (404.0), visit_integrity "
     "(365.1) and number_of_supporting_visits (346.1) at the top, while all three raw distance "
     "features contribute zero gain \u2014 they were constant at training time (Table 17, Figure 5). "
     "A naive \u201cnearest successful visit\u201d heuristic is therefore explicitly not what the "
     "model learned; text similarity and evidence quality are."),
    ('The data is structurally clean enough to evaluate losslessly.',
     "Zero orphan rows across all five core joins and zero duplicate primary keys (Tables 5\u20136) "
     "mean every evaluated address is comparable across every baseline, and nulls are confined to "
     "optional attributes. This is what makes the head-to-head of Section 7 fair: no baseline is "
     "evaluated on a silently different subset of the 66 addresses."),
    ('Causal impact claims are withheld by design, and that is measurable.',
     "The dataset contains outcomes but no treatment-arm column and no independent recovery outcome, "
     "so the artifact returns not_estimable for IPW/doubly-robust policy evaluation (Section 9.7). "
     "Treating that status as a first-class, hash-pinned output \u2014 rather than as a missing score "
     "\u2014 is what prevents the project from claiming pilot-grade causality before the pilot "
     "records the fields that would make it identifiable."),
]
for i, (title, body) in enumerate(insights, 1):
    story.append(Paragraph(f'{i}.&nbsp;&nbsp;<b>{_safe(title)}</b>', st['numitem']))
    story.append(Paragraph(_safe(body), S(f'ins{i}', leftIndent=18, spaceBefore=0, spaceAfter=6)))
story.append(P(
    "Taken together, these findings support a staged rollout: shadow-mode measurement first "
    "(Section 11), auto-routing only where confidence is calibrated and high, and verification as "
    "the default action for the uncertain middle \u2014 which is precisely the deployment plan in "
    "Section 11."))
story.append(Spacer(1, 4))

# ===========================================================================
# 9. Evaluation framework
# ===========================================================================
story += h1block(9, 'Evaluation Framework and Reproducibility')
story.append(H2('9.1', 'Versioned experiment artifacts'))
story.append(P(
    "Every reproducible evaluation run writes a single JSON artifact, <i>ps3_eval_&lt;run_id&gt;.json</i> "
    "(the notebook writer produces <i>ps3_notebook_train.json</i>), containing: the artifact version "
    "and UTC run ID; the split and coordinate-system declaration; SHA-256 hashes of the source files; "
    "dataset counts; baseline metrics; ablation metrics; temporal and geography split metadata; the "
    "counterfactual-estimability status; and radar metrics with their evidence boundary."))
story.append(codeblock([
    'cd backend',
    '.\\venv\\Scripts\\python.exe -m evaluation.ps3_experiments ..\\Dataset `',
    '  --split train --output-dir ..\\evaluation_artifacts',
]))
story.append(P(
    "Because the artifact pins the exact input files by hash, any reported number can be re-verified "
    "against the identical inputs at any later date."))

story.append(H2('9.2', 'Controlled ablations'))
story.append(P(
    "The artifact separates four settings \u2014 address only; address plus visits; address plus visits "
    "plus integrity weighting; and address plus nearby evidence. The nearby-account ablation is marked "
    "<i>not_estimable</i> when the dataset lacks an independent nearby-account treatment/evidence "
    "table, and a locality centroid is never substituted silently, because that would confound the "
    "ablation. Nulls and <i>not_estimable</i> statuses in the artifact are intentional: they prevent "
    "unsupported claims."))

story.append(H2('9.3', 'Radar metrics'))
story.append(P(
    "The radar reports six axes \u2014 accuracy, coverage, calibration, robustness, explainability and "
    "latency. The currently generated radar is explicitly labelled <i>baseline_coverage</i>: it uses "
    "measured baseline values and does not pretend to be a complete production-model radar. Production "
    "reporting should replace baseline values with frozen-model measurements on held-out data and "
    "document how robustness is calculated across towns and evidence-integrity strata."))

story.append(H2('9.4', 'Temporal split'))
story.append(P(
    "Visits are ordered by check-in time; the evaluator defines a cutoff and uses only pre-cutoff "
    "visits for the temporal evidence calculation, so future visits never construct the pre-cutoff "
    "prediction. The artifact records the cutoff and counts plus a pre-cutoff weighted-centroid "
    "diagnostic. For production certification the model must be retrained or frozen using only data "
    "available before the cutoff and evaluated on later outcomes, without tuning thresholds against "
    "the future set."))

story.append(H2('9.5', 'Geography holdout'))
story.append(P(
    "The evaluator holds out one town and evaluates the address-only baseline on that town without "
    "using held-out-town visit evidence. This is a leakage-safe diagnostic, not a complete "
    "production-model generalisation score: the production model must be retrained on train-town data "
    "only and then scored on the held-out town, repeating across towns when sample sizes allow."))

story.append(H2('9.6', 'Account-level splitting'))
story.append(P(
    "Visit rows from the same account must never be randomly split between training and evaluation, "
    "or the model can memorise one of an account\u2019s visits and appear accurate. The harness "
    "materialises account groups before fitting and asserts that train and evaluation account IDs are "
    "disjoint; the ranker\u2019s deterministic 80/20 account partition (Section 6.5) implements this "
    "rule."))

story.append(H2('9.7', 'Counterfactual evaluation: deliberately not estimable'))
story.append(P(
    "IPW and doubly-robust policy evaluation cannot be validly computed from the provided PS3 files "
    "alone: they contain visit outcomes, but no randomised or policy-assigned treatment/action column "
    "and no independent recovery outcome. The artifact therefore returns an explicit status:"))
story.append(codeblock([
    '{',
    '  "status": "not_estimable",',
    '  "estimand": "policy value / treatment effect",',
    '  "required_columns": [',
    '    "treatment/action/policy_arm",',
    '    "recovery outcome",',
    '    "pre-treatment covariates"',
    '  ]',
    '}',
]))
story.append(P(
    "This is a feature, not a missing score: fabricating a causal estimate would violate the "
    "counterfactual-data requirement. A controlled pilot should record the policy arm, channel/action, "
    "pre-treatment covariates, contact eligibility, recovery outcome, cost and compliance events. Once "
    "those fields exist, the runner can compute propensities, weight diagnostics, effective sample "
    "size, IPW policy value and a doubly-robust estimate with confidence intervals."))
story.append(Spacer(1, 4))

# ===========================================================================
# 10. Security & compliance
# ===========================================================================
story += h1block(10, 'Security, RBAC and Compliance')
story.append(H2('10.1', 'Role-based access control'))
story.append(P(
    "Borrower locations, visit trails, agent GPS, remarks, planner output and territory metrics are "
    "sensitive operational data. A field agent should not automatically receive every lender\u2019s "
    "accounts or every territory\u2019s history; managers need broader territory views; auditors need "
    "evidence and audit access; administrators need configuration access. The backend enforces "
    "authenticated operational routes with permission dependencies, and changing model state "
    "(retraining) requires the admin permission. Production deployment must add lender/tenant and "
    "territory scoping at the data-query boundary, not only at the UI."))
story.append(H2('10.2', 'RBI and DPDP boundaries'))
story.append(P(
    "The prototype does not claim that a generic configuration satisfies every lender\u2019s legal "
    "obligations. Each deployment must configure and audit: permitted contact hours and frequency; "
    "consent and purpose limitation; retention and deletion windows; access logging and export "
    "controls; separation of collections data from unrelated uses; agent-monitoring governance; and "
    "incident response and correction workflows. The geocoder should not infer locations beyond what "
    "collections requires."))
story.append(Spacer(1, 4))

# ===========================================================================
# 11. Deployment plan
# ===========================================================================
story += h1block(11, 'Deployment Plan')
phases = [
    ('Phase 1 \u2014 Shadow mode', [
        "ingest visit evidence without changing planner decisions;",
        "measure distance error, coverage and calibration;",
        "inspect integrity alerts and remark extraction;",
        "establish tenant, territory and retention policies;",
        "review false positives with field managers.",
    ]),
    ('Phase 2 \u2014 Controlled pilot', [
        "select comparable territories;",
        "freeze a time-based model version;",
        "define incumbent and geocoder-assisted policies;",
        "record action assignment and recovery outcomes;",
        "measure productive visits per agent-day and cost per recovery;",
        "monitor complaint, contact-hour and privacy events.",
    ]),
    ('Phase 3 \u2014 Guarded rollout', [
        "enable direct visits only above calibrated thresholds;",
        "route low-confidence cases through verification;",
        "keep confirmed and predicted write-back separate;",
        "monitor town-level drift and agent-integrity anomalies;",
        "retain a rollback path to the incumbent policy.",
    ]),
    ('Phase 4 \u2014 Continuous governance', [
        "version data, model, configuration and evaluation artifacts;",
        "rerun temporal and geography holdouts;",
        "recalibrate after population or device changes;",
        "review cluster-propagation thresholds;",
        "delete data according to lender retention policy;",
        "audit access and correction requests.",
    ]),
]
for title, items in phases:
    story.append(H3(title))
    for b in items:
        story.append(B(b))
story.append(Spacer(1, 4))

# ===========================================================================
# 12. Limitations
# ===========================================================================
story += h1block(12, 'Known Limitations and Next Engineering Work')
lims = [
    "The planner now supports an origin and maximum-distance budget with deterministic distance-aware prioritisation, but is not yet a full travel-time or cost-aware route optimiser.",
    "The available PS3 dataset cannot support a causal policy-value estimate (Section 9.7).",
    "The nearby-account ablation needs an independent evidence table.",
    "The production-model geography holdout requires train-town-only retraining before accuracy is reported.",
    "Ranker training creates a deterministic account-level 80/20 partition and asserts zero overlap before fitting; a complete production harness should also score the held-out partition separately.",
    "Multilingual remark-to-offset extraction remains conservative by design.",
    "Cluster propagation requires lender-specific scale thresholds.",
    "Offline retries now move five-time failures to a local dead-letter store; conflict resolution, retry observability and server-side idempotency still need production hardening.",
    "Tenant and territory filtering must be enforced in repository queries.",
    "Full notebook execution requires the notebook dependencies in the backend environment.",
]
for i, t in enumerate(lims, 1):
    story.append(Paragraph(f'{i}.&nbsp;&nbsp;{t}', st['numitem']))
story.append(Spacer(1, 4))

# ===========================================================================
# 13. Deliverables
# ===========================================================================
story += h1block(13, 'Deliverables and Submission')
story.append(H2('13.1', 'Deliverables mapped to the PS3 problem statement'))
story.append(tcap('Table 22. PS3 deliverables, their location and the evidence for each.'))
deliv = [
    ['1', 'EDA and evaluation notebook', 'PS3_Geocoder_EDA.ipynb',
     '22 cells: data-quality checks, coverage, visit evidence analysis, baseline and embedded-backend '
     'evaluation, calibration, town summaries, artifact writer, interpretation. JSON and extracted '
     'Python syntax-validated.'],
    ['2', 'Trained ranker model', 'Embedded in the notebook (base64 LightGBM artifact)',
     '150 trees, 21-feature contract; deterministic account-level 80/20 partition with overlap '
     'assertion; architecture and feature analysis in Section 6.'],
    ['3', 'Versioned evaluation artifact', 'evaluation_artifacts/ps3_notebook_train.json '
     '(runner: ps3_eval_<run_id>.json)',
     'SHA-256 input hashes, run ID, split and CRS declaration, baselines, ablations, split metadata, '
     'radar and causal-estimability status (Section 9).'],
    ['4', 'Backend geocoder service', 'Project backend (per solution documentation)',
     'Authenticated routes: planner, PS2 RPC location features, account search with pagination, admin '
     'retraining; RBAC permissions; null-safe and data-tolerant metrics paths (Section 6.8).'],
    ['5', 'Frontend field app and dashboards', 'Project frontend (per solution documentation)',
     'Corrected pin + radius + evidence display, offline queue with dead-letter, service-worker cache, '
     'light/dark mode, optional Google Maps with WGS84-only rule (Sections 6.8, 6.6).'],
    ['6', 'Solution documentation', 'PS3_PROBLEM_SOLUTION_REPORT.md',
     'Problem\u2013solution mapping, pipeline, evaluation design, security and compliance, deployment '
     'plan, acceptance checklist.'],
    ['7', 'This report', 'PS3_Report.pdf',
     'Findings, measured evidence, model architecture and delivery status for PS3.'],
]
story.append(table([['#', 'Deliverable', 'Location', 'Evidence / status']] + deliv,
                   [8 * mm, 32 * mm, 38 * mm, 78 * mm], align_right_cols=(0,)))

story.append(H2('13.2', 'Pre-pilot acceptance checklist'))
story.append(P("Before a lender pilot is approved, the following must be confirmed:"))
story.append(tcap('Table 23. Acceptance checklist (x = satisfied by current implementation).'))
checks = [
    '[ ]  All operational routes require authentication and scoped permissions',
    '[ ]  Tenant and territory filters are enforced server-side',
    '[ ]  RBI contact-hour and frequency policy is configured',
    '[ ]  DPDP consent, purpose and retention controls are configured',
    '[ ]  Projected and WGS84 coordinate systems are explicit at every boundary',
    '[ ]  Confirmed locations cannot be overwritten by weak predictions',
    '[ ]  Visit-integrity alerts are reviewed',
    '[ ]  Baseline and ablation artifact hashes are stored',
    '[ ]  Temporal and geography holdouts are frozen before tuning',
    '[x]  Ranker training asserts disjoint account IDs before fitting',
    '[ ]  Held-out account partition is scored separately',
    '[ ]  Counterfactual fields exist before any IPW/DR claim',
    '[ ]  Offline sync conflict handling is tested',
    '[ ]  Field users can see directions, radius and evidence offline',
    '[ ]  Rollback to the incumbent planner is tested',
    '[ ]  Productive-visit and cost metrics are measured in a controlled pilot',
]
for c in checks:
    story.append(Paragraph(c.replace('[x]', '<b>[x]</b>'), S('chk', fontSize=10.5, leading=15,
                                                           alignment=TA_LEFT, spaceAfter=1.5)))
story.append(Spacer(1, 6))

# ===========================================================================
# 14. Conclusion
# ===========================================================================
story += h1block(14, 'Conclusion')
story.append(P(
    "The project addresses the core PS3 problem with a practical evidence-learning geocoder rather "
    "than a generic address lookup. The model architecture of Section 6 \u2014 normalisation, entity "
    "extraction, five-source candidate generation, reliability weighting, a 150-tree LightGBM ranker "
    "over a 21-feature evidence contract, and uncertainty-driven action decisions \u2014 is built to "
    "combine messy address understanding with noisy field observations, and to give the planner "
    "uncertainty instead of false precision."))
story.append(P(
    "The measured evidence is clear: on the 66 surveyed train addresses, historical visit evidence "
    "fused with reliability weights cuts median error by 46.3% against the commercial baseline and "
    "more than doubles the share of addresses within 250 m, at a latency of a few milliseconds. The "
    "insights of Section 8 explain where the system is strong (high-confidence predictions, evidence-"
    "rich accounts) and where it must stay honest (the uncertain middle, the 27% without visit "
    "history, and causal claims that the data cannot support). The evaluation framework makes those "
    "boundaries visible as well \u2014 descriptive baselines are measured now, leakage-safe split "
    "diagnostics are recorded, calibration is reported with its caveats, and causal evaluation waits "
    "for the data that would make it identifiable. That discipline, not a single leaderboard number, "
    "is what makes the system ready to enter shadow mode behind a real collections operation."))

# ===========================================================================
# build
# ===========================================================================
def build():
    doc = Doc(OUT, pagesize=A4,
              leftMargin=ML, rightMargin=MR, topMargin=MT, bottomMargin=MB,
              title='PS3 AI-Native Field Address Geocoder - EDA, Model Architecture, Evaluation and Delivery Report',
              author='Kartik',
              subject='Problem Set 3 report')
    cover_frame = Frame(ML, 60, BODY_W, PAGE_H - 60 - 150, id='cover')
    body_frame = Frame(ML, MB, BODY_W, PAGE_H - MT - MB, id='body')
    doc.addPageTemplates([
        PageTemplate(id='Cover', frames=[cover_frame], onPage=draw_cover),
        PageTemplate(id='Body', frames=[body_frame], onPage=draw_body),
    ])
    doc.multiBuild(story)
    print('wrote', OUT)

if __name__ == '__main__':
    build()
