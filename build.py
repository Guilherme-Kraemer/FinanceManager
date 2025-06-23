import os
import sys
import subprocess
import shutil
import json
from pathlib import Path

def create_config_file():
    '''Cria arquivo de configuração padrão'''
    config_content = {
        "database_path": "./Data/financial_data.json",
        "backup_path": "./Data/backups/",
        "app_name": "Controle Financeiro",
        "version": "2.0.0",
        "auto_backup": True,
        "backup_interval_days": 7,
        "suggestions_enabled": True,
        "max_suggestions": 10,
        "window_width": 1000,
        "window_height": 800,
        "theme": "clam"
    }
    
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config_content, f, indent=2, ensure_ascii=False)
    
    print("✅ config.json criado")

def install_pyinstaller():
    '''Instala PyInstaller se necessário'''
    try:
        import PyInstaller
        print("✅ PyInstaller já instalado")
        return True
    except ImportError:
        print("📦 Instalando PyInstaller...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✅ PyInstaller instalado com sucesso")
            return True
        except subprocess.CalledProcessError:
            print("❌ Erro ao instalar PyInstaller")
            return False

def clean_build_folders():
    '''Limpa pastas de build anteriores'''
    folders_to_clean = ["build", "dist", "__pycache__"]
    
    for folder in folders_to_clean:
        if Path(folder).exists():
            shutil.rmtree(folder)
            print(f"🧹 {folder} limpo")

def build_executable():
    '''Constrói o executável'''
    print("🔨 Construindo executável...")
    
    try:
        cmd = [
            "pyinstaller",
            "--onefile",
            "--windowed",
            "--name=ControleFinanceiro",
            "--add-data=config.json;.",
            "--distpath=dist",
            "--workpath=build",
            "main.py"
        ]
        
        # Adicionar ícone se existir
        if os.path.exists("icon.ico"):
            cmd.extend(["--icon=icon.ico"])
        
        subprocess.check_call(cmd)
        print("✅ Executável criado com sucesso!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao criar executável: {e}")
        return False

def create_distribution():
    '''Cria estrutura de distribuição final'''
    print("📦 Criando distribuição...")
    
    # Criar pasta de distribuição
    dist_folder = Path("ControleFinanceiro_v2")
    if dist_folder.exists():
        shutil.rmtree(dist_folder)
    
    dist_folder.mkdir()
    
    # Copiar executável
    exe_source = Path("dist/ControleFinanceiro.exe")
    if exe_source.exists():
        shutil.copy2(exe_source, dist_folder / "ControleFinanceiro.exe")
        print("✅ Executável copiado")
    else:
        print("❌ Executável não encontrado")
        return False
    
    # Criar pastas necessárias
    (dist_folder / "Data").mkdir()
    (dist_folder / "Data" / "backups").mkdir()
    
    # Copiar config.json
    if os.path.exists("config.json"):
        shutil.copy2("config.json", dist_folder / "config.json")
    
    # Copiar ícone se existir
    if os.path.exists("icon.ico"):
        shutil.copy2("icon.ico", dist_folder / "icon.ico")
    
    # Criar README
    readme_content = '''
# 💰 Controle Financeiro v2.0

## 🚀 Como usar:
1. Execute **ControleFinanceiro.exe**
2. Seus dados serão salvos automaticamente na pasta **Data/**
3. O programa é completamente portátil - pode mover toda a pasta

## 📁 Estrutura:
- **ControleFinanceiro.exe** → Programa principal
- **Data/** → Seus dados financeiros e backups
- **config.json** → Configurações do programa
- **LEIA-ME.txt** → Este arquivo

## ✨ Principais recursos:
- ➕ **Adicionar transações** com sugestões inteligentes
- 👁️ **Visualizar** e filtrar todas as transações
- 📊 **Relatórios** detalhados com gráficos
- 💡 **Sugestões automáticas** baseadas no histórico
- 💾 **Backup automático** dos seus dados
- ⚙️ **Configurações** personalizáveis

## 🧠 Sistema de Sugestões:
- **Autocomplete** nas descrições
- **Categorias automáticas** baseadas no texto
- **Valores sugeridos** baseados no histórico
- **Transações rápidas** com um clique

## 💾 Backup e Segurança:
- Backup automático a cada 7 dias
- Backup manual quando desejar
- Restauração fácil de qualquer backup
- Dados sempre seguros na pasta Data/

## 🔧 Solução de problemas:
- Se o programa não abrir, verifique se tem permissão na pasta
- Se perder dados, verifique a pasta Data/backups/
- Para reportar bugs, anote a mensagem de erro exata

## 📞 Suporte:
Desenvolvido com Python + Tkinter
Versão 2.0.0 - Sistema completo de controle financeiro
    '''.strip()
    
    with open(dist_folder / "LEIA-ME.txt", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print(f"✅ Distribuição criada em: {dist_folder.absolute()}")
    return True

def main():
    '''Função principal do build'''
    print("🚀 SISTEMA DE CONTROLE FINANCEIRO - BUILD v2.0")
    print("=" * 50)
    
    # Verificar se está no diretório correto
    if not os.path.exists("main.py"):
        print("❌ Arquivo main.py não encontrado!")
        print("Execute este script na mesma pasta do main.py")
        input("Pressione Enter para sair...")
        return
    
    # Passos do build
    print("1. Limpando builds anteriores...")
    clean_build_folders()
    
    print("2. Criando arquivo de configuração...")
    create_config_file()
    
    print("3. Verificando PyInstaller...")
    if not install_pyinstaller():
        print("❌ Falha na instalação do PyInstaller")
        input("Pressione Enter para sair...")
        return
    
    print("4. Construindo executável...")
    if not build_executable():
        print("❌ Falha na construção do executável")
        input("Pressione Enter para sair...")
        return
    
    print("5. Criando distribuição final...")
    if create_distribution():
        print("\n🎉 BUILD CONCLUÍDO COM SUCESSO!")
        print("📁 Pasta: ControleFinanceiro_v2/")
        print("🚀 Execute: ControleFinanceiro_v2/ControleFinanceiro.exe")
    else:
        print("\n❌ FALHA NA CRIAÇÃO DA DISTRIBUIÇÃO")
    
    input("\nPressione Enter para sair...")

if __name__ == "__main__":
    main()
