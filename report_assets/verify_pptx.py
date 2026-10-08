"""Verify PS3_Report.pptx: no shape off-slide, text fits boxes, tables fit space.

Wrapping is estimated with DejaVu Serif (wider than Times New Roman), so any
overflow reported here would also overflow in PowerPoint; clean result means
the deck is safe.
"""
from PIL import ImageFont
from pptx import Presentation
from pptx.util import Emu

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'
FONT_B = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
EMU_IN = 914400
# cache: (bold, pt*4) -> ImageFont
_cache = {}

def _font(bold, pt):
    key = (bold, int(pt * 4))
    if key not in _cache:
        _cache[key] = ImageFont.truetype(FONT_B if bold else FONT, max(8, int(pt * 4)))
    return _cache[key]

def _w(font, s):
    return font.getlength(s) / 4.0  # back to pt (rendered at 4x)

def wrap_lines(text, bold, pt, avail_pt):
    """Greedy word wrap; returns number of lines (min 1)."""
    if not text:
        return 1
    f = _font(bold, pt)
    words, lines, cur = text.split(), 1, ''
    for w in words:
        trial = (cur + ' ' + w).strip()
        if _w(f, trial) <= avail_pt or not cur:
            cur = trial
        else:
            lines += 1
            cur = w
    return lines

def para_metrics(p):
    """Return (text, pt, bold, space_after_pt)."""
    text = ''.join(r.text for r in p.runs)
    if not p.runs:
        return (text, 12, False, 0)
    pt = max(r.font.size.pt if r.font.size else 12 for r in p.runs)
    bold = any(r.font.bold for r in p.runs)
    sa = p.space_after.pt if p.space_after else 0
    return (text, pt, bold, sa)

def text_height_pt(tf, avail_w_pt):
    total = 0.0
    for p in tf.paragraphs:
        text, pt, bold, sa = para_metrics(p)
        n = wrap_lines(text, bold, pt, avail_w_pt)
        total += n * pt * 1.25 + sa
    return total

def check_shapes(prs, slide, issues):
    sw, sh = prs.slide_width / EMU_IN, prs.slide_height / EMU_IN
    for shp in slide.shapes:
        try:
            l, t, w, h = (shp.left / EMU_IN, shp.top / EMU_IN,
                          shp.width / EMU_IN, shp.height / EMU_IN)
        except TypeError:
            continue
        if l < -0.01 or t < -0.01 or l + w > sw + 0.01 or t + h > sh + 0.01:
            issues.append(f'  OFF-SLIDE: {shp.shape_type} "{getattr(shp, "name", "?")}" '
                          f'at ({l:.2f},{t:.2f}) size ({w:.2f}x{h:.2f})')
        if shp.has_text_frame and shp.text_frame.text.strip():
            tf = shp.text_frame
            inset = (tf.margin_left or 91440) / EMU_IN + (tf.margin_right or 91440) / EMU_IN
            avail_w_pt = max(20.0, (w - inset) * 72)
            top_inset = (tf.margin_top or 45720) / EMU_IN
            need = text_height_pt(tf, avail_w_pt) / 72.0 + top_inset + 0.03
            if need > h + 0.02:
                snippet = tf.text[:48].replace('\n', ' ')
                issues.append(f'  TEXT OVERFLOW: box "{snippet}…" needs {need:.2f}in > {h:.2f}in '
                              f'(at {l:.2f},{t:.2f})')
        if shp.has_table:
            tbl = shp.table
            # sum of minimum row heights
            min_total = sum(r.height / EMU_IN for r in tbl.rows)
            if t + min_total > sh + 0.02:
                issues.append(f'  TABLE MIN-HEIGHT overflow: needs {min_total:.2f}in from top '
                              f'{t:.2f}in, slide is {sh:.2f}in')
            # estimate row growth from cell text wrapping (cell width = column width)
            col_w = [c.width / EMU_IN for c in tbl.columns]
            total = 0.0
            for row in tbl.rows:
                row_need = row.height / EMU_IN
                for ci, cell in enumerate(row.cells):
                    cw = (col_w[ci] - 0.18) * 72  # cell L/R margins
                    ch = text_height_pt(cell.text_frame, max(20.0, cw)) / 72.0 + 0.12
                    row_need = max(row_need, ch)
                total += row_need
            if t + total > sh + 0.05:
                issues.append(f'  TABLE GROWN overflow: est {total:.2f}in from top {t:.2f}in '
                              f'(bottom {t + total:.2f}in) vs slide {sh:.2f}in')

def main():
    prs = Presentation('/home/user/PS3_ADI/PS3_Report.pptx')
    slides = list(prs.slides)
    print(f'slides: {len(slides)}')
    problems = 0
    for i, s in enumerate(slides, 1):
        issues = []
        check_shapes(prs, s, issues)
        if issues:
            problems += 1
            print(f'slide {i}: {len(issues)} issue(s)')
            print('\n'.join(issues))
    print('CLEAN' if problems == 0 else f'{problems} slide(s) with issues')

if __name__ == '__main__':
    main()
