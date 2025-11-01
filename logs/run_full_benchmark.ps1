# --- Trinity Δ₂ Full-System Benchmark Orchestrator ---
# Executes baseline → orchestrated → comparison automatically
$Root = "C:\Users\user\Desktop\Trinity_STEM"
Set-Location $Root
Write-Host "`n🚀 Launching Trinity Δ₂ Full-System Benchmark Suite...`n"

function Run-Phase {
    param([string]$name, [string]$script, [string]$outfile)
    Write-Host "`n=== Running $name Phase ===`n"
    $proc = Start-Process -FilePath "python" -ArgumentList "-u $script" -PassThru -NoNewWindow

    $elapsed = 0
    while (-not $proc.HasExited) {
        Start-Sleep -Seconds 30
        $elapsed += 30
        $cpu = (Get-Counter '\Processor(_Total)\% Processor Time').CounterSamples.CookedValue
        $mem = (Get-Counter '\Memory\% Committed Bytes In Use').CounterSamples.CookedValue
        Write-Host ("[{0}] ⏱  Elapsed {1,6:N0}s | CPU {2,5:N1}% | MEM {3,5:N1}%" -f $name, $elapsed, $cpu, $mem)
    }

    Write-Host "`n✅ $name Phase Complete — output → $outfile`n"
}

# --- PHASE 1: Baseline probe (no orchestrator) ---
Run-Phase "Baseline" "benchmarks\baseline_probe.py" "benchmarks\baseline_metrics.json"

# --- PHASE 2: Trinity orchestrated run (Δ₂ enabled) ---
Run-Phase "Orchestrated" "benchmarks\runtime_orchestrator.py" "benchmarks\orchestrated_metrics.json"

# --- PHASE 3: Comparison ---
Write-Host "`n=== Comparing Results ===`n"
python -u "benchmarks\compare_results.py"

Write-Host "`n🎯 Full Benchmark Suite Complete! Results saved to benchmarks\performance_differential.json`n"
