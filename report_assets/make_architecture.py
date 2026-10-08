"""Architecture diagram for the PS3 report (themed to match the report palette)."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

PRIMARY = '#1F3864'
ACCENT = '#2E74B5'
LIGHT = '#DEEAF6'
ZEBRA = '#F2F6FB'
MUTED = '#595959'

fig, ax = plt.subplots(figsize=(6.27, 3.9), dpi=200)
ax.set_xlim(0, 100)
ax.set_ylim(0, 52)
ax.axis('off')

def box(x, y, w, h, text, fc, tc, fs=7.2, bold=False, ec='#8EAADB'):
    p = FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.6,rounding_size=1.2',
                       fc=fc, ec=ec, lw=0.8)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha='center', va='center',
            fontsize=fs, color=tc,
            fontweight='bold' if bold else 'normal', linespacing=1.4)

def arrow(p1, p2, color=MUTED, lw=1.1):
    a = FancyArrowPatch(p1, p2, arrowstyle='-|>', mutation_scale=9,
                        color=color, lw=lw, shrinkA=1.5, shrinkB=1.5)
    ax.add_patch(a)

# --- inputs (top)
inputs = [
    (1.5,  'Raw address text\n(multilingual)'),
    (21.5, 'Landmarks\n& POI'),
    (41.5, 'Localities\n& towns'),
    (61.5, 'Field visits\n+ GPS trails'),
    (81.5, 'Confirmed account\nlocations'),
]
for x, t in inputs:
    box(x, 44, 17, 6.5, t, ZEBRA, PRIMARY, fs=7.2)

# --- stage row
stages = [
    (0.5,   'Normalisation', 'Unicode, spacing,\nabbreviations'),
    (21.0,  'Entity extraction', 'house, road,\nlandmark, relation'),
    (41.5,  'Candidate\n generation', '5 evidence sources'),
    (62.0,  'Evidence\n weighting', 'accuracy, dwell,\noutcome, integrity'),
    (82.5,  'LightGBM ranker', '150 trees,\n21 features'),
]
for x, t1, t2 in stages:
    box(x, 30, 17, 7.5, f'{t1}\n{t2}', PRIMARY, 'white', fs=6.9, bold=True)

# --- decision row
box(62.0, 15, 17, 7.5, 'Uncertainty\nradius +\nconfidence', ACCENT, 'white', fs=7.2, bold=True)
box(82.5, 15, 17, 7.5, 'Action decision\nvisit_directly /\nverify_first / skip', ACCENT, 'white', fs=6.9, bold=True)

# --- consumers (bottom)
consumers = [
    (0.5,   'Field app\noffline queue\n+ cache'),
    (21.0,  'Visit planner API\nconf, radius,\nsource'),
    (41.5,  'PS2 RPC\nlocation\nfeatures'),
    (62.0,  'Dashboards\nmeasured\nmetrics'),
    (82.5,  'Location fields\ncanonical, confirmed,\npredicted'),
]
for x, t in consumers:
    box(x, 1, 17, 7.5, t, LIGHT, PRIMARY, fs=7.0)

# --- arrows: inputs -> stages
arrow((10, 44), (9, 37.5))             # raw address -> normalisation
arrow((30, 44), (48, 37.5))            # landmarks -> candidate gen
arrow((50, 44), (50, 37.5))            # localities -> candidate gen
arrow((70, 44), (53, 37.5))            # visits -> candidate gen
arrow((90, 44), (55, 37.5))            # confirmed -> candidate gen
arrow((70, 44), (70.5, 37.5))          # visits -> weighting

# --- stage chain
arrow((17.5, 33.75), (21.0, 33.75))
arrow((38.0, 33.75), (41.5, 33.75))
arrow((58.5, 33.75), (62.0, 33.75))
arrow((79.0, 33.75), (82.5, 33.75))

# --- ranker -> uncertainty -> action
arrow((91, 30), (70.5, 22.5))
arrow((79.0, 18.75), (82.5, 18.75))

# --- action -> consumers (bus)
arrow((91, 15), (91, 11), lw=1.3, color=ACCENT)
ax.plot([9, 91], [11, 11], color=ACCENT, lw=1.3, solid_capstyle='round')
for x in (9, 29.5, 50, 70.5, 91):
    arrow((x, 11), (x, 8.5), lw=1.0, color=ACCENT)

plt.tight_layout(pad=0.2)
plt.savefig('/home/user/PS3_ADI/report_assets/figures/fig_architecture.png',
            dpi=200, bbox_inches='tight', facecolor='white')
print('architecture figure written')
