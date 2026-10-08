#!/usr/bin/env python3
"""Build the PS3 report as a PowerPoint deck (matches the PDF theme and content)."""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# ---------------------------------------------------------------- theme
NAVY = RGBColor(0x1F, 0x38, 0x64)
ACCENT = RGBColor(0x2E, 0x74, 0xB5)
LIGHT = RGBColor(0xDE, 0xEA, 0xF6)
ZEBRA = RGBColor(0xF2, 0xF6, 0xFB)
TEXT = RGBColor(0x1A, 0x1A, 0x1A)
MUTED = RGBColor(0x59, 0x59, 0x59)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = 'Times New Roman'
CODE = 'Courier New'

FIG = '/home/user/PS3_ADI/report_assets/figures'
OUT = '/home/user/PS3_ADI/PS3_Report.pptx'

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
PAGE_W = 13.333
MARGIN = 0.55
BODY_W = PAGE_W - 2 * MARGIN

page_no = 0

# ---------------------------------------------------------------- helpers
def slide_new():
    return prs.slides.add_slide(BLANK)

def _set_run(r, text, size, bold=False, color=TEXT, italic=False, font=FONT):
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.name = font
    r.font.color.rgb = color

def txbox(s, x, y, w, h):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    return tf

def para(tf, text, size=12, bold=False, color=TEXT, italic=False, align=PP_ALIGN.LEFT,
         space_before=0, space_after=4, font=FONT, first=False):
    p = tf.paragraphs[0] if first and not tf.paragraphs[0].runs else tf.add_paragraph()
    p.alignment = align
    p.space_before = Pt(space_before)
    p.space_after = Pt(space_after)
    _set_run(p.add_run(), text, size, bold, color, italic, font)
    return p

def bullet(tf, text, size=11, bold=False, color=TEXT, level=0, space_after=4, first=False):
    p = tf.paragraphs[0] if first and not tf.paragraphs[0].runs else tf.add_paragraph()
    p.level = level
    p.space_after = Pt(space_after)
    bullet_char = '\u2022  ' if level == 0 else '\u2013  '
    _set_run(p.add_run(), bullet_char, size, bold, ACCENT if level == 0 else MUTED)
    _set_run(p.add_run(), text, size, bold, color)
    return p

def rect(s, x, y, w, h, fill, line=None):
    sh = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(0.75)
    sh.shadow.inherit = False
    return sh

def header(s, kicker, title):
    tf = txbox(s, MARGIN, 0.22, BODY_W, 0.3)
    para(tf, kicker.upper(), size=10.5, bold=True, color=ACCENT, space_after=0, first=True)
    tf2 = txbox(s, MARGIN, 0.48, BODY_W, 0.62)
    para(tf2, title, size=25, bold=True, color=NAVY, space_after=0, first=True)
    rect(s, MARGIN, 1.16, BODY_W, 0.032, ACCENT)

def footer(s):
    global page_no
    page_no += 1
    if page_no == 1:
        return
    tf = txbox(s, MARGIN, 7.12, BODY_W, 0.3)
    p = tf.paragraphs[0]
    p.space_after = Pt(0)
    _set_run(p.add_run(), 'PS3 \u2014 AI-Native Field Address Geocoder', 9, False, MUTED, True)
    p2 = txbox(s, PAGE_W - 1.55, 7.12, 1.0, 0.3).paragraphs[0]
    p2.alignment = PP_ALIGN.RIGHT
    p2.space_after = Pt(0)
    _set_run(p2.add_run(), str(page_no), 9, False, MUTED)

def make_table(s, x, y, w, data, col_w, font=9.5, header_font=None, row_h=0.24,
               align_right=(), zebra=True):
    rows, cols = len(data), len(data[0])
    gfx = s.shapes.add_table(rows, cols, Inches(x), Inches(y), Inches(w), Inches(row_h * rows))
    t = gfx.table
    t.first_row = False
    t.horz_banding = False
    for i, cw in enumerate(col_w):
        t.columns[i].width = Inches(cw)
    for ri in range(rows):
        t.rows[ri].height = Inches(row_h)
        for ci in range(cols):
            cell = t.cell(ri, ci)
            cell.margin_left = Inches(0.05)
            cell.margin_right = Inches(0.05)
            cell.margin_top = Inches(0.01)
            cell.margin_bottom = Inches(0.01)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.RIGHT if (ci in align_right and ri > 0) else PP_ALIGN.LEFT
            p.space_after = Pt(0)
            if ri == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = NAVY
                _set_run(p.add_run(), str(data[ri][ci]), header_font or font, True, WHITE)
            else:
                cell.fill.solid()
                cell.fill.fore_color.rgb = ZEBRA if (zebra and ri % 2 == 0) else WHITE
                _set_run(p.add_run(), str(data[ri][ci]), font, False, TEXT)
    return t

def pic(s, path, x, y, w, caption=None, max_h=None, box_w=None):
    """Place figure at (x, y), width w; if it exceeds max_h, shrink to fit and
    centre horizontally within box_w (defaults to the requested w)."""
    from PIL import Image as PILImage
    im = PILImage.open(path)
    h = w * im.size[1] / im.size[0]
    if max_h is not None and h > max_h:
        h = max_h
        w = h * im.size[0] / im.size[1]
        x = x + (box_w - w) / 2 if box_w is not None else x
    s.shapes.add_picture(path, Inches(x), Inches(y), width=Inches(w))
    if caption:
        tf = txbox(s, x, y + h + 0.04, w, 0.5)
        para(tf, caption, size=9.5, italic=True, color=MUTED, align=PP_ALIGN.CENTER,
             space_after=0, first=True)
    return h

def codebox(s, x, y, w, h, lines, size=10.5):
    rect(s, x, y, w, h, LIGHT, line=RGBColor(0xBF, 0xBF, 0xBF))
    tf = txbox(s, x + 0.12, y + 0.08, w - 0.24, h - 0.16)
    for i, ln in enumerate(lines):
        para(tf, ln, size=size, font=CODE, color=TEXT, space_after=2, first=(i == 0))

