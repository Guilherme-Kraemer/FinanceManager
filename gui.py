import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
from typing import Optional
from finance_manager import FinanceManager
from models import TransactionType, Category

class FinanceApp:
    """Classe principal da interface gráfica atualizada"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.finance_manager = FinanceManager()
        
        self.setup_window()
        self.create_widgets()
        self.refresh_data()
    
    def setup_window(self):
        """Configura a janela principal"""
        self.root.title("Controle Econômico Pessoal - v1.0")
        self.root.geometry("950x750")
        self.root.resizable(True, True)
        
        # Configurar estilo
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurar ícone da janela (se existir)
        try:
            self.root.iconbitmap('assets/icon.ico')
        except:
            pass
    
    def create_widgets(self):
        """Cria todos os widgets da interface"""
        # Notebook para abas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Criar abas
        self.create_add_transaction_tab()
        self.create_view_transactions_tab()
        self.create_reports_tab()
        self.create_backup_tab()  # NOVA ABA
    
    def create_add_transaction_tab(self):
        """Cria a aba para adicionar transações"""
        self.add_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.add_frame, text="Adicionar Transação")
        
        # Frame principal
        main_frame = ttk.LabelFrame(self.add_frame, text="Nova Transação", padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Descrição
        ttk.Label(main_frame, text="Descrição:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.desc_entry = ttk.Entry(main_frame, width=40)
        self.desc_entry.grid(row=0, column=1, columnspan=2, sticky=tk.W+tk.E, pady=5)
        
        # Valor
        ttk.Label(main_frame, text="Valor (R$):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.amount_entry = ttk.Entry(main_frame, width=20)
        self.amount_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Tipo de transação
        ttk.Label(main_frame, text="Tipo:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(main_frame, textvariable=self.type_var, 
                                      values=["Receita", "Despesa"], state="readonly")
        self.type_combo.grid(row=2, column=1, sticky=tk.W, pady=5)
        self.type_combo.bind('<<ComboboxSelected>>', self.on_type_change)
        
        # Categoria
        ttk.Label(main_frame, text="Categoria:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(main_frame, textvariable=self.category_var, state="readonly")
        self.category_combo.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Data
        ttk.Label(main_frame, text="Data:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.date_entry = ttk.Entry(main_frame, width=20)
        self.date_entry.grid(row=4, column=1, sticky=tk.W, pady=5)
        self.date_entry.insert(0, datetime.now().strftime("%d/%m/%Y"))
        
        # Observações
        ttk.Label(main_frame, text="Observações:").grid(row=5, column=0, sticky=tk.W+tk.N, pady=5)
        self.notes_text = tk.Text(main_frame, width=40, height=4)
        self.notes_text.grid(row=5, column=1, columnspan=2, sticky=tk.W+tk.E, pady=5)
        
        # Botões
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=20)
        
        ttk.Button(button_frame, text="Adicionar", command=self.add_transaction).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Limpar", command=self.clear_form).pack(side=tk.LEFT, padx=5)
        
        # Configurar grid
        main_frame.columnconfigure(1, weight=1)
    
    def create_view_transactions_tab(self):
        """Cria a aba para visualizar transações"""
        self.view_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.view_frame, text="Visualizar Transações")
        
        # Frame de filtros
        filter_frame = ttk.LabelFrame(self.view_frame, text="Filtros", padding=10)
        filter_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        ttk.Label(filter_frame, text="Período:").grid(row=0, column=0, padx=5)
        self.period_var = tk.StringVar()
        period_combo = ttk.Combobox(filter_frame, textvariable=self.period_var,
                                   values=["Todos", "Último mês", "Últimos 3 meses", "Este ano"],
                                   state="readonly")
        period_combo.grid(row=0, column=1, padx=5)
        period_combo.set("Último mês")
        
        ttk.Button(filter_frame, text="Atualizar", command=self.refresh_data).grid(row=0, column=2, padx=10)
        
        # Status da database
        self.status_label = ttk.Label(filter_frame, text="", foreground="green")
        self.status_label.grid(row=0, column=3, padx=20)
        self.update_status()
        
        # Treeview para transações
        self.tree_frame = ttk.Frame(self.view_frame)
        self.tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        columns = ("Data", "Descrição", "Tipo", "Categoria", "Valor")
        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show="headings", height=15)
        
        # Configurar colunas
        self.tree.heading("Data", text="Data")
        self.tree.heading("Descrição", text="Descrição")
        self.tree.heading("Tipo", text="Tipo")
        self.tree.heading("Categoria", text="Categoria")
        self.tree.heading("Valor", text="Valor (R$)")
        
        self.tree.column("Data", width=100)
        self.tree.column("Descrição", width=200)
        self.tree.column("Tipo", width=100)
        self.tree.column("Categoria", width=150)
        self.tree.column("Valor", width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Botão para excluir
        ttk.Button(self.view_frame, text="Excluir Selecionado", 
                  command=self.delete_transaction).pack(pady=10)
    
    def create_reports_tab(self):
        """Cria a aba de relatórios"""
        self.reports_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.reports_frame, text="Relatórios")
        
        # Frame do resumo
        summary_frame = ttk.LabelFrame(self.reports_frame, text="Resumo Financeiro", padding=20)
        summary_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Labels para mostrar valores
        self.balance_labels = {}
        row = 0
        for label in ["Receitas:", "Despesas:", "Saldo:"]:
            ttk.Label(summary_frame, text=label, font=("Arial", 12, "bold")).grid(row=row, column=0, sticky=tk.W, pady=5)
            value_label = ttk.Label(summary_frame, text="R$ 0,00", font=("Arial", 12))
            value_label.grid(row=row, column=1, sticky=tk.W, padx=20, pady=5)
            self.balance_labels[label] = value_label
            row += 1
        
        # Frame para categorias
        cat_frame = ttk.LabelFrame(self.reports_frame, text="Gastos por Categoria", padding=20)
        cat_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Treeview para categorias
        cat_columns = ("Categoria", "Valor", "Percentual")
        self.cat_tree = ttk.Treeview(cat_frame, columns=cat_columns, show="headings", height=10)
        
        for col in cat_columns:
            self.cat_tree.heading(col, text=col)
            self.cat_tree.column(col, width=150)
        
        self.cat_tree.pack(fill=tk.BOTH, expand=True)
    
    def create_backup_tab(self):
        """Cria a aba de backup e configurações"""
        self.backup_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.backup_frame, text="Backup & Config")
        
        # Frame de backup
        backup_frame = ttk.LabelFrame(self.backup_frame, text="Gerenciar Backups", padding=20)
        backup_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Botões de backup
        button_frame = ttk.Frame(backup_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Criar Backup Agora", 
                  command=self.create_manual_backup).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Restaurar Backup", 
                  command=self.restore_backup_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Atualizar Lista", 
                  command=self.refresh_backup_list).pack(side=tk.LEFT, padx=5)
        
        # Lista de backups
        self.backup_tree = ttk.Treeview(backup_frame, columns=("Data", "Tamanho"), show="headings", height=8)
        self.backup_tree.heading("Data", text="Data do Backup")
        self.backup_tree.heading("Tamanho", text="Tamanho")
        self.backup_tree.column("Data", width=200)
        self.backup_tree.column("Tamanho", width=100)
        self.backup_tree.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Frame de configurações
        config_frame = ttk.LabelFrame(self.backup_frame, text="Configurações", padding=20)
        config_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Localização da database
        ttk.Label(config_frame, text="Local dos Dados:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.db_path_var = tk.StringVar()
        self.db_path_entry = ttk.Entry(config_frame, textvariable=self.db_path_var, width=50, state="readonly")
        self.db_path_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5, padx=5)
        ttk.Button(config_frame, text="Alterar", command=self.change_db_location).grid(row=0, column=2, pady=5)
        
        # Backup automático
        self.auto_backup_var = tk.BooleanVar()
        ttk.Checkbutton(config_frame, text="Backup Automático", 
                       variable=self.auto_backup_var, command=self.update_auto_backup).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        # Intervalo de backup
        ttk.Label(config_frame, text="Intervalo (dias):").grid(row=1, column=1, sticky=tk.W, pady=5, padx=(20, 5))
        self.backup_interval_var = tk.StringVar()
        interval_spinbox = ttk.Spinbox(config_frame, from_=1, to=30, width=10, textvariable=self.backup_interval_var)
        interval_spinbox.grid(row=1, column=2, sticky=tk.W, pady=5)
        interval_spinbox.bind('<FocusOut>', self.update_backup_interval)
        
        # Configurar grid
        config_frame.columnconfigure(1, weight=1)
        
        # Carregar configurações atuais
        self.load_current_config()
        self.refresh_backup_list()
    
    def update_status(self):
        """Atualiza status da database"""
        db_path = self.finance_manager.config_manager.get_database_path()
        status_text = f"Dados: {db_path}"
        self.status_label.config(text=status_text)
    
    def load_current_config(self):
        """Carrega configurações atuais"""
        config = self.finance_manager.config_manager
        
        self.db_path_var.set(config.get_database_path())
        self.auto_backup_var.set(config.get("auto_backup", True))
        self.backup_interval_var.set(str(config.get("backup_interval_days", 7)))
    
    def create_manual_backup(self):
        """Cria backup manual"""
        if self.finance_manager.create_backup():
            messagebox.showinfo("Sucesso", "Backup criado com sucesso!")
            self.refresh_backup_list()
        else:
            messagebox.showerror("Erro", "Erro ao criar backup!")
    
    def restore_backup_dialog(self):
        """Diálogo para restaurar backup"""
        selection = self.backup_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um backup para restaurar!")
            return
        
        item = selection[0]
        backup_filename = self.backup_tree.item(item)['values'][0]
        
        if messagebox.askyesno("Confirmação", 
                              f"Tem certeza que deseja restaurar o backup:\n{backup_filename}\n\n"
                              "Os dados atuais serão substituídos!"):
            if self.finance_manager.restore_backup(backup_filename):
                messagebox.showinfo("Sucesso", "Backup restaurado com sucesso!")
                self.refresh_data()
            else:
                messagebox.showerror("Erro", "Erro ao restaurar backup!")
    
    def refresh_backup_list(self):
        """Atualiza lista de backups"""
        # Limpar lista atual
        for item in self.backup_tree.get_children():
            self.backup_tree.delete(item)
        
        # Carregar backups
        backups = self.finance_manager.list_backups()
        
        for backup in backups:
            size_kb = backup['size'] / 1024
            size_text = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
            
            self.backup_tree.insert("", tk.END, values=(
                backup['filename'],
                size_text
            ))
    
    def change_db_location(self):
        """Altera localização da database"""
        current_path = self.finance_manager.config_manager.get_database_path()
        new_path = filedialog.asksaveasfilename(
            title="Escolher nova localização dos dados",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="financial_data.json"
        )
        
        if new_path:
            # Confirmar mudança
            if messagebox.askyesno("Confirmação", 
                                  f"Alterar localização dos dados para:\n{new_path}\n\n"
                                  "Os dados atuais serão movidos. Continuar?"):
                try:
                    # Fazer backup dos dados atuais
                    self.finance_manager.create_backup()
                    
                    # Salvar dados na nova localização
                    old_path = self.finance_manager.data_file
                    self.finance_manager.config_manager.set("database_path", new_path)
                    self.finance_manager.data_file = new_path
                    self.finance_manager.save_data()
                    
                    # Atualizar interface
                    self.db_path_var.set(new_path)
                    self.update_status()
                    
                    messagebox.showinfo("Sucesso", "Localização alterada com sucesso!")
                    
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao alterar localização: {e}")
    
    def update_auto_backup(self):
        """Atualiza configuração de backup automático"""
        self.finance_manager.config_manager.set("auto_backup", self.auto_backup_var.get())
    
    def update_backup_interval(self, event=None):
        """Atualiza intervalo de backup"""
        try:
            interval = int(self.backup_interval_var.get())
            if interval < 1:
                interval = 1
            elif interval > 30:
                interval = 30
            
            self.finance_manager.config_manager.set("backup_interval_days", interval)
            self.backup_interval_var.set(str(interval))
        except ValueError:
            self.backup_interval_var.set("7")  # Valor padrão
    
    # Métodos originais da interface (mantidos iguais)
    def on_type_change(self, event=None):
        """Atualiza as categorias baseado no tipo selecionado"""
        transaction_type = self.type_var.get()
        
        if transaction_type == "Receita":
            categories = [cat.value for cat in Category if "Receita" in cat.value or cat.value in 
                         ["Salário", "Freelance", "Investimentos"]]
        else:
            categories = [cat.value for cat in Category if "Despesa" in cat.value or cat.value not in 
                         ["Salário", "Freelance", "Investimentos", "Outros (Receita)"]]
        
        self.category_combo['values'] = categories
        if categories:
            self.category_combo.set(categories[0])
    
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
            else:
                messagebox.showerror("Erro", "Erro ao adicionar transação!")
        
        except Exception as e:
            messagebox.showerror("Erro", f"Erro inesperado: {str(e)}")
    
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
    
    def refresh_data(self):
        """Atualiza os dados exibidos"""
        # Determinar período
        period = self.period_var.get()
        start_date = None
        
        if period == "Último mês":
            start_date = datetime.now() - timedelta(days=30)
        elif period == "Últimos 3 meses":
            start_date = datetime.now() - timedelta(days=90)
        elif period == "Este ano":
            start_date = datetime(datetime.now().year, 1, 1)
        
        # Atualizar treeview de transações
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        transactions = self.finance_manager.get_transactions(start_date)
        for transaction in transactions:
            tipo = "Receita" if transaction.transaction_type == TransactionType.RECEITA else "Despesa"
            valor = f"R$ {transaction.amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
            self.tree.insert("", tk.END, values=(
                transaction.date.strftime("%d/%m/%Y"),
                transaction.description,
                tipo,
                transaction.category.value,
                valor
            ), tags=(transaction.id,))
        
        # Atualizar resumo financeiro
        balance = self.finance_manager.calculate_balance(start_date)
        
        for label, value in [
            ("Receitas:", balance['receitas']),
            ("Despesas:", balance['despesas']),
            ("Saldo:", balance['saldo'])
        ]:
            formatted_value = f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            if label == "Saldo:" and value < 0:
                formatted_value = f"-{formatted_value}"
            self.balance_labels[label].config(text=formatted_value)
            
            # Colorir saldo
            if label == "Saldo:":
                color = "green" if value >= 0 else "red"
                self.balance_labels[label].config(foreground=color)
        
        # Atualizar categorias
        for item in self.cat_tree.get_children():
            self.cat_tree.delete(item)
        
        categories = self.finance_manager.get_category_summary(start_date)
        total_despesas = sum(categories['despesas'].values())
        
        for category, amount in categories['despesas'].items():
            percentage = (amount / total_despesas * 100) if total_despesas > 0 else 0
            formatted_amount = f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
            self.cat_tree.insert("", tk.END, values=(
                category,
                formatted_amount,
                f"{percentage:.1f}%"
            ))
    
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
            else:
                messagebox.showerror("Erro", "Erro ao excluir transação!")
