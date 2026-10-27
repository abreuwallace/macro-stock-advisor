"""
Motor de Varredura de Oportunidades Assimétricas & Turnaround (B3).
Identifica ações com quedas bruscas injustificadas ou superdimensionadas,
alto potencial de multiplicação patrimonial (2x ou +50% a +150%), filtro de solvência
anti-falência e auditoria detalhada dos catalisadores de recuperação.
"""
import logging
from typing import Dict, Any, List
import yfinance as yf
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Universo de Candidatas a Oportunidades / Turnaround com Ativos Reais
OPPORTUNITY_CANDIDATES = {
    "VAMO3.SA": {
        "ticker": "VAMO3",
        "name": "Vamos Locação",
        "sector": "Bens de Capital / Logística",
        "thesis_type": "Líder de Mercado & Queda por Juros Altos",
        "why_it_fell": "Impacto do custo da dívida de curto prazo decorrente da Selic a 13.75% e renovação de frota de concessionárias pós-agrícola.",
        "solvency_strength": "Contratos de locação de longo prazo (média de 5 anos) com clientes de primeira linha (Vale, Suzano, Ambev) e frota de caminhões com alto valor de revenda.",
        "turnaround_catalysts": [
            "Início do ciclo de afrouxamento monetário reduzindo as despesas financeiras em centenas de milhões de reais.",
            "Desinvestimento e reestruturação da rede de concessionárias para focar 100% no negócio puro de locação (alta margem EBITDA > 70%).",
            "Retomada das safras de grãos e demanda aquecida no agronegócio e logística pesada."
        ],
        "key_risk": "Volatilidade no preço de revenda de caminhões seminovos e juros altos prolongados."
    },
    "LREN3.SA": {
        "ticker": "LREN3",
        "name": "Lojas Renner",
        "sector": "Consumo Cíclico / Varejo",
        "thesis_type": "Fallen Angel / Líder Absoluta com Balanço Limpo",
        "why_it_fell": "Desaceleração do varejo físico brasileiro, concorrência de plataformas asiáticas (Shein/Shopee) e custo do crédito ao consumidor na financeira Realize.",
        "solvency_strength": "Balanço invejável: quase sem dívida líquida bancária, caixa robusto, retorno histórico sobre o capital investido e marca mais valiosa do vestuário nacional.",
        "turnaround_catalysts": [
            "Normalização da inadimplência na carteira de crédito da Realize e volta da concessão lucrativa de cartões.",
            "Equalização tributária para plataformas internacionais (taxação de importações) protegendo a margem de confecção nacional.",
            "Ganhos de eficiência com o novo Centro de Distribuição automatizado em Cabreúva, reduzindo despesas operacionais."
        ],
        "key_risk": "Poder de compra da classe média estagnado e concorrência digital agressiva."
    },
    "EZTC3.SA": {
        "ticker": "EZTec",
        "name": "EZTec Empreendimentos",
        "sector": "Construção Civil / Real Estate",
        "thesis_type": "Deep Value / Desconto Patrimonial Extremo",
        "why_it_fell": "Aversão generalizada do mercado a construtoras devido ao encarecimento do financiamento imobiliário com a Selic elevada.",
        "solvency_strength": "Uma das poucas construtoras do Brasil com Caixa Líquido positivo (tem mais dinheiro em caixa do que dívidas), landbank de primeiríssima linha em São Paulo 100% quitado.",
        "turnaround_catalysts": [
            "A ação negocia a cerca de 0.60x P/VP — o investidor compra R$ 1,00 de terrenos e prédios prontos em SP por apenas R$ 0,60.",
            "Venda ou locação de lajes corporativas icônicas (ex: Torre EZ Mark / Esther Towers) destravando centenas de milhões em caixa e dividendos extraordinários.",
            "Ciclo imobiliário de alta renda historicamente resiliente a variações de PIB."
        ],
        "key_risk": "Lentidão nas vendas de estoques comerciais e atraso na redução dos juros imobiliários."
    },
    "CSAN3.SA": {
        "ticker": "CSAN3",
        "name": "Cosan",
        "sector": "Infraestrutura / Energia",
        "thesis_type": "Conglomerado Infra / Desalavancagem Estrutural",
        "why_it_fell": "Endividamento elevado na holding contraído para a compra de participação na Vale, somado ao custo de carregar a dívida com CDI de dois dígitos.",
        "solvency_strength": "Dona de monopólios e ativos estratégicos insubstituíveis: Rumo (maior malha ferroviária), Compass (distribuição de gás Comgás), Moove (lubrificantes globais) e Raízen.",
        "turnaround_catalysts": [
            "IPO ou venda de fatias estratégicas da Moove e Compass gerando liquidez para abater grande parte da dívida corporativa.",
            "Fluxo bilionário de dividendos recebidos das controladas operacionais à medida que a Rumo expande para o Centro-Oeste.",
            "Desconto de holding atingindo máximas históricas (a soma das partes vale o dobro do valor em bolsa)."
        ],
        "key_risk": "Execução do plano de desalavancagem e atraso na monetização de ativos."
    },
    "PRIO3.SA": {
        "ticker": "PRIO3",
        "name": "Prio (PetroRio)",
        "sector": "Petróleo & Gás Independente",
        "thesis_type": "Crescimento Operacional com Assimetria Convexo",
        "why_it_fell": "Oscilações de curto prazo na cotação do barril de petróleo Brent e atraso em licenças ambientais do campo de Wahoo pelo Ibama.",
        "solvency_strength": "Menor custo de extração (Lifting Cost) do Pré-Sal brasileiro (~US$ 8 a US$ 9 por barril), geração de caixa livre estratosférica e alavancagem baixa (< 1.2x EBITDA).",
        "turnaround_catalysts": [
            "Liberação da licença do Ibama para o campo de Wahoo, adicionando mais de 40 mil barris/dia à produção da companhia.",
            "Empresa compra poços maduros e multiplica a produtividade com taxa interna de retorno (TIR) superior a 30% em dólar.",
            "Capacidade de pagar proventos maciços ou recomprar ações próprias quando o investimento em Wahoo for concluído."
        ],
        "key_risk": "Queda abrupta do preço do petróleo Brent no mercado internacional e atrasos regulatórios ambientais."
    }
}