def kpi_strip(s, y, kpis):
    n = len(kpis)
    gap = 0.18
    bw = (BODY_W - gap * (n - 1)) / n
    for i, (val, lab) in enumerate(kpis):
        x = MARGIN + i * (bw + gap)
        rect(s, x, y, bw, 1.05, LIGHT)
        tf = txbox(s, x + 0.08, y + 0.10, bw - 0.16, 0.5)
        para(tf, val, size=21, bold=True, color=NAVY, align=PP_ALIGN.CENTER, space_after=0, first=True)
        tf2 = txbox(s, x + 0.08, y + 0.62, bw - 0.16, 0.4)
        para(tf2, lab, size=9, color=MUTED, align=PP_ALIGN.CENTER, space_after=0, first=True)

def notes(s, text):
    s.notes_slide.notes_text_frame.text = text

# =========================================================================
# Slide 1 — Title
# =========================================================================
s = slide_new()
rect(s, 0, 0, PAGE_W, 7.5, NAVY)
rect(s, 0, 7.18, PAGE_W, 0.32, ACCENT)
tf = txbox(s, 1.0, 0.75, 11.33, 0.5)
para(tf, 'Indian Institute of Technology Kharagpur', size=16, bold=True, color=WHITE,
     align=PP_ALIGN.CENTER, space_after=0, first=True)
tf = txbox(s, 1.0, 1.25, 11.33, 0.4)
para(tf, 'Applied Data Intelligence (ADI)  \u2022  Problem Set 3', size=12, color=LIGHT,
     align=PP_ALIGN.CENTER, space_after=0, first=True)
tf = txbox(s, 1.0, 2.35, 11.33, 0.5)
para(tf, 'PROBLEM SET 3', size=14, bold=True, color=RGBColor(0x9D, 0xC3, 0xE6),
     align=PP_ALIGN.CENTER, space_after=0, first=True)
tf = txbox(s, 1.0, 2.85, 11.33, 1.1)
para(tf, 'AI-Native Field Address Geocoder', size=40, bold=True, color=WHITE,
     align=PP_ALIGN.CENTER, space_after=0, first=True)
tf = txbox(s, 1.0, 4.0, 11.33, 0.8)
para(tf, 'Exploratory Data Analysis, Model Architecture,', size=17, color=WHITE,
     align=PP_ALIGN.CENTER, space_after=0, first=True)
para(tf, 'Evaluation and Delivery Report', size=17, color=WHITE, align=PP_ALIGN.CENTER)
tf = txbox(s, 1.0, 5.35, 11.33, 0.9)
para(tf, 'Name: Kartik        Roll No.: 2025112', size=14, color=WHITE,
     align=PP_ALIGN.CENTER, space_after=2, first=True)
para(tf, 'October 2026', size=12, color=LIGHT, align=PP_ALIGN.CENTER)
tf = txbox(s, 1.0, 7.20, 11.33, 0.3)
para(tf, 'PS3_Geocoder_EDA.ipynb  \u2022  PS3_PROBLEM_SOLUTION_REPORT.md  \u2022  evaluation artifact (SHA-256 pinned)',
     size=9, color=LIGHT, align=PP_ALIGN.CENTER, space_after=0, first=True)
notes(s, 'Title slide. PS3: address-intelligence geocoder with uncertainty and evidence trails.')

# =========================================================================
# Slide 2 — Outline
# =========================================================================
s = slide_new()
header(s, 'Contents', 'Report Outline')
footer(s)
left = [
    '1.  Executive Summary',
    '2.  The Business Problem',
    '3.  Dataset and Data Quality',
    '4.  Exploratory Analysis of Field-Visit Evidence',
    '5.  Commercial Baseline Geocoder Evaluation',
    '6.  Model Architecture and Detailed Design',
    '7.  Model Evaluation',
    '8.  Key Insights and Interpretation',
]
right = [
    '9.  Evaluation Framework and Reproducibility',
    '10. Security, RBAC and Compliance',
    '11. Deployment Plan',
    '12. Known Limitations and Next Engineering Work',
    '13. Deliverables and Submission',
    '14. Conclusion',
]
tf = txbox(s, MARGIN + 0.2, 1.5, 5.8, 5.4)
for i, t in enumerate(left):
    para(tf, t, size=14, color=TEXT, space_after=10, first=(i == 0))
tf = txbox(s, 6.9, 1.5, 5.8, 5.4)
for i, t in enumerate(right):
    para(tf, t, size=14, color=TEXT, space_after=10, first=(i == 0))
notes(s, 'Fourteen sections; the deck follows the report order.')

# =========================================================================
# Slide 3 — Executive summary
# =========================================================================
s = slide_new()
header(s, 'Section 1', 'Executive Summary')
footer(s)
tf = txbox(s, MARGIN, 1.35, BODY_W, 2.1)
bullet(tf, 'Problem: collection addresses are descriptions, not pins \u2014 the commercial geocoder '
           'returns a locality centre while the operational answer is \u201cbehind the ration shop, two '
           'lanes after the temple\u201d.', size=11.5, first=True, space_after=6)
bullet(tf, 'Solution: an evidence-fusion geocoder \u2014 address text + landmarks + visit history + GPS '
           'quality + dwell + integrity signals \u2192 location + uncertainty radius + evidence trail + '
           'operational action (visit_directly / verify_first / skip).', size=11.5, space_after=6)
bullet(tf, 'Model: 150-tree LightGBM ranker over a 21-feature evidence contract, fronted by a '
           'deterministic reliability-weighted aggregator; confirmed and predicted locations kept '
           'strictly separate.', size=11.5, space_after=6)
