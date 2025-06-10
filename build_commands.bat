echo Instalando dependencias...
pip install pyinstaller

echo Limpando builds anteriores...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
rmdir /s /q __pycache__ 2>nul

echo Criando executavel...
pyinstaller --onefile --windowed --name=ControleFinanceiro main_updated.py

echo Criando estrutura de distribuicao...
mkdir ControleFinanceiro_Portable 2>nul
mkdir ControleFinanceiro_Portable\Data 2>nul

copy dist\ControleFinanceiro.exe ControleFinanceiro_Portable\
copy config.json ControleFinanceiro_Portable\ 2>nul

echo {
echo   "database_path": "./Data/financial_data.json",
echo   "backup_path": "./Data/backups/",
echo   "app_name": "Controle Financeiro",
echo   "version": "1.0.0",
echo   "auto_backup": true,
echo   "backup_interval_days": 7
echo } > ControleFinanceiro_Portable\config.json

echo.
echo ===================================
echo  BUILD CONCLUIDO!
echo ===================================
echo Pasta: ControleFinanceiro_Portable
echo.
pause
