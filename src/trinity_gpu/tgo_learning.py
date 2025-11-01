import os, json, glob, numpy as np, pandas as pd, matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from datetime import datetime

def load_all_phase_data(root="benchmarks"):
    files = sorted(glob.glob(os.path.join(root, "**", "tgo_phase*_predictive.json"), recursive=True))
    data = []
    for f in files:
        try:
            with open(f, "r") as fh:
                j = json.load(fh)
            data.append({
                "file": os.path.basename(f),
                "timestamp": j.get("timestamp"),
                "cpu_avg": j.get("cpu_avg", 0),
                "mem_avg": j.get("mem_avg", 0),
                "duty_mean": j.get("duty_mean", 0)
            })
        except Exception as e:
            print(f"[warn] skipping {f}: {e}")
    return pd.DataFrame(data)

def learn_curve(df):
    if len(df) < 2:
        return None, None
    X = df[["cpu_avg","mem_avg"]].values
    y = df["duty_mean"].values
    model = LinearRegression().fit(X, y)
    return model, model.score(X, y)

if __name__ == "__main__":
    root = os.path.join(os.getcwd(), "benchmarks")
    outdir = os.environ.get("TGO_OUTDIR", ".")
    df = load_all_phase_data(root)
    if df.empty:
        print("[TGO Learning] No predictive data found.")
        exit()

    model, r2 = learn_curve(df)
    coeffs = dict(zip(["cpu_avg","mem_avg"], model.coef_)) if model else {}
    baseline = float(model.intercept_) if model else 0.0

    result = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "samples": len(df),
        "r2": r2 if r2 is not None else "n/a",
        "coefficients": coeffs,
        "baseline": baseline,
        "data": df.to_dict(orient="records")
    }

    os.makedirs(outdir, exist_ok=True)
    outfile = os.path.join(outdir, "tgo_phase5_learning.json")
    with open(outfile, "w") as f: json.dump(result, f, indent=4)
    print(f"[TGO Learning] Model saved: {outfile}")

    plt.figure(figsize=(8,6))
    plt.scatter(df["cpu_avg"], df["duty_mean"], c='b', label="CPU vs Duty")
    plt.scatter(df["mem_avg"], df["duty_mean"], c='g', label="MEM vs Duty")
    if model:
        grid = np.linspace(df["cpu_avg"].min(), df["cpu_avg"].max(), 50)
        pred = model.predict(np.column_stack([grid, np.full_like(grid, df["mem_avg"].mean())]))
        plt.plot(grid, pred, color='r', linewidth=2, label="Regression Fit")
    plt.title(f"Trinity Learning Curve (R²={r2 if r2 is not None else 0:.3f})")
    plt.xlabel("Avg CPU %")
    plt.ylabel("Mean Duty")
    plt.legend(); plt.grid(True, linestyle="--", alpha=0.4)
    img_path = os.path.join(outdir, "tgo_phase5_learning_plot.png")
    plt.tight_layout(); plt.savefig(img_path)
    print(f"[TGO Learning] Plot saved: {img_path}")
