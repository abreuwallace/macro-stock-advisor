"""
Motor de Simulação, Auditoria e Gestão Ativa de Carteira Montada (B3).
Avalia uma carteira já existente do investidor (Ação, Quantidade e Preço Médio de Compra),
calcula todas as métricas de rentabilidade, risco, dividendos (Yield on Cost),
compara com o regime macroeconômico atual e emite recomendações táticas de como atuar
(Manter, Aportar/Comprar Mais, Realizar Lucro, Rebalancear ou Acionar Stop/Trocar).
"""
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List

from config.universe import UNIVERSE_B3
from collectors.macro_collector import MacroCollector
from collectors.market_collector import MarketCollector
from collectors.fund_collector import FundamentalCollector
from engines.macro_regime import MacroRegimeEngine
from engines.stock_screener import StockScreener
from engines.price_engine import PriceEngine

logger = logging.getLogger(__name__)


class PortfolioSimulatorEngine:
    """
    Analisa uma carteira já montada pelo usuário e gera diagnósticos completos,
    métricas consolidadas e instruções táticas de atuação para cada posição.
    """

    def __init__(self):
        self.macro_collector = MacroCollector()
        self.market_collector = MarketCollector()
        self.fund_collector = FundamentalCollector()
        self.regime_engine = MacroRegimeEngine()
        self.screener = StockScreener()
        self.price_engine = PriceEngine()
        self.universe_map = {
            k.replace(".SA", ""): v for k, v in UNIVERSE_B3.items()
        }

    def _resolve_stock_meta(self, clean_ticker: str) -> Dict[str, Any]:
        """Obtém os metadados da ação no universo B3 ou cria metadados dinâmicos para qualquer ticker da B3."""
        if clean_ticker in self.universe_map:
            return self.universe_map[clean_ticker]
        is_def = clean_ticker[:4] in (
            "ITUB", "BBDC", "BBAS", "SANB", "CXSE", "BBSE", "PSSA",
            "TAEE", "ISAE", "EGIE", "CPFE", "CMIG", "ELET", "EQTL", "SAPR", "SBSP", "CSMG", "VIVT", "TIMS", "WEGE", "KLBN"
        )
        return {
            "ticker": clean_ticker,
            "name": f"{clean_ticker} (Ativo B3)",
            "sector": "Financeiro" if clean_ticker[:4] in ("ITUB", "BBDC", "BBAS", "SANB", "BPAC", "CXSE", "BBSE", "PSSA")
            else "Utilities" if clean_ticker[:4] in ("TAEE", "ISAE", "EGIE", "CPFE", "CMIG", "ELET", "EQTL", "SAPR", "SBSP", "ENGI", "CSMG")
            else "Commodities / Petróleo" if clean_ticker[:4] in ("PETR", "PRIO", "RECV")
            else "Commodities / Materiais" if clean_ticker[:4] in ("VALE", "SUZB", "KLBN", "GGBR", "CSNA")
            else "Telecomunicações" if clean_ticker[:4] in ("VIVT", "TIMS")
            else "Bens Industriais",
            "subsector": "Ação Listada na B3",
            "profile": "Defensivo / Dividendos" if is_def else "Ciclo Doméstico",
            "beta": 0.65 if is_def else 1.05,
            "is_defensive": is_def,
            "description": f"Ativo {clean_ticker} negociado na B3.",
        }

    def _evaluate_single_holding(
        self,
        holding: Dict[str, Any],
        macro_regime: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Coleta dados ao vivo da B3/CVM e avalia uma posição individual da carteira do usuário."""
        raw_ticker = str(holding.get("ticker", "")).strip().upper().replace(".SA", "")
        shares = max(1, int(holding.get("shares", 100)))
        avg_price = float(holding.get("avg_price", 0.0))

        meta = self._resolve_stock_meta(raw_ticker)
        yf_symbol = f"{raw_ticker}.SA"

        tech = self.market_collector.get_stock_technical_metrics(yf_symbol)
        fund = self.fund_collector.get_stock_fundamentals(yf_symbol)
        scored = self.screener.score_stock(meta, tech, fund, macro_regime.get("sector_weights", {}))
        stock_bundle = {
            "symbol": yf_symbol,
            "meta": meta,
            "tech": tech,
            "fund": fund,
            "score": scored["score"],
            "confidence_pct": scored["confidence_pct"],
        }
        prices = self.price_engine.calculate_price_levels(stock_bundle)

        current_price = float(prices["current_price"])
        if avg_price <= 0:
            avg_price = current_price

        invested_cost = round(shares * avg_price, 2)
        current_value = round(shares * current_price, 2)
        pnl_brl = round(current_value - invested_cost, 2)
        pnl_pct = round(((current_price / avg_price) - 1.0) * 100.0, 2) if avg_price > 0 else 0.0

        current_dy = float(fund.get("dividend_yield", 0.0))
        # Yield on Cost (YoC): dividendo anual em relação ao preço médio pago pelo usuário
        yoc_pct = round(current_dy * (current_price / avg_price), 2) if avg_price > 0 else current_dy
        annual_dividends_brl = round(current_value * (current_dy / 100.0), 2)

        target_price = float(prices["target_price"])
        stop_loss_price = float(prices["stop_loss_price"])
        entry_max = float(prices["entry_max"])
        upside_from_current_pct = round(((target_price / current_price) - 1.0) * 100.0, 2)
        stop_distance_pct = round(((stop_loss_price / current_price) - 1.0) * 100.0, 2)

        score = float(scored["score"])
        confidence_pct = int(scored["confidence_pct"])
        rsi_14 = float(tech.get("rsi_14", 50.0))

        return {
            "ticker": raw_ticker,
            "symbol": yf_symbol,
            "name": meta["name"].replace(f" ({raw_ticker})", ""),
            "sector": meta["sector"],
            "shares_count": shares,
            "avg_price": round(avg_price, 2),
            "current_price": round(current_price, 2),
            "invested_cost": invested_cost,
            "current_value": current_value,
            "invested_amount": current_value,  # compatibilidade com motores de Monte Carlo, Backtest e Projeções
            "pnl_brl": pnl_brl,
            "pnl_pct": pnl_pct,
            "dividend_yield": round(current_dy, 2),
            "yield_on_cost_pct": yoc_pct,
            "annual_dividends_brl": annual_dividends_brl,
            "target_price": round(target_price, 2),
            "potential_gain_pct": upside_from_current_pct,
            "stop_loss_price": round(stop_loss_price, 2),
            "max_loss_pct": stop_distance_pct,
            "entry_min": round(float(prices["entry_min"]), 2),
            "entry_max": round(entry_max, 2),
            "score": score,
            "confidence_pct": confidence_pct,
            "rsi_14": round(rsi_14, 1),
            "pe_ratio": fund.get("pe_ratio"),
            "roe": fund.get("roe"),
            "reasons": scored.get("reasons", []),
        }

    def _determine_tactical_action(
        self,
        pos: Dict[str, Any],
        weight_pct: float,
        top_recommended_tickers: List[str]
    ) -> Dict[str, Any]:
        """
        Define a recomendação tática ('Como Atuar') para uma posição da carteira do investidor,
        cruzando Preço Atual, Preço Médio, Preço-Alvo, Stop Loss, Score Macro e Peso na Carteira.
        """
        ticker = pos["ticker"]
        curr = pos["current_price"]
        avg = pos["avg_price"]
        target = pos["target_price"]
        stop = pos["stop_loss_price"]
        entry_max = pos["entry_max"]
        score = pos["score"]
        pnl_pct = pos["pnl_pct"]
        rsi = pos["rsi_14"]
        shares = pos["shares_count"]
        in_top_picks = ticker in top_recommended_tickers

        # Caso 1: Atingiu meta de lucro sobre o Preço Médio (>= +20%) ou forte alta com RSI esticado
        if pnl_pct >= 20.0 or (pnl_pct >= 12.0 and rsi >= 65.0):
            sell_shares = max(1, int(round(shares * 0.50)))
            keep_shares = shares - sell_shares
            trailing_stop = round(curr * 0.94, 2)
            return {
                "action_badge": "🎯 REALIZAR LUCRO (VENDA PARCIAL/TOTAL)",
                "action_priority": "ALTA — Embolsar Ganho",
                "alert_type": "success",
                "summary_command": f"Vender {sell_shares} ações (50%) a R$ {curr:.2f} no Itaú e manter {keep_shares} ações subindo o Stop de Lucro para R$ {trailing_stop:.2f}.",
                "rationale": (
                    f"Sua posição em {ticker} acumula excelente lucro de {pnl_pct:+.1f}% (R$ {pos['pnl_brl']:+,.2f}) sobre seu Preço Médio de R$ {avg:.2f}, "
                    f"atingindo o objetivo de ganho de capital. Vender 50% agora coloca o lucro no bolso (isento de IR para vendas totais até R$ 20 mil/mês na B3) "
                    f"e deixa a outra metade correr com Stop Móvel protegido em R$ {trailing_stop:.2f} (Novo Alvo estendido: R$ {target:.2f})."
                ),
            }

        # Caso 2: Violou limite de Stop Loss (-8.5% sobre o Preço Médio) ou Deterioração de Score (< 62)
        if pnl_pct <= -8.5 or score < 62.0:
            if score >= 78.0 and pnl_pct <= -8.5:
                return {
                    "action_badge": "🛑 ALERTA DE STOP / AVALIAR PREÇO MÉDIO",
                    "action_priority": "ALTA — Decisão Tática",
                    "alert_type": "error",
                    "summary_command": f"Atenção: Queda de {pnl_pct:.1f}% violou o Stop de compra (R$ {round(avg * 0.92, 2):.2f}), mas Score Fundamental segue alto ({score:.1f}/100). Definir Stop rígido em R$ {stop:.2f}.",
                    "rationale": (
                        f"{ticker} recuou {pnl_pct:.1f}% desde sua compra a R$ {avg:.2f}. Se você segue disciplina estrita de Stop Curto, o limite de -8% foi acionado. "
                        f"Porém, a auditoria fundamentalista mostra que a empresa segue extremamente sólida (Score {score:.1f}/100 e DY de {pos['dividend_yield']}%). "
                        f"Recomendação: mantenha apenas se respeitar o suporte técnico de R$ {stop:.2f}; caso perca esse nível, substitua por uma Top Pick defensiva."
                    ),
                }
            return {
                "action_badge": "🛑 REDUZIR / SUBSTITUIR POSIÇÃO (DEFESA)",
                "action_priority": "ALTA — Proteção de Capital",
                "alert_type": "error",
                "summary_command": f"Programar saída defensiva de {shares} ações de {ticker} (Cotação R$ {curr:.2f}) e realocar nas Top Picks defensivas.",
                "rationale": (
                    f"O Score Macro-Quantamental de {ticker} caiu para {score:.1f}/100 no cenário atual ou a cotação violou a margem de segurança "
                    f"({pnl_pct:+.1f}% vs. seu preço médio). O capital terá melhor relação risco-retorno e maior Dividend Yield migrando para os líderes atuais do ranking."
                ),
            }

        # Caso 3: Excesso de Concentração (> 28% da carteira em um único papel)
        if weight_pct > 28.0:
            trim_pct = round(weight_pct - 20.0, 1)
            trim_shares = max(1, int(round(shares * (trim_pct / weight_pct))))
            return {
                "action_badge": "⚖️ REBALANCEAR PESO (REDUZIR CONCENTRAÇÃO)",
                "action_priority": "MÉDIA — Controle de Risco HHI",
                "alert_type": "warning",
                "summary_command": f"Vender {trim_shares} ações de {ticker} para reduzir o peso de {weight_pct:.1f}% para ~20% da carteira.",
                "rationale": (
                    f"{ticker} possui excelentes fundamentos (Score {score:.1f}/100), porém representa {weight_pct:.1f}% da sua carteira — acima do teto prudencial "
                    f"de 25%-28% por ativo. Reduzir {trim_shares} ações elimina risco de concentração e libera caixa para reforçar as demais posições."
                ),
            }

        # Caso 4: Excelente Score (>= 78) e preço descontado / próximo ao Preço Médio (-8% a +3%)
        if score >= 78.0 and (-8.0 <= pnl_pct <= 3.0) and weight_pct < 23.0:
            return {
                "action_badge": "🛒 OPORTUNIDADE DE APORTE (COMPRAR MAIS)",
                "action_priority": "MÉDIA-ALTA — Preço Atrativo",
                "alert_type": "info",
                "summary_command": f"Manter as {shares} ações atuais e usar novos aportes/dividendos para comprar mais até R$ {entry_max:.2f}.",
                "rationale": (
                    f"{ticker} continua com nota altíssima no modelo ({score:.1f}/100, DY de {pos['dividend_yield']}%) e negocia a R$ {curr:.2f} "
                    f"(próximo ao seu preço médio de R$ {avg:.2f}), com potencial de +{pos['potential_gain_pct']:.1f}% até o alvo de R$ {target:.2f}. Excelente ponto para reinvestir dividendos."
                ),
            }

        # Caso 5: Padrão — Ativo saudável em trajetória de ganho (+4.5% a +20%)
        status_note = "Continua no Top 5 atual do robô." if in_top_picks else "Mesmo fora do Top 5 deste mês, mantém fundamentos sólidos que justificam a manutenção sem giro desnecessário."
        return {
            "action_badge": "✅ MANTER EM CARTEIRA (HOLD & DIVIDENDOS)",
            "action_priority": "NORMAL — Acompanhamento",
            "alert_type": "success",
            "summary_command": f"Manter as {shares} ações de {ticker}. Alarme de Venda (Gain) em R$ {target:.2f} e Stop de proteção em R$ {stop:.2f}.",
            "rationale": (
                f"{ticker} opera de forma saudável (Score {score:.1f}/100, lucro acumulado de {pnl_pct:+.1f}%, Yield on Cost de {pos['yield_on_cost_pct']:.2f}% a.a.). "
                f"{status_note} Não há motivo para girar a posição; siga recebendo os proventos isentos de IR até atingir o Preço-Alvo de R$ {target:.2f}."
            ),
        }

    def evaluate_user_portfolio(
        self,
        user_holdings: List[Dict[str, Any]],
        user_profile: str = "Segura / Dividendos & Qualidade",
        recommended_allocations: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executa a avaliação completa da carteira montada pelo usuário em paralelo.
        """
        valid_holdings = [
            h for h in user_holdings
            if h.get("ticker") and str(h.get("ticker")).strip() != "" and float(h.get("shares", 0)) > 0
        ]
        if not valid_holdings:
            return {}

        macro_snapshot = self.macro_collector.get_macro_snapshot()
        macro_regime = self.regime_engine.analyze_regime(macro_snapshot, user_profile=user_profile)

        top_recommended_tickers = [
            a["ticker"] for a in (recommended_allocations or [])
        ]

        evaluated_positions: List[Dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {
                executor.submit(self._evaluate_single_holding, h, macro_regime): idx
                for idx, h in enumerate(valid_holdings)
            }
            temp_results = {}
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    temp_results[idx] = future.result()
                except Exception as e:
                    logger.error(f"Erro ao avaliar posição {valid_holdings[idx]}: {e}")

        for idx in sorted(temp_results.keys()):
            evaluated_positions.append(temp_results[idx])

        if not evaluated_positions:
            return {}

        total_invested_cost = round(sum(p["invested_cost"] for p in evaluated_positions), 2)
        total_current_value = round(sum(p["current_value"] for p in evaluated_positions), 2)
        total_pnl_brl = round(total_current_value - total_invested_cost, 2)
        total_pnl_pct = round(((total_current_value / total_invested_cost) - 1.0) * 100.0, 2) if total_invested_cost > 0 else 0.0
        total_annual_dividends_brl = round(sum(p["annual_dividends_brl"] for p in evaluated_positions), 2)

        # Calcular pesos atuais e recomendações táticas por ativo
        for pos in evaluated_positions:
            w_pct = round((pos["current_value"] / total_current_value) * 100.0, 1) if total_current_value > 0 else 0.0
            pos["weight_pct"] = w_pct
            tactical = self._determine_tactical_action(pos, w_pct, top_recommended_tickers)
            pos.update(tactical)

        # Métricas ponderadas da carteira do usuário
        weighted_dy_current = round(
            sum(p["dividend_yield"] * (p["weight_pct"] / 100.0) for p in evaluated_positions), 2
        )
        weighted_yoc = round(
            (total_annual_dividends_brl / total_invested_cost) * 100.0, 2
        ) if total_invested_cost > 0 else weighted_dy_current

        weighted_upside = round(
            sum(p["potential_gain_pct"] * (p["weight_pct"] / 100.0) for p in evaluated_positions), 2
        )
        weighted_score = round(
            sum(p["score"] * (p["weight_pct"] / 100.0) for p in evaluated_positions), 1
        )
        weighted_confidence = round(
            sum(p["confidence_pct"] * (p["weight_pct"] / 100.0) for p in evaluated_positions), 1
        )

        # HHI de concentração da carteira do usuário
        hhi_index = int(round(sum((p["weight_pct"] ** 2) for p in evaluated_positions)))

        # Comparação de alinhamento com a carteira ideal de hoje
        user_tickers = {p["ticker"] for p in evaluated_positions}
        rec_tickers = set(top_recommended_tickers)
        common_tickers = sorted(list(user_tickers.intersection(rec_tickers)))
        new_opportunities = [
            a for a in (recommended_allocations or []) if a["ticker"] not in user_tickers
        ]
        candidates_to_review = [
            p for p in evaluated_positions if p["ticker"] not in rec_tickers
        ]

        # Contagem de ações por tipo de recomendação
        counts = {
            "manter": sum(1 for p in evaluated_positions if "MANTER" in p["action_badge"]),
            "aportar": sum(1 for p in evaluated_positions if "APORTE" in p["action_badge"]),
            "realizar_lucro": sum(1 for p in evaluated_positions if "REALIZAR LUCRO" in p["action_badge"]),
            "rebalancear": sum(1 for p in evaluated_positions if "REBALANCEAR" in p["action_badge"]),
            "reduzir_stop": sum(1 for p in evaluated_positions if ("REDUZIR" in p["action_badge"] or "STOP" in p["action_badge"])),
        }

        return {
            "positions": evaluated_positions,
            "summary": {
                "total_invested_cost": total_invested_cost,
                "total_current_value": total_current_value,
                "total_pnl_brl": total_pnl_brl,
                "total_pnl_pct": total_pnl_pct,
                "total_annual_dividends_brl": total_annual_dividends_brl,
                "weighted_dy_current": weighted_dy_current,
                "weighted_yoc_pct": weighted_yoc,
                "weighted_upside_pct": weighted_upside,
                "weighted_score": weighted_score,
                "weighted_confidence": weighted_confidence,
                "hhi_index": hhi_index,
                "num_positions": len(evaluated_positions),
                "action_counts": counts,
            },
            "alignment": {
                "common_tickers": common_tickers,
                "new_top_picks": new_opportunities,
                "outside_top_picks": candidates_to_review,
            },
            "macro_snapshot": macro_snapshot,
            "macro_regime": macro_regime,
        }


if __name__ == "__main__":
    sim = PortfolioSimulatorEngine()
    sample_holdings = [
        {"ticker": "BBAS3", "shares": 160, "avg_price": 23.50},
        {"ticker": "TAEE11", "shares": 90, "avg_price": 38.00},
        {"ticker": "CXSE3", "shares": 210, "avg_price": 16.50},
        {"ticker": "BBSE3", "shares": 110, "avg_price": 33.00},
        {"ticker": "PETR4", "shares": 90, "avg_price": 36.00},
    ]
    res = sim.evaluate_user_portfolio(sample_holdings)
    print("Summary:", res["summary"])
    for p in res["positions"]:
        print(p["ticker"], "P&L:", p["pnl_pct"], "% | Action:", p["action_badge"])
