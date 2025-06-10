"""
🚀 GUIA COMPLETO: CRIAR EXECUTÁVEL COM DATABASE EXTERNA

## 1. PREPARAÇÃO DO PROJETO

### Estrutura de arquivos necessária:
```
projeto/
├── main.py                    # Original ou main_updated.py
├── models.py                  # Mesmo arquivo
├── finance_manager.py         # Original ou finance_manager_updated.py
├── gui.py                     # Original ou gui_updated.py
├── utils.py                   # Mesmo arquivo
├── config_manager.py          # NOVO - gerencia configurações
├── build_setup.py             # NOVO - script de build
└── config.json                # NOVO - configurações
```

## 2. INSTALAÇÃO DE DEPENDÊNCIAS

```bash
# Instalar PyInstaller
pip install pyinstaller

# Opcional: Interface gráfica para PyInstaller
pip install auto-py-to-exe
```

## 3. MÉTODOS PARA CRIAR EXECUTÁVEL

### Método 1: Script Automático (RECOMENDADO)
```bash
python build_setup.py
```

### Método 2: Comando Manual Simples
```bash
pyinstaller --onefile --windowed --name=ControleFinanceiro main.py
```

### Método 3: Comando Manual Avançado
```bash
pyinstaller --onefile ^
    --windowed ^
    --name=ControleFinanceiro ^
    --add-data="config.json;." ^
    --distpath=dist ^
    --workpath=build ^
    main_updated.py
```

### Método 4: Interface Gráfica
```bash
auto-py-to-exe
# Selecionar arquivo main.py e configurar opções visualmente
```

## 4. CONFIGURAÇÃO DE DATABASE EXTERNA

### O arquivo config.json controla onde os dados são salvos:
```json
{
  "database_path": "./Data/financial_data.json",
  "backup_path": "./Data/backups/",
  "app_name": "Controle Financeiro", 
  "version": "1.0.0",
  "auto_backup": true,
  "backup_interval_days": 7
}
```

### Opções de caminho:
- `"./Data/"` - Pasta Data ao lado do .exe
- `"C:/MeusDados/"` - Pasta específica no Windows
- `"/home/usuario/dados/"` - Pasta específica no Linux
- `"~/Documents/Financeiro/"` - Pasta na home do usuário

## 5. ESTRUTURA FINAL DISTRIBUIÇÃO

```
ControleFinanceiro_Portable/
├── ControleFinanceiro.exe     # Executável principal
├── config.json                # Configurações
├── Data/                      # Dados do usuário
│   ├── financial_data.json    # Database principal
│   └── backups/               # Backups automáticos
└── LEIA-ME.txt               # Instruções para usuário
```

## 6. COMANDOS RÁPIDOS

### Windows (PowerShell/CMD):
```batch
# Build completo
python build_setup.py

# Ou comando direto
pyinstaller --onefile --windowed --name=ControleFinanceiro main.py
```

### Linux/Mac:
```bash
# Build completo
python3 build_setup.py

# Ou comando direto
pyinstaller --onefile --windowed --name=ControleFinanceiro main.py
```

## 7. VANTAGENS DA CONFIGURAÇÃO EXTERNA

✅ **Database Portátil**: Dados na pasta Data/
✅ **Backup Automático**: Backups periódicos automáticos
✅ **Fácil Migração**: Copiar pasta inteira move tudo
✅ **Configurável**: Usuário pode alterar config.json
✅ **Multiplataforma**: Funciona Windows/Linux/Mac
✅ **Sem Instalação**: Executável único portátil

## 8. PERSONALIZAÇÕES AVANÇADAS

### Adicionar ícone:
```bash
pyinstaller --onefile --windowed --icon=icone.ico main.py
```

### Incluir arquivos extras:
```bash
pyinstaller --onefile --add-data="templates;templates" main.py
```

### Múltiplos arquivos:
```bash
pyinstaller --windowed main.py  # Cria pasta dist/ com vários arquivos
```

## 9. SOLUÇÃO DE PROBLEMAS

### Erro: "Module not found"
- Adicionar: `--hidden-import=nome_modulo`

### Executável muito grande
- Usar: `--exclude-module=modulo_desnecessario`

### Não abre no Windows
- Remover: `--windowed` para ver erros no console
- Adicionar: `--debug=all` para debug completo

### Database não encontrada
- Verificar config.json
- Verificar permissões da pasta Data/

## 10. DISTRIBUIÇÃO FINAL

1. Testar executável em máquina limpa
2. Criar instalador com NSIS/Inno Setup (opcional)
3. Documentar para usuário final
4. Incluir instruções de backup

Pronto! Seu programa estará completamente portátil com database externa configurável! 🎉
"""