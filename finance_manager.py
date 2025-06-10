import json
import uuid
import os
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from collections import defaultdict
from config_manager import ConfigManager
from models import Transaction, TransactionType, Category

class FinanceManager:
    """Versão atualizada do gerenciador financeiro com database externa"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_manager = ConfigManager(config_file)
        self.data_file = self.config_manager.get_database_path()
        self.transactions: List[Transaction] = []
        self.load_data()
        
        # Configurar backup automático
        if self.config_manager.get("auto_backup", True):
            self._check_backup()
    
    def _check_backup(self):
        """Verifica se precisa fazer backup automático"""
        backup_path = self.config_manager.get("backup_path")
        backup_interval = self.config_manager.get("backup_interval_days", 7)
        
        if not backup_path:
            return
        
        # Verificar último backup
        backup_files = []
        if os.path.exists(backup_path):
            backup_files = [f for f in os.listdir(backup_path) if f.endswith('.json')]
        
        should_backup = True
        if backup_files:
            # Verificar data do último backup
            latest_backup = max(backup_files)
            try:
                # Assumir formato: financial_data_YYYY-MM-DD_HH-MM-SS.json
                date_part = latest_backup.split('_')[2:4]
                date_str = f"{date_part[0]} {date_part[1].replace('-', ':').replace('.json', '')}"
                last_backup_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                
                days_since_backup = (datetime.now() - last_backup_date).days
                should_backup = days_since_backup >= backup_interval
                
            except (ValueError, IndexError):
                # Se não conseguir parse da data, fazer backup
                should_backup = True
        
        if should_backup:
            self.create_backup()
    
    def create_backup(self) -> bool:
        """Cria backup da database"""
        try:
            backup_path = self.config_manager.get("backup_path")
            if not backup_path:
                return False
            
            os.makedirs(backup_path, exist_ok=True)
            
            # Nome do arquivo de backup com timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_filename = f"financial_data_{timestamp}.json"
            backup_file_path = os.path.join(backup_path, backup_filename)
            
            # Copiar arquivo atual
            if os.path.exists(self.data_file):
                shutil.copy2(self.data_file, backup_file_path)
                print(f"✅ Backup criado: {backup_filename}")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Erro ao criar backup: {e}")
            return False
    
    def restore_backup(self, backup_filename: str) -> bool:
        """Restaura backup específico"""
        try:
            backup_path = self.config_manager.get("backup_path")
            backup_file_path = os.path.join(backup_path, backup_filename)
            
            if os.path.exists(backup_file_path):
                # Fazer backup do arquivo atual antes de restaurar
                current_backup = f"current_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                current_backup_path = os.path.join(backup_path, current_backup)
                
                if os.path.exists(self.data_file):
                    shutil.copy2(self.data_file, current_backup_path)
                
                # Restaurar backup
                shutil.copy2(backup_file_path, self.data_file)
                self.load_data()  # Recarregar dados
                
                print(f"✅ Backup restaurado: {backup_filename}")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Erro ao restaurar backup: {e}")
            return False
    
    def list_backups(self) -> List[Dict]:
        """Lista todos os backups disponíveis"""
        backup_path = self.config_manager.get("backup_path")
        backups = []
        
        if not os.path.exists(backup_path):
            return backups
        
        backup_files = [f for f in os.listdir(backup_path) if f.endswith('.json')]
        
        for backup_file in sorted(backup_files, reverse=True):
            backup_file_path = os.path.join(backup_path, backup_file)
            
            try:
                # Obter informações do arquivo
                stat = os.stat(backup_file_path)
                size = stat.st_size
                modified = datetime.fromtimestamp(stat.st_mtime)
                
                backups.append({
                    'filename': backup_file,
                    'size': size,
                    'modified': modified,
                    'path': backup_file_path
                })
                
            except Exception:
                continue
        
        return backups
    
    # Métodos do FinanceManager original (mantidos iguais)
    def add_transaction(self, description: str, amount: float, 
                       transaction_type: TransactionType, category: Category,
                       date: datetime = None, notes: str = None) -> bool:
        """Adiciona uma nova transação"""
        try:
            if date is None:
                date = datetime.now()
            
            transaction = Transaction(
                id=str(uuid.uuid4()),
                description=description,
                amount=abs(amount),
                transaction_type=transaction_type,
                category=category,
                date=date,
                notes=notes
            )
            
            self.transactions.append(transaction)
            self.save_data()
            return True
        except Exception as e:
            print(f"Erro ao adicionar transação: {e}")
            return False
    
    def remove_transaction(self, transaction_id: str) -> bool:
        """Remove uma transação pelo ID"""
        try:
            self.transactions = [t for t in self.transactions if t.id != transaction_id]
            self.save_data()
            return True
        except Exception as e:
            print(f"Erro ao remover transação: {e}")
            return False
    
    def get_transactions(self, start_date: datetime = None, 
                        end_date: datetime = None) -> List[Transaction]:
        """Obtém transações filtradas por período"""
        transactions = self.transactions.copy()
        
        if start_date:
            transactions = [t for t in transactions if t.date >= start_date]
        
        if end_date:
            transactions = [t for t in transactions if t.date <= end_date]
        
        return sorted(transactions, key=lambda x: x.date, reverse=True)
    
    def calculate_balance(self, start_date: datetime = None, 
                         end_date: datetime = None) -> Dict[str, float]:
        """Calcula o balanço financeiro"""
        transactions = self.get_transactions(start_date, end_date)
        
        total_receitas = sum(t.amount for t in transactions 
                           if t.transaction_type == TransactionType.RECEITA)
        total_despesas = sum(t.amount for t in transactions 
                           if t.transaction_type == TransactionType.DESPESA)
        
        return {
            'receitas': total_receitas,
            'despesas': total_despesas,
            'saldo': total_receitas - total_despesas
        }
    
    def get_category_summary(self, start_date: datetime = None,
                           end_date: datetime = None) -> Dict[str, Dict[str, float]]:
        """Obtém resumo por categoria"""
        transactions = self.get_transactions(start_date, end_date)
        
        receitas_por_categoria = defaultdict(float)
        despesas_por_categoria = defaultdict(float)
        
        for transaction in transactions:
            if transaction.transaction_type == TransactionType.RECEITA:
                receitas_por_categoria[transaction.category.value] += transaction.amount
            else:
                despesas_por_categoria[transaction.category.value] += transaction.amount
        
        return {
            'receitas': dict(receitas_por_categoria),
            'despesas': dict(despesas_por_categoria)
        }
    
    def save_data(self):
        """Salva os dados em arquivo JSON"""
        try:
            data = {
                'transactions': [t.to_dict() for t in self.transactions],
                'saved_at': datetime.now().isoformat(),
                'version': self.config_manager.get('version', '1.0.0')
            }
            
            # Garantir que o diretório existe
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Erro ao salvar dados: {e}")
    
    def load_data(self):
        """Carrega os dados do arquivo JSON"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.transactions = [Transaction.from_dict(t) for t in data.get('transactions', [])]
            else:
                print("Arquivo de dados não encontrado. Criando novo arquivo.")
                self.transactions = []
                
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            self.transactions = []