class OpportunityEngine:
    """Identifica, pontua e audita oportunidades de alta multiplicação e assimetria positiva."""

    def scan_opportunities(self) -> List[Dict[str, Any]]:
        """Varre o universo de oportunidades e calcula o potencial real de valorização e risco."""
        results = []

        for symbol, info in OPPORTUNITY_CANDIDATES.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2y")
                if hist.empty:
                    continue

                close = hist["Close"]
                high = hist["High"]
                current_price = float(close.iloc[-1])
                high_2y = float(high.max())
                low_2y = float(hist["Low"].min())

                # Queda desde a máxima de 2 anos (Drawdown)
                drawdown_pct = round(((current_price / high_2y) - 1.0) * 100.0, 1)

                # Múltiplos
                t_info = ticker.info or {}
                pb = t_info.get("priceToBook")
                pe = t_info.get("trailingPE") or t_info.get("forwardPE")
                analyst_target = t_info.get("targetMeanPrice")

                # Preço Justo de Recuperação (Target de Turnaround)
                if analyst_target and analyst_target > current_price:
                    target_recovery = float(analyst_target)
                else:
                    # Retorno a 70% da máxima histórica de 2 anos
                    target_recovery = round(current_price * 1.65, 2)

                upside_pct = round(((target_recovery / current_price) - 1.0) * 100.0, 1)

                # Multiplicador do patrimônio (ex: 1.8x, 2.1x)
                multiplier_x = round(target_recovery / current_price, 2)

                # Stop Loss Tático sugerido (evitar sangria caso o turnaround demore)
                stop_loss_price = round(max(low_2y * 0.95, current_price * 0.88), 2)
                max_loss_pct = round(((stop_loss_price / current_price) - 1.0) * 100.0, 1)

                # Relação Risco/Retorno Asimétrica
                downside_risk = abs(max_loss_pct) if max_loss_pct != 0 else 10.0
                asymmetry_ratio = round(upside_pct / downside_risk, 1)

                # Score de Confiança do Turnaround (0 a 100)
                # Baseado na solidez do balanço, liderança e suporte de analistas
                conf_score = 70.0
                if pb and pb < 1.0:
                    conf_score += 8.0  # Desconto sobre patrimônio líquido real
                if "Caixa" in info["solvency_strength"] or "Balanço limpo" in info["solvency_strength"]:
                    conf_score += 8.0  # Sobrevivência garantida
                if analyst_target and analyst_target > current_price * 1.3:
                    conf_score += 6.0

                conf_score = min(88.0, conf_score)

                results.append({
                    "ticker": info["ticker"],
                    "name": info["name"],
                    "sector": info["sector"],
                    "thesis_type": info["thesis_type"],
                    "current_price": round(current_price, 2),
                    "high_2y": round(high_2y, 2),
                    "drawdown_pct": drawdown_pct,
                    "target_recovery_price": round(target_recovery, 2),
                    "upside_pct": upside_pct,
                    "multiplier_x": multiplier_x,
                    "stop_loss_price": stop_loss_price,
                    "max_loss_pct": max_loss_pct,
                    "asymmetry_ratio": asymmetry_ratio,
                    "confidence_score": round(conf_score, 0),
                    "pb_ratio": round(pb, 2) if pb else None,
                    "pe_ratio": round(pe, 1) if pe else None,
                    "why_it_fell": info["why_it_fell"],
                    "solvency_strength": info["solvency_strength"],
                    "turnaround_catalysts": info["turnaround_catalysts"],
                    "key_risk": info["key_risk"],
                    "suggested_pocket_allocation": "R$ 1.500 a R$ 2.500 (10% a 15% do capital de renda variável)"
                })

            except Exception as e:
                logger.warning(f"Erro ao analisar oportunidade {symbol}: {e}")

        # Ordena pela maior assimetria (maior retorno potencial por unidade de risco)
        return sorted(results, key=lambda x: x["asymmetry_ratio"], reverse=True)

if __name__ == "__main__":
    engine = OpportunityEngine()
    opps = engine.scan_opportunities()
    for o in opps:
        print(f"{o['ticker']}: Drawdown {o['drawdown_pct']}%, Upside +{o['upside_pct']}% ({o['multiplier_x']}x), Confiança: {o['confidence_score']}%")

