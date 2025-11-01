import json, matplotlib.pyplot as plt, numpy as np, os

# Load results
with open('benchmarks/results/delta1_vs_adam.json') as f:
    data = json.load(f)

# Extract metrics
labels = ['Error Variance', 'Abs. Error Mean', 'Output Std. Dev.']
dp1_vals = [data['Δ+1_controller']['error_var'], data['Δ+1_controller']['abs_error_mean'], data['Δ+1_controller']['output_std']]
adam_vals = [data['Adam_optimizer']['error_var'], data['Adam_optimizer']['abs_error_mean'], data['Adam_optimizer']['output_std']]

x = np.arange(len(labels))
width = 0.35

fig, ax = plt.subplots(figsize=(8,5))
bars1 = ax.bar(x - width/2, dp1_vals, width, label='Δ + 1 Controller', color='#00C853')
bars2 = ax.bar(x + width/2, adam_vals, width, label='Adam Optimizer', color='#D50000')

ax.set_ylabel('Metric Value')
ax.set_title('Δ + 1 vs Adam Comparative Benchmark')
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=15)
ax.legend()
ax.grid(axis='y', linestyle='--', alpha=0.6)

# Annotate bars
for bars in (bars1, bars2):
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height*1.01, f'{height:.3f}', ha='center', va='bottom', fontsize=8)

os.makedirs('benchmarks/results', exist_ok=True)
outfile = 'benchmarks/results/delta1_vs_adam_plot.png'
plt.tight_layout()
plt.savefig(outfile, dpi=300)
print(f"\n✅ Plot saved to {outfile}")
