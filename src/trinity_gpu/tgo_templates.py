import json, os
from datetime import datetime

# === Trinity GPU Template Library ===
# These templates define default tuning parameters for various GPU classes.
# Adjust as needed after initial probe runs (Phase 8/10).

TEMPLATES = {
    "integrated_gpu": {
        "description": "Shared memory / low power iGPU (e.g., Intel UHD, Vega iGPU)",
        "heat_coeff": 0.045,
        "cool_coeff": 0.085,
        "target_duty": 0.65,
        "max_duty": 0.75,
        "safe_temp": 72.0
    },
    "mobile_discrete_gpu": {
        "description": "Laptop-class dGPU (e.g., RTX 3050M, RX 6600M)",
        "heat_coeff": 0.035,
        "cool_coeff": 0.07,
        "target_duty": 0.8,
        "max_duty": 0.9,
        "safe_temp": 82.0
    },
    "desktop_discrete_gpu": {
        "description": "Desktop-class dGPU (e.g., RTX 4070, RX 7900)",
        "heat_coeff": 0.025,
        "cool_coeff": 0.05,
        "target_duty": 0.88,
        "max_duty": 0.95,
        "safe_temp": 85.0
    }
}

def export_templates(outdir="."):
    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "templates": TEMPLATES
    }
    outfile = os.path.join(outdir, "tgo_phase11_templates.json")
    with open(outfile, "w") as f:
        json.dump(data, f, indent=4)
    print(f"[TGO Templates] Saved template library: {outfile}")
    return outfile

if __name__ == "__main__":
    outdir = os.environ.get("TGO_OUTDIR", ".")
    export_templates(outdir)
