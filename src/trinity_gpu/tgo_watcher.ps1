while (True) {
    Start-Sleep -Seconds 180
    if (-not (Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { \.Path -like '*Trinity_STEM*' })) {
        Start-Process 'C:\Users\user\Desktop\Trinity_STEM\venv\Scripts\python.exe' -ArgumentList 'C:\Users\user\Desktop\Trinity_STEM\trinity_gpu\tgo_continuous.py' -WindowStyle Hidden
        powershell.exe -ExecutionPolicy Bypass -File 'C:\Users\user\Desktop\Trinity_STEM\notify_restart.ps1'
        Add-Content 'C:\Users\user\Desktop\Trinity_STEM\benchmarks\autoboot_log.txt' ('[' + (Get-Date) + '] Auto-Restart triggered')
    }
}
