Write-Host 'Iniciando MariaDB en modo temporal de recuperacion...' -ForegroundColor Yellow
Write-Host 'Puerto configurado: 3307' -ForegroundColor Yellow
Start-Process -FilePath 'C:\xampp\mysql\bin\mysqld.exe' -ArgumentList "--defaults-file=C:\xampp\mysql\bin\my.ini --console --skip-grant-tables --port=3307" -WindowStyle Hidden
Start-Sleep -Seconds 3
try {
  & 'C:\xampp\mysql\bin\mysql.exe' -u root --port=3307 -N -e "SELECT 1;"
  Write-Host 'MariaDB recovery activo.' -ForegroundColor Green
} catch {
  Write-Host 'No fue posible validar MariaDB recovery.' -ForegroundColor Red
  exit 1
}