kpi_strip(s, 3.75, [
    ('204.4 m', 'median error (weighted geocoder, n = 66)'),
    ('\u221246.3%', 'median error vs commercial baseline (380.8 m)'),
    ('53.0%', 'within 250 m (baseline: 28.8%)'),
    ('72.7%', 'radius coverage of true location'),
    ('3.3 ms', 'per prediction \u2022 ECE 0.155'),
])
tf = txbox(s, MARGIN, 5.15, BODY_W, 1.7)
bullet(tf, 'Conservative by design: projected metres (not WGS84), no check-in treated as ground '
           'truth, no causal claims without treatment assignment + independent recovery outcome.',
       size=11, space_after=5, first=True)
bullet(tf, 'Reproducible: every run writes a JSON artifact with run ID, SHA-256 source hashes, '
           'baselines, ablations, split metadata and explicit limitations.', size=11)
notes(s, 'Headline results on the train split: 2,175 addresses, 3,896 visits, 66 surveyed truth addresses.')

# =========================================================================
# Slide 4 — Business problem
# =========================================================================
s = slide_new()
header(s, 'Section 2', 'The Business Problem: Cost and Motivation')
footer(s)
make_table(s, MARGIN, 1.45, 5.4, [
    ['Channel', 'Fully-loaded cost'],
    ['SMS / WhatsApp', 'fraction of a rupee'],
    ['AI voice', '~INR 1\u20133 per call'],
    ['Human tele-caller', '~INR 15\u201330 per connect'],
    ['Productive field visit', '~INR 150\u2013400'],
], [2.9, 2.5], font=10, row_h=0.34)
tf = txbox(s, MARGIN, 3.5, 5.4, 0.9)
para(tf, 'Objective: recovery net of contact cost, goodwill and compliance risk.', size=11,
     italic=True, color=NAVY, first=True)
tf = txbox(s, 6.3, 1.45, BODY_W - (6.3 - MARGIN), 5.3)
para(tf, 'Why ordinary geocoding fails', size=13, bold=True, color=NAVY, space_after=4, first=True)
bullet(tf, 'Mixed Devanagari / Roman / Kannada / Hindi / English text and transliteration variants')
bullet(tf, 'Relational descriptions: \u201cbehind\u201d, \u201cnear\u201d, \u201copposite\u201d \u2014 informal '
           'landmarks absent from global geocoders')
bullet(tf, 'Locality names shared by several towns; addresses that name a shop or workplace, not a '
           'residence')
para(tf, 'Why visit GPS is valuable but imperfect', size=13, bold=True, color=NAVY,
     space_before=10, space_after=4)
bullet(tf, 'Check-ins are evidence, not truth: met at work, poor GPS, tea-stall check-ins, failed '
           'searches near (not at) the address')
bullet(tf, 'Fix: combine evidence with reliability weights and uncertainty \u2014 never copy the latest '
           'latitude and longitude', bold=True)
notes(s, 'A geocoder is useful only if it raises the probability a field visit is productive.')

# =========================================================================
# Slide 5 — Dataset
# =========================================================================
s = slide_new()
header(s, 'Section 3', 'Dataset and Data Quality (train split)')
footer(s)
make_table(s, MARGIN, 1.4, 6.3, [
    ['Table', 'Rows', 'Size'],
    ['accounts', '1,680', '220.8 KB'],
    ['addresses', '2,175', '278.3 KB'],
    ['field_visits', '3,896', '658.3 KB'],
    ['agents', '30', '1.0 KB'],
    ['baseline_geocodes', '2,010', '64.6 KB'],
    ['surveyed_addresses', '66', '1.6 KB'],
    ['visit_gps_points', '112,080', '5.1 MB'],
    ['landmarks_poi', '240', '11.3 KB'],
    ['localities / towns', '36 / 3', '1.9 KB'],
], [2.5, 1.9, 1.9], font=9.5, row_h=0.3, align_right=(1, 2))
rx = 7.15
rect(s, rx, 1.4, 5.63, 1.15, LIGHT)
tf = txbox(s, rx + 0.15, 1.5, 5.35, 1.0)
para(tf, 'Coordinates are projected local metres \u2014 not WGS84', size=11, bold=True, color=NAVY,
     first=True, space_after=2)
para(tf, 'error_m = sqrt((\u0394x)\u00b2 + (\u0394y)\u00b2); ranges \u00b14,400 m confirm a local CRS', size=10)
tf = txbox(s, rx, 2.75, 5.63, 4.0)
bullet(tf, '0 orphan rows across all 5 core joins (addresses\u2192accounts, visits\u2192addresses, '
           'surveyed\u2192addresses, baseline\u2192addresses)', size=10.5, first=True, space_after=5)
bullet(tf, '0 duplicate primary keys in any table; nulls only in optional attributes', size=10.5,
       space_after=5)
bullet(tf, '3 towns \u00b7 3 address styles (karnataka, hindi, metro) \u00b7 2,175 addresses \u00b7 '
           '240 landmarks', size=10.5, space_after=5)
bullet(tf, 'Address mix: 78% residence, 15% office, 7% permanent-native; 99% from KYC origination, '
           '19 skip_trace (the hard cases)', size=10.5, space_after=5)
bullet(tf, 'Every artifact records SHA-256 of source files \u2014 results reproducible against '
           'identical inputs', size=10.5)
notes(s, 'Table 3 of the report lists the full 10-file inventory.')

# =========================================================================
# Slide 6 — EDA outcomes
# =========================================================================
s = slide_new()
header(s, 'Section 4', 'EDA \u2014 Field-Visit Outcomes (n = 3,896)')
footer(s)
make_table(s, MARGIN, 1.45, 5.9, [
    ['Outcome', 'Visits', 'Share'],
    ['address_not_traceable', '957', '24.6%'],
    ['locked_premises', '901', '23.1%'],
    ['met_borrower', '766', '19.7%'],
    ['met_family', '730', '18.7%'],
    ['neighbour_says_shifted', '332', '8.5%'],
    ['no_such_person', '151', '3.9%'],
    ['cash_collected', '59', '1.5%'],
], [3.1, 1.4, 1.4], font=10, row_h=0.36, align_right=(1, 2))
tf = txbox(s, MARGIN, 4.55, 5.9, 2.2)
bullet(tf, '1,555 of 3,896 visits (39.9%) are successful contacts (orange in the chart)', size=11,
       first=True, space_after=5)
