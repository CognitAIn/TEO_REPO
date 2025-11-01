import os, json, tkinter as tk
from tkinter import ttk

APP_PATH = os.path.dirname(__file__)
CFG_PATH = os.path.join(APP_PATH, "ui_config.json")

def load_cfg():
    if os.path.exists(CFG_PATH):
        with open(CFG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"theme": "dark", "window": [720, 480]}

def save_cfg(cfg):
    with open(CFG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

cfg = load_cfg()
root = tk.Tk()
root.title("Trinity Control Panel")
root.geometry(f"{cfg['window'][0]}x{cfg['window'][1]}")
root.resizable(True, True)

bg = "#101010" if cfg["theme"] == "dark" else "#f0f0f0"
root.configure(bg=bg)

status = tk.StringVar(value="Ready.")
ttk.Label(root, textvariable=status).pack(pady=5)

def open_perf_panel():
    os.system(f'python "{os.path.join(APP_PATH, "performance_mode.py")}"')

def rescan_files():
    os.system(f'python "{os.path.join(APP_PATH, "always_on_index.py")}"')
    status.set("Rescan complete.")

btn_frame = ttk.Frame(root)
btn_frame.pack(pady=15)
ttk.Button(btn_frame, text="Performance Modes", command=open_perf_panel).grid(row=0, column=0, padx=6)
ttk.Button(btn_frame, text="Rebuild Cache", command=rescan_files).grid(row=0, column=1, padx=6)
ttk.Button(btn_frame, text="Exit", command=root.destroy).grid(row=0, column=2, padx=6)

root.mainloop()
