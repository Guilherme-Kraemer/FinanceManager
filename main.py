import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import uuid
import os
import shutil
import sys
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# ============================================================================
# MODELOS DE DADOS
# ============================================================================

class TransactionType(Enum):
    RECEITA = "receita"
    DESPESA = "despesa"

class Category(Enum):
    # Categorias de Receita
    SALARIO = "Salário"
    FREELANCE = "Freelance"
    INVESTIMENTOS = "Investimentos"
    VENDAS = "Vendas"
    BONUS = "Bônus"
    OUTROS_RECEITA = "Outros (Receita)"
    
    # Categorias de Despesa
    ALIMENTACAO = "Alimentação"
    TRANSPORTE = "Transporte"
    MORADIA = "Moradia"
    SAUDE = "Saúde"
    EDUCACAO = "Educação"
    ENTRETENIMENTO = "Entretenimento"
    COMPRAS = "Compras"
    CONTAS = "Contas"
    VESTUARIO = "Vestuário"
    TECNOLOGIA = "Tecnologia"
    OUTROS_DESPESA = "Outros (Despesa)"

@dataclass
class Transaction:
    """Classe para representar uma transação financeira"""
    id: str
    description: str
    amount: float
    transaction_type: TransactionType
    category: Category
    date: datetime
    notes: Optional[str] = None

    def to_dict(self) -> Dict:
        """Converte a transação para dicionário"""
        return {
            'id': self.id,
            'description': self.description,
            'amount': self.amount,
            'transaction_type': self.transaction_type.value,
            'category': self.category.value,
            'date': self.date.isoformat(),
            'notes': self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Transaction':
        """Cria uma transação a partir de um dicionário"""
        return cls(
            id=data['id'],
            description=data['description'],
            amount=data['amount'],
            transaction_type=TransactionType(data['transaction_type']),
            category=Category(data['category']),
            date=datetime.fromisoformat(data['date']),
            notes=data.get('notes')
        )

# ============================================================================
# GERENCIADOR DE CONFIGURAÇÕES
# ============================================================================

class ConfigManager:
    """Gerencia todas as configurações da aplicação"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Carrega configurações do arquivo"""
        default_config = {
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
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            
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
        
        if not os.path.isabs(db_path):
            if hasattr(sys, '_MEIPASS'):
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
            
            db_path = os.path.join(base_path, db_path)
        
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        return db_path

# ============================================================================
# SISTEMA DE SUGESTÕES INTELIGENTES
# ============================================================================

class SmartSuggestionEngine:
    """Motor de sugestões inteligentes baseado no histórico"""
    
    def __init__(self):
        self.suggestion_cache = {}
        self.category_patterns = defaultdict(list)
        self.description_history = defaultdict(list)
        self.amount_patterns = defaultdict(list)
        self.last_update = None
        self.word_frequency = defaultdict(int)
    
    def update_suggestions(self, transactions: List[Transaction]):
        """Atualiza as sugestões baseadas nas transações"""
        if not transactions:
            return
        
        # Limpar caches
        self.category_patterns.clear()
        self.description_history.clear()
        self.amount_patterns.clear()
        self.word_frequency.clear()
        
        # Analisar transações
        for transaction in transactions:
            trans_type = transaction.transaction_type.value
            description = transaction.description.lower().strip()
            category = transaction.category
            amount = transaction.amount
            
            # Guardar descrições por tipo
            if description not in self.description_history[trans_type]:
                self.description_history[trans_type].append(description)
            
            # Padrões de categoria por palavras-chave
            words = self._extract_keywords(description)
            for word in words:
                self.word_frequency[word] += 1
                if category not in self.category_patterns[word]:
                    self.category_patterns[word].append(category)
            
            # Valores típicos por descrição
            self.amount_patterns[description].append(amount)
        
        self.last_update = datetime.now()
    
    def _extract_keywords(self, description: str) -> List[str]:
        """Extrai palavras-chave relevantes da descrição"""
        # Remover caracteres especiais e dividir em palavras
        cleaned = re.sub(r'[^\w\s]', ' ', description.lower())
        words = [w.strip() for w in cleaned.split() if len(w.strip()) > 2]
        
        # Filtrar palavras irrelevantes
        stop_words = {
            'com', 'para', 'por', 'que', 'uma', 'dos', 'das', 'the', 'and', 'or',
            'mas', 'por', 'ate', 'sem', 'sob', 'sobre', 'tras', 'entre', 'ante'
        }
        keywords = [w for w in words if w not in stop_words]
        
        return keywords[:4]  # Máximo 4 palavras-chave
    
    def get_description_suggestions(self, partial_text: str, transaction_type: str, limit: int = 10) -> List[str]:
        """Obtém sugestões de descrição baseadas no texto parcial"""
        if len(partial_text) < 1:
            # Retornar as mais comuns se texto vazio
            descriptions = self.description_history.get(transaction_type, [])
            # Ordenar por frequência
            desc_counter = Counter(descriptions)
            return [desc.title() for desc, _ in desc_counter.most_common(limit)]
        
        partial_lower = partial_text.lower()
        suggestions = []
        
        # Buscar descrições que começam com o texto
        for description in self.description_history.get(transaction_type, []):
            if description.startswith(partial_lower):
                suggestions.append(description.title())
        
        # Buscar descrições que contêm o texto
        for description in self.description_history.get(transaction_type, []):
            if partial_lower in description and not description.startswith(partial_lower):
                suggestions.append(description.title())
        
        # Remover duplicatas e limitar
        unique_suggestions = list(dict.fromkeys(suggestions))
        return unique_suggestions[:limit]
    
    def suggest_category(self, description: str, transaction_type: str) -> Optional[Category]:
        """Sugere categoria baseada na descrição"""
        keywords = self._extract_keywords(description)
        category_scores = Counter()
        
        for keyword in keywords:
            for category in self.category_patterns.get(keyword, []):
                if self._is_category_compatible(category, transaction_type):
                    # Peso baseado na frequência da palavra
                    weight = self.word_frequency.get(keyword, 1)
                    category_scores[category] += weight
        
        if category_scores:
            return category_scores.most_common(1)[0][0]
        
        return None
    
    def suggest_amount(self, description: str) -> Optional[float]:
        """Sugere valor baseado em descrições similares"""
        description_lower = description.lower().strip()
        
        # Busca exata
        if description_lower in self.amount_patterns:
            amounts = self.amount_patterns[description_lower]
            return sum(amounts) / len(amounts)
        
        # Busca por similaridade
        keywords = self._extract_keywords(description_lower)
        similar_amounts = []
        
        for stored_desc, amounts in self.amount_patterns.items():
            stored_keywords = self._extract_keywords(stored_desc)
            common_keywords = set(keywords) & set(stored_keywords)
            
            if common_keywords:
                # Peso baseado no número de palavras em comum
                weight = len(common_keywords) / max(len(keywords), len(stored_keywords))
                if weight > 0.3:  # Threshold de similaridade
                    similar_amounts.extend(amounts)
        
        if similar_amounts:
            return sum(similar_amounts) / len(similar_amounts)
        
        return None
    
    def _is_category_compatible(self, category: Category, transaction_type: str) -> bool:
        """Verifica se a categoria é compatível com o tipo de transação"""
        receita_categories = {
            Category.SALARIO, Category.FREELANCE, Category.INVESTIMENTOS,
            Category.VENDAS, Category.BONUS, Category.OUTROS_RECEITA
        }
        
        if transaction_type == "receita":
            return category in receita_categories
        else:
            return category not in receita_categories
    
    def get_popular_transactions(self, transaction_type: str, limit: int = 6) -> List[Dict]:
        """Retorna as transações mais populares por tipo"""
        descriptions = self.description_history.get(transaction_type, [])
        if not descriptions:
            return []
        
        # Contar frequência das descrições
        description_count = Counter(descriptions)
        popular = description_count.most_common(limit)
        
        result = []
        for description, count in popular:
            category = self.suggest_category(description, transaction_type)
            amount = self.suggest_amount(description)
            
            result.append({
                'description': description.title(),
                'category': category,
                'amount': amount,
                'frequency': count
            })
        
        return result
    
    def get_statistics(self) -> Dict:
        """Retorna estatísticas do sistema de sugestões"""
        total_descriptions = sum(len(descs) for descs in self.description_history.values())
        unique_descriptions = len(set(
            desc for descs in self.description_history.values() for desc in descs
        ))
        
        return {
            'total_descriptions': total_descriptions,
            'unique_descriptions': unique_descriptions,
            'keywords_learned': len(self.word_frequency),
            'category_patterns': len(self.category_patterns),
            'last_update': self.last_update
        }

# ============================================================================
# WIDGET DE AUTOCOMPLETE CUSTOMIZADO
# ============================================================================

class AutocompleteCombobox(ttk.Combobox):
    """Combobox com autocomplete inteligente"""
    
    def __init__(self, parent, suggestion_engine: SmartSuggestionEngine, 
                 transaction_type_var: tk.StringVar, **kwargs):
        super().__init__(parent, **kwargs)
        self.suggestion_engine = suggestion_engine
        self.transaction_type_var = transaction_type_var
        
        # Configurar eventos
        self.bind('<KeyRelease>', self.on_key_release)
        self.bind('<Button-1>', self.on_click)
        self.bind('<FocusIn>', self.on_focus_in)
        
        # Variáveis de controle
        self.var = self['textvariable'] or tk.StringVar()
        if not self['textvariable']:
            self['textvariable'] = self.var
    
    def on_key_release(self, event):
        """Evento de liberação de tecla"""
        if event.keysym in ('Up', 'Down', 'Left', 'Right', 'Tab', 'Return', 'Escape'):
            return
        
        current_text = self.get()
        transaction_type = self.transaction_type_var.get().lower()
        
        if len(current_text) >= 1 and transaction_type:
            suggestions = self.suggestion_engine.get_description_suggestions(
                current_text, transaction_type, limit=8
            )
            self['values'] = suggestions
    
    def on_click(self, event):
        """Evento de clique"""
        transaction_type = self.transaction_type_var.get().lower()
        
        if not self.get() and transaction_type:
            # Mostrar transações populares
            popular = self.suggestion_engine.get_popular_transactions(transaction_type, limit=8)
            suggestions = [item['description'] for item in popular]
            self['values'] = suggestions
    
    def on_focus_in(self, event):
        """Evento ao receber foco"""
        self.on_click(event)

# ============================================================================
# GERENCIADOR FINANCEIRO
# ============================================================================

class FinanceManager:
    """Gerenciador financeiro principal"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_manager = ConfigManager(config_file)
        self.data_file = self.config_manager.get_database_path()
        self.transactions: List[Transaction] = []
        self.suggestion_engine = SmartSuggestionEngine()
        
        self.load_data()
        self.update_suggestions()
        
        if self.config_manager.get("auto_backup", True):
            self._check_backup()
    
    def update_suggestions(self):
        """Atualiza o sistema de sugestões"""
        if self.config_manager.get("suggestions_enabled", True):
            self.suggestion_engine.update_suggestions(self.transactions)
    
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
            self.update_suggestions()
            return True
        except Exception as e:
            print(f"Erro ao adicionar transação: {e}")
            return False
    
    def remove_transaction(self, transaction_id: str) -> bool:
        """Remove uma transação pelo ID"""
        try:
            old_count = len(self.transactions)
            self.transactions = [t for t in self.transactions if t.id != transaction_id]
            
            if len(self.transactions) < old_count:
                self.save_data()
                self.update_suggestions()
                return True
            return False
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
    
    def _check_backup(self):
        """Verifica se precisa fazer backup automático"""
        backup_path = self.config_manager.get("backup_path")
        backup_interval = self.config_manager.get("backup_interval_days", 7)
        
        if not backup_path or not os.path.exists(self.data_file):
            return
        
        backup_files = []
        if os.path.exists(backup_path):
            backup_files = [f for f in os.listdir(backup_path) 
                          if f.startswith('financial_data_') and f.endswith('.json')]
        
        should_backup = True
        if backup_files:
            latest_backup = max(backup_files)
            try:
                # Extrair data do nome do arquivo
                date_part = latest_backup.replace('financial_data_', '').replace('.json', '')
                parts = date_part.split('_')
                if len(parts) >= 2:
                    date_str = f"{parts[0]} {parts[1].replace('-', ':')}"
                    last_backup_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                    
                    days_since_backup = (datetime.now() - last_backup_date).days
                    should_backup = days_since_backup >= backup_interval
                
            except (ValueError, IndexError):
                should_backup = True
        
        if should_backup:
            self.create_backup()
    
    def create_backup(self) -> bool:
        """Cria backup da database"""
        try:
            backup_path = self.config_manager.get("backup_path")
            if not backup_path or not os.path.exists(self.data_file):
                return False
            
            os.makedirs(backup_path, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_filename = f"financial_data_{timestamp}.json"
            backup_file_path = os.path.join(backup_path, backup_filename)
            
            shutil.copy2(self.data_file, backup_file_path)
            print(f"✅ Backup criado: {backup_filename}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar backup: {e}")
            return False
    
    def restore_backup(self, backup_filename: str) -> bool:
        """Restaura backup específico"""
        try:
            backup_path = self.config_manager.get("backup_path")
            backup_file_path = os.path.join(backup_path, backup_filename)
            
            if os.path.exists(backup_file_path):
                # Backup do arquivo atual
                if os.path.exists(self.data_file):
                    current_backup = f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    current_backup_path = os.path.join(backup_path, current_backup)
                    shutil.copy2(self.data_file, current_backup_path)
                
                # Restaurar backup
                shutil.copy2(backup_file_path, self.data_file)
                self.load_data()
                self.update_suggestions()
                
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
        
        backup_files = [f for f in os.listdir(backup_path) 
                       if f.startswith('financial_data_') and f.endswith('.json')]
        
        for backup_file in sorted(backup_files, reverse=True):
            backup_file_path = os.path.join(backup_path, backup_file)
            
            try:
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
    
    def save_data(self):
        """Salva os dados em arquivo JSON"""
        try:
            data = {
                'transactions': [t.to_dict() for t in self.transactions],
                'saved_at': datetime.now().isoformat(),
                'version': self.config_manager.get('version', '2.0.0'),
                'total_transactions': len(self.transactions)
            }
            
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
                    self.transactions = [Transaction.from_dict(t) 
                                       for t in data.get('transactions', [])]
            else:
                print("Arquivo de dados não encontrado. Criando novo arquivo.")
                self.transactions = []
                
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            self.transactions = []

# ============================================================================
# INTERFACE GRÁFICA PRINCIPAL
# ============================================================================

class FinanceApp:
    """Interface gráfica principal da aplicação"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.finance_manager = FinanceManager()
        
        self.setup_window()
        self.create_styles()
        self.create_widgets()
        self.refresh_data()
    
    def setup_window(self):
        """Configura a janela principal"""
        config = self.finance_manager.config_manager
        
        self.root.title(f"{config.get('app_name')} - v{config.get('version')}")
        
        width = config.get('window_width', 1000)
        height = config.get('window_height', 800)
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(900, 700)
        
        # Centralizar janela
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Configurar fechamento
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
    
    def create_styles(self):
        """Cria estilos customizados"""
        self.style = ttk.Style()
        theme = self.finance_manager.config_manager.get('theme', 'clam')
        self.style.theme_use(theme)
        
        # Estilo para labels de valor
        self.style.configure('Value.TLabel', font=('Arial', 11, 'bold'))
        self.style.configure('BigValue.TLabel', font=('Arial', 14, 'bold'))
        
        # Estilo para botões principais
        self.style.configure('Action.TButton', font=('Arial', 10, 'bold'))
    
    def create_widgets(self):
        """Cria todos os widgets da interface"""
        # Notebook principal
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Criar todas as abas
        self.create_add_transaction_tab()
        self.create_view_transactions_tab()
        self.create_reports_tab()
        self.create_suggestions_tab()
        self.create_backup_tab()
        self.create_settings_tab()
    
    # ========================================================================
    # ABA: ADICIONAR TRANSAÇÃO
    # ========================================================================
    
    def create_add_transaction_tab(self):
        """Cria a aba para adicionar transações"""
        self.add_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.add_frame, text="➕ Adicionar")
        
        # Container principal com scroll
        canvas = tk.Canvas(self.add_frame)
        scrollbar = ttk.Scrollbar(self.add_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Frame de transações rápidas (topo)
        self.quick_frame = ttk.LabelFrame(scrollable_frame, text="⚡ Transações Rápidas", padding=15)
        self.quick_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        # Frame principal do formulário
        main_frame = ttk.LabelFrame(scrollable_frame, text="📝 Nova Transação", padding=20)
        main_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Tipo de transação (primeira linha)
        ttk.Label(main_frame, text="Tipo:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=8)
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(main_frame, textvariable=self.type_var, 
                                      values=["Receita", "Despesa"], state="readonly", width=15)
        self.type_combo.grid(row=0, column=1, sticky=tk.W, pady=8, padx=(10, 0))
        self.type_combo.bind('<<ComboboxSelected>>', self.on_type_change)
        
        # Descrição com autocomplete (segunda linha)
        ttk.Label(main_frame, text="Descrição:", font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=8)
        
        desc_frame = ttk.Frame(main_frame)
        desc_frame.grid(row=1, column=1, columnspan=3, sticky=tk.W+tk.E, pady=8, padx=(10, 0))
        
        self.desc_entry = AutocompleteCombobox(
            desc_frame, 
            self.finance_manager.suggestion_engine,
            self.type_var,
            width=40
        )
        self.desc_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.desc_entry.bind('<FocusOut>', self.on_description_change)
        self.desc_entry.bind('<<ComboboxSelected>>', self.on_description_selected)
        
        # Valor com sugestão (terceira linha)
        ttk.Label(main_frame, text="Valor (R$):", font=('Arial', 10, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=8)
        
        value_frame = ttk.Frame(main_frame)
        value_frame.grid(row=2, column=1, columnspan=3, sticky=tk.W+tk.E, pady=8, padx=(10, 0))
        
        self.amount_entry = ttk.Entry(value_frame, width=20, font=('Arial', 11))
        self.amount_entry.pack(side=tk.LEFT)
        
        ttk.Button(value_frame, text="💡", command=self.suggest_amount, width=4).pack(side=tk.LEFT, padx=(5, 0))
        
        # Categoria com sugestão (quarta linha)
        ttk.Label(main_frame, text="Categoria:", font=('Arial', 10, 'bold')).grid(row=3, column=0, sticky=tk.W, pady=8)
        
        category_frame = ttk.Frame(main_frame)
        category_frame.grid(row=3, column=1, columnspan=3, sticky=tk.W+tk.E, pady=8, padx=(10, 0))
        
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(category_frame, textvariable=self.category_var, 
                                         state="readonly", width=30)
        self.category_combo.pack(side=tk.LEFT)
        
        ttk.Button(category_frame, text="💡", command=self.suggest_category, width=4).pack(side=tk.LEFT, padx=(5, 0))
        
        # Data (quinta linha)
        ttk.Label(main_frame, text="Data:", font=('Arial', 10, 'bold')).grid(row=4, column=0, sticky=tk.W, pady=8)
        self.date_entry = ttk.Entry(main_frame, width=15)
        self.date_entry.grid(row=4, column=1, sticky=tk.W, pady=8, padx=(10, 0))
        self.date_entry.insert(0, datetime.now().strftime("%d/%m/%Y"))
        
        ttk.Button(main_frame, text="📅 Hoje", command=self.set_today_date, width=8).grid(row=4, column=2, pady=8, padx=(5, 0))
        
        # Observações (sexta linha)
        ttk.Label(main_frame, text="Observações:", font=('Arial', 10, 'bold')).grid(row=5, column=0, sticky=tk.W+tk.N, pady=8)
        self.notes_text = tk.Text(main_frame, width=50, height=3, font=('Arial', 10))
        self.notes_text.grid(row=5, column=1, columnspan=3, sticky=tk.W+tk.E, pady=8, padx=(10, 0))
        
        # Botões principais (sétima linha)
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=4, pady=20)
        
        ttk.Button(button_frame, text="✅ Adicionar", command=self.add_transaction, 
                  style='Action.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🧹 Limpar", command=self.clear_form).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🎯 Auto-Preencher", command=self.auto_fill_form).pack(side=tk.LEFT, padx=5)
        
        # Configurar grid
        main_frame.columnconfigure(1, weight=1)
        desc_frame.columnconfigure(0, weight=1)
        value_frame.columnconfigure(0, weight=1)
        category_frame.columnconfigure(0, weight=1)
        
        # Configurar scroll
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Criar botões de transações rápidas
        self.update_quick_buttons()
    
    def update_quick_buttons(self):
        """Atualiza os botões de transações rápidas"""
        # Limpar botões existentes
        for widget in self.quick_frame.winfo_children():
            widget.destroy()
        
        # Criar frames para receitas e despesas
        receita_frame = ttk.LabelFrame(self.quick_frame, text="💰 Receitas Frequentes")
        receita_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        despesa_frame = ttk.LabelFrame(self.quick_frame, text="💸 Despesas Frequentes")
        despesa_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Obter transações populares
        popular_receitas = self.finance_manager.suggestion_engine.get_popular_transactions("receita", 4)
        popular_despesas = self.finance_manager.suggestion_engine.get_popular_transactions("despesa", 4)
        
        # Criar botões para receitas
        for i, item in enumerate(popular_receitas):
            btn_text = self._format_quick_button_text(item)
            btn = ttk.Button(receita_frame, text=btn_text, 
                           command=lambda x=item: self.quick_fill_transaction(x, "Receita"))
            btn.pack(fill=tk.X, pady=2)
        
        # Criar botões para despesas
        for i, item in enumerate(popular_despesas):
            btn_text = self._format_quick_button_text(item)
            btn = ttk.Button(despesa_frame, text=btn_text,
                           command=lambda x=item: self.quick_fill_transaction(x, "Despesa"))
            btn.pack(fill=tk.X, pady=2)
    
    def _format_quick_button_text(self, item: Dict) -> str:
        """Formata o texto do botão de transação rápida"""
        description = item['description']
        if len(description) > 20:
            description = description[:17] + "..."
        
        if item['amount']:
            return f"{description}\nR$ {item['amount']:.2f}"
        else:
            return description
    
    def quick_fill_transaction(self, transaction_data: Dict, transaction_type: str):
        """Preenche formulário rapidamente com dados de transação popular"""
        self.type_var.set(transaction_type)
        self.on_type_change()
        
        self.desc_entry.set(transaction_data['description'])
        
        if transaction_data['amount']:
            self.amount_entry.delete(0, tk.END)
            self.amount_entry.insert(0, f"{transaction_data['amount']:.2f}")
        
        if transaction_data['category']:
            self.category_var.set(transaction_data['category'].value)
    
    def on_type_change(self, event=None):
        """Atualiza categorias baseado no tipo selecionado"""
        transaction_type = self.type_var.get()
        
        if transaction_type == "Receita":
            categories = [cat.value for cat in Category if cat.value in [
                "Salário", "Freelance", "Investimentos", "Vendas", "Bônus", "Outros (Receita)"
            ]]
        else:
            categories = [cat.value for cat in Category if cat.value not in [
                "Salário", "Freelance", "Investimentos", "Vendas", "Bônus", "Outros (Receita)"
            ]]
        
        self.category_combo['values'] = categories
        if categories:
            self.category_combo.set(categories[0])
        
        # Atualizar sugestões de descrição
        self.desc_entry.on_focus_in(None)
    
    def on_description_change(self, event=None):
        """Evento quando descrição é alterada"""
        description = self.desc_entry.get().strip()
        if len(description) >= 3:
            self.suggest_category()
    
    def on_description_selected(self, event=None):
        """Evento quando descrição é selecionada do dropdown"""
        description = self.desc_entry.get().strip()
        if description:
            self.suggest_category()
            self.suggest_amount()
    
    def suggest_category(self):
        """Sugere categoria baseada na descrição"""
        description = self.desc_entry.get().strip()
        transaction_type = self.type_var.get().lower()
        
        if description and transaction_type:
            suggested_category = self.finance_manager.suggestion_engine.suggest_category(
                description, transaction_type
            )
            
            if suggested_category:
                self.category_var.set(suggested_category.value)
    
    def suggest_amount(self):
        """Sugere valor baseado na descrição"""
        description = self.desc_entry.get().strip()
        
        if description:
            suggested_amount = self.finance_manager.suggestion_engine.suggest_amount(description)
            
            if suggested_amount:
                self.amount_entry.delete(0, tk.END)
                self.amount_entry.insert(0, f"{suggested_amount:.2f}")
    
    def auto_fill_form(self):
        """Auto-preenche o formulário com sugestões"""
        self.suggest_category()
        self.suggest_amount()
    
    def set_today_date(self):
        """Define a data como hoje"""
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, datetime.now().strftime("%d/%m/%Y"))
    
    def clear_form(self):
        """Limpa o formulário"""
        self.desc_entry.delete(0, tk.END)
        self.amount_entry.delete(0, tk.END)
        self.type_var.set("")
        self.category_var.set("")
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.notes_text.delete("1.0", tk.END)
        self.category_combo['values'] = []
    
    def add_transaction(self):
        """Adiciona uma nova transação"""
        try:
            # Validar campos
            description = self.desc_entry.get().strip()
            if not description:
                messagebox.showerror("Erro", "Descrição é obrigatória!")
                return
            
            amount_str = self.amount_entry.get().strip().replace(",", ".")
            try:
                amount = float(amount_str)
                if amount <= 0:
                    raise ValueError("Valor deve ser positivo")
            except ValueError:
                messagebox.showerror("Erro", "Valor inválido!")
                return
            
            transaction_type_str = self.type_var.get()
            if not transaction_type_str:
                messagebox.showerror("Erro", "Selecione o tipo de transação!")
                return
            
            transaction_type = TransactionType.RECEITA if transaction_type_str == "Receita" else TransactionType.DESPESA
            
            category_str = self.category_var.get()
            if not category_str:
                messagebox.showerror("Erro", "Selecione uma categoria!")
                return
            
            category = Category(category_str)
            
            # Converter data
            date_str = self.date_entry.get().strip()
            try:
                date = datetime.strptime(date_str, "%d/%m/%Y")
            except ValueError:
                messagebox.showerror("Erro", "Data inválida! Use o formato DD/MM/AAAA")
                return
            
            notes = self.notes_text.get("1.0", tk.END).strip()
            
            # Adicionar transação
            success = self.finance_manager.add_transaction(
                description=description,
                amount=amount,
                transaction_type=transaction_type,
                category=category,
                date=date,
                notes=notes if notes else None
            )
            
            if success:
                messagebox.showinfo("Sucesso", "Transação adicionada com sucesso!")
                self.clear_form()
                self.refresh_data()
                self.update_quick_buttons()
            else:
                messagebox.showerror("Erro", "Erro ao adicionar transação!")
        
        except Exception as e:
            messagebox.showerror("Erro", f"Erro inesperado: {str(e)}")
    
    # ========================================================================
    # ABA: VISUALIZAR TRANSAÇÕES
    # ========================================================================
    
    def create_view_transactions_tab(self):
        """Cria a aba para visualizar transações"""
        self.view_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.view_frame, text="👁️ Visualizar")
        
        # Frame de filtros
        filter_frame = ttk.LabelFrame(self.view_frame, text="🔍 Filtros", padding=15)
        filter_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        # Filtro por período
        ttk.Label(filter_frame, text="Período:").grid(row=0, column=0, padx=5)
        self.period_var = tk.StringVar()
        period_combo = ttk.Combobox(filter_frame, textvariable=self.period_var,
                                   values=["Todos", "Hoje", "Esta semana", "Último mês", 
                                          "Últimos 3 meses", "Este ano"],
                                   state="readonly", width=15)
        period_combo.grid(row=0, column=1, padx=5)
        period_combo.set("Último mês")
        
        # Filtro por tipo
        ttk.Label(filter_frame, text="Tipo:").grid(row=0, column=2, padx=(20, 5))
        self.filter_type_var = tk.StringVar()
        type_filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_type_var,
                                        values=["Todos", "Receitas", "Despesas"],
                                        state="readonly", width=12)
        type_filter_combo.grid(row=0, column=3, padx=5)
        type_filter_combo.set("Todos")
        
        # Filtro por categoria
        ttk.Label(filter_frame, text="Categoria:").grid(row=0, column=4, padx=(20, 5))
        self.filter_category_var = tk.StringVar()
        self.category_filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_category_var,
                                                 state="readonly", width=15)
        self.category_filter_combo.grid(row=0, column=5, padx=5)
        
        # Botão atualizar
        ttk.Button(filter_frame, text="🔄 Atualizar", command=self.refresh_data).grid(row=0, column=6, padx=20)
        
        # Status
        self.status_label = ttk.Label(filter_frame, text="", foreground="green")
        self.status_label.grid(row=1, column=0, columnspan=7, pady=(10, 0))
        
        # Frame da tabela
        table_frame = ttk.LabelFrame(self.view_frame, text="📋 Transações", padding=15)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Treeview
        columns = ("Data", "Descrição", "Tipo", "Categoria", "Valor", "Observações")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        # Configurar colunas
        self.tree.heading("Data", text="Data")
        self.tree.heading("Descrição", text="Descrição")
        self.tree.heading("Tipo", text="Tipo")
        self.tree.heading("Categoria", text="Categoria")
        self.tree.heading("Valor", text="Valor (R$)")
        self.tree.heading("Observações", text="Observações")
        
        self.tree.column("Data", width=100)
        self.tree.column("Descrição", width=200)
        self.tree.column("Tipo", width=100)
        self.tree.column("Categoria", width=150)
        self.tree.column("Valor", width=120)
        self.tree.column("Observações", width=150)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Posicionar treeview e scrollbars
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Frame de ações
        action_frame = ttk.Frame(self.view_frame)
        action_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(action_frame, text="❌ Excluir Selecionado", 
                  command=self.delete_transaction).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="📊 Exportar", 
                  command=self.export_transactions).pack(side=tk.LEFT, padx=5)
        
        # Estatísticas rápidas
        stats_frame = ttk.LabelFrame(action_frame, text="📈 Estatísticas Rápidas")
        stats_frame.pack(side=tk.RIGHT, padx=(20, 0))
        
        self.stats_label = ttk.Label(stats_frame, text="", font=('Arial', 9))
        self.stats_label.pack(padx=10, pady=5)
        
        self.update_status()
    
    def update_status(self):
        """Atualiza status da database e filtros"""
        db_path = self.finance_manager.config_manager.get_database_path()
        short_path = "..." + db_path[-40:] if len(db_path) > 40 else db_path
        
        total_transactions = len(self.finance_manager.transactions)
        last_backup = "Nunca"
        
        backups = self.finance_manager.list_backups()
        if backups:
            last_backup = backups[0]['modified'].strftime("%d/%m/%Y %H:%M")
        
        status_text = f"📂 {short_path} | 📊 {total_transactions} transações | 💾 Último backup: {last_backup}"
        self.status_label.config(text=status_text)
        
        # Atualizar filtro de categorias
        all_categories = ["Todos"] + [cat.value for cat in Category]
        self.category_filter_combo['values'] = all_categories
        if not self.filter_category_var.get():
            self.filter_category_var.set("Todos")
    
    def export_transactions(self):
        """Exporta transações para CSV"""
        try:
            file_path = filedialog.asksaveasfilename(
                title="Exportar Transações",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if file_path:
                transactions = self._get_filtered_transactions()
                
                with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
                    import csv
                    writer = csv.writer(f, delimiter=';')
                    
                    # Cabeçalho
                    writer.writerow(['Data', 'Descrição', 'Tipo', 'Categoria', 'Valor', 'Observações'])
                    
                    # Dados
                    for transaction in transactions:
                        writer.writerow([
                            transaction.date.strftime("%d/%m/%Y"),
                            transaction.description,
                            "Receita" if transaction.transaction_type == TransactionType.RECEITA else "Despesa",
                            transaction.category.value,
                            f"{transaction.amount:.2f}".replace(".", ","),
                            transaction.notes or ""
                        ])
                
                messagebox.showinfo("Sucesso", f"Transações exportadas para:\n{file_path}")
        
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar: {e}")
    
    def _get_filtered_transactions(self) -> List[Transaction]:
        """Obtém transações filtradas pelos critérios atuais"""
        # Filtro por período
        period = self.period_var.get()
        start_date = None
        
        if period == "Hoje":
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "Esta semana":
            start_date = datetime.now() - timedelta(days=datetime.now().weekday())
        elif period == "Último mês":
            start_date = datetime.now() - timedelta(days=30)
        elif period == "Últimos 3 meses":
            start_date = datetime.now() - timedelta(days=90)
        elif period == "Este ano":
            start_date = datetime(datetime.now().year, 1, 1)
        
        transactions = self.finance_manager.get_transactions(start_date)
        
        # Filtro por tipo
        filter_type = self.filter_type_var.get()
        if filter_type == "Receitas":
            transactions = [t for t in transactions if t.transaction_type == TransactionType.RECEITA]
        elif filter_type == "Despesas":
            transactions = [t for t in transactions if t.transaction_type == TransactionType.DESPESA]
        
        # Filtro por categoria
        filter_category = self.filter_category_var.get()
        if filter_category and filter_category != "Todos":
            transactions = [t for t in transactions if t.category.value == filter_category]
        
        return transactions
    
    def delete_transaction(self):
        """Exclui a transação selecionada"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma transação para excluir!")
            return
        
        if messagebox.askyesno("Confirmação", "Tem certeza que deseja excluir esta transação?"):
            item = selection[0]
            transaction_id = self.tree.item(item)['tags'][0]
            
            if self.finance_manager.remove_transaction(transaction_id):
                messagebox.showinfo("Sucesso", "Transação excluída com sucesso!")
                self.refresh_data()
                self.update_quick_buttons()
            else:
                messagebox.showerror("Erro", "Erro ao excluir transação!")
    
    # ========================================================================
    # ABA: RELATÓRIOS
    # ========================================================================
    
    def create_reports_tab(self):
        """Cria a aba de relatórios"""
        self.reports_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.reports_frame, text="📊 Relatórios")
        
        # Frame superior com resumo
        summary_frame = ttk.LabelFrame(self.reports_frame, text="💰 Resumo Financeiro", padding=20)
        summary_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Grid para valores
        self.balance_labels = {}
        
        # Primeira linha - Receitas e Despesas
        ttk.Label(summary_frame, text="Receitas:", font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.balance_labels["Receitas:"] = ttk.Label(summary_frame, text="R$ 0,00", style='BigValue.TLabel', foreground='green')
        self.balance_labels["Receitas:"].grid(row=0, column=1, sticky=tk.W, padx=20, pady=5)
        
        ttk.Label(summary_frame, text="Despesas:", font=('Arial', 12, 'bold')).grid(row=0, column=2, sticky=tk.W, pady=5, padx=(40, 0))
        self.balance_labels["Despesas:"] = ttk.Label(summary_frame, text="R$ 0,00", style='BigValue.TLabel', foreground='red')
        self.balance_labels["Despesas:"].grid(row=0, column=3, sticky=tk.W, padx=20, pady=5)
        
        # Segunda linha - Saldo
        ttk.Label(summary_frame, text="Saldo:", font=('Arial', 14, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=10)
        self.balance_labels["Saldo:"] = ttk.Label(summary_frame, text="R$ 0,00", font=('Arial', 16, 'bold'))
        self.balance_labels["Saldo:"].grid(row=1, column=1, columnspan=3, sticky=tk.W, padx=20, pady=10)
        
        # Frame inferior dividido em duas colunas
        content_frame = ttk.Frame(self.reports_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Coluna esquerda - Categorias
        left_frame = ttk.LabelFrame(content_frame, text="📈 Gastos por Categoria", padding=15)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Treeview para categorias
        cat_columns = ("Categoria", "Valor", "Percentual", "Transações")
        self.cat_tree = ttk.Treeview(left_frame, columns=cat_columns, show="headings", height=12)
        
        for col in cat_columns:
            self.cat_tree.heading(col, text=col)
        
        self.cat_tree.column("Categoria", width=120)
        self.cat_tree.column("Valor", width=100)
        self.cat_tree.column("Percentual", width=80)
        self.cat_tree.column("Transações", width=80)
        
        cat_scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.cat_tree.yview)
        self.cat_tree.configure(yscrollcommand=cat_scrollbar.set)
        
        self.cat_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Coluna direita - Estatísticas mensais
        right_frame = ttk.LabelFrame(content_frame, text="📅 Resumo Mensal", padding=15)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Seletor de mês/ano
        month_frame = ttk.Frame(right_frame)
        month_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(month_frame, text="Mês/Ano:").pack(side=tk.LEFT)
        
        self.month_var = tk.StringVar()
        month_combo = ttk.Combobox(month_frame, textvariable=self.month_var, width=15, state="readonly")
        month_combo.pack(side=tk.LEFT, padx=10)
        
        # Gerar opções de mês/ano
        months = []
        current_date = datetime.now()
        for i in range(12):  # Últimos 12 meses
            date = current_date - timedelta(days=30*i)
            month_text = date.strftime("%m/%Y")
            months.append(month_text)
        
        month_combo['values'] = months
        month_combo.set(current_date.strftime("%m/%Y"))
        month_combo.bind('<<ComboboxSelected>>', self.update_monthly_report)
        
        # Área de texto para estatísticas mensais
        self.monthly_text = tk.Text(right_frame, height=12, width=30, font=('Arial', 10))
        self.monthly_text.pack(fill=tk.BOTH, expand=True)
        
        monthly_scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.monthly_text.yview)
        self.monthly_text.configure(yscrollcommand=monthly_scrollbar.set)
        monthly_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Atualizar relatório mensal inicial
        self.update_monthly_report()
    
    def update_monthly_report(self, event=None):
        """Atualiza o relatório mensal"""
        try:
            month_year = self.month_var.get()
            if not month_year:
                return
            
            month, year = map(int, month_year.split('/'))
            
            # Calcular período do mês
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            
            # Obter dados do mês
            transactions = self.finance_manager.get_transactions(start_date, end_date)
            balance = self.finance_manager.calculate_balance(start_date, end_date)
            categories = self.finance_manager.get_category_summary(start_date, end_date)
            
            # Montar relatório
            report = f"📅 RELATÓRIO DE {month:02d}/{year}\n"
            report += "=" * 30 + "\n\n"
            
            report += f"💰 RESUMO FINANCEIRO:\n"
            report += f"   Receitas: R$ {balance['receitas']:,.2f}\n"
            report += f"   Despesas: R$ {balance['despesas']:,.2f}\n"
            report += f"   Saldo: R$ {balance['saldo']:,.2f}\n\n"
            
            report += f"📊 ESTATÍSTICAS:\n"
            report += f"   Total de transações: {len(transactions)}\n"
            report += f"   Ticket médio: R$ {(balance['receitas'] + balance['despesas']) / max(len(transactions), 1):,.2f}\n\n"
            
            if categories['despesas']:
                report += f"💸 TOP 5 CATEGORIAS (DESPESAS):\n"
                sorted_categories = sorted(categories['despesas'].items(), key=lambda x: x[1], reverse=True)
                for i, (cat, amount) in enumerate(sorted_categories[:5], 1):
                    percentage = (amount / balance['despesas'] * 100) if balance['despesas'] > 0 else 0
                    report += f"   {i}. {cat}: R$ {amount:,.2f} ({percentage:.1f}%)\n"
            
            # Atualizar widget de texto
            self.monthly_text.delete(1.0, tk.END)
            self.monthly_text.insert(1.0, report)
            
        except Exception as e:
            print(f"Erro ao atualizar relatório mensal: {e}")
    
    # ========================================================================
    # ABA: SUGESTÕES
    # ========================================================================
    
    def create_suggestions_tab(self):
        """Cria a aba de configurações de sugestões"""
        self.suggestions_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.suggestions_frame, text="💡 Sugestões")
        
        # Frame de estatísticas
        stats_frame = ttk.LabelFrame(self.suggestions_frame, text="📊 Estatísticas do Sistema", padding=20)
        stats_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Grid de estatísticas
        self.stats_labels = {}
        stats_info = [
            ("Total de Descrições:", "total_descriptions"),
            ("Descrições Únicas:", "unique_descriptions"),
            ("Palavras-chave Aprendidas:", "keywords_learned"),
            ("Padrões de Categoria:", "category_patterns"),
            ("Última Atualização:", "last_update"),
            ("Status das Sugestões:", "suggestions_status")
        ]
        
        for i, (label, key) in enumerate(stats_info):
            row = i // 2
            col = (i % 2) * 2
            
            ttk.Label(stats_frame, text=label, font=('Arial', 10, 'bold')).grid(
                row=row, column=col, sticky=tk.W, pady=5, padx=(0, 10)
            )
            value_label = ttk.Label(stats_frame, text="Carregando...", font=('Arial', 10))
            value_label.grid(row=row, column=col+1, sticky=tk.W, pady=5, padx=(0, 40))
            self.stats_labels[key] = value_label
        
        # Frame de configurações
        config_frame = ttk.LabelFrame(self.suggestions_frame, text="⚙️ Configurações", padding=20)
        config_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Habilitar/desabilitar sugestões
        self.suggestions_enabled_var = tk.BooleanVar()
        ttk.Checkbutton(config_frame, text="Habilitar Sistema de Sugestões", 
                       variable=self.suggestions_enabled_var, 
                       command=self.toggle_suggestions).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # Máximo de sugestões
        ttk.Label(config_frame, text="Máximo de Sugestões:").grid(row=0, column=1, sticky=tk.W, pady=5, padx=(40, 5))
        self.max_suggestions_var = tk.StringVar()
        max_suggestions_spinbox = ttk.Spinbox(config_frame, from_=5, to=20, width=10, 
                                            textvariable=self.max_suggestions_var)
        max_suggestions_spinbox.grid(row=0, column=2, sticky=tk.W, pady=5, padx=10)
        max_suggestions_spinbox.bind('<FocusOut>', self.update_max_suggestions)
        
        # Botões de controle
        btn_frame = ttk.Frame(config_frame)
        btn_frame.grid(row=1, column=0, columnspan=3, pady=20)
        
        ttk.Button(btn_frame, text="🔄 Atualizar Sugestões", 
                  command=self.manual_update_suggestions).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🧹 Limpar Cache", 
                  command=self.clear_suggestions_cache).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📊 Atualizar Estatísticas", 
                  command=self.update_suggestions_stats).pack(side=tk.LEFT, padx=5)
        
        # Frame de análises
        analysis_frame = ttk.LabelFrame(self.suggestions_frame, text="📈 Padrões Detectados", padding=20)
        analysis_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Treeview para mostrar padrões
        columns = ("Palavra-chave", "Categoria Sugerida", "Frequência", "Confiança")
        self.patterns_tree = ttk.Treeview(analysis_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.patterns_tree.heading(col, text=col)
            self.patterns_tree.column(col, width=150)
        
        patterns_scrollbar = ttk.Scrollbar(analysis_frame, orient=tk.VERTICAL, command=self.patterns_tree.yview)
        self.patterns_tree.configure(yscrollcommand=patterns_scrollbar.set)
        
        self.patterns_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        patterns_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Carregar configurações
        self.load_suggestions_config()
        self.update_suggestions_stats()
    
    def load_suggestions_config(self):
        """Carrega configurações de sugestões"""
        config = self.finance_manager.config_manager
        self.suggestions_enabled_var.set(config.get("suggestions_enabled", True))
        self.max_suggestions_var.set(str(config.get("max_suggestions", 10)))
    
    def toggle_suggestions(self):
        """Habilita/desabilita sistema de sugestões"""
        enabled = self.suggestions_enabled_var.get()
        self.finance_manager.config_manager.set("suggestions_enabled", enabled)
        
        if enabled:
            self.finance_manager.update_suggestions()
        
        messagebox.showinfo("Configuração", 
                          f"Sugestões {'habilitadas' if enabled else 'desabilitadas'} com sucesso!")
    
    def update_max_suggestions(self, event=None):
        """Atualiza máximo de sugestões"""
        try:
            max_suggestions = int(self.max_suggestions_var.get())
            max_suggestions = max(5, min(20, max_suggestions))  # Entre 5 e 20
            
            self.finance_manager.config_manager.set("max_suggestions", max_suggestions)
            self.max_suggestions_var.set(str(max_suggestions))
        except ValueError:
            self.max_suggestions_var.set("10")
    
    def manual_update_suggestions(self):
        """Atualiza sugestões manualmente"""
        self.finance_manager.update_suggestions()
        self.update_suggestions_stats()
        messagebox.showinfo("Sucesso", "Sugestões atualizadas com sucesso!")
    
    def clear_suggestions_cache(self):
        """Limpa cache de sugestões"""
        if messagebox.askyesno("Confirmação", "Tem certeza que deseja limpar o cache de sugestões?"):
            self.finance_manager.suggestion_engine = SmartSuggestionEngine()
            self.finance_manager.update_suggestions()
            self.update_suggestions_stats()
            messagebox.showinfo("Sucesso", "Cache de sugestões limpo!")
    
    def update_suggestions_stats(self):
        """Atualiza estatísticas das sugestões"""
        try:
            stats = self.finance_manager.suggestion_engine.get_statistics()
            config = self.finance_manager.config_manager
            
            # Atualizar labels
            self.stats_labels["total_descriptions"].config(text=str(stats['total_descriptions']))
            self.stats_labels["unique_descriptions"].config(text=str(stats['unique_descriptions']))
            self.stats_labels["keywords_learned"].config(text=str(stats['keywords_learned']))
            self.stats_labels["category_patterns"].config(text=str(stats['category_patterns']))
            
            last_update = stats['last_update'].strftime("%d/%m/%Y %H:%M") if stats['last_update'] else "Nunca"
            self.stats_labels["last_update"].config(text=last_update)
            
            suggestions_status = "✅ Habilitado" if config.get("suggestions_enabled", True) else "❌ Desabilitado"
            self.stats_labels["suggestions_status"].config(text=suggestions_status)
            
            # Atualizar padrões detectados
            for item in self.patterns_tree.get_children():
                self.patterns_tree.delete(item)
            
            engine = self.finance_manager.suggestion_engine
            pattern_items = []
            
            for keyword, categories in engine.category_patterns.items():
                if categories:
                    category_counter = Counter(categories)
                    most_common = category_counter.most_common(1)[0]
                    category_name = most_common[0].value
                    frequency = most_common[1]
                    confidence = (frequency / len(categories)) * 100
                    
                    pattern_items.append((keyword, category_name, frequency, confidence))
            
            # Ordenar por frequência
            pattern_items.sort(key=lambda x: x[2], reverse=True)
            
            for keyword, category, frequency, confidence in pattern_items[:20]:
                self.patterns_tree.insert("", tk.END, values=(
                    keyword.title(),
                    category,
                    f"{frequency}x",
                    f"{confidence:.1f}%"
                ))
                
        except Exception as e:
            print(f"Erro ao atualizar estatísticas: {e}")
    
    # ========================================================================
    # ABA: BACKUP
    # ========================================================================
    
    def create_backup_tab(self):
        """Cria a aba de backup e configurações"""
        self.backup_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.backup_frame, text="💾 Backup")
        
        # Frame de backup
        backup_frame = ttk.LabelFrame(self.backup_frame, text="💾 Gerenciar Backups", padding=20)
        backup_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Botões de backup
        button_frame = ttk.Frame(backup_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame, text="💾 Criar Backup Agora", 
                  command=self.create_manual_backup, style='Action.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📂 Restaurar Backup", 
                  command=self.restore_backup_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔄 Atualizar Lista", 
                  command=self.refresh_backup_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📁 Abrir Pasta", 
                  command=self.open_backup_folder).pack(side=tk.LEFT, padx=5)
        
        # Lista de backups
        list_frame = ttk.Frame(backup_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        backup_columns = ("Nome do Arquivo", "Data", "Tamanho")
        self.backup_tree = ttk.Treeview(list_frame, columns=backup_columns, show="headings", height=8)
        
        for col in backup_columns:
            self.backup_tree.heading(col, text=col)
        
        self.backup_tree.column("Nome do Arquivo", width=250)
        self.backup_tree.column("Data", width=150)
        self.backup_tree.column("Tamanho", width=100)
        
        backup_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.backup_tree.yview)
        self.backup_tree.configure(yscrollcommand=backup_scrollbar.set)
        
        self.backup_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        backup_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Frame de configurações
        config_frame = ttk.LabelFrame(self.backup_frame, text="⚙️ Configurações", padding=20)
        config_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Localização da database
        ttk.Label(config_frame, text="📂 Local dos Dados:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.db_path_var = tk.StringVar()
        self.db_path_entry = ttk.Entry(config_frame, textvariable=self.db_path_var, width=60, state="readonly")
        self.db_path_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5, padx=10)
        ttk.Button(config_frame, text="📁 Alterar", command=self.change_db_location).grid(row=0, column=2, pady=5)
        
        # Configurações de backup automático
        ttk.Label(config_frame, text="⚡ Backup Automático:", font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        auto_frame = ttk.Frame(config_frame)
        auto_frame.grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=5, padx=10)
        
        self.auto_backup_var = tk.BooleanVar()
        ttk.Checkbutton(auto_frame, text="Habilitado", 
                       variable=self.auto_backup_var, command=self.update_auto_backup).pack(side=tk.LEFT)
        
        ttk.Label(auto_frame, text="Intervalo:").pack(side=tk.LEFT, padx=(20, 5))
        self.backup_interval_var = tk.StringVar()
        interval_spinbox = ttk.Spinbox(auto_frame, from_=1, to=30, width=10, 
                                     textvariable=self.backup_interval_var)
        interval_spinbox.pack(side=tk.LEFT)
        interval_spinbox.bind('<FocusOut>', self.update_backup_interval)
        ttk.Label(auto_frame, text="dias").pack(side=tk.LEFT, padx=(5, 0))
        
        # Configurar grid
        config_frame.columnconfigure(1, weight=1)
        
        # Carregar configurações atuais
        self.load_current_config()
        self.refresh_backup_list()
    
    def load_current_config(self):
        """Carrega configurações atuais"""
        config = self.finance_manager.config_manager
        
        self.db_path_var.set(config.get_database_path())
        self.auto_backup_var.set(config.get("auto_backup", True))
        self.backup_interval_var.set(str(config.get("backup_interval_days", 7)))
    
    def create_manual_backup(self):
        """Cria backup manual"""
        if self.finance_manager.create_backup():
            messagebox.showinfo("Sucesso", "✅ Backup criado com sucesso!")
            self.refresh_backup_list()
        else:
            messagebox.showerror("Erro", "❌ Erro ao criar backup!")
    
    def restore_backup_dialog(self):
        """Diálogo para restaurar backup"""
        selection = self.backup_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um backup para restaurar!")
            return
        
        item = selection[0]
        backup_filename = self.backup_tree.item(item)['values'][0]
        
        if messagebox.askyesno("⚠️ Confirmação", 
                              f"Tem certeza que deseja restaurar o backup:\n\n{backup_filename}\n\n"
                              "⚠️ ATENÇÃO: Os dados atuais serão substituídos!\n"
                              "Um backup dos dados atuais será criado automaticamente."):
            if self.finance_manager.restore_backup(backup_filename):
                messagebox.showinfo("Sucesso", "✅ Backup restaurado com sucesso!")
                self.refresh_data()
                self.update_suggestions_stats()
                self.update_quick_buttons()
            else:
                messagebox.showerror("Erro", "❌ Erro ao restaurar backup!")
    
    def open_backup_folder(self):
        """Abre a pasta de backups no explorador"""
        backup_path = self.finance_manager.config_manager.get("backup_path")
        if backup_path and os.path.exists(backup_path):
            try:
                if sys.platform.startswith('win'):
                    os.startfile(backup_path)
                elif sys.platform.startswith('darwin'):
                    os.system(f'open "{backup_path}"')
                else:
                    os.system(f'xdg-open "{backup_path}"')
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao abrir pasta: {e}")
        else:
            messagebox.showwarning("Aviso", "Pasta de backup não encontrada!")
    
    def refresh_backup_list(self):
        """Atualiza lista de backups"""
        # Limpar lista atual
        for item in self.backup_tree.get_children():
            self.backup_tree.delete(item)
        
        # Carregar backups
        backups = self.finance_manager.list_backups()
        
        for backup in backups:
            size_kb = backup['size'] / 1024
            if size_kb < 1024:
                size_text = f"{size_kb:.1f} KB"
            else:
                size_text = f"{size_kb/1024:.1f} MB"
            
            date_text = backup['modified'].strftime("%d/%m/%Y %H:%M")
            
            self.backup_tree.insert("", tk.END, values=(
                backup['filename'],
                date_text,
                size_text
            ))
    
    def change_db_location(self):
        """Altera localização da database"""
        new_path = filedialog.asksaveasfilename(
            title="Escolher nova localização dos dados",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="financial_data.json"
        )
        
        if new_path:
            if messagebox.askyesno("Confirmação", 
                                  f"Alterar localização dos dados para:\n\n{new_path}\n\n"
                                  "Os dados atuais serão movidos para o novo local. Continuar?"):
                try:
                    # Fazer backup dos dados atuais
                    self.finance_manager.create_backup()
                    
                    # Atualizar configuração e salvar dados na nova localização
                    self.finance_manager.config_manager.set("database_path", new_path)
                    self.finance_manager.data_file = new_path
                    self.finance_manager.save_data()
                    
                    # Atualizar interface
                    self.db_path_var.set(new_path)
                    self.update_status()
                    
                    messagebox.showinfo("Sucesso", "✅ Localização alterada com sucesso!")
                    
                except Exception as e:
                    messagebox.showerror("Erro", f"❌ Erro ao alterar localização: {e}")
    
    def update_auto_backup(self):
        """Atualiza configuração de backup automático"""
        self.finance_manager.config_manager.set("auto_backup", self.auto_backup_var.get())
    
    def update_backup_interval(self, event=None):
        """Atualiza intervalo de backup"""
        try:
            interval = int(self.backup_interval_var.get())
            interval = max(1, min(30, interval))  # Entre 1 e 30 dias
            
            self.finance_manager.config_manager.set("backup_interval_days", interval)
            self.backup_interval_var.set(str(interval))
        except ValueError:
            self.backup_interval_var.set("7")  # Valor padrão
    
    # ========================================================================
    # ABA: CONFIGURAÇÕES
    # ========================================================================
    
    def create_settings_tab(self):
        """Cria a aba de configurações gerais"""
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="⚙️ Configurações")
        
        # Frame de aparência
        appearance_frame = ttk.LabelFrame(self.settings_frame, text="🎨 Aparência", padding=20)
        appearance_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Tema
        ttk.Label(appearance_frame, text="Tema:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.theme_var = tk.StringVar()
        theme_combo = ttk.Combobox(appearance_frame, textvariable=self.theme_var,
                                  values=["clam", "alt", "default", "classic"], state="readonly")
        theme_combo.grid(row=0, column=1, sticky=tk.W, pady=5, padx=10)
        theme_combo.bind('<<ComboboxSelected>>', self.change_theme)
        
        # Tamanho da janela
        ttk.Label(appearance_frame, text="Tamanho da Janela:", font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        size_frame = ttk.Frame(appearance_frame)
        size_frame.grid(row=1, column=1, sticky=tk.W, pady=5, padx=10)
        
        self.width_var = tk.StringVar()
        self.height_var = tk.StringVar()
        
        ttk.Entry(size_frame, textvariable=self.width_var, width=8).pack(side=tk.LEFT)
        ttk.Label(size_frame, text="x").pack(side=tk.LEFT, padx=5)
        ttk.Entry(size_frame, textvariable=self.height_var, width=8).pack(side=tk.LEFT)
        ttk.Button(size_frame, text="Aplicar", command=self.apply_window_size).pack(side=tk.LEFT, padx=(10, 0))
        
        # Frame de informações
        info_frame = ttk.LabelFrame(self.settings_frame, text="ℹ️ Informações do Sistema", padding=20)
        info_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Informações
        info_text = f"""
📱 Aplicação: {self.finance_manager.config_manager.get('app_name')}
🔢 Versão: {self.finance_manager.config_manager.get('version')}
📊 Total de Transações: {len(self.finance_manager.transactions)}
💾 Localização dos Dados: {self.finance_manager.config_manager.get_database_path()}
🐍 Python: {sys.version.split()[0]}
🖥️ Sistema: {sys.platform}
        """.strip()
        
        info_label = ttk.Label(info_frame, text=info_text, font=('Arial', 10))
        info_label.pack(anchor=tk.W)
        
        # Frame de ações
        actions_frame = ttk.LabelFrame(self.settings_frame, text="🔧 Ações", padding=20)
        actions_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Botões de ação
        action_buttons_frame = ttk.Frame(actions_frame)
        action_buttons_frame.pack()
        
        ttk.Button(action_buttons_frame, text="🔄 Recarregar Dados", 
                  command=self.reload_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_buttons_frame, text="🧹 Limpar Cache", 
                  command=self.clear_all_cache).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_buttons_frame, text="📋 Copiar Info Sistema", 
                  command=self.copy_system_info).pack(side=tk.LEFT, padx=5)
        
        # Carregar configurações atuais
        self.load_settings_config()
    
    def load_settings_config(self):
        """Carrega configurações de interface"""
        config = self.finance_manager.config_manager
        
        self.theme_var.set(config.get('theme', 'clam'))
        self.width_var.set(str(config.get('window_width', 1000)))
        self.height_var.set(str(config.get('window_height', 800)))
    
    def change_theme(self, event=None):
        """Altera o tema da interface"""
        new_theme = self.theme_var.get()
        try:
            self.style.theme_use(new_theme)
            self.finance_manager.config_manager.set('theme', new_theme)
            messagebox.showinfo("Tema", f"Tema alterado para: {new_theme}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao alterar tema: {e}")
    
    def apply_window_size(self):
        """Aplica novo tamanho de janela"""
        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            
            # Validar limites
            width = max(900, min(1920, width))
            height = max(700, min(1080, height))
            
            self.root.geometry(f"{width}x{height}")
            
            # Salvar configurações
            self.finance_manager.config_manager.set('window_width', width)
            self.finance_manager.config_manager.set('window_height', height)
            
            # Atualizar variáveis se foram ajustadas
            self.width_var.set(str(width))
            self.height_var.set(str(height))
            
            messagebox.showinfo("Tamanho", f"Tamanho da janela alterado para: {width}x{height}")
            
        except ValueError:
            messagebox.showerror("Erro", "Valores de tamanho inválidos!")
    
    def reload_data(self):
        """Recarrega todos os dados"""
        try:
            self.finance_manager.load_data()
            self.finance_manager.update_suggestions()
            self.refresh_data()
            self.update_suggestions_stats()
            self.update_quick_buttons()
            messagebox.showinfo("Sucesso", "✅ Dados recarregados com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"❌ Erro ao recarregar dados: {e}")
    
    def clear_all_cache(self):
        """Limpa todos os caches do sistema"""
        if messagebox.askyesno("Confirmação", "Tem certeza que deseja limpar todos os caches?"):
            try:
                # Limpar cache de sugestões
                self.finance_manager.suggestion_engine = SmartSuggestionEngine()
                self.finance_manager.update_suggestions()
                
                # Atualizar interface
                self.update_suggestions_stats()
                self.update_quick_buttons()
                
                messagebox.showinfo("Sucesso", "✅ Cache limpo com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"❌ Erro ao limpar cache: {e}")
    
    def copy_system_info(self):
        """Copia informações do sistema para a área de transferência"""
        try:
            config = self.finance_manager.config_manager
            
            info = f"""Sistema de Controle Financeiro - Informações
============================================
Aplicação: {config.get('app_name')}
Versão: {config.get('version')}
Total de Transações: {len(self.finance_manager.transactions)}
Localização dos Dados: {config.get_database_path()}
Python: {sys.version.split()[0]}
Sistema: {sys.platform}
Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

Estatísticas de Sugestões:
{self.finance_manager.suggestion_engine.get_statistics()}

Configurações:
- Backup Automático: {config.get('auto_backup', True)}
- Intervalo de Backup: {config.get('backup_interval_days', 7)} dias
- Sugestões Habilitadas: {config.get('suggestions_enabled', True)}
- Máximo de Sugestões: {config.get('max_suggestions', 10)}
- Tema: {config.get('theme', 'clam')}
"""
            
            self.root.clipboard_clear()
            self.root.clipboard_append(info)
            messagebox.showinfo("Sucesso", "✅ Informações copiadas para a área de transferência!")
            
        except Exception as e:
            messagebox.showerror("Erro", f"❌ Erro ao copiar informações: {e}")
    
    # ========================================================================
    # MÉTODOS AUXILIARES
    # ========================================================================
    
    def refresh_data(self):
        """Atualiza todos os dados exibidos nas abas"""
        try:
            # Atualizar aba de visualização
            self._refresh_transactions_view()
            
            # Atualizar aba de relatórios
            self._refresh_reports()
            
            # Atualizar status
            self.update_status()
            
        except Exception as e:
            print(f"Erro ao atualizar dados: {e}")
    
    def _refresh_transactions_view(self):
        """Atualiza a visualização de transações"""
        # Limpar tabela atual
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Obter transações filtradas
        transactions = self._get_filtered_transactions()
        
        # Adicionar transações à tabela
        for transaction in transactions:
            tipo = "Receita" if transaction.transaction_type == TransactionType.RECEITA else "Despesa"
            valor = f"R$ {transaction.amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
            # Cor da linha baseada no tipo
            tags = [transaction.id]
            if transaction.transaction_type == TransactionType.RECEITA:
                tags.append("receita")
            else:
                tags.append("despesa")
            
            self.tree.insert("", tk.END, values=(
                transaction.date.strftime("%d/%m/%Y"),
                transaction.description,
                tipo,
                transaction.category.value,
                valor,
                transaction.notes[:30] + "..." if transaction.notes and len(transaction.notes) > 30 else transaction.notes or ""
            ), tags=tuple(tags))
        
        # Configurar cores das linhas
        self.tree.tag_configure("receita", background="#e8f5e8")
        self.tree.tag_configure("despesa", background="#ffe8e8")
        
        # Atualizar estatísticas rápidas
        if transactions:
            total_receitas = sum(t.amount for t in transactions if t.transaction_type == TransactionType.RECEITA)
            total_despesas = sum(t.amount for t in transactions if t.transaction_type == TransactionType.DESPESA)
            saldo = total_receitas - total_despesas
            
            stats_text = f"Transações: {len(transactions)} | Saldo: R$ {saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            self.stats_label.config(text=stats_text)
            
            # Cor do saldo
            color = "green" if saldo >= 0 else "red"
            self.stats_label.config(foreground=color)
        else:
            self.stats_label.config(text="Nenhuma transação encontrada", foreground="gray")
    
    def _refresh_reports(self):
        """Atualiza os relatórios"""
        # Determinar período para relatórios (último mês por padrão)
        start_date = datetime.now() - timedelta(days=30)
        
        # Calcular balanço
        balance = self.finance_manager.calculate_balance(start_date)
        
        # Atualizar labels de resumo financeiro
        for label, value in [
            ("Receitas:", balance['receitas']),
            ("Despesas:", balance['despesas']),
            ("Saldo:", balance['saldo'])
        ]:
            formatted_value = f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            self.balance_labels[label].config(text=formatted_value)
            
            # Cores especiais
            if label == "Receitas:":
                self.balance_labels[label].config(foreground='green')
            elif label == "Despesas:":
                self.balance_labels[label].config(foreground='red')
            elif label == "Saldo:":
                color = "green" if value >= 0 else "red"
                self.balance_labels[label].config(foreground=color)
        
        # Atualizar tabela de categorias
        for item in self.cat_tree.get_children():
            self.cat_tree.delete(item)
        
        categories = self.finance_manager.get_category_summary(start_date)
        
        # Processar despesas por categoria
        if categories['despesas']:
            total_despesas = sum(categories['despesas'].values())
            transactions_by_category = defaultdict(int)
            
            # Contar transações por categoria
            for transaction in self.finance_manager.get_transactions(start_date):
                if transaction.transaction_type == TransactionType.DESPESA:
                    transactions_by_category[transaction.category.value] += 1
            
            # Ordenar por valor
            sorted_categories = sorted(categories['despesas'].items(), key=lambda x: x[1], reverse=True)
            
            for category, amount in sorted_categories:
                percentage = (amount / total_despesas * 100) if total_despesas > 0 else 0
                formatted_amount = f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                transaction_count = transactions_by_category[category]
                
                self.cat_tree.insert("", tk.END, values=(
                    category,
                    formatted_amount,
                    f"{percentage:.1f}%",
                    f"{transaction_count}x"
                ))
        
        # Atualizar relatório mensal
        self.update_monthly_report()
    
    def on_closing(self):
        """Evento de fechamento da aplicação"""
        try:
            # Salvar configurações da janela
            geometry = self.root.geometry()
            width, height = geometry.split('+')[0].split('x')
            
            self.finance_manager.config_manager.set('window_width', int(width))
            self.finance_manager.config_manager.set('window_height', int(height))
            
            # Criar backup automático se necessário
            if self.finance_manager.config_manager.get("auto_backup", True):
                backups = self.finance_manager.list_backups()
                if not backups or len(backups) == 0:
                    self.finance_manager.create_backup()
            
            # Fechar aplicação
            self.root.destroy()
            
        except Exception as e:
            print(f"Erro ao fechar aplicação: {e}")
            self.root.destroy()

# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    """Função principal da aplicação"""
    try:
        # Configurar diretório de trabalho
        if hasattr(sys, '_MEIPASS'):
            # Executando como executável PyInstaller
            work_dir = os.path.dirname(sys.executable)
        else:
            # Executando como script Python
            work_dir = os.path.dirname(os.path.abspath(__file__))
        
        os.chdir(work_dir)
        
        # Criar e executar aplicação
        root = tk.Tk()
        app = FinanceApp(root)
        
        # Configurar ícone se disponível
        try:
            root.iconbitmap('icon.ico')
        except:
            pass
        
        # Executar loop principal
        root.mainloop()
        
    except Exception as e:
        # Em caso de erro, mostrar mensagem e aguardar input
        print(f"❌ Erro crítico ao iniciar aplicação: {e}")
        import traceback
        traceback.print_exc()
        
        # Se for executável, aguardar input para não fechar imediatamente
        if hasattr(sys, '_MEIPASS'):
            input("Pressione Enter para sair...")

if __name__ == "__main__":
    main()