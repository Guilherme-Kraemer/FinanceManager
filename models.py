"""
Modelos de dados para o sistema financeiro
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum

class TransactionType(Enum):
    RECEITA = "receita"
    DESPESA = "despesa"

class Category(Enum):
    # Categorias de Receita
    SALARIO = "Salário"
    FREELANCE = "Freelance"
    INVESTIMENTOS = "Investimentos"
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