bullet(tf, 'Failed visits are still information: they mark where agents searched and found nobody \u2014 '
           'the raw signal behind \u201caddress-not-traceable\u201d', size=11)
pic(s, f'{FIG}/fig_outcomes.png', 6.9, 1.7, 5.85,
    'Figure 1. Outcome distribution; orange = successful-contact evidence.')
notes(s, 'Notebook Section 4; Table 9 of the report.')

# =========================================================================
# Slide 7 — EDA evidence quality
# =========================================================================
s = slide_new()
header(s, 'Section 4', 'EDA \u2014 Evidence Quality: GPS Accuracy vs Dwell')
footer(s)
make_table(s, MARGIN, 1.45, 5.9, [
    ['Metric', 'Mean', 'Median', 'P90', 'Max'],
    ['GPS accuracy (m)', '11.28', '9.9', '18.7', '54.0'],
    ['Dwell time (s)', '339.8', '203.0', '908.0', '1,495.0'],
], [1.9, 1.0, 1.0, 1.0, 1.0], font=10, row_h=0.34, align_right=(1, 2, 3, 4))
tf = txbox(s, MARGIN, 2.85, 5.9, 3.9)
bullet(tf, 'Dwell is the discriminator: median 876 s on met_borrower vs 78 s on '
           'address_not_traceable \u2014 an 11\u00d7 gap', size=11, first=True, space_after=6)
bullet(tf, 'GPS accuracy barely moves across outcomes (9.1\u201310.9 m median) \u2014 it is a filter, not '
           'a discriminator', size=11, space_after=6)
bullet(tf, 'Weighting encodes the separation: (1/accuracy) \u00d7 dwell/300', size=11, bold=True,
       color=NAVY, space_after=6)
bullet(tf, 'Agent concentration is mild (top agent 470 vs fleet average 130) \u2192 agent-independence '
           'feature guards clusters', size=11)
pic(s, f'{FIG}/fig_01_cell10.png', 6.75, 1.75, 6.0,
    'Figure 2. GPS-accuracy distribution (left) and dwell by outcome (right).')
notes(s, 'Notebook Section 4; Tables 10\u201312 of the report.')

# =========================================================================
# Slide 8 — Baseline evaluation
# =========================================================================
s = slide_new()
header(s, 'Section 5', 'Commercial Baseline Geocoder (n = 66 surveyed)')
footer(s)
make_table(s, MARGIN, 1.4, 5.9, [
    ['Metric', 'Value'],
    ['Median error (m)', '380.8'],
    ['P90 / P95 error (m)', '745.6 / 1,176.9'],
    ['Within 50 m', '4.5%'],
    ['Within 100 m', '9.1%'],
    ['Within 250 m', '28.8%'],
    ['Within 500 m', '71.2%'],
], [3.4, 2.5], font=10, row_h=0.32, align_right=(1,))
make_table(s, MARGIN, 3.9, 5.9, [
    ['Town', 'Median (m)', 'Within 250 m'],
    ['T2 Devgarh Nagar (hindi)', '359.3', '33.3%'],
    ['T3 Navanagara East (metro)', '369.3', '28.6%'],
    ['T1 Kaveripura (karnataka)', '420.2', '25.0%'],
], [2.9, 1.5, 1.5], font=9.5, row_h=0.3, align_right=(1, 2))
tf = txbox(s, MARGIN, 5.55, 5.9, 1.3)
para(tf, 'The failure tracks address style: the weakest town is the Kannataka-style T1 \u2014 '
         'transliteration and script diversity degrade global geocoders.', size=10.5, italic=True,
     color=NAVY, first=True)
pic(s, f'{FIG}/fig_02_cell12.png', 6.9, 1.6, 4.9,
    'Figure 3. Baseline error distribution: tight core near 400\u2013600 m, heavy tail to ~2.2 km.')
notes(s, 'Table 13\u201314 of the report. Only 28.8% within 250 m \u2014 the headroom the evidence geocoder must fill.')

# =========================================================================
# Slide 9 — Architecture
# =========================================================================
s = slide_new()
header(s, 'Section 6', 'Model Architecture: End-to-End View')
footer(s)
pic(s, f'{FIG}/fig_architecture.png', 0.85, 1.4, 11.6,
    'Figure 4. Inputs \u2192 normalisation \u2192 entities \u2192 five-source candidate generation \u2192 '
    'evidence weighting \u2192 LightGBM ranker \u2192 uncertainty \u2192 action \u2192 consumers.',
    max_h=5.2, box_w=11.6)
notes(s, 'The deterministic aggregator (stage 4) works even where the learned ranker has no support.')

