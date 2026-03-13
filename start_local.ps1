param(
  [string]$MysqlIni = 'C:\xampp\mysql\bin\my.ini'
)

function Get-ConfiguredMysqlPort {
  param([string]$IniPath)

  if (-not (Test-Path $IniPath)) { return '3306' }

  $inMysqld = $false
  foreach ($line in Get-Content $IniPath) {
    $trim = $line.Trim()
    if ($trim -match '^\[mysqld\]$') { $inMysqld = $true; continue }
    if ($inMysqld -and $trim -match '^\[') { break }
    if ($inMysqld -and $trim -match '^port\s*=\s*(\d+)$') { return $Matches[1] }
  }

  return '3306'
}

$port = if ($env:MYSQL_PORT) { $env:MYSQL_PORT } else { Get-ConfiguredMysqlPort -IniPath $MysqlIni }
$env:MYSQL_PORT = $port

Write-Host "Usando MYSQL_PORT=$port" -ForegroundColor Cyan

try {
  $tcp = Test-NetConnection -ComputerName '127.0.0.1' -Port ([int]$port) -WarningAction SilentlyContinue
  if (-not $tcp.TcpTestSucceeded) {
    Write-Host "MySQL no esta escuchando en el puerto $port." -ForegroundColor Yellow
    Write-Host 'Si MariaDB normal falla, ejecuta primero start_mysql_recovery.ps1.' -ForegroundColor Yellow
    exit 1
  }
} catch {
  Write-Host "No fue posible verificar el puerto $port de MySQL." -ForegroundColor Yellow
  exit 1
}

Write-Host 'Iniciando backend Flask...' -ForegroundColor Green
venv\Scripts\python.exe backend\app.py
