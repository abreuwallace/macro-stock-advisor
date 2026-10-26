"""
Configurações globais e parâmetros de risco do Robô de Recomendação Macro (B3).
"""
import os
from dataclasses import dataclass

@dataclass
class PortfolioSettings:
    # Capital total disponível para renda variável
    EQUITY_CAPITAL: float = 20_000.00
    # Capital total de patrimônio (reserva de segurança)
    TOTAL_PATRIMONY: float = 100_000.00
    # Número alvo de ativos na carteira (diversificação sem pulverização)
    MIN_ASSETS: int = 4
    MAX_ASSETS: int = 6
    # Limites de alocação por ativo (mínimo 15%, máximo 30%)
    MIN_WEIGHT_PER_ASSET: float = 0.15
    MAX_WEIGHT_PER_ASSET: float = 0.30
    # Perfil padrão solicitado pelo usuário: Mais segura (Dividendos, Qualidade e Valor)
    DEFAULT_PROFILE: str = "Segura / Dividendos & Qualidade"
    # Margem de segurança máxima de stop-loss sugerida
    MAX_STOP_LOSS_PCT: float = 0.08  # 8%
    # Ganho mínimo desejado para justificar entrada (relação risco/retorno >= 2.0)
    MIN_RISK_REWARD_RATIO: float = 2.0

SETTINGS = PortfolioSettings()

