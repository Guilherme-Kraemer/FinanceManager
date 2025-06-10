import os
import sys
import subprocess
import shutil
from pathlib import Path

def install_dependencies():
    """Instala as dependências necessárias para build"""
    print("📦 Instalando dependências para build...")
    
    dependencies = [
        "pyinstaller",
        "auto-py-to-exe"  # Interface gráfica opcional
    ]
    
    for dep in dependencies:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✅ {dep} instalado com sucesso")
        except subprocess.CalledProcessError:
            print(f"❌ Erro ao instalar {dep}")
            return False
    
    return True

def create_build_structure():
    """Cria a estrutura de pastas para o build"""
    print("📁 Criando estrutura de pastas...")
    
    folders = [
        "build",
        "dist", 
        "data",
        "config"
    ]
    
    for folder in folders:
        Path(folder).mkdir(exist_ok=True)
        print(f"✅ Pasta '{folder}' criada")

def create_spec_file():
    """Cria arquivo .spec personalizado para PyInstaller"""
    spec_content = '''
# finance_app.spec - Configuração personalizada do PyInstaller

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config/config.json', 'config'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ControleFinanceiro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # False para não mostrar console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico'  # Adicione um ícone se tiver
)
'''
    
    with open("finance_app.spec", "w", encoding="utf-8") as f:
        f.write(spec_content)
    
    print("✅ Arquivo .spec criado")

def build_executable():
    """Constrói o executável usando PyInstaller"""
    print("🔨 Construindo executável...")
    
    try:
        # Comando básico do PyInstaller
        cmd = [
            "pyinstaller",
            "--onefile",              # Arquivo único
            "--windowed",             # Sem console
            "--name=ControleFinanceiro",
            "--distpath=dist",
            "--workpath=build",
            "main.py"
        ]
        
        subprocess.check_call(cmd)
        print("✅ Executável criado com sucesso!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao criar executável: {e}")
        return False

def create_installer_structure():
    """Cria estrutura final para distribuição"""
    print("📦 Criando estrutura de distribuição...")
    
    # Criar pasta final de distribuição
    dist_folder = Path("ControleFinanceiro_Portable")
    dist_folder.mkdir(exist_ok=True)
    
    # Copiar executável
    exe_source = Path("dist/ControleFinanceiro.exe")
    exe_dest = dist_folder / "ControleFinanceiro.exe"
    
    if exe_source.exists():
        shutil.copy2(exe_source, exe_dest)
        print("✅ Executável copiado")
    
    # Criar pasta de dados
    data_folder = dist_folder / "Data"
    data_folder.mkdir(exist_ok=True)
    
    # Criar arquivo de configuração
    config_file = dist_folder / "config.json"
    config_content = {
        "database_path": "./Data/financial_data.json",
        "backup_path": "./Data/backups/",
        "app_name": "Controle Financeiro",
        "version": "1.0.0"
    }
    
    import json
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config_content, f, indent=2, ensure_ascii=False)
    
    print("✅ Configuração criada")
    
    # Criar README para o usuário
    readme_content = """
# Controle Financeiro - Versão Portátil

## Como usar:
1. Execute ControleFinanceiro.exe
2. Seus dados serão salvos na pasta 'Data'
3. Você pode mover toda a pasta para qualquer lugar

## Estrutura:
- ControleFinanceiro.exe    → Programa principal
- Data/                     → Seus dados financeiros
- config.json              → Configurações do programa

## Backup:
- Seus dados ficam na pasta 'Data'
- Faça backup copiando toda a pasta 'Data'

Desenvolvido em Python - Versão Portátil
"""
    
    readme_file = dist_folder / "LEIA-ME.txt"
    with open(readme_file, "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print("✅ README criado")
    print(f"📁 Distribuição pronta em: {dist_folder.absolute()}")

def main():
    """Função principal do build"""
    print("🚀 Iniciando processo de build...")
    print("=" * 50)
    
    if not install_dependencies():
        print("❌ Falha na instalação de dependências")
        return
    
    create_build_structure()
    create_spec_file()
    
    if build_executable():
        create_installer_structure()
        print("\n🎉 Build concluído com sucesso!")
        print("📁 Verifique a pasta 'ControleFinanceiro_Portable'")
    else:
        print("\n❌ Falha no build")

if __name__ == "__main__":
    main()
