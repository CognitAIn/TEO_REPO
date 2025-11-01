import json, os, tkinter as tk
from tkinter import ttk

CONFIG_PATH = os.path.expanduser(r"~\\Desktop\\Trinity_STEM\\performance_config.json")

DEFAULTS = {
    "eco":     {"lambda": 1.5, "beta": 1.2, "desc": "Cool & silent — longest battery life"},
    "normal":  {"lambda": 1.0, "beta": 1.0, "desc": "Balanced operation"},
    "high":    {"lambda": 0.7, "beta": 0.6, "desc": "Maximum speed — higher power draw"}
}

def save_mode(mode):
    cfg = {"mode": mode, "weights": DEFAULTS[mode]}
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    status.set(f"Mode set to {mode.title()}  |  {DEFAULTS[mode]['desc']}")
    print(f"✅  Trinity mode updated: {mode}  (λ={DEFAULTS[mode]['lambda']}, β={DEFAULTS[mode]['beta']})")

def load_mode():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("mode", "normal")
        except Exception:
            return "normal"
    return "normal"

# --- UI ---
root = tk.Tk()
root.title("Trinity Performance Mode")
root.geometry("420x160")
root.resizable(False, False)

style = ttk.Style(root)
style.theme_use("clam")

current = tk.StringVar(value=load_mode())
status = tk.StringVar(value=f"Current mode: {current.get().title()}")

frm = ttk.LabelFrame(root, text="Select Trinity Mode", padding=10)
frm.pack(fill="both", expand=True, padx=10, pady=10)

for mode, info in DEFAULTS.items():
    ttk.Radiobutton(
        frm, text=f"{mode.title()}  –  {info['desc']}",
        variable=current, value=mode,
        command=lambda m=mode: save_mode(m)
    ).pack(anchor="w", pady=2)

ttk.Label(root, textvariable=status, foreground="#00cc66").pack(pady=5)
ttk.Button(root, text="Close", command=root.destroy).pack(pady=3)

root.mainloop()
