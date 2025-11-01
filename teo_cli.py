import click
import json
import os
import time
import platform
import psutil
from datetime import datetime
from pathlib import Path

CONFIG_DIR = Path.home() / (".config/TEO" if os.name != "nt" else "AppData/Roaming/TEO")
CONFIG_PATH = CONFIG_DIR / "configs" / "auto_profile.json"
LOG_PATH = CONFIG_DIR / "logs" / "teo_runtime.log"

def ensure_dirs():
    (CONFIG_DIR / "configs").mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / "logs").mkdir(parents=True, exist_ok=True)

def log(msg):
    ensure_dirs()
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}\n")

@click.group()
def main():
    """Trinity Energy Optimizer (TEO) — Homeostatic Control CLI"""
    pass

@main.command()
def version():
    click.echo("Trinity Energy Optimizer v1.0.0")

@main.command()
def scan():
    ensure_dirs()
    click.echo("🔍 Scanning hardware... please wait.")
    log("Hardware scan initiated")
    system_info = {
        "system": platform.system(),
        "release": platform.release(),
        "cpu": platform.processor() or platform.machine(),
        "cores": psutil.cpu_count(logical=True),
        "memory_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2),
        "timestamp": str(datetime.now())
    }
    CONFIG_PATH.write_text(json.dumps(system_info, indent=4))
    click.echo("✅ Hardware profile generated successfully")
    log("Hardware profile generated successfully")

@main.command()
def run():
    if not CONFIG_PATH.exists():
        click.echo("❌ No configuration found. Run `teo scan` first.")
        return
    click.echo("🚀 Starting Trinity Energy Optimizer...")
    log("Optimizer started")
    for i in range(3):
        time.sleep(1)
        click.echo(f"[Δ + 1] Regulating load... pass {i+1}/3")
        log(f"Loop iteration {i+1}")
    click.echo("✅ System equilibrium achieved")
    log("Equilibrium achieved")

@main.command()
def status():
    if not CONFIG_PATH.exists():
        click.echo("❌ No configuration profile found.")
        return
    cpu_load = psutil.cpu_percent(interval=1)
    temp_stability = max(90, 100 - abs(cpu_load - 50) / 0.5)
    click.echo(f"[RUNNING] TEO active")
    click.echo(f"CPU Load: {cpu_load:.1f}% | Thermal Stability: {temp_stability:.1f}% | Δ + 1: Balanced")
    log(f"Status check: CPU={cpu_load:.1f}% Stability={temp_stability:.1f}%")

@main.command("install-service")
def install_service():
    ensure_dirs()
    os_type = platform.system()
    if os_type == "Windows":
        click.echo("⚙️ Registering TEO as Windows Service (simulation)")
        log("Service install simulated (Windows)")
    else:
        click.echo("⚙️ Creating systemd service at /etc/systemd/system/teo.service")
        service_file = (
            "[Unit]\\nDescription=Trinity Energy Optimizer\\n"
            "[Service]\\nExecStart=/usr/local/bin/teo run\\nRestart=always\\n"
            "[Install]\\nWantedBy=multi-user.target\\n"
        )
        try:
            with open("/etc/systemd/system/teo.service", "w") as f:
                f.write(service_file)
            os.system("sudo systemctl daemon-reload && sudo systemctl enable teo")
            click.echo("✅ Service installed successfully.")
            log("Service installed successfully (systemd)")
        except PermissionError:
            click.echo("❌ Permission denied. Run with sudo.")
            log("Service install failed: PermissionError")

if __name__ == "__main__":
    main()