# =========================================================================
# Slide 10 — Pipeline stages
# =========================================================================
s = slide_new()
header(s, 'Section 6', 'Pipeline: Stage-by-Stage Contract')
footer(s)
make_table(s, MARGIN, 1.35, BODY_W, [
    ['Stage', 'Input', 'Processing', 'Output'],
    ['1. Ingestion & CRS validation', '10 CSV files', 'Existence checks, SHA-256, projected-CRS declaration', 'Clean tables + artifact metadata'],
    ['2. Address normalisation', 'Raw multilingual text', 'Unicode, whitespace, abbreviations, transliteration-aware tokens', 'Normalised string (original kept for audit)'],
    ['3. Entity & relation extraction', 'Normalised address', 'House/plot, roads, village/town, landmarks, relations, pincodes', 'Searchable entity set'],
    ['4. Candidate generation', 'Entities + 5 sources', 'Resolve vs landmarks, localities, visits, confirmed accounts, remarks', 'Alternative coordinates'],
    ['5. Evidence weighting', 'Check-ins + quality signals', 'w = (1/acc) \u00d7 dwell/300; integrity, recency, agent controls', 'Weighted evidence'],
    ['6. Candidate ranking', '21-feature vector', 'LightGBM, 150 trees', 'Accept probabilities'],
    ['7. Uncertainty & action', 'Winner + spread', 'radius = max(50, wRMS); conf = 1 \u2212 r/1000; thresholds', 'Pin + radius + action'],
    ['8. Persistence & serving', 'Prediction + confirmed', 'Confirmed/predicted separation; RBAC routes', 'App, planner, PS2 RPC, dashboards'],
], [2.5, 2.6, 4.3, 2.83], font=9, row_h=0.55)
notes(s, 'Table 15 of the report.')

# =========================================================================
# Slide 11 — Evidence weighting & candidates
# =========================================================================
s = slide_new()
header(s, 'Section 6', 'Evidence Weighting and Candidate Sources')
footer(s)
codebox(s, MARGIN, 1.5, 6.0, 2.2, [
    'SUCCESSFUL = {met_borrower, met_family, cash_collected}',
    '',
    'weight    = (1 / gps_accuracy) * clip(dwell, 1, 600) / 300',
    'predicted = weighted average of successful check-ins',
    'radius    = max(50 m, weighted RMS spread)',
    'confidence = clip(1 - radius / 1000, 0, 1)',
], size=10.5)
tf = txbox(s, MARGIN, 4.0, 6.0, 2.8)
para(tf, 'No usable successful visit \u2192 fall back to the commercial geocode with a 500 m radius. '
         'Shared-place clusters propagate only under source and reliability thresholds \u2014 '
         'never unconditional copying.', size=10.5, first=True)
tf = txbox(s, 6.9, 1.5, BODY_W - (6.9 - MARGIN), 5.3)
para(tf, 'Five candidate sources', size=13, bold=True, color=NAVY, first=True, space_after=6)
bullet(tf, 'Commercial / open geocoder \u2014 prior and fallback', size=10.5, space_after=5, first=True)
bullet(tf, 'Historical successful visits \u2014 weighted centroid (strongest source)', size=10.5,
       space_after=5)
bullet(tf, 'Nearby confirmed accounts / shared-place clusters \u2014 guarded corroboration', size=10.5,
       space_after=5)
bullet(tf, 'Landmarks & locality centroids \u2014 anchor for \u201cbehind the temple\u201d', size=10.5,
       space_after=5)
bullet(tf, 'Agent-remarks corrections \u2014 conservative, high-precision only', size=10.5)
notes(s, 'Table 16 + the Section 6.4 formulas of the report.')

# =========================================================================
# Slide 12 — Ranker contract & training
# =========================================================================
s = slide_new()
header(s, 'Section 6', 'Ranker: 21-Feature Contract and Training')
footer(s)
make_table(s, MARGIN, 1.3, 6.6, [
    ['Group', 'Feature', 'Training range'],
    ['Text similarity', 'address_similarity', '0.10\u20130.60'],
    ['Text similarity', 'landmark_similarity', '0.00\u20130.40'],
    ['Text similarity', 'locality_similarity', '0.30\u20130.80'],
    ['Visit evidence', 'distance_to_successful_visits', 'const 999999'],
    ['Visit evidence', 'distance_to_failed_visits', 'const 999999'],
    ['Visit evidence', 'number_of_supporting_visits', '0\u20137'],
    ['Visit evidence', 'weighted_successful_visit_count', '0\u20137'],
    ['Evidence quality', 'visit_integrity', '0.80\u20131.00'],
    ['Evidence quality', 'gps_accuracy', '4.1\u20131000 m'],
    ['Evidence quality', 'dwell_time', '0\u20131475 s'],
    ['Evidence quality', 'trajectory_quality', '0.20\u20130.70'],
    ['Corroboration', 'nearby_account_support', 'default'],
    ['Corroboration', 'place_cluster_support', 'default'],
    ['Commercial ref.', 'commercial_geocoder_distance', 'default'],
    ['Adversarial', 'agent_independence', '0\u20131'],
    ['Source one-hot (6)', 'source_historical / nearby / geocoder / landmark / locality / pincode', '0\u20131'],
], [1.7, 3.3, 1.6], font=8.5, row_h=0.3, align_right=(2,))
make_table(s, 7.5, 1.3, 5.28, [
    ['Parameter', 'Value'],
    ['Framework', 'LightGBM binary (sigmoid), text v4'],
    ['Trees', '150 retained (cap 200)'],
    ['Learning rate', '0.05'],
    ['Leaves per tree', '31 (trees 452\u2013885 nodes)'],
    ['Bagging', '0.8, every 5 iters (seed 400)'],
    ['Min data in leaf', '3'],
    ['Split', 'Deterministic account-level 80/20, disjoint-ID assertion'],
    ['Check', 'P(accept | zero vector) = 0.6927'],
    ['Portability', 'Embedded base64 in notebook'],
], [1.9, 3.38], font=8.5, row_h=0.3)
notes(s, 'Tables 17\u201318 of the report; ranges from the model artifact feature_infos.')

# =========================================================================
# Slide 13 — Feature importance
# =========================================================================
s = slide_new()
header(s, 'Section 6', 'What the Ranker Learned: Feature Importance')
footer(s)
make_table(s, MARGIN, 1.4, 5.9, [
    ['Feature', 'Gain', 'Splits'],
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
], [3.3, 1.3, 1.3], font=9.5, row_h=0.3, align_right=(1, 2))
tf = txbox(s, MARGIN, 5.6, 5.9, 1.2)
para(tf, 'Text similarity and evidence quality dominate; the three raw distance features and five '
         'corroboration/source features contribute no gain (constant at training).', size=10,
     italic=True, color=NAVY, first=True)
