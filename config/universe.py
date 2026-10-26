"""
Universo de Ativos Elegíveis da B3 para Análise Top-Down.
Foco em empresas com alta liquidez (> R$ 10M/dia), saúde financeira,
histórico de lucros e solidez para o perfil conservador/defensivo.
"""
from typing import Dict, Any

UNIVERSE_B3: Dict[str, Dict[str, Any]] = {
    "BBAS3.SA": {
        "ticker": "BBAS3",
        "name": "Banco do Brasil",
        "sector": "Financeiro",
        "subsector": "Bancos",
        "profile": "Dividendos / Valor",
        "beta": 0.85,
        "is_defensive": True,
        "description": "Maior banco do país em crédito rural, com dividend yield historicamente alto e valuation descontado."
    },
    "ITUB4.SA": {
        "ticker": "ITUB4",
        "name": "Itaú Unibanco",
        "sector": "Financeiro",
        "subsector": "Bancos",
        "profile": "Qualidade / Dividendos",
        "beta": 0.78,
        "is_defensive": True,
        "description": "Maior banco privado da América Latina, referência em rentabilidade (ROE > 20%), baixíssima inadimplência e governança."
    },
    "BBSE3.SA": {
        "ticker": "BBSE3",
        "name": "BB Seguridade",
        "sector": "Financeiro",
        "subsector": "Previdência & Seguros",
        "profile": "Dividendos / Defensivo",
        "beta": 0.55,
        "is_defensive": True,
        "description": "Empresa com modelo de negócios leve em capital, forte distribuição de dividendos e float financeiro impulsionado por juros altos."
    },
    "CXSE3.SA": {
        "ticker": "CXSE3",
        "name": "Caixa Seguridade",
        "sector": "Financeiro",
        "subsector": "Previdência & Seguros",
        "profile": "Dividendos / Defensivo",
        "beta": 0.58,
        "is_defensive": True,
        "description": "Parcerias exclusivas com a Caixa Econômica Federal em crédito imobiliário, alta conversão de caixa em proventos."
    },
    "EGIE3.SA": {
        "ticker": "EGIE3",
        "name": "Engie Brasil",
        "sector": "Utilities",
        "subsector": "Geração & Transmissão Elétrica",
        "profile": "Defensivo / Dividendos",
        "beta": 0.45,
        "is_defensive": True,
        "description": "Maior geradora privada de energia renovável do Brasil, contratos de longo prazo e estabilidade operacional."
    },
    "CPFE3.SA": {
        "ticker": "CPFE3",
        "name": "CPFL Energia",
        "sector": "Utilities",
        "subsector": "Distribuição & Geração Elétrica",
        "profile": "Dividendos / Defensivo",
        "beta": 0.50,
        "is_defensive": True,
        "description": "Concessões de distribuição de alta eficiência e histórico consistente de proventos atrativos."
    },
    "TAEE11.SA": {
        "ticker": "TAEE11",
        "name": "Taesa",
        "sector": "Utilities",
        "subsector": "Transmissão Elétrica",
        "profile": "Dividendos / Hiper-Defensivo",
        "beta": 0.40,
        "is_defensive": True,
        "description": "Negócio de transmissão pura com receita anual permitida (RAP) indexada à inflação (IPCA/IGP-M) e sem risco de volume."
    },
    "ISAE4.SA": {
        "ticker": "ISAE4",
        "name": "ISA CTEEP",
        "sector": "Utilities",
        "subsector": "Transmissão Elétrica",
        "profile": "Dividendos / Hiper-Defensivo",
        "beta": 0.42,
        "is_defensive": True,
        "description": "Uma das maiores transmissoras do país, receitas reguladas e blindadas contra oscilações de PIB."
    },
    "SAPR11.SA": {
        "ticker": "SAPR11",
        "name": "Sanepar",
        "sector": "Utilities",
        "subsector": "Saneamento",
        "profile": "Valor / Dividendos",
        "beta": 0.52,
        "is_defensive": True,
        "description": "Monopólio natural de saneamento no Paraná, múltiplos de valuation muito atrativos (baixo P/L e P/VP)."
    },
    "CSMG3.SA": {
        "ticker": "CSMG3",
        "name": "Copasa",
        "sector": "Utilities",
        "subsector": "Saneamento",
        "profile": "Valor / Dividendos",
        "beta": 0.56,
        "is_defensive": True,
        "description": "Companhia de saneamento de Minas Gerais, forte payout de proventos e estabilidade de demanda."
    },
    "VIVT3.SA": {
        "ticker": "VIVT3",
        "name": "Telefônica Brasil (Vivo)",
        "sector": "Telecomunicações",
        "subsector": "Serviços Perenes",
        "profile": "Defensivo / Dividendos",
        "beta": 0.48,
        "is_defensive": True,
        "description": "Líder de mercado em telefonia móvel e fibra, demanda inelástica, forte geração de caixa livre e programa de recompra/proventos."
    },
    "WEGE3.SA": {
        "ticker": "WEGE3",
        "name": "WEG",
        "sector": "Bens Industriais",
        "subsector": "Motores & Equipamentos Elétricos",
        "profile": "Qualidade Extrema / Crescimento Seguro",
        "beta": 0.72,
        "is_defensive": True,
        "description": "Multinacional brasileira com retorno sobre capital investido (ROIC > 25%), presença global e proteção cambial."
    },
    "VALE3.SA": {
        "ticker": "VALE3",
        "name": "Vale",
        "sector": "Commodities / Materiais",
        "subsector": "Mineração",
        "profile": "Dividendos / Ciclo Global",
        "beta": 1.05,
        "is_defensive": False,
        "description": "Uma das maiores mineradoras de minério de ferro do mundo, geradora maciça de caixa e dividendos, sensível à China."
    },
    "PETR4.SA": {
        "ticker": "PETR4",
        "name": "Petrobras",
        "sector": "Commodities / Petróleo",
        "subsector": "Óleo & Gás",
        "profile": "Dividendos / Ciclo de Energia",
        "beta": 1.10,
        "is_defensive": False,
        "description": "Líder em exploração offshore no Pré-Sal, custo de extração ultra competitivo e elevado retorno em proventos."
    },
    "KLBN11.SA": {
        "ticker": "KLBN11",
        "name": "Klabin",
        "sector": "Commodities / Papel & Celulose",
        "subsector": "Embalagens & Papel",
        "profile": "Valor / Defensivo",
        "beta": 0.65,
        "is_defensive": True,
        "description": "Maior produtora e exportadora de papéis para embalagens do Brasil, receita dolarizada e demanda essencial perene."
    }
}
