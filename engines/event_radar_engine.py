"""
Motor de Radar de Eventos Cíclicos (Eleições, Copom, Balanços, Fiscal) e
Eventos Contingentes / Imprevisíveis (Tensões Geopolíticas, Commodities, Clima, Estatais).

Monitora indicadores de estresse em tempo real sem viés comercial (^VIX, Ouro GC=F,
Petróleo Brent BZ=F, Treasury 10Y ^TNX, Dólar USDBRL=X) para calibrar alertas,
probabilidades e planos de ação táticos para a carteira de R$ 20.000 no Itaú.
"""
import datetime
import logging
import warnings
from typing import Dict, Any, List
import yfinance as yf

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)


class EventRadarEngine:
    """
    Mapeia e monitora eventos previsíveis (cíclicos/calendário) e imprevisíveis
    (geopolíticos/exógenos) que induzem quedas ou subidas bruscas na B3.
    """

    def _fetch_live_stress_indicators(self) -> Dict[str, Any]:
        """
        Coleta indicadores globais de risco e refúgio em tempo real:
        - ^VIX: Índice de Volatilidade / Medo S&P 500 (CBOE)
        - GC=F: Ouro Futuro (Termômetro de tensão geopolítica / busca por refúgio)
        - BZ=F: Petróleo Brent (Termômetro de conflitos no Oriente Médio / oferta de energia)
        - ^TNX: US 10-Year Treasury Yield (Estresse monetário global)
        - USDBRL=X: Câmbio Dólar/Real (Termômetro de risco fiscal e eleitoral doméstico)
        """
        metrics = {
            "vix_level": 18.5,
            "vix_change_5d_pct": 0.0,
            "gold_usd": 2700.0,
            "gold_change_20d_pct": 2.5,
            "brent_usd": 75.0,
            "brent_change_20d_pct": 0.0,
            "us10y_yield": 4.25,
            "usd_brl": 5.70,
            "usd_volatility_20d_pct": 12.0,
        }

        tickers_map = {
            "^VIX": ("vix_level", "vix_change_5d_pct", 5),
            "GC=F": ("gold_usd", "gold_change_20d_pct", 20),
            "BZ=F": ("brent_usd", "brent_change_20d_pct", 20),
            "^TNX": ("us10y_yield", None, 5),
            "USDBRL=X": ("usd_brl", None, 20),
        }

        for symbol, (val_key, chg_key, lookback) in tickers_map.items():
            try:
                hist = yf.Ticker(symbol).history(period="2mo")
                if not hist.empty and "Close" in hist.columns:
                    closes = hist["Close"].dropna()
                    if len(closes) >= 1:
                        metrics[val_key] = round(float(closes.iloc[-1]), 2)
                    if chg_key and len(closes) > lookback:
                        ref_val = float(closes.iloc[-(lookback + 1)])
                        if ref_val > 0:
                            metrics[chg_key] = round(((float(closes.iloc[-1]) / ref_val) - 1.0) * 100.0, 2)
                    if symbol == "USDBRL=X" and len(closes) > 10:
                        daily_ret = closes.pct_change().dropna()
                        metrics["usd_volatility_20d_pct"] = round(float(daily_ret.std() * (252 ** 0.5) * 100.0), 1)
            except Exception as e:
                logger.warning(f"Falha ao coletar indicador de estresse {symbol}: {e}")

        # Cálculo do Score de Tensão Global & Doméstica (0 a 100)
        stress_score = 30  # Base neutra
        if metrics["vix_level"] >= 25:
            stress_score += 25
        elif metrics["vix_level"] >= 20:
            stress_score += 12

        if metrics["gold_change_20d_pct"] >= 4.0:
            stress_score += 15  # Forte corrida para o Ouro (tensão geopolítica)
        elif metrics["gold_change_20d_pct"] >= 2.0:
            stress_score += 8

        if abs(metrics["brent_change_20d_pct"]) >= 8.0 or metrics["brent_usd"] >= 95.0:
            stress_score += 15  # Choque de petróleo / prêmio geopolítico no Brent

        if metrics["us10y_yield"] >= 4.5:
            stress_score += 10  # Pressão nos Treasuries americanos

        if metrics["usd_volatility_20d_pct"] >= 15.0 or metrics["usd_brl"] >= 5.65:
            stress_score += 15  # Pressão cambial / ruído doméstico

        stress_score = min(95, max(15, stress_score))

        if stress_score >= 65:
            regime_alert = "ALTA TENSÃO (Defesa Máxima & Caixa Tático)"
            alert_color = "error"
        elif stress_score >= 45:
            regime_alert = "ALERTA MODERADO (Atenção a Ruídos Eleitorais e Geopolíticos)"
            alert_color = "warning"
        else:
            regime_alert = "AMBIENTE ESTÁVEL (Operação Normal por Fundamentos)"
            alert_color = "success"

        metrics["stress_score"] = stress_score
        metrics["regime_alert"] = regime_alert
        metrics["alert_color"] = alert_color
        return metrics

    def get_predictable_cyclical_events(self, current_date: datetime.date = None) -> List[Dict[str, Any]]:
        """
        Retorna a matriz de Eventos Previsíveis e Cíclicos (Calendário Institucional e Eleitoral)
        que historicamente provocam quedas ou subidas bruscas na B3.
        """
        if current_date is None:
            current_date = datetime.date.today()

        year = current_date.year
        month = current_date.month
        is_presidential_election_year = (year % 2 == 0)

        # Status dinâmico do ciclo eleitoral
        if is_presidential_election_year and month in (8, 9, 10, 11):
            election_status = "🔴 ATIVO AGORA (Janela Crítica de Volatilidade Eleitoral / Transição)"
        elif is_presidential_election_year:
            election_status = "🟡 ANO ELEITORAL EM CURSO (Monitorar Pesquisas e Âncora Fiscal)"
        else:
            election_status = "🟢 Fora de Pico Eleitoral (Monitoramento Estrutural)"

        # Status dinâmico da temporada de balanços
        if month in (2, 3, 5, 8, 11):
            earnings_status = "🔴 ATIVO NESTE MÊS (Divulgação de Balanços CVM — ITR/DFP)"
        else:
            earnings_status = "🟡 Próxima Janela Trimestral (Acompanhar Prévia Operacional)"

        return [
            {
                "event_name": "🗳️ Ciclo Eleitoral (Eleições Presidenciais / Gerais no Brasil e EUA)",
                "category": "Cíclico Previsível (A cada 2 / 4 anos — Pico entre Agosto e Novembro)",
                "current_status": election_status,
                "historical_impact": "Oscilações bruscas de -15% a +25% no Ibovespa; forte volatilidade no Dólar e nos Juros Futuros (DI).",
                "why_it_moves_market": (
                    "Eleições alteram expectativas sobre o teto/arcabouço fiscal, endividamento público, "
                    "nomeação de diretorias em estatais (Banco do Brasil, Petrobras) e trajetória da Taxa Selic. "
                    "Antes do pleito, a incerteza eleva o prêmio de risco (quedas bruscas); definido o cenário "
                    "e sinalizada responsabilidade fiscal, ocorre forte rali de alívio (subida brusca)."
                ),
                "vulnerable_sectors": "Estatais (BBAS3, PETR4), Varejo/Construção sensíveis a juros longos (LREN3, EZTC3).",
                "resilient_sectors": "Transmissoras privadas/mistas com receita blindada pela inflação (TAEE11, ISAE4), Seguradoras (CXSE3, BBSE3) e Exportadoras Dolarizadas (WEGE3, SUZB3, VALE3).",
                "action_protocol": (
                    "1. ANTES/DURANTE A ELEIÇÃO: Nunca concentre mais de 20% a 25% da carteira em uma única estatal; "
                    "mantenha os 80% do patrimônio (R$ 80.000) protegidos no CDI.\n"
                    "2. EM QUEDAS BRUSCAS POR PÂNICO ELEITORAL: Se estatais lucrativas (como BBAS3) caírem para múltiplos "
                    "abaixo de 3,5x P/L sem mudança real no estatuto, evite vender no fundo e aproveite para comprar em tranches.\n"
                    "3. EM SUBIDAS BRUSCAS (RALI PÓS-URNAS): Realize lucro parcial nas ações que atingirem o Preço-Alvo."
                )
            },
            {
                "event_name": "🏦 Super Quarta: Decisões de Juros do COPOM (Brasil) e FOMC (EUA)",
                "category": "Cíclico Previsível (A cada 45 dias — 8 reuniões anuais)",
                "current_status": "🟡 Recorrente a cada 6 semanas (Gatilho Direto de Reprecificação)",
                "historical_impact": "Movimentos rápidos de -3% a +5% em um único pregão dependendo do comunicado (Hawkish vs. Dovish).",
                "why_it_moves_market": (
                    "A taxa básica de juros é a 'gravidade' do preço das ações. Quando o Banco Central sinaliza "
                    "cortes de juros (Dovish), ações cíclicas e pagadoras de dividendos disparam; quando sinaliza "
                    "alta ou manutenção prolongada (Hawkish), o fluxo migra para a renda fixa, derrubando múltiplos."
                ),
                "vulnerable_sectors": "Empresas alavancadas com dívida atrelada ao CDI (VAMO3, CSAN3, Varejo).",
                "resilient_sectors": "Seguradoras (BBSE3, CXSE3) e Bancos (ITUB4, BBAS3), cujo resultado financeiro cresce com a Selic alta.",
                "action_protocol": (
                    "Evite enviar ordens a mercado nos últimos 30 minutos antes do fechamento em dias de Copom/Fed. "
                    "Posicione ordens limitadas na Faixa de Entrada para capturar sombras de volatilidade no pregão seguinte."
                )
            },
            {
                "event_name": "📊 Temporada de Balanços CVM (ITR/DFP) e Cortes de Data-Com (Dividendos)",
                "category": "Cíclico Previsível (Fevereiro/Março, Maio, Agosto e Novembro)",
                "current_status": earnings_status,
                "historical_impact": "Saltos ou quedas individuais de -8% a +12% na abertura do pregão pós-balanço.",
                "why_it_moves_market": (
                    "É o momento em que o lucro real auditado confronta a expectativa do mercado, além do anúncio "
                    "oficial de Dividendos e JCP. Semanas antes da 'Data-Com', ações de alto dividendo costumam "
                    "subir pela corrida de compradores; no dia seguinte ('Data-Ex'), o preço ajusta mecanicamente pelo valor do provento."
                ),
                "vulnerable_sectors": "Empresas com margens voláteis ou alto endividamento financeiro.",
                "resilient_sectors": "Concessões elétricas (EGIE3, TAEE11, CPFE3) e Seguradoras com altíssima previsibilidade de caixa.",
                "action_protocol": (
                    "Não confunda o ajuste técnico de 'Data-Ex' (quando o dividendo é descontado do preço da tela e vai "
                    "para sua conta no Itaú) com queda de fundamento! Nunca acione Stop Loss por causa de desconto de dividendo."
                )
            },
            {
                "event_name": "⚖️ Ciclo Orçamentário e Metas Fiscais (LDO em Abril / PLOA em Agosto)",
                "category": "Cíclico Previsível (Abril, Agosto e Revisões Bimestrais)",
                "current_status": "🟡 Monitoramento Contínuo do Arcabouço Fiscal",
                "historical_impact": "Oscilações de -5% a +8% na bolsa e abertura/fechamento de 50 a 100 bps nos juros longos.",
                "why_it_moves_market": (
                    "Dúvidas sobre o cumprimento da meta de superávit primário ou propostas de tributação sobre "
                    "JCP e Dividendos provocam saída temporária de investidores estrangeiros e alta do Dólar."
                ),
                "vulnerable_sectors": "Setores dependentes de subsídios ou altamente sensíveis à curva longa de juros.",
                "resilient_sectors": "Empresas com baixa alavancagem, receita dolarizada ou contratos indexados ao IPCA/IGP-M.",
                "action_protocol": (
                    "Mantenha diversificação entre setores regulados (Utilities) e Financeiro, evitando exposição a "
                    "empresas que dependam de incentivos governamentais."
                )
            },
            {
                "event_name": "⏱️ Vencimento Mensal de Opções sobre Ações e Índice Bovespa",
                "category": "Cíclico Previsível (Toda 3ª Sexta-Feira do Mês / Quarta-Feira pós dia 15)",
                "current_status": "🟢 Calendário Técnico Mensal da B3",
                "historical_impact": "Movimentos técnicos intradiários de ±2% a ±4% sem notícia fundamentalista.",
                "why_it_moves_market": (
                    "Grandes fundos e formadores de mercado defendem preços de exercício (strikes) de opções, "
                    "gerando pressão compradora ou vendedora artificial que se dissipa no pregão seguinte."
                ),
                "vulnerable_sectors": "Blue chips de altíssima liquidez em derivativos (PETR4, VALE3, BBAS3, ITUB4).",
                "resilient_sectors": "Ações de menor especulação em derivativos (CXSE3, ISAE4, TAEE11, VIVT3).",
                "action_protocol": (
                    "Se uma ação recomendada cair até a Faixa de Entrada Ideal numa 3ª sexta-feira sem nenhuma notícia "
                    "negativa na CVM, trata-se de distorção técnica de vencimento — excelente ponto de entrada limitada."
                )
            },
        ]

    def get_contingent_unpredictable_events(self, live_stress: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Retorna a matriz de Eventos Contingentes / Imprevisíveis (Geopolítica, China, Clima, Estatais),
        calibrando a probabilidade e o nível de alerta com os indicadores reais de mercado.
        """
        vix = live_stress.get("vix_level", 18.5)
        brent_usd = live_stress.get("brent_usd", 75.0)
        brent_chg = abs(live_stress.get("brent_change_20d_pct", 0.0))
        gold_chg = live_stress.get("gold_change_20d_pct", 2.0)
        usd_brl = live_stress.get("usd_brl", 5.70)
        usd_vol = live_stress.get("usd_volatility_20d_pct", 12.0)

        geo_prob = "🔴 Alta (Alerta Geopolítico Ativo — Petróleo/Refúgio Pressionados)" if (gold_chg > 3.5 or brent_chg > 7.0 or brent_usd >= 95.0 or vix > 22) else "🟡 Moderada (Latente)"
        fiscal_prob = "🔴 Alta (Volatilidade Cambial / Eleitoral Elevada)" if (usd_brl >= 5.55 or usd_vol >= 18.0) else "🟡 Moderada"

        return [
            {
                "event_name": "🌍 Escalada de Tensões Geopolíticas e Conflitos Armados (Oriente Médio / Leste Europeu / Ásia)",
                "probability_status": geo_prob,
                "early_warning_signals": (
                    f"Disparo do Ouro (atual {gold_chg:+.1f}% em 20d), salto no Petróleo Brent "
                    f"(US$ {live_stress['brent_usd']:.2f}) e alta do índice VIX (atual {vix:.1f} pts)."
                ),
                "market_shock_mechanism": (
                    "Guerras e bloqueios de rotas marítimas (Estreito de Ormuz, Mar Vermelho, Taiwan) provocam "
                    "fuga global para o Dólar e Ouro ('Flight to Quality'), encarecem o frete e o petróleo, "
                    "pressionam a inflação mundial e atrasam cortes de juros nos EUA e no Brasil."
                ),
                "losers_in_b3": "Aviação, Varejo, Consumo Cíclico e empresas com dívida em Dólar sem receita em moeda forte.",
                "winners_or_hedges_in_b3": (
                    "Petroleiras (PETR4, PRIO3 — ganham com Brent alto), Exportadoras com receita em Dólar "
                    "(SUZB3, WEGE3, VALE3) e Concessões Domésticas Essenciais (TAEE11, ISAE4, CXSE3)."
                ),
                "contingency_plan": (
                    "1. Não venda ações de energia elétrica ou seguros durante pânicos geopolíticos: o consumo de eletricidade "
                    "no Brasil não cai por conflitos externos e a inflação maior reajusta a receita das elétricas.\n"
                    "2. Caso o conflito escale severamente, adicione uma posição tática de 10% a 15% em exportadoras/commodities "
                    "(PRIO3, PETR4 ou WEGE3) como hedge cambial e energético."
                )
            },
            {
                "event_name": "🏛️ Ruído Político em Estatais ou Mudança Súbita na Tributação de Dividendos/JCP",
                "probability_status": fiscal_prob,
                "early_warning_signals": (
                    f"Dólar acima de R$ 5,50 (atual R$ {usd_brl:.2f}), declarações sobre retenção de dividendos "
                    "extraordinários ou propostas legislativas alterando alíquotas de JCP."
                ),
                "market_shock_mechanism": (
                    "Qualquer sinal de uso de empresas de economia mista para políticas públicas sem retorno "
                    "de mercado derruba abruptamente o múltiplo P/L das estatais (-10% a -20% em poucos dias)."
                ),
                "losers_in_b3": "Estatais diretas (BBAS3, PETR4) no curto prazo.",
                "winners_or_hedges_in_b3": "Bancos e Seguradoras Privadas (ITUB4) e Elétricas Privadas (EGIE3, CPFE3).",
                "contingency_plan": (
                    "1. Respeite rigorosamente o Stop Loss paramétrico (-8% máx) caso ocorra mudança real no Estatuto Social.\n"
                    "2. Se for apenas ruído verbal sem alteração estatutária nem queda no ROE, aguarde a estabilização "
                    "acima do suporte de 30 dias antes de ampliar posição."
                )
            },
            {
                "event_name": "🐉 Desaceleração Abrupta ou Pacote de Estímulo Massivo na China",
                "probability_status": "Moderada (Ciclo Industrial Asiático)",
                "early_warning_signals": "Oscilações bruscas no Minério de Ferro em Dalian/Singapura (> ±10%) e dados de PMI Chinês.",
                "market_shock_mechanism": (
                    "A China compra mais de 60% do minério de ferro marítimo global e grande parte da celulose e "
                    "soja do Brasil. Frustrações imobiliárias na China derrubam VALE3/GGBR4; pacotes de estímulo "
                    "do Politburo geram subidas explosivas (+10% a +20% em dias) nas ações de commodities."
                ),
                "losers_in_b3": "Mineradoras e Siderúrgicas (VALE3, GGBR4) em caso de desaceleração chinesa.",
                "winners_or_hedges_in_b3": "Setores domésticos descorrelacionados da China (Utilities, Telecom VIVT3, Seguros CXSE3/BBSE3).",
                "contingency_plan": (
                    "Nossa carteira defensiva já mantém peso reduzido em minério/siderurgia justamente para blindar "
                    "seus R$ 20.000 contra solavancos da economia chinesa."
                )
            },
            {
                "event_name": "🌦️ Choques Climáticos Extremos (Crise Hídrica / El Niño ou La Niña Severos)",
                "probability_status": "Baixa a Moderada (Monitoramento ONS / Reservatórios)",
                "early_warning_signals": "Queda nos níveis dos reservatórios do Sudeste/Centro-Oeste abaixo de 40% e acionamento de bandeira vermelha tarifária.",
                "market_shock_mechanism": (
                    "Secas severas obrigam o acionamento de termelétricas caras, elevando a inflação (IPCA) e "
                    "impedindo quedas da Selic. Além disso, geradoras hidrelétricas sofrem com o risco hidrológico (GSF)."
                ),
                "losers_in_b3": "Geradoras hidrelétricas puras expostas ao mercado spot e setor de Alimentos/Varejo.",
                "winners_or_hedges_in_b3": (
                    "Transmissoras de Energia (TAEE11, ISAE4)! Elas são pagas pela disponibilidade das linhas de "
                    "transmissão (RAP corrigida por inflação) e NÃO dependem do volume de chuva."
                ),
                "contingency_plan": (
                    "Priorizar transmissoras (TAEE11, ISAE4) dentro do setor elétrico garante imunidade contra crises hídricas."
                )
            },
            {
                "event_name": "⚡ Crise de Liquidez Global / Reprecificação dos Juros nos EUA (Choque no VIX)",
                "probability_status": "Moderada" if vix < 22 else "Alta (Volatilidade Global Elevada)",
                "early_warning_signals": f"Índice VIX rompendo 25-30 pontos (atual: {vix:.1f}) e Treasury de 10 Anos acima de 4,50% (atual: {live_stress['us10y_yield']:.2f}%).",
                "market_shock_mechanism": (
                    "Quando ocorre pânico em Wall Street (inflação persistente nos EUA, crise bancária regional ou "
                    "desmonte de Carry Trade no Japão), fundos globais vendem mercados emergentes indiscriminadamente "
                    "para levantar caixa em Dólar, gerando quedas bruscas porém temporárias na B3."
                ),
                "losers_in_b3": "Small Caps ilíquidas e empresas de tecnologia/crescimento com múltiplos esticados.",
                "winners_or_hedges_in_b3": "Empresas geradoras de caixa líquido imediato e alto Dividend Yield (BBSE3, CXSE3, TAEE11).",
                "contingency_plan": (
                    "Quedas causadas por liquidez externa (sem deterioração nos balanços brasileiros) historicamente "
                    "se recuperam em 30 a 90 dias. É o momento clássico em que sua reserva de R$ 80.000 no CDI "
                    "lhe dá tranquilidade psicológica para não vender no pânico."
                )
            },
        ]

    def simulate_event_impact_on_portfolio(
        self,
        allocations: List[Dict[str, Any]],
        scenario_key: str
    ) -> Dict[str, Any]:
        """
        Simula o impacto específico de um grande evento (Eleitoral, Geopolítico, Estatais, etc.)
        sobre cada ação da carteira recomendada de R$ 20.000.
        """
        scenarios_catalog = {
            "🗳️ Estresse Pré-Eleitoral Polarizado (Dólar +10%, Juros Futuros +150 bps)": {
                "description": (
                    "Simula período de alta incerteza pré-1º/2º turno eleitoral: abertura da curva de juros, "
                    "alta do Dólar e desconto de risco político sobre estatais."
                ),
                "ibov_shock_pct": -14.0,
                "ticker_shocks": {
                    "BBAS3": -12.5,
                    "PETR4": -14.0,
                    "CXSE3": -4.0,
                    "BBSE3": -4.5,
                    "TAEE11": -2.5,
                    "ISAE4": -3.0,
                    "EGIE3": -3.5,
                    "CPFE3": -3.5,
                    "ITUB4": -6.0,
                    "VIVT3": -4.0,
                    "WEGE3": +4.5,
                    "SUZB3": +6.0,
                    "VALE3": +2.0,
                },
                "tactical_recommendation": (
                    "🛡️ AÇÃO RECOMENDADA: Não zerar posições defensivas. Transmissoras (TAEE11, ISAE4) e Seguradoras "
                    "(CXSE3, BBSE3) amortecem mais de 70% do choque do Ibovespa. Se BBAS3 cair mais de 12% apenas por "
                    "temor eleitoral (mantendo ROE > 18%), torna-se oportunidade de compra com desconto histórico."
                )
            },
            "🚀 Rali Pós-Eleitoral / Compromisso Fiscal e Queda da Selic (-200 bps)": {
                "description": (
                    "Simula a dissipação da incerteza pós-eleições ou aprovação de reforma fiscal estrutural, "
                    "com entrada de capital estrangeiro e forte fechamento dos juros futuros."
                ),
                "ibov_shock_pct": +22.0,
                "ticker_shocks": {
                    "BBAS3": +24.0,
                    "PETR4": +20.0,
                    "CXSE3": +15.0,
                    "BBSE3": +14.0,
                    "TAEE11": +16.5,
                    "ISAE4": +17.0,
                    "EGIE3": +18.0,
                    "CPFE3": +16.0,
                    "ITUB4": +21.0,
                    "VIVT3": +15.5,
                    "WEGE3": +18.0,
                    "SUZB3": +8.0,
                    "VALE3": +14.0,
                },
                "tactical_recommendation": (
                    "🎯 AÇÃO RECOMENDADA: Realizar lucro parcial (vender 30% a 50% da posição) nas ações que "
                    "ultrapassarem rapidamente o Preço-Alvo calculado pelo robô, embolsando o ganho de capital."
                )
            },
            "🌍 Escalada Geopolítica Severa (Petróleo Brent a US$ 105+ e VIX > 30)": {
                "description": (
                    "Simula conflito militar de grandes proporções no Oriente Médio ou Ásia, com disparada "
                    "do petróleo, ouro e dólar, e aversão global a risco."
                ),
                "ibov_shock_pct": -9.5,
                "ticker_shocks": {
                    "PETR4": +14.0,
                    "SUZB3": +7.0,
                    "WEGE3": +3.0,
                    "VALE3": -4.0,
                    "TAEE11": -1.5,
                    "ISAE4": -2.0,
                    "EGIE3": -2.5,
                    "CPFE3": -2.5,
                    "CXSE3": -3.0,
                    "BBSE3": -3.0,
                    "BBAS3": -6.5,
                    "ITUB4": -5.5,
                    "VIVT3": -3.0,
                },
                "tactical_recommendation": (
                    "🛡️ AÇÃO RECOMENDADA: Sua carteira de Utilities e Seguros sofre menos da metade da queda do Ibovespa "
                    "pois a inflação global mais alta reajusta os contratos de transmissão elétrica (IPCA/IGP-M) e mantém "
                    "a receita financeira das seguradoras elevada."
                )
            },
            "🏛️ Ruído Agudo em Estatais / Proposta de Mudança no JCP": {
                "description": (
                    "Simula declarações políticas de intervenção em preços/dividendos de estatais ou rumor "
                    "de alteração tributária sobre Juros sobre Capital Próprio."
                ),
                "ibov_shock_pct": -7.5,
                "ticker_shocks": {
                    "BBAS3": -14.0,
                    "PETR4": -16.5,
                    "CXSE3": -6.5,
                    "BBSE3": -7.0,
                    "TAEE11": -1.0,
                    "ISAE4": -1.0,
                    "EGIE3": +1.5,
                    "CPFE3": +1.0,
                    "ITUB4": -3.5,
                    "VIVT3": -2.0,
                    "WEGE3": +2.0,
                },
                "tactical_recommendation": (
                    "⚠️ AÇÃO RECOMENDADA: Acompanhar o Stop Loss de proteção nas estatais (BBAS3). Notar como "
                    "as transmissoras e elétricas privadas (TAEE11, ISAE4, EGIE3) funcionam como porto seguro imediato."
                )
            },
        }

        chosen = scenarios_catalog.get(scenario_key, list(scenarios_catalog.values())[0])
        shocks_map = chosen["ticker_shocks"]

        rows = []
        total_current = 0.0
        total_shocked = 0.0

        for item in allocations:
            ticker = item["ticker"]
            invested = float(item["invested_amount"])
            shock_pct = shocks_map.get(ticker, -4.0)
            impact_brl = invested * (shock_pct / 100.0)
            new_val = invested + impact_brl

            total_current += invested
            total_shocked += new_val

            rows.append({
                "Ação": ticker,
                "Empresa": item.get("name", ticker),
                "Setor": item.get("sector", ""),
                "Valor Atual": f"R$ {invested:,.2f}",
                "Impacto Estimado (%)": f"{shock_pct:+.1f}%",
                "Impacto em R$": f"R$ {impact_brl:+,.2f}",
                "Saldo Pós-Evento": f"R$ {new_val:,.2f}",
            })

        port_shock_brl = total_shocked - total_current
        port_shock_pct = (port_shock_brl / total_current * 100.0) if total_current > 0 else 0.0
        ibov_shock_pct = chosen["ibov_shock_pct"]
        ibov_shock_brl = total_current * (ibov_shock_pct / 100.0)

        return {
            "scenario_name": scenario_key,
            "description": chosen["description"],
            "portfolio_impact_pct": round(port_shock_pct, 2),
            "portfolio_impact_brl": round(port_shock_brl, 2),
            "portfolio_final_brl": round(total_shocked, 2),
            "ibov_impact_pct": round(ibov_shock_pct, 2),
            "ibov_impact_brl": round(ibov_shock_brl, 2),
            "relative_protection_pct": round(port_shock_pct - ibov_shock_pct, 2),
            "tactical_recommendation": chosen["tactical_recommendation"],
            "asset_impacts": rows,
            "available_scenarios": list(scenarios_catalog.keys()),
        }

    def get_full_event_radar(self, allocations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Retorna todo o diagnóstico de eventos cíclicos, contingentes e indicadores de tensão."""
        live_stress = self._fetch_live_stress_indicators()
        cyclical = self.get_predictable_cyclical_events()
        contingent = self.get_contingent_unpredictable_events(live_stress)
        default_sim = self.simulate_event_impact_on_portfolio(
            allocations,
            "🗳️ Estresse Pré-Eleitoral Polarizado (Dólar +10%, Juros Futuros +150 bps)"
        )
        return {
            "live_stress": live_stress,
            "cyclical_events": cyclical,
            "contingent_events": contingent,
            "default_simulation": default_sim,
        }


if __name__ == "__main__":
    engine = EventRadarEngine()
    mock_alloc = [
        {"ticker": "CXSE3", "name": "Caixa Seguridade", "sector": "Financeiro", "invested_amount": 4000.0},
        {"ticker": "TAEE11", "name": "Taesa", "sector": "Utilities", "invested_amount": 4000.0},
        {"ticker": "ISAE4", "name": "ISA CTEEP", "sector": "Utilities", "invested_amount": 4000.0},
        {"ticker": "BBSE3", "name": "BB Seguridade", "sector": "Financeiro", "invested_amount": 4000.0},
        {"ticker": "BBAS3", "name": "Banco do Brasil", "sector": "Financeiro", "invested_amount": 4000.0},
    ]
    radar = engine.get_full_event_radar(mock_alloc)
    print("Live Stress:", radar["live_stress"])
    print("Cyclical Events Count:", len(radar["cyclical_events"]))
    print("Contingent Events Count:", len(radar["contingent_events"]))
    print("Sim Impact:", radar["default_simulation"]["portfolio_impact_pct"], "% vs Ibov", radar["default_simulation"]["ibov_impact_pct"], "%")