pic(s, f'{FIG}/fig_importance.png', 6.9, 1.6, 5.85, 'Figure 5. Feature gain (log scale).')
notes(s, 'Table 19 + Figure 5 of the report.')

# =========================================================================
# Slide 14 — Head-to-head
# =========================================================================
s = slide_new()
header(s, 'Section 7', 'Model Evaluation: Head-to-Head (n = 66)')
footer(s)
make_table(s, MARGIN, 1.3, BODY_W, [
    ['Metric', 'Commercial baseline', 'Weighted visit centroid', 'Change'],
    ['Median error (m)', '380.8', '204.4', '\u221246.3%'],
    ['P90 / P95 error (m)', '745.6 / 1,176.9', '639.2 / 797.1', '\u221214.3% / \u221232.3%'],
    ['Within 50 / 100 m', '4.5% / 9.1%', '27.3% / 37.9%', '+22.7 / +28.8 pts'],
    ['Within 250 m', '28.8%', '53.0%', '+24.2 pts'],
    ['Within 500 m', '71.2%', '78.8%', '+7.6 pts'],
    ['Radius coverage (error \u2264 radius)', '\u2014', '72.7%', '\u2014'],
    ['Latency (ms / prediction)', '\u2014', '3.31', '\u2014'],
], [4.6, 2.7, 3.0, 1.93], font=9.5, row_h=0.34, align_right=(1, 2, 3))
pic(s, f'{FIG}/fig_comparison_wide.png', 0.85, 4.2, 11.6,
    'Figure 6. Error percentiles (left) and share within each threshold (right).',
    max_h=2.25, box_w=11.6)
notes(s, 'Table 20 + Figure 6. 48/66 addresses use visit evidence; 18 fall back to the geocode.')

# =========================================================================
# Slide 15 — Calibration
# =========================================================================
s = slide_new()
header(s, 'Section 7', 'Uncertainty Coverage and Calibration')
footer(s)
make_table(s, MARGIN, 1.45, 5.9, [
    ['Bin', 'Mean predicted', 'Empirical \u2264 250 m', 'n'],
    ['0.5 \u2013 0.6', '0.500', '0.302', '43'],
    ['0.8 \u2013 0.9', '0.880', '0.667', '3'],
    ['0.9 \u2013 1.0', '0.946', '1.000', '20'],
], [1.7, 1.6, 1.7, 0.9], font=10, row_h=0.34, align_right=(1, 2, 3))
tf = txbox(s, MARGIN, 3.2, 5.9, 3.5)
bullet(tf, 'ECE = 0.155 on 66 predictions; radius coverage 72.7%', size=11, first=True, space_after=6)
bullet(tf, 'High-confidence bin (radius \u2264 100 m): 20/20 correct within 250 m', size=11, space_after=6)
bullet(tf, 'Middle bin over-confident (0.50 predicted vs 0.30 observed) \u2192 default verify_first; '
           'recalibrate on held-out data before pilot thresholds', size=11, space_after=6)
bullet(tf, 'Coverage is reported with accuracy: the 27% without visit history get the geocode '
           'fallback, not silence', size=11)
pic(s, f'{FIG}/fig_03_cell15.png', 7.1, 1.7, 4.7,
    'Figure 7. Predicted confidence vs empirical within-250 m accuracy.')
notes(s, 'Table 21 + Figure 7 of the report.')

# =========================================================================
# Slide 16 — Insights 1-4
# =========================================================================
s = slide_new()
header(s, 'Section 8', 'Key Insights (1\u20134)')
footer(s)
ins1 = [
    ('1. The baseline fails for linguistic, not geographic, reasons.',
     'Within-250 m share tracks address style: T1 karnataka 25.0% vs T2 hindi 33.3% \u2014 the pipeline '
     'invests in normalisation and entity resolution, not locale tuning.'),
    ('2. Dwell is the evidence discriminator; GPS accuracy is the filter.',
     'Median dwell 876 s (met_borrower) vs 78 s (not_traceable) \u2014 11\u00d7; accuracy moves only '
     '9.1\u201310.9 m. The weight (1/acc) \u00d7 dwell/300 encodes exactly this.'),
    ('3. Visit history already contains the location the geocoder is missing.',
     'A single deterministic weighted centroid cuts median error 46.3% \u2014 the learned ranker refines '
     'the signal, it does not replace it.'),
    ('4. The hard 27% define the fallback contract.',
     '18/66 addresses have no usable successful visit \u2192 geocode + 500 m radius. Coverage and '
     'accuracy are reported together, always.'),
]
tf = txbox(s, MARGIN, 1.4, BODY_W, 5.5)
for i, (t, b) in enumerate(ins1):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.space_before = Pt(0 if i == 0 else 8)
    p.space_after = Pt(3)
    _set_run(p.add_run(), t, 12, True, NAVY)
    p2 = tf.add_paragraph()
    p2.space_after = Pt(6)
    _set_run(p2.add_run(), b, 10.5, False, TEXT)
notes(s, 'Insights 1\u20134 of Section 8.')

