import os, subprocess, psutil, tkinter as tk
from tkinter import ttk

APP_PATH = os.path.dirname(__file__)
ICON_PATH = os.path.join(APP_PATH, 'Trinity_Logo.ico')
TGO_PROC = ['always_on_index.py', 'performance_mode.py']

def find_processes():
    active = []
    for p in psutil.process_iter(['cmdline']):
        try:
            cmd = p.info['cmdline']
            if cmd and any(f in ' '.join(cmd) for f in TGO_PROC):
                active.append(p)
        except Exception:
            pass
    return active

def toggle_tgo():
    procs = find_processes()
    if procs:
        # Turn OFF
        for p in procs:
            try: p.terminate()
            except: pass
        status.set('OFF')
        btn.configure(text='Turn ON', style='On.TButton')
    else:
        # Turn ON
        subprocess.Popen(['python', os.path.join(APP_PATH, 'always_on_index.py')])
        subprocess.Popen(['python', os.path.join(APP_PATH, 'performance_mode.py')])
        status.set('ON')
        btn.configure(text='Turn OFF', style='Off.TButton')

root = tk.Tk()
root.title('TGO Controller')
root.geometry('280x140')
root.resizable(False, False)

# Attach your Trinity logo as icon
if os.path.exists(ICON_PATH):
    try:
        root.iconbitmap(ICON_PATH)
    except Exception as e:
        print(f'Icon load error: {e}')

style = ttk.Style(root)
style.configure('On.TButton', font=('Segoe UI', 11), padding=8)
style.configure('Off.TButton', font=('Segoe UI', 11), padding=8)

status = tk.StringVar(value='ON' if find_processes() else 'OFF')
btn_text = 'Turn OFF' if status.get() == 'ON' else 'Turn ON'

btn = ttk.Button(root, text=btn_text, style=('Off.TButton' if status.get() == 'ON' else 'On.TButton'),
                 command=toggle_tgo)
btn.pack(pady=25)

ttk.Label(root, textvariable=status, font=('Segoe UI', 12)).pack()
root.mainloop()
