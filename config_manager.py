import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional

class ConfigManager:
    """Gerencia configurações da aplicação"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Carrega configurações do arquivo"""
        default_config = {
            "database_path": "./Data/financial_data.json",
            "backup_path": "./Data/backups/",
            "app_name": "Controle Financeiro",
            "version": "1.0.0",
            "auto_backup": True,
            "backup_interval_days": 7
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Mesclar com configuração padrão
                    default_config.update(loaded_config)
            
            # Criar pastas necessárias
            self._ensure_directories(default_config)
            
            return default_config
            
        except Exception as e:
            print(f"Erro ao carregar configuração: {e}")
            return default_config
    
    def _ensure_directories(self, config: Dict):
        """Garante que os diretórios necessários existam"""
        paths_to_create = [
            os.path.dirname(config["database_path"]),
            config["backup_path"]
        ]
        
        for path in paths_to_create:
            if path and not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
    
    def save_config(self):
        """Salva configurações no arquivo"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar configuração: {e}")
    
    def get(self, key: str, default=None):
        """Obtém valor de configuração"""
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        """Define valor de configuração"""
        self.config[key] = value
        self.save_config()
    
    def get_database_path(self) -> str:
        """Retorna caminho completo da database"""
        db_path = self.get("database_path")
        
        # Se for caminho relativo, tornar absoluto baseado no executável
        if not os.path.isabs(db_path):
            if hasattr(sys, '_MEIPASS'):
                # Executando como executável PyInstaller
                base_path = os.path.dirname(sys.executable)
            else:
                # Executando como script Python
                base_path = os.path.dirname(os.path.abspath(__file__))
            
            db_path = os.path.join(base_path, db_path)
        
        # Garantir que o diretório existe
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        return db_path