# =========================================================================
# Slide 17 — Insights 5-8
# =========================================================================
s = slide_new()
header(s, 'Section 8', 'Key Insights (5\u20138)')
footer(s)
ins2 = [
    ('5. Confidence is bimodal: near-perfect at the top, over-confident in the middle.',
     '20/20 correct in the 0.9\u20131.0 bin; 0.50 predicted vs 0.30 observed in the middle \u2192 '
     'govern thresholds: auto-route only above the calibrated bar.'),
    ('6. The ranker is evidence-driven, not proximity-driven.',
     'Top gains: address_similarity 816.8, gps_accuracy 404.0, visit_integrity 365.1, '
     'supporting visits 346.1; all raw distance features zero gain.'),
    ('7. The data is structurally clean enough to evaluate losslessly.',
     '0 orphans, 0 duplicate keys \u2192 every baseline is evaluated on the identical 66 addresses.'),
    ('8. Causal claims are withheld by design, and that is measurable.',
     'No treatment arm, no independent recovery outcome \u2192 the artifact returns not_estimable '
     'as a first-class, hash-pinned status.'),
]
tf = txbox(s, MARGIN, 1.4, BODY_W, 5.5)
for i, (t, b) in enumerate(ins2):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.space_before = Pt(0 if i == 0 else 8)
    p.space_after = Pt(3)
    _set_run(p.add_run(), t, 12, True, NAVY)
    p2 = tf.add_paragraph()
    p2.space_after = Pt(6)
    _set_run(p2.add_run(), b, 10.5, False, TEXT)
notes(s, 'Insights 5\u20138 of Section 8.')

# =========================================================================
# Slide 18 — Evaluation framework
# =========================================================================
s = slide_new()
header(s, 'Section 9', 'Evaluation Framework and Reproducibility')
footer(s)
tf = txbox(s, MARGIN, 1.4, 6.6, 5.5)
bullet(tf, 'Versioned JSON artifact per run: run ID, artifact version, split, SHA-256 input '
           'hashes, baselines, ablations, split metadata, radar, causal status', size=10.5,
       first=True, space_after=6)
bullet(tf, 'Ablations: address-only / +visits / +integrity / +nearby (not_estimable without an '
           'independent nearby table \u2014 never silently substituted)', size=10.5, space_after=6)
bullet(tf, 'Radar: 6 axes, explicitly labelled baseline_coverage until a frozen model scores '
           'held-out data', size=10.5, space_after=6)
bullet(tf, 'Temporal split: pre-cutoff visits only; geography holdout: held-out town, '
           'train-town retrain before scoring; account-level split: disjoint-ID assertion',
       size=10.5, space_after=6)
bullet(tf, 'Runner: python -m evaluation.ps3_experiments Dataset --split train', size=10.5)
codebox(s, 7.5, 1.6, 5.28, 2.5, [
    '{',
    '  "status": "not_estimable",',
    '  "estimand": "policy value /',
    '    treatment effect",',
    '  "required_columns": [',
    '    "treatment/action/policy_arm",',
    '    "recovery outcome",',
    '    "pre-treatment covariates"',
    '  ]',
    '}',
], size=10)
tf = txbox(s, 7.5, 4.35, 5.28, 2.3)
para(tf, 'Counterfactual policy evaluation (IPW / doubly robust) is deliberately not computable '
         'from the supplied files. This is a feature \u2014 a pilot must record policy arm, '
         'covariates, recovery and cost before any causal claim.', size=10.5, italic=True,
     color=NAVY, first=True)
notes(s, 'Section 9 of the report.')

# =========================================================================
# Slide 19 — Security & compliance
# =========================================================================
s = slide_new()
header(s, 'Section 10', 'Security, RBAC and Compliance')
footer(s)
tf = txbox(s, MARGIN, 1.5, 6.0, 5.3)
para(tf, 'Role-based access control', size=13, bold=True, color=NAVY, first=True, space_after=5)
bullet(tf, 'Borrower locations, visit trails, agent GPS, remarks and territory metrics are '
           'sensitive operational data', size=10.5, space_after=5, first=True)
bullet(tf, 'Agents: own territory only \u00b7 managers: broader views \u00b7 auditors: evidence + audit '
           '\u00b7 admins: configuration', size=10.5, space_after=5)
bullet(tf, 'Retraining endpoint protected by backend RBAC \u2014 hiding the UI nav item is not the '
           'security boundary', size=10.5, space_after=5)
bullet(tf, 'Production: tenant + territory scoping at the data-query boundary, not only the UI',
       size=10.5, bold=True)
tf = txbox(s, 6.9, 1.5, BODY_W - (6.9 - MARGIN), 5.3)
para(tf, 'RBI and DPDP boundaries', size=13, bold=True, color=NAVY, first=True, space_after=5)
bullet(tf, 'Per-deployment configuration and audit: contact hours and frequency', size=10.5,
       space_after=5, first=True)
bullet(tf, 'Consent and purpose limitation; retention and deletion windows', size=10.5, space_after=5)
bullet(tf, 'Access logging and export controls; separation of collections data from unrelated uses',
       size=10.5, space_after=5)
bullet(tf, 'Agent-monitoring governance; incident response and correction workflows', size=10.5,
       space_after=5)
bullet(tf, 'The geocoder must not infer locations beyond what collections requires', size=10.5,
       bold=True)
notes(s, 'Section 10 of the report.')

# =========================================================================
# Slide 20 — Deployment plan
# =========================================================================
s = slide_new()
header(s, 'Section 11', 'Deployment Plan')
footer(s)
phases = [
    ('Phase 1 \u2014 Shadow mode', [
        'ingest evidence without changing planner decisions',
        'measure error, coverage, calibration',
        'review integrity alerts with field managers',
    ]),
    ('Phase 2 \u2014 Controlled pilot', [
        'comparable territories; frozen model version',
        'record action assignment + recovery outcomes',
        'productive visits/agent-day; cost per recovery',
    ]),
    ('Phase 3 \u2014 Guarded rollout', [
        'direct visits only above calibrated thresholds',
        'low confidence \u2192 verification route',
        'rollback path to incumbent planner',
    ]),
    ('Phase 4 \u2014 Continuous governance', [
        'version data / model / config / artifacts',
        'rerun temporal + geography holdouts',
        'recalibrate; retention-driven deletion; audits',
    ]),
]
bw, bh = 6.0, 2.55
pos = [(MARGIN, 1.45), (MARGIN + bw + 0.23, 1.45), (MARGIN, 1.45 + bh + 0.2),
       (MARGIN + bw + 0.23, 1.45 + bh + 0.2)]
