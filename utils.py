"""
Funções utilitárias para o sistema financeiro
"""

from datetime import datetime
from typing import List, Dict
import locale

def format_currency(value: float) -> str:
    """Formata um valor para moeda brasileira"""
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
        return locale.currency(value, grouping=True)
    except:
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def parse_currency(value_str: str) -> float:
    """Converte string de moeda para float"""
    # Remove símbolos e converte vírgula para ponto
    cleaned = value_str.replace("R$", "").replace(".", "").replace(",", ".").strip()
    return float(cleaned)

def validate_date(date_str: str) -> bool:
    """Valida se uma string está no formato de data correto"""
    try:
        datetime.strptime(date_str, "%d/%m/%Y")
        return True
    except ValueError:
        return False

def get_month_name(month: int) -> str:
    """Retorna o nome do mês em português"""
    months = [
        "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    return months[month] if 1 <= month <= 12 else ""

def calculate_percentage(part: float, total: float) -> float:
    """Calcula a porcentagem"""
    return (part / total * 100) if total > 0 else 0
