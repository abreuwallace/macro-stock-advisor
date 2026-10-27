"""
Dimensionador de Carteira e Gestão de Risco para R$ 20.000,00.
Calcula a quantidade exata de ações (lotes e fracionário) para execução no Itaú.
"""
from typing import List, Dict, Any

class PortfolioAllocator:
    """Distribui o capital de R$ 20.000 entre as melhores ações recomendadas."""

    def __init__(self, total_capital: float = 20_000.00):
        self.total_capital = total_capital

    def allocate_portfolio(self, top_stocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcula a alocação de capital e a quantidade exata de ações
        para cada ativo selecionado.
        """
        n_assets = len(top_stocks)
        if n_assets == 0:
            return {"allocations": [], "total_allocated": 0.0, "cash_remaining": self.total_capital}

        # Pesos baseados no score relativo
        total_score = sum(s["score"] for s in top_stocks)
        allocations = []
        total_invested = 0.0

        for stock in top_stocks:
            ticker_b3 = stock["meta"]["ticker"]
            current_price = stock["price_levels"]["current_price"]
            weight = stock["score"] / total_score
            target_amount = self.total_capital * weight

            # Quantidade inteira de ações
            shares_count = int(target_amount // current_price)
            actual_amount = round(shares_count * current_price, 2)
            total_invested += actual_amount

            # Instrução de boleta no Itaú (lote de 100 ou fracionário)
            lotes_100 = shares_count // 100
            fracionario = shares_count % 100
            if lotes_100 > 0 and fracionario > 0:
                execution_instruction = f"{lotes_100} lote(s) padrão ({lotes_100 * 100} de {ticker_b3}) + {fracionario} no fracionário ({ticker_b3}F)"
            elif lotes_100 > 0 and fracionario == 0:
                execution_instruction = f"{lotes_100} lote(s) padrão de {ticker_b3} ({shares_count} ações)"
            else:
                execution_instruction = f"{shares_count} ações no fracionário ({ticker_b3}F)"

            allocations.append({
                "ticker": ticker_b3,
                "name": stock["meta"]["name"],
                "sector": stock["meta"]["sector"],
                "score": stock["score"],
                "confidence_pct": stock["confidence_pct"],
                "current_price": current_price,
                "shares_count": shares_count,
                "invested_amount": actual_amount,
                "weight_pct": round((actual_amount / self.total_capital) * 100, 1),
                "execution_instruction": execution_instruction,
                "entry_action": stock["price_levels"]["entry_action"],
                "target_price": stock["price_levels"]["target_price"],
                "potential_gain_pct": stock["price_levels"]["potential_gain_pct"],
                "stop_loss_price": stock["price_levels"]["stop_loss_price"],
                "max_loss_pct": stock["price_levels"]["max_loss_pct"],
                "dividend_yield": stock["fund"].get("dividend_yield", 0.0),
                "pe_ratio": stock["fund"].get("pe_ratio"),
                "roe": stock["fund"].get("roe"),
                "valuation": stock.get("valuation"),
                "forensic": stock.get("forensic"),
                "seasonality": stock.get("seasonality"),
                "bazin_fair_price": stock.get("valuation", {}).get("bazin_fair_price") if stock.get("valuation") else None,
                "graham_fair_price": stock.get("valuation", {}).get("graham_fair_price") if stock.get("valuation") else None,
                "piotroski_score": stock.get("forensic", {}).get("piotroski_score") if stock.get("forensic") else None,
                "piotroski_badge": stock.get("forensic", {}).get("piotroski_badge") if stock.get("forensic") else None,
            })

        cash_remaining = round(self.total_capital - total_invested, 2)
        portfolio_dy = round(sum(a["dividend_yield"] * (a["invested_amount"] / total_invested) for a in allocations if total_invested > 0), 2)
        portfolio_potential_gain = round(sum(a["potential_gain_pct"] * (a["invested_amount"] / total_invested) for a in allocations if total_invested > 0), 2)

        return {
            "allocations": allocations,
            "total_capital": self.total_capital,
            "total_allocated": round(total_invested, 2),
            "cash_remaining": cash_remaining,
            "portfolio_dividend_yield": portfolio_dy,
            "portfolio_expected_upside": portfolio_potential_gain,
            "num_positions": len(allocations),
        }