for (title, items), (x, y) in zip(phases, pos):
    rect(s, x, y, bw, bh, LIGHT)
    tf = txbox(s, x + 0.18, y + 0.12, bw - 0.36, 0.4)
    para(tf, title, size=12.5, bold=True, color=NAVY, first=True, space_after=0)
    tf = txbox(s, x + 0.18, y + 0.58, bw - 0.36, bh - 0.7)
    for i, it in enumerate(items):
        bullet(tf, it, size=10, space_after=4, first=(i == 0))
notes(s, 'Four-phase rollout from shadow mode to continuous governance.')

# =========================================================================
# Slide 21 — Limitations
# =========================================================================
s = slide_new()
header(s, 'Section 12', 'Known Limitations and Next Engineering Work')
footer(s)
lims_l = [
    'Planner: distance-aware prioritiser, not yet a travel-time/cost route optimiser',
    'PS3 dataset cannot support a causal policy-value estimate',
    'Nearby-account ablation needs an independent evidence table',
    'Geography holdout requires train-town-only retraining before scoring',
    'Held-out account partition should be scored separately by the full harness',
]
lims_r = [
    'Remark-to-offset extraction stays conservative by design',
    'Cluster propagation needs lender-specific scale thresholds',
    'Offline: dead-letter exists; conflict resolution + idempotency need hardening',
    'Tenant/territory filtering must be enforced in repository queries',
    'Full notebook execution needs backend notebook dependencies',
]
tf = txbox(s, MARGIN, 1.6, 6.0, 5.2)
for i, t in enumerate(lims_l):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.space_after = Pt(8)
    _set_run(p.add_run(), f'{i+1}.  ', 11, True, ACCENT)
    _set_run(p.add_run(), t, 10.5)
tf = txbox(s, 6.9, 1.6, BODY_W - (6.9 - MARGIN), 5.2)
for i, t in enumerate(lims_r):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.space_after = Pt(8)
    _set_run(p.add_run(), f'{i+6}.  ', 11, True, ACCENT)
    _set_run(p.add_run(), t, 10.5)
notes(s, 'Ten limitations, verbatim in substance from Section 12 of the report.')

# =========================================================================
# Slide 22 — Deliverables
# =========================================================================
s = slide_new()
header(s, 'Section 13', 'PS3 Deliverables and Evidence')
footer(s)
make_table(s, MARGIN, 1.4, BODY_W, [
    ['#', 'Deliverable', 'Location', 'Evidence'],
    ['1', 'EDA + evaluation notebook', 'PS3_Geocoder_EDA.ipynb', '22 cells; syntax-validated; embedded ranker; artifact writer'],
    ['2', 'Trained ranker model', 'Embedded base64 in notebook', '150 trees, 21 features, account-level 80/20 split (Sec. 6)'],
    ['3', 'Versioned evaluation artifact', 'ps3_notebook_train.json / ps3_eval_<run_id>.json', 'SHA-256 hashes, run ID, ablations, splits, causal status (Sec. 9)'],
    ['4', 'Backend geocoder service', 'Project backend', 'Planner, PS2 RPC, account search, admin retraining, RBAC (Sec. 6.8)'],
    ['5', 'Frontend field app + dashboards', 'Project frontend', 'Pin + radius + evidence, offline queue, WGS84-only maps rule (Sec. 6.8)'],
    ['6', 'Solution documentation', 'PS3_PROBLEM_SOLUTION_REPORT.md', 'Problem\u2013solution mapping, deployment plan, checklist'],
    ['7', 'This report + deck', 'PS3_Report.pdf / PS3_Report.pptx', 'Findings, architecture, evidence, delivery status'],
], [0.45, 2.7, 3.2, 5.88], font=9.5, row_h=0.52, align_right=(0,))
notes(s, 'Table 22 of the report. Acceptance checklist (Table 23): 1 of 16 items satisfied pre-pilot \u2014 ranker disjoint-ID assertion.')

# =========================================================================
# Slide 23 — Conclusion
# =========================================================================
s = slide_new()
header(s, 'Section 14', 'Conclusion')
footer(s)
tf = txbox(s, MARGIN, 1.5, BODY_W, 3.6)
bullet(tf, 'An evidence-learning geocoder, not a generic lookup: normalisation \u2192 entities \u2192 '
           'five-source candidates \u2192 reliability weighting \u2192 150-tree LightGBM ranker \u2192 '
           'uncertainty-driven action', size=12, first=True, space_after=8)
bullet(tf, 'Measured: median error 204.4 m vs 380.8 m (\u221246.3%), within-250 m 53.0% vs 28.8%, '
           '72.7% radius coverage, ECE 0.155, 3.3 ms per prediction \u2014 all reproducible from the '
           'SHA-256-pinned artifact', size=12, space_after=8)
bullet(tf, 'Where it is strong: high-confidence predictions (20/20) and evidence-rich accounts. '
           'Where it stays honest: the uncertain middle band, the 27% without visit history, and '
           'causal claims the data cannot support', size=12, space_after=8)
bullet(tf, 'Ready for Phase 1 shadow mode behind a real collections operation \u2014 that discipline, '
           'not a single number, is the delivery claim', size=12, bold=True, color=NAVY)
rect(s, MARGIN, 5.35, BODY_W, 1.15, LIGHT)
tf = txbox(s, MARGIN + 0.25, 5.5, BODY_W - 0.5, 0.9)
para(tf, 'Thank you \u2014 questions on the model, the evaluation boundary, or the rollout plan '
         'are welcome.', size=13, italic=True, color=NAVY, align=PP_ALIGN.CENTER, first=True)
notes(s, 'Closing slide.')

prs.save(OUT)
print('wrote', OUT, '| slides:', len(prs.slides._sldIdLst))
