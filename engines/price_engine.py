"""
Motor de Preços Operacionais: Faixa de Compra, Preço-Alvo, Stop Loss e Risco/Retorno.
Gera os parâmetros exatos para você abrir a boleta de compra/venda no banco Itaú.
"""
from typing import Dict, Any

class PriceEngine:
    """Calcula pontos objetivos de entrada, realização de lucro e stop de segurança."""

    def calculate_price_levels(self, stock_item: Dict[str, Any]) -> Dict[str, Any]:
        tech = stock_item["tech"]
        fund = stock_item["fund"]

        current_price = tech["current_price"]
        support = tech.get("support_price", current_price * 0.95)
        resistance = tech.get("resistance_price", current_price * 1.10)
        atr = tech.get("atr_14", current_price * 0.03)
        analyst_target = fund.get("analyst_target_price")

        # 1. Faixa de Entrada Ideal (Buy Zone)
        # Se o ativo estiver perto do suporte ou em retração técnica
        entry_min = round(max(support, current_price - (1.2 * atr)), 2)
        entry_max = round(current_price * 1.015, 2)  # Até 1.5% acima da cotação atual

        # 2. Preço-Alvo (Take Profit)
        # Combina consenso de analistas e resistência técnica
        if analyst_target and analyst_target > current_price:
            # Se o analista sugerir alvo razoável (entre 12% e 35%)
            implied_target = analyst_target
        else:
            # Projeção fundamentalista conservadora (+18% a +22%)
            implied_target = current_price * 1.20

        target_price = round(max(implied_target, current_price * 1.14), 2)
        potential_gain_pct = round(((target_price / current_price) - 1) * 100, 2)

        # 3. Stop Loss de Segurança (Safety Cut)
        # Ponto abaixo do suporte técnico ou 2x ATR, limitado a 8% de perda máxima
        calculated_stop = min(current_price - (1.8 * atr), support * 0.985)
        # Garantir limite de segurança: perda de no máximo 8%
        min_allowed_stop = current_price * 0.92
        stop_loss_price = round(max(calculated_stop, min_allowed_stop), 2)
        max_loss_pct = round(((stop_loss_price / current_price) - 1) * 100, 2)

        # 4. Relação Risco / Retorno
        downside_pct = abs(max_loss_pct) if max_loss_pct != 0 else 5.0
        risk_reward_ratio = round(potential_gain_pct / downside_pct, 2)

        # 5. Tipo de Ordem recomendada no Itaú
        if current_price <= entry_max:
            order_recommendation = "COMPRA A MERCADO / LIMITADA NA FAIXA"
            entry_action = f"Comprar entre R$ {entry_min:.2f} e R$ {entry_max:.2f}"
        else:
            order_recommendation = "AGUARDAR RECUO (Ordem Limitada de Compra)"
            entry_action = f"Deixar ordem limitada programada a R$ {entry_min:.2f}"

        return {
            "current_price": current_price,
            "entry_min": entry_min,
            "entry_max": entry_max,
            "entry_action": entry_action,
            "target_price": target_price,
            "potential_gain_pct": potential_gain_pct,
            "stop_loss_price": stop_loss_price,
            "max_loss_pct": max_loss_pct,
            "risk_reward_ratio": risk_reward_ratio,
            "order_recommendation": order_recommendation,
            "exit_rule_gain": f"Vender (realizar lucro) ao atingir R$ {target_price:.2f} (+{potential_gain_pct}%)",
            "exit_rule_stop": f"Vender (stop loss de proteção) se cair para R$ {stop_loss_price:.2f} ({max_loss_pct}%)",
        }

