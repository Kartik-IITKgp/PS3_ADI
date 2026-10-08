"""Generate the three additional report figures in the notebook's seaborn whitegrid style."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

sns.set_theme(style='whitegrid')
OUT = '/home/user/PS3_ADI/report_assets/figures'
W = 6.27  # inches, matches report text width
DPI = 200

# ---------------------------------------------------------------- baseline vs weighted
fig, axes = plt.subplots(1, 2, figsize=(W, 2.9))

labels = ['Median', 'P90', 'P95']
base_err = [380.755842, 745.589665, 1176.861491]
wgt_err = [204.436755, 639.160780, 797.103753]
x = np.arange(len(labels)); w = 0.36
axes[0].bar(x - w / 2, base_err, w, label='Commercial baseline', color='#4C72B0')
axes[0].bar(x + w / 2, wgt_err, w, label='Weighted visit centroid', color='#DD8452')
axes[0].set_xticks(x); axes[0].set_xticklabels(labels)
axes[0].set_ylabel('Error (projected metres)')
axes[0].set_title('Location error by percentile')
axes[0].legend(fontsize=8, frameon=True)
for i, (b, g) in enumerate(zip(base_err, wgt_err)):
    axes[0].text(i - w / 2, b + 18, f'{b:.0f}', ha='center', fontsize=7)
    axes[0].text(i + w / 2, g + 18, f'{g:.0f}', ha='center', fontsize=7)

thr = ['50 m', '100 m', '250 m', '500 m']
base_w = [4.55, 9.09, 28.79, 71.21]
wgt_w = [27.27, 37.88, 53.03, 78.79]
x = np.arange(len(thr))
axes[1].bar(x - w / 2, base_w, w, label='Commercial baseline', color='#4C72B0')
axes[1].bar(x + w / 2, wgt_w, w, label='Weighted visit centroid', color='#DD8452')
axes[1].set_xticks(x); axes[1].set_xticklabels(thr)
axes[1].set_ylabel('Share of 66 surveyed addresses (%)')
axes[1].set_title('Share within threshold')
axes[1].legend(fontsize=8, frameon=True)
for i, (b, g) in enumerate(zip(base_w, wgt_w)):
    axes[1].text(i - w / 2, b + 1.2, f'{b:.1f}', ha='center', fontsize=7)
    axes[1].text(i + w / 2, g + 1.2, f'{g:.1f}', ha='center', fontsize=7)
plt.tight_layout()
plt.savefig(f'{OUT}/fig_comparison.png', dpi=DPI, bbox_inches='tight')
plt.close(fig)

# --------------------------------------------- wide variant for the PowerPoint
fig, axes = plt.subplots(1, 2, figsize=(11.0, 2.9))
x = np.arange(len(labels))
axes[0].bar(x - w / 2, base_err, w, label='Commercial baseline', color='#4C72B0')
axes[0].bar(x + w / 2, wgt_err, w, label='Weighted visit centroid', color='#DD8452')
axes[0].set_xticks(x); axes[0].set_xticklabels(labels)
axes[0].set_ylabel('Error (projected metres)')
axes[0].set_title('Location error by percentile')
axes[0].legend(fontsize=8, frameon=True)
for i, (b, g) in enumerate(zip(base_err, wgt_err)):
    axes[0].text(i - w / 2, b + 18, f'{b:.0f}', ha='center', fontsize=7)
    axes[0].text(i + w / 2, g + 18, f'{g:.0f}', ha='center', fontsize=7)
x = np.arange(len(thr))
axes[1].bar(x - w / 2, base_w, w, label='Commercial baseline', color='#4C72B0')
axes[1].bar(x + w / 2, wgt_w, w, label='Weighted visit centroid', color='#DD8452')
axes[1].set_xticks(x); axes[1].set_xticklabels(thr)
axes[1].set_ylabel('Share of 66 surveyed addresses (%)')
axes[1].set_title('Share within threshold')
axes[1].legend(fontsize=8, frameon=True)
for i, (b, g) in enumerate(zip(base_w, wgt_w)):
    axes[1].text(i - w / 2, b + 1.2, f'{b:.1f}', ha='center', fontsize=7)
    axes[1].text(i + w / 2, g + 1.2, f'{g:.1f}', ha='center', fontsize=7)
plt.tight_layout()
plt.savefig(f'{OUT}/fig_comparison_wide.png', dpi=DPI, bbox_inches='tight')
plt.close(fig)

# ---------------------------------------------------------------- outcomes
outcomes = {
    'address_not_traceable': 957, 'locked_premises': 901, 'met_borrower': 766,
    'met_family': 730, 'neighbour_says_shifted': 332, 'no_such_person': 151,
    'cash_collected': 59,
}
fig, ax = plt.subplots(figsize=(W, 2.7))
names = list(outcomes.keys()); vals = list(outcomes.values())
colors = ['#DD8452' if n in ('met_borrower', 'met_family', 'cash_collected') else '#4C72B0' for n in names]
ax.barh(names[::-1], vals[::-1], color=colors[::-1])
ax.set_xlabel('Visits')
ax.set_title('Field-visit outcome distribution (n = 3,896)')
for i, v in enumerate(vals[::-1]):
    ax.text(v + 8, i, str(v), va='center', fontsize=8)
plt.tight_layout()
plt.savefig(f'{OUT}/fig_outcomes.png', dpi=DPI, bbox_inches='tight')
plt.close(fig)

# ---------------------------------------------------------------- feature importance
feats = [
    ('address_similarity', 8.168053e+02, 181),
    ('gps_accuracy', 4.040447e+02, 74),
    ('visit_integrity', 3.650561e+02, 38),
    ('number_of_supporting_visits', 3.460824e+02, 39),
    ('locality_similarity', 1.294731e+02, 105),
    ('landmark_similarity', 1.092850e+02, 26),
    ('weighted_successful_visit_count', 8.250420e+01, 14),
    ('source_locality', 3.609319e+01, 12),
    ('source_geocoder', 4.267115e+00, 13),
    ('agent_independence', 2.405553e+00, 4),
    ('source_pincode', 1.086018e+00, 4),
    ('trajectory_quality', 6.687914e-02, 2),
]
feats = feats[::-1]
fig, ax = plt.subplots(figsize=(W, 3.4))
names = [f[0] for f in feats]; gains = [f[1] for f in feats]
bars = ax.barh(names, gains, color='#4C72B0')
ax.set_xscale('log')
ax.set_xlabel('Gain (log scale)')
ax.set_title('Ranker feature importance (LightGBM, 150 trees)')
for i, g in enumerate(gains):
    ax.text(g * 1.06, i, f'{g:,.1f}', va='center', fontsize=8)
ax.set_xlim(1e-2, 1e4)
plt.tight_layout()
plt.savefig(f'{OUT}/fig_importance.png', dpi=DPI, bbox_inches='tight')
plt.close(fig)

print('figures written')
