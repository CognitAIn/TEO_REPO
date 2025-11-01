param(
  [int]$Duration = 60,            # seconds per phase
  [int]$WarmupSeconds = 15,       # orchestrator warm-up
  [string]$OrchestratorCmd = "python -u `"$($PWD.Path)\run_trinity.py`""  # adjust if different
)

$ErrorActionPreference = "Stop"

# Paths
$Root = (Get-Location).Path
$Bench = Join-Path $Root "benchmarks"
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$LogDir = Join-Path $Bench ("demo_logs_" + $ts)
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$TranscriptPath = Join-Path $LogDir "transcript.txt"
Start-Transcript -Path $TranscriptPath -Force | Out-Null
Write-Host "Log folder: $LogDir"

# Ensure psutil is available
$psutilOK = $false
try {
  $out = python -c "import psutil; print('OK')" 2>$null
  if ($out -eq "OK") { $psutilOK = $true }
} catch {}
if (-not $psutilOK) {
  Write-Host "Installing psutil..."
  python -m pip install --user psutil | Out-Host
}

# File paths
$ProbePy    = Join-Path $Bench "demo_probe.py"
$ComparePy  = Join-Path $Bench "demo_compare.py"
$BaselineJson      = Join-Path $LogDir "baseline_metrics.json"
$BaselineConsole   = Join-Path $LogDir "baseline_console.log"
$OrchestratedJson  = Join-Path $LogDir "orchestrated_metrics.json"
$OrchestratedConsole = Join-Path $LogDir "orchestrated_console.log"
$CompareJson       = Join-Path $LogDir "comparison_metrics.json"
$CompareConsole    = Join-Path $LogDir "comparison_console.log"

Write-Host "`n=== Phase 1: Baseline (no orchestrator) ==="
python -u $ProbePy --label baseline --duration $Duration --out $BaselineJson `
  | Tee-Object -FilePath $BaselineConsole

Write-Host "`n=== Phase 2: Start Orchestrator ==="
Write-Host "Command: $OrchestratorCmd"
# Start orchestrator in background
$orchProc = Start-Process -FilePath "powershell" -ArgumentList "-NoProfile","-Command",$OrchestratorCmd -PassThru -WindowStyle Hidden
Write-Host "Orchestrator PID: $($orchProc.Id)"
Write-Host "Warm-up $WarmupSeconds seconds..."
Start-Sleep -Seconds $WarmupSeconds

Write-Host "`n=== Phase 3: Orchestrated run ==="
python -u $ProbePy --label orchestrated --duration $Duration --out $OrchestratedJson `
  | Tee-Object -FilePath $OrchestratedConsole

Write-Host "`n=== Phase 4: Stop Orchestrator ==="
try {
  if ($orchProc -and -not $orchProc.HasExited) {
    Stop-Process -Id $orchProc.Id -Force -ErrorAction SilentlyContinue
    Write-Host "Orchestrator stopped."
  } else {
    Write-Host "Orchestrator already exited."
  }
} catch {
  Write-Host "Stop-Process warning: $($_.Exception.Message)"
}

Write-Host "`n=== Phase 5: Compare ==="
python -u $ComparePy $BaselineJson $OrchestratedJson --out $CompareJson `
  | Tee-Object -FilePath $CompareConsole

Write-Host "`n--- Comparison JSON ---"
Get-Content $CompareJson

Stop-Transcript | Out-Null
Write-Host "`nAll logs saved in: $LogDir"
