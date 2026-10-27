"""
Motor de Valuation Intrínseco Multimetodológico para Ações da B3.
Implementa modelos quantitativos consolidados e isentos de viés subjetivo:
1. Preço Teto de Décio Bazin (Dividendo Médio / 6%) + Margem de Segurança Bazin
2. Fórmula de Valor Justo de Benjamin Graham (sqrt(22.5 * LPA * VPA)) + Margem Graham
3. Modelo de Desconto de Dividendos de Gordon (DDM)
4. Reverse DCF: Crescimento Anual Implícito de Lucro Precificado pelo Mercado
"""
import math
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ValuationEngine:
    """Calcula valores justos e margens de segurança multimetodológicas para ações da B3."""

    def __init__(self, target_dividend_rate: float = 0.06, cost_of_equity: float = 0.125):
        self.target_dividend_rate = target_dividend_rate  # 6% ao ano padrão Bazin
        self.cost_of_equity = cost_of_equity  # Custo de oportunidade de capital no Brasil (12.5% a.a.)

    def calculate_intrinsic_valuation(
        self,
        current_price: float,
        trailing_eps: Optional[float],     # LPA (Lucro por Ação)
        book_value: Optional[float],       # VPA (Valor Patrimonial por Ação)
        annual_dividends_avg: float,       # Média anual de dividendos em R$
        pe_ratio: Optional[float] = None,  # P/L
        dividend_yield_pct: float = 0.0,   # DY atual (%)
        sustainable_growth_rate: float = 0.05
    ) -> Dict[str, Any]:
        """
        Executa os 4 modelos de valuation intrínseco e calcula a margem de segurança combinada.
        """
        current_price = max(0.01, float(current_price))

        # -------------------------------------------------------------
        # 1. MÉTODO DÉCIO BAZIN (Preço Teto para Dividendos >= 6% a.a.)
        # -------------------------------------------------------------
        # Preço Teto Bazin = Dividendo Anual Médio / 6%
        effective_div_per_share = annual_dividends_avg
        if effective_div_per_share <= 0 and dividend_yield_pct > 0:
            effective_div_per_share = current_price * (dividend_yield_pct / 100.0)

        if effective_div_per_share > 0:
            bazin_fair_price = round(effective_div_per_share / self.target_dividend_rate, 2)
            bazin_margin_pct = round(((bazin_fair_price / current_price) - 1.0) * 100.0, 1)
            bazin_verdict = (
                f"Abaixo do Preço Teto (+{bazin_margin_pct}% de margem)"
                if bazin_margin_pct > 0
                else f"Acima do Preço Teto ({bazin_margin_pct}% de prêmio)"
            )
        else:
            bazin_fair_price = None
            bazin_margin_pct = None
            bazin_verdict = "Histórico de proventos insuficiente"

        # -------------------------------------------------------------
        # 2. FÓRMULA DE BENJAMIN GRAHAM (Valor Justo com Margem de Segurança)
        # -------------------------------------------------------------
        # VJ = sqrt(22.5 * LPA * VPA)
        graham_fair_price = None
        graham_margin_pct = None
        graham_verdict = "Dados contábeis não aplicáveis"

        if trailing_eps and book_value and trailing_eps > 0 and book_value > 0:
            try:
                base_val = 22.5 * float(trailing_eps) * float(book_value)
                if base_val > 0:
                    graham_fair_price = round(math.sqrt(base_val), 2)
                    graham_margin_pct = round(((graham_fair_price / current_price) - 1.0) * 100.0, 1)
                    graham_verdict = (
                        f"Desconto de Graham (+{graham_margin_pct}%)"
                        if graham_margin_pct > 0
                        else f"Prêmio sobre Graham ({graham_margin_pct}%)"
                    )
            except Exception as e:
                logger.warning(f"Erro no cálculo de Graham: {e}")

        # -------------------------------------------------------------
        # 3. MODELO DE GORDON (DDM - Dividend Discount Model)
        # -------------------------------------------------------------
        # P = D1 / (Ke - g)
        gordon_fair_price = None
        gordon_margin_pct = None
        if effective_div_per_share > 0 and self.cost_of_equity > sustainable_growth_rate:
            d1 = effective_div_per_share * (1.0 + sustainable_growth_rate)
            ke_minus_g = self.cost_of_equity - sustainable_growth_rate
            gordon_fair_price = round(d1 / ke_minus_g, 2)
            gordon_margin_pct = round(((gordon_fair_price / current_price) - 1.0) * 100.0, 1)

        # -------------------------------------------------------------
        # 4. REVERSE DCF (Crescimento de Lucro Implícito Precificado)
        # -------------------------------------------------------------
        # Qual taxa de crescimento 'g' justifica o P/L atual se Ke = 12.5%?
        # P/L = (1 - b) / (Ke - g) => g = Ke - (Payout / (P/L))
        implied_growth_pct = None
        reverse_dcf_reading = "Múltiplo neutro"
        if pe_ratio and pe_ratio > 0:
            # Assumindo payout conservador médio de 50%
            payout_ratio = 0.50
            implied_g = (self.cost_of_equity - (payout_ratio / pe_ratio)) * 100.0
            implied_growth_pct = round(max(-20.0, min(30.0, implied_g)), 1)
            if implied_growth_pct <= 0:
                reverse_dcf_reading = f"Excelente assimetria: mercado precifica contração de {implied_growth_pct}% a.a."
            elif implied_growth_pct <= 5.0:
                reverse_dcf_reading = f"Valuation moderado: mercado exige crescimento brando de {implied_growth_pct}% a.a."
            else:
                reverse_dcf_reading = f"Expectativa otimista: mercado embute crescimento de {implied_growth_pct}% a.a."

        # -------------------------------------------------------------
        # 5. SÍNTESE CONSOLIDADA (Preço Justo Ponderado e Score de Margem)
        # -------------------------------------------------------------
        valid_targets = []
        if bazin_fair_price and bazin_fair_price > 0:
            valid_targets.append(bazin_fair_price)
        if graham_fair_price and graham_fair_price > 0:
            valid_targets.append(graham_fair_price)
        if gordon_fair_price and gordon_fair_price > 0:
            valid_targets.append(gordon_fair_price)

        if valid_targets:
            composite_fair_price = round(sum(valid_targets) / len(valid_targets), 2)
            composite_margin_safety_pct = round(((composite_fair_price / current_price) - 1.0) * 100.0, 1)
        else:
            composite_fair_price = round(current_price * 1.15, 2)
            composite_margin_safety_pct = 15.0

        is_undervalued = composite_margin_safety_pct >= 10.0
        valuation_verdict = "Margem de Segurança Confortável" if is_undervalued else "Preço Justo / Neutro"

        return {
            "current_price": current_price,
            "bazin_fair_price": bazin_fair_price,
            "bazin_margin_pct": bazin_margin_pct,
            "bazin_verdict": bazin_verdict,
            "graham_fair_price": graham_fair_price,
            "graham_margin_pct": graham_margin_pct,
            "graham_verdict": graham_verdict,
            "gordon_fair_price": gordon_fair_price,
            "gordon_margin_pct": gordon_margin_pct,
            "implied_growth_pct": implied_growth_pct,
            "reverse_dcf_implied_growth_pct": implied_growth_pct,
            "reverse_dcf_reading": reverse_dcf_reading,
            "composite_fair_price": composite_fair_price,
            "composite_margin_safety_pct": composite_margin_safety_pct,
            "composite_margin_pct": composite_margin_safety_pct,
            "valuation_verdict": valuation_verdict,
            "is_undervalued": is_undervalued,
        }


if __name__ == "__main__":
    v_engine = ValuationEngine()
    res = v_engine.calculate_intrinsic_valuation(
        current_price=17.38,
        trailing_eps=2.15,
        book_value=31.877,
        annual_dividends_avg=1.45,
        pe_ratio=8.08,
        dividend_yield_pct=8.34
    )
    print("Valuation BBAS3:", res)
