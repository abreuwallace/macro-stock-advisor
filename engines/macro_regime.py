"""
Motor de Regime Macroeconômico para a B3.
Analisa os ciclos de juros, inflação, câmbio e commodities para definir
a atratividade setorial com foco máximo em SEGURANÇA e PRESERVAÇÃO DE CAPITAL.
"""
from typing import Dict, Any, List

class MacroRegimeEngine:
    """Classifica o regime macroeconômico e define pesos setoriais ideais."""

    def analyze_regime(self, macro_snapshot: Dict[str, Any], user_profile: str = "Segura") -> Dict[str, Any]:
        selic = macro_snapshot.get("selic_rate", 10.5)
        ipca = macro_snapshot.get("ipca_12m", 4.5)
        real_rate = macro_snapshot.get("real_rate", 6.0)
        usd = macro_snapshot.get("usd_brl", 5.40)
        brent = macro_snapshot.get("brent_usd", 80.0)

        # 1. Determinação do Regime Dominante
        if selic >= 10.75 or real_rate >= 6.5:
            regime_name = "Juros Reais Elevados & Defensivo"
            regime_description = (
                f"Selic em {selic}% e Juro Real de {real_rate}% ao ano. "
                "Cenário exige foco em empresas com geração de caixa previsível, "
                "baixo endividamento, float financeiro positivo (seguradoras) "
                "e contratos indexados à inflação (elétricas e saneamento)."
            )
            favored_sectors = [
                "Financeiro",
                "Utilities",
                "Telecomunicações",
            ]
            avoid_sectors = [
                "Varejo Discricionário",
                "Construção Civil",
                "Tecnologia Alavancada"
            ]
            sector_weights = {
                "Utilities": 1.40,        # Energia e Saneamento (Máxima segurança)
                "Financeiro": 1.30,       # Grandes Bancos e Seguradoras (Float alto)
                "Telecomunicações": 1.15, # Receita perene e dividendos
                "Bens Industriais": 1.00, # WEG (Qualidade global)
                "Commodities / Petróleo": 0.85,
                "Commodities / Materiais": 0.80,
            }

        elif brent >= 90.0 or usd >= 5.60:
            regime_name = "Ciclo de Commodities & Câmbio Alto"
            regime_description = (
                f"Dólar cotado a R$ {usd:.2f} e Petróleo em US$ {brent:.1f}. "
                "Exportadoras e empresas com receita dolarizada se beneficiam diretamente."
            )
            favored_sectors = [
                "Commodities / Petróleo",
                "Commodities / Materiais",
                "Financeiro"
            ]
            avoid_sectors = ["Importadoras", "Empresas com Dívida Dolarizada sem Hedge"]
            sector_weights = {
                "Utilities": 1.20,
                "Financeiro": 1.20,
                "Commodities / Petróleo": 1.25,
                "Commodities / Materiais": 1.10,
                "Telecomunicações": 1.00,
                "Bens Industriais": 1.05,
            }

        else:
            regime_name = "Ciclo Moderado / Neutro"
            regime_description = (
                f"Selic em {selic}% e IPCA em {ipca}%. Mercado em transição cíclica. "
                "Equilíbrio entre empresas defensivas e empresas de qualidade com valuation justo."
            )
            favored_sectors = ["Utilities", "Financeiro", "Bens Industriais"]
            avoid_sectors = ["Empresas com prejuízo recorrente"]
            sector_weights = {
                "Utilities": 1.30,
                "Financeiro": 1.25,
                "Telecomunicações": 1.10,
                "Bens Industriais": 1.10,
                "Commodities / Petróleo": 0.95,
                "Commodities / Materiais": 0.90,
            }

        # Ajuste específico para a escolha do usuário: "Mais segura / Dividendos"
        if "Segura" in user_profile or "Dividendos" in user_profile:
            sector_weights["Utilities"] = max(sector_weights.get("Utilities", 1.0), 1.45)
            sector_weights["Financeiro"] = max(sector_weights.get("Financeiro", 1.0), 1.30)
            sector_weights["Telecomunicações"] = max(sector_weights.get("Telecomunicações", 1.0), 1.20)
            # Limitar a exposição a commodities cíclicas voláteis (Vale/Petrobras) no perfil seguro
            sector_weights["Commodities / Petróleo"] = min(sector_weights.get("Commodities / Petróleo", 1.0), 0.90)
            sector_weights["Commodities / Materiais"] = min(sector_weights.get("Commodities / Materiais", 1.0), 0.85)

        return {
            "regime_name": regime_name,
            "description": regime_description,
            "favored_sectors": favored_sectors,
            "avoid_sectors": avoid_sectors,
            "sector_weights": sector_weights,
            "interest_environment": "Elevado" if selic >= 11.0 else ("Médio" if selic >= 8.5 else "Baixo"),
            "inflation_environment": "Pressionada" if ipca >= 5.0 else "Controlada",
        }

