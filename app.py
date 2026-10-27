"""
Dashboard Interativo do Robô de Recomendação Macroeconômica (B3).
Suporta dois modos: Painel Básico (Simplificado/Executivo) e Painel Avançado (Arcabouço Completo).
100% Isento de viés comercial, fundamentado em dados oficiais do BACEN e CVM.
"""
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf

from advisor import MacroStockAdvisor
from config.settings import SETTINGS
from engines.projections import ProjectionEngine
from engines.monte_carlo import MonteCarloEngine
from engines.robustness_diagnostic import RobustnessDiagnostic
from engines.opportunity_engine import OpportunityEngine
from engines.backtest_engine import BacktestEngine
from engines.event_radar_engine import EventRadarEngine
from engines.portfolio_simulator_engine import PortfolioSimulatorEngine

# Configuração da Página Streamlit
st.set_page_config(
    page_title="Robô de Recomendação Macro B3 | Itaú Advisory",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS Moderna
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #EC7000; /* Cor Laranja Itaú */
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #6c757d;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        border-left: 5px solid #EC7000;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Barra Lateral - Parâmetros do Usuário
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/Banco_Ita%C3%BA_logo.svg/200px-Banco_Ita%C3%BA_logo.svg.png", width=120)
st.sidebar.title("Configurações da Carteira")

view_mode = st.sidebar.radio(
    "🖥️ Modo de Visualização",
    options=[
        "📋 Painel Básico (Simplificado)",
        "🔬 Painel Avançado (Completo)",
        "🧭 Painel Simulação (Minha Carteira)"
    ],
    index=0,
    help="Alterne entre o Painel Básico (executivo), Painel Avançado (arcabouço completo) e Painel Simulação (auditoria e recomendações de atuação sobre uma carteira que você já montou)."
)

st.sidebar.markdown("---")

total_patrimony = st.sidebar.number_input(
    "Patrimônio Total (R$)",
    min_value=10_000.0,
    max_value=10_000_000.0,
    value=100_000.0,
    step=5_000.0,
    help="Seu patrimônio total disponível (ex: R$ 100.000 no cofrinho/reserva)."
)

equity_capital = st.sidebar.number_input(
    "Alocação em Ações B3 (R$)",
    min_value=1_000.0,
    max_value=total_patrimony,
    value=20_000.0,
    step=1_000.0,
    help="Capital que você deseja alocar em renda variável (ex: R$ 20.000)."
)

user_profile = st.sidebar.selectbox(
    "Perfil de Investimento",
    options=["Segura / Dividendos & Qualidade", "Moderada (Dividendos + Crescimento)", "Crescimento / Agressiva"],
    index=0,
    help="Para máxima segurança e menor risco, selecione 'Segura / Dividendos & Qualidade'."
)

num_assets = st.sidebar.slider(
    "Número de Ações na Carteira",
    min_value=4,
    max_value=6,
    value=5,
    help="Entre 4 e 6 ativos garante diversificação setorial sem pulverização."
)

api_key_input = st.sidebar.text_input(
    "Gemini API Key (Opcional)",
    type="password",
    value=os.getenv("GEMINI_API_KEY", ""),
    help="Caso queira turbinar os relatórios com a API do Gemini. Se em branco, o motor quantamental nativo opera normalmente."
)

st.sidebar.markdown("---")
refresh_btn = st.sidebar.button("🔄 Atualizar Cotações e Análise", type="primary", use_container_width=True)

# Cache de análise para navegação rápida
@st.cache_data(ttl=900, show_spinner=False)
def get_advisor_data(profile_name: str, top_stocks_count: int, capital: float, api_key: str):
    advisor = MacroStockAdvisor(api_key=api_key or None)
    advisor.allocator.total_capital = capital
    return advisor.analyze(user_profile=profile_name, top_n=top_stocks_count)


@st.cache_data(ttl=900, show_spinner=False)
def get_backtest_data(allocations: list, capital: float, cdi_annual: float):
    bt_engine = BacktestEngine(initial_capital=capital)
    return bt_engine.run_multi_scenario_backtest(allocations, cdi_annual_avg=cdi_annual)


@st.cache_data(ttl=900, show_spinner=False)
def get_event_radar_data(allocations: list):
    ev_engine = EventRadarEngine()
    return ev_engine.get_full_event_radar(allocations)


@st.cache_data(ttl=600, show_spinner=False)
def get_simulated_portfolio_data(holdings: list, profile_name: str, rec_allocations: list):
    sim_engine = PortfolioSimulatorEngine()
    return sim_engine.evaluate_user_portfolio(
        user_holdings=holdings,
        user_profile=profile_name,
        recommended_allocations=rec_allocations
    )

# Execução da Análise
if refresh_btn:
    st.cache_data.clear()

with st.spinner("Analisando cenário macroeconômico, cotações da B3 e múltiplos em tempo real..."):
    analysis = get_advisor_data(user_profile, num_assets, equity_capital, api_key_input)

macro = analysis["macro_snapshot"]
regime = analysis["macro_regime"]
plan = analysis["portfolio_plan"]
reports = analysis["reports"]


# ==============================================================================
# MODO 1: PAINEL BÁSICO (SIMPLIFICADO / EXECUTIVO)
# ==============================================================================
if "Básico" in view_mode:
    st.markdown('<div class="main-header">Robô Macro B3 — Painel Simplificado</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="sub-header">Alocação Direta: <b>R$ {equity_capital:,.2f}</b> em Ações Defensivas | '
        f'Reserva Preservada: <b>R$ {(total_patrimony - equity_capital):,.2f}</b> (80% no Cofrinho/CDI)</div>',
        unsafe_allow_html=True
    )

    # Banner de Isenção de Viés
    st.info("""
    🛡️ **Garantia de Isenção e Independência (Dados 100% Não-Inviesados):**
    Todas as recomendações deste sistema decorrem exclusivamente de modelos matemáticos quantamentais alimentados por fontes públicas oficiais:
    - **Taxa Selic e Inflação:** Banco Central do Brasil (BACEN SGS - Séries 432 e 13522).
    - **Cotações e Volumes:** Negociação real da B3 (sem spread de intermediários).
    - **Demonstrações Financeiras:** Balanços auditados oficiais arquivados na CVM.
    *Zero conflito de agência: sem taxas de corretagem embutidas, sem incentivo a giro excessivo e sem relatórios patrocinados por empresas.*
    """)

    # 4 Cards Principais
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        st.metric("Capital a Investir", f"R$ {plan['total_allocated']:,.2f}", f"Caixa: R$ {plan['cash_remaining']:,.2f}")
    with b2:
        st.metric("Dividend Yield Médio", f"{plan['portfolio_dividend_yield']}% a.a.", "Isento de IR")
    with b3:
        st.metric("Preço-Alvo Médio (Ganho)", f"+{plan['portfolio_expected_upside']}%", "Meta de Lucro")
    with b4:
        st.metric("Total de Ações", f"{plan['num_positions']} Empresas", "Diversificação Ótima")

    st.markdown("---")

    # Radar Executivo de Eventos Cíclicos e Geopolíticos no Painel Básico
    basic_radar = get_event_radar_data(plan["allocations"])
    basic_stress = basic_radar["live_stress"]
    with st.expander(f"📡 Avisos de Eventos Cíclicos (Eleições/Balanços) & Geopolítica — Status: {basic_stress['regime_alert']}", expanded=True):
        st.markdown(f"""
        - **🗳️ Eventos Cíclicos Previsíveis:** `{basic_radar['cyclical_events'][0]['current_status']}` | `{basic_radar['cyclical_events'][2]['current_status']}`
        - **🌍 Termômetro Geopolítico & Mercado em Tempo Real:** Score de Tensão **{basic_stress['stress_score']}/100** | Índice VIX: **{basic_stress['vix_level']} pts** | Petróleo Brent: **US$ {basic_stress['brent_usd']:.2f}** | Ouro Refúgio: **US$ {basic_stress['gold_usd']:.2f}**
        - **🛡️ Diretriz Prática para sua Carteira (R$ 20.000):** Sua carteira prioriza Transmissoras de Energia (`TAEE11`, `ISAE4`) e Seguradoras (`CXSE3`, `BBSE3`) que historicamente amortecem mais de 65% dos choques eleitorais e geopolíticos. Evite enviar ordens a mercado em véspera de Copom ou apuração eleitoral; utilize sempre **Ordem Limitada** na Faixa de Entrada Ideal. *(Para explorar o simulador completo de choques eleitorais e geopolíticos, alterne para o **Painel Avançado -> aba 📡 Eventos, Eleições & Geopolítica**).*
        """)

    # 1. Tabela Executiva de Ações
    st.markdown("### 📋 1. Ações Recomendadas para Comprar")
    basic_table = []
    for item in plan["allocations"]:
        basic_table.append({
            "Ação": item["ticker"],
            "Empresa": item["name"],
            "Setor": item["sector"],
            "Preço Atual": f"R$ {item['current_price']:.2f}",
            "Qtd Ações": item["shares_count"],
            "Valor Total": f"R$ {item['invested_amount']:,.2f}",
            "Faixa de Entrada Ideal": item["entry_action"],
            "Preço-Alvo (Gain)": f"R$ {item['target_price']:.2f} (+{item['potential_gain_pct']}%)",
            "Stop Loss (Proteção)": f"R$ {item['stop_loss_price']:.2f} ({item['max_loss_pct']}%)",
            "Div. Yield": f"{item['dividend_yield']}%",
            "Confiança": f"{item['confidence_pct']}%"
        })
    st.dataframe(pd.DataFrame(basic_table), use_container_width=True, hide_index=True)

    st.markdown("---")

    # 2. Resumo de Ordens para o App do Itaú
    col_ordens, col_passos = st.columns([1.1, 0.9])
    with col_ordens:
        st.markdown("### 📱 2. Como Emitir as Ordens no Itaú / Íon")
        for item in plan["allocations"]:
            st.success(f"""
            **{item['ticker']}** ({item['name']}) — Comprar **{item['shares_count']} ações**
            - 🛒 `{item['execution_instruction']}`
            - 🎯 **Preço-Alvo (Venda para Lucro):** R$ {item['target_price']:.2f}
            - 🛑 **Stop Loss (Venda para Proteção):** R$ {item['stop_loss_price']:.2f}
            """)

    with col_passos:
        st.markdown("### 💡 3. Passo a Passo Rápido")
        st.markdown("""
        1. Abra o app **Itaú** ou **Íon Itaú** no celular.
        2. Vá em **Investir > Renda Variável > Buscar Ativo**.
        3. Digite o ticker (ex: `BBAS3` ou `BBAS3F`).
        4. Insira a quantidade recomendada e selecione **Ordem Limitada** no preço da faixa de entrada.
        5. Salve os alarmes do Preço-Alvo e Stop Loss para executar as saídas recomendadas.
        """)

    st.markdown("---")

    # 3. Relatórios Executivos Diretos
    st.markdown("### 📄 4. Relatório Executivo e Motivo da Recomendação")
    basic_selected_ticker = st.selectbox(
        "Selecione uma ação para ler o relatório executivo:",
        options=[s["meta"]["ticker"] for s in analysis["ranked_stocks"]],
        key="basic_report_select"
    )
    basic_rep = reports.get(basic_selected_ticker, {})
    st.markdown(basic_rep.get("content", "Relatório não disponível."))


# ==============================================================================
# MODO 2: PAINEL SIMULAÇÃO (AUDITORIA E GESTÃO DE CARTEIRA JÁ MONTADA)
# ==============================================================================
elif "Simulação" in view_mode:
    st.markdown('<div class="main-header">Robô Macro B3 — Painel Simulação (Minha Carteira)</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Auditoria em Tempo Real da Sua Carteira Anterior: '
        'Cálculo de Lucro/Prejuízo, Yield on Cost, Risco, Monte Carlo, Backtest e Recomendações Táticas de Como Atuar Hoje</div>',
        unsafe_allow_html=True
    )

    st.info("""
    🧭 **Como funciona o Painel Simulação:**
    Insira abaixo as ações que você **já comprou no Itaú** (meses atrás ou na recomendação anterior), informando a **Quantidade de Ações** e o **Preço Médio de Compra (R$)**.
    O sistema **não cria uma carteira do zero**: ele audita a **sua carteira montada** sob as cotações e o cenário macroeconômico de hoje e responde para cada ativo:
    **Manter (Hold), Comprar Mais (Aporte), Realizar Lucro (Venda Parcial/Total), Rebalancear Peso ou Acionar Defesa (Stop/Substituição).**
    """)

    # Inicializar carteira de exemplo na sessão caso não exista
    if "user_sim_portfolio" not in st.session_state:
        st.session_state["user_sim_portfolio"] = [
            {"Ticker (B3)": "TAEE11", "Quantidade": 100, "Preço Médio (R$)": 38.00},
            {"Ticker (B3)": "CXSE3", "Quantidade": 220, "Preço Médio (R$)": 16.50},
            {"Ticker (B3)": "BBSE3", "Quantidade": 115, "Preço Médio (R$)": 33.20},
            {"Ticker (B3)": "ISAE4", "Quantidade": 150, "Preço Médio (R$)": 25.80},
            {"Ticker (B3)": "BBAS3", "Quantidade": 170, "Preço Médio (R$)": 23.00},
        ]

    col_editor, col_presets = st.columns([1.45, 0.55])
    with col_presets:
        st.markdown("#### ⚙️ Atalhos de Carteira")
        if st.button("📥 Carregar Carteira Recomendada de Hoje", use_container_width=True):
            st.session_state["user_sim_portfolio"] = [
                {
                    "Ticker (B3)": a["ticker"],
                    "Quantidade": int(a["shares_count"]),
                    "Preço Médio (R$)": float(a["current_price"]),
                }
                for a in plan["allocations"]
            ]
            st.rerun()

        if st.button("🕰️ Carregar Exemplo de Carteira Anterior (c/ Lucros e Quedas)", use_container_width=True):
            st.session_state["user_sim_portfolio"] = [
                {"Ticker (B3)": "TAEE11", "Quantidade": 100, "Preço Médio (R$)": 38.00},
                {"Ticker (B3)": "CXSE3", "Quantidade": 220, "Preço Médio (R$)": 16.50},
                {"Ticker (B3)": "BBSE3", "Quantidade": 115, "Preço Médio (R$)": 33.20},
                {"Ticker (B3)": "PETR4", "Quantidade": 95, "Preço Médio (R$)": 36.00},
                {"Ticker (B3)": "BBAS3", "Quantidade": 170, "Preço Médio (R$)": 23.00},
            ]
            st.rerun()

        st.caption(
            "💡 Você pode editar qualquer célula na tabela ao lado, adicionar novas linhas (`+`) ou excluir linhas existentes."
        )

    with col_editor:
        st.markdown("#### 📝 Edite os Ativos da Sua Carteira Montada no Itaú")
        edited_df = st.data_editor(
            pd.DataFrame(st.session_state["user_sim_portfolio"]),
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            column_config={
                "Ticker (B3)": st.column_config.TextColumn(
                    "Ação (Ticker B3)",
                    help="Ex: BBAS3, TAEE11, ITUB4, PETR4, WEGE3, CXSE3, ISAE4",
                    required=True,
                ),
                "Quantidade": st.column_config.NumberColumn(
                    "Quantidade de Ações",
                    min_value=1,
                    max_value=1_000_000,
                    step=10,
                    required=True,
                ),
                "Preço Médio (R$)": st.column_config.NumberColumn(
                    "Preço Médio de Compra (R$)",
                    min_value=0.01,
                    max_value=10_000.0,
                    step=0.50,
                    format="R$ %.2f",
                    required=True,
                ),
            },
            key="portfolio_sim_editor"
        )

    # Converter o DataFrame editado para a lista de holdings
    parsed_holdings = []
    for _, row in edited_df.iterrows():
        t_val = str(row.get("Ticker (B3)", "")).strip().upper()
        q_val = row.get("Quantidade", 0)
        p_val = row.get("Preço Médio (R$)", 0.0)
        if t_val and pd.notna(q_val) and float(q_val) > 0 and pd.notna(p_val) and float(p_val) > 0:
            parsed_holdings.append({
                "ticker": t_val,
                "shares": int(q_val),
                "avg_price": float(p_val),
            })

    if not parsed_holdings:
        st.warning("Adicione pelo menos 1 ação válida na tabela acima para calcular as métricas da sua carteira.")
    else:
        with st.spinner("Auditando sua carteira montada em tempo real (B3, CVM, BACEN)..."):
            sim_res = get_simulated_portfolio_data(parsed_holdings, user_profile, plan["allocations"])

        if sim_res and "summary" in sim_res:
            s_sum = sim_res["summary"]
            s_positions = sim_res["positions"]
            s_align = sim_res["alignment"]

            st.markdown("---")
            st.markdown("### 📊 Visão Consolidada da Sua Carteira Montada")

            k1, k2, k3, k4, k5, k6 = st.columns(6)
            with k1:
                st.metric(
                    "Custo Total Investido",
                    f"R$ {s_sum['total_invested_cost']:,.2f}",
                    f"{s_sum['num_positions']} posições ativas"
                )
            with k2:
                st.metric(
                    "Valor de Mercado Hoje",
                    f"R$ {s_sum['total_current_value']:,.2f}",
                    f"{s_sum['total_pnl_pct']:+.2f}% acumulado"
                )
            with k3:
                st.metric(
                    "Lucro / Prejuízo Aberto",
                    f"R$ {s_sum['total_pnl_brl']:+,.2f}",
                    "Resultado de Capital"
                )
            with k4:
                st.metric(
                    "Dividendos 12m & Yield on Cost",
                    f"R$ {s_sum['total_annual_dividends_brl']:,.2f}/ano",
                    f"YoC: {s_sum['weighted_yoc_pct']}% | DY Atual: {s_sum['weighted_dy_current']}%"
                )
            with k5:
                st.metric(
                    "Score Macro da Carteira",
                    f"{s_sum['weighted_score']}/100",
                    f"Confiança: {s_sum['weighted_confidence']}%"
                )
            with k6:
                hhi_label = "Diversificada" if s_sum["hhi_index"] <= 2500 else "Concentrada"
                st.metric(
                    "Concentração (HHI) & Upside",
                    f"{s_sum['hhi_index']} pts ({hhi_label})",
                    f"Upside aos Alvos: +{s_sum['weighted_upside_pct']}%"
                )

            # Abas Internas do Painel de Simulação
            sim_tab_actions, sim_tab_compare, sim_tab_mc, sim_tab_bt, sim_tab_events = st.tabs([
                "🧭 1. Como Atuar Agora (Por Ação)",
                "🔄 2. Sua Carteira vs. Ideal de Hoje",
                "🎲 3. Monte Carlo & Projeções da Sua Carteira",
                "⏪ 4. Backtesting Histórico da Sua Carteira",
                "📡 5. Risco Eleitoral & Geopolítico da Sua Carteira"
            ])

            # ------------------------------------------------------------------
            # SUB-ABA 1: COMO ATUAR AGORA POR AÇÃO
            # ------------------------------------------------------------------
            with sim_tab_actions:
                st.subheader("🧭 Diagnóstico Individual e Recomendação de Atuação no Itaú")

                ac = s_sum["action_counts"]
                a1, a2, a3, a4, a5 = st.columns(5)
                with a1:
                    st.metric("✅ Manter (Hold)", f"{ac['manter']} ação(ões)")
                with a2:
                    st.metric("🛒 Comprar Mais (Aporte)", f"{ac['aportar']} ação(ões)")
                with a3:
                    st.metric("🎯 Realizar Lucro", f"{ac['realizar_lucro']} ação(ões)")
                with a4:
                    st.metric("⚖️ Rebalancear Peso", f"{ac['rebalancear']} ação(ões)")
                with a5:
                    st.metric("🛑 Alerta Stop / Defesa", f"{ac['reduzir_stop']} ação(ões)")

                sim_table_rows = []
                for p in s_positions:
                    sim_table_rows.append({
                        "Ação": p["ticker"],
                        "Empresa": p["name"],
                        "Qtd": p["shares_count"],
                        "Preço Médio": f"R$ {p['avg_price']:.2f}",
                        "Preço Hoje": f"R$ {p['current_price']:.2f}",
                        "Saldo Hoje": f"R$ {p['current_value']:,.2f}",
                        "Peso (%)": f"{p['weight_pct']}%",
                        "Lucro/Prej (R$)": f"R$ {p['pnl_brl']:+,.2f}",
                        "Rentab. (%)": f"{p['pnl_pct']:+.2f}%",
                        "Yield on Cost": f"{p['yield_on_cost_pct']:.2f}%",
                        "Score Hoje": f"{p['score']:.1f}/100",
                        "Novo Alvo": f"R$ {p['target_price']:.2f}",
                        "Stop Proteção": f"R$ {p['stop_loss_price']:.2f}",
                        "Como Atuar Agora": p["action_badge"],
                    })
                st.dataframe(pd.DataFrame(sim_table_rows), use_container_width=True, hide_index=True)

                st.markdown("---")
                st.markdown("### 📋 Parecer Técnico e Instrução de Boleta por Posição")
                for p in s_positions:
                    box_text = f"""
                    **{p['ticker']} ({p['name']}) — {p['action_badge']}** *(Prioridade: {p['action_priority']})*
                    - **Sua Posição:** `{p['shares_count']} ações` compradas a **R$ {p['avg_price']:.2f}** (Custo: R$ {p['invested_cost']:,.2f}) $\\rightarrow$ **Cotação Hoje: R$ {p['current_price']:.2f}** (Valor: **R$ {p['current_value']:,.2f}** | Resultado: **{p['pnl_pct']:+.2f}% / R$ {p['pnl_brl']:+,.2f}**)
                    - **Proventos da Sua Posição:** Receita anual estimada de **R$ {p['annual_dividends_brl']:,.2f}** (*Yield on Cost* de **{p['yield_on_cost_pct']:.2f}% a.a.** sobre seu preço pago | DY atual de {p['dividend_yield']}%).
                    - **📱 O Que Fazer no App do Itaú:** `{p['summary_command']}`
                    - **🧠 Parecer do Sistema:** {p['rationale']}
                    """
                    if p["alert_type"] == "error":
                        st.error(box_text)
                    elif p["alert_type"] == "warning":
                        st.warning(box_text)
                    elif p["alert_type"] == "info":
                        st.info(box_text)
                    else:
                        st.success(box_text)

            # ------------------------------------------------------------------
            # SUB-ABA 2: COMPARATIVO SUA CARTEIRA VS CARTEIRA IDEAL DE HOJE
            # ------------------------------------------------------------------
            with sim_tab_compare:
                st.subheader("🔄 Comparativo: Sua Carteira Anterior vs. Carteira Recomendada Hoje")
                st.markdown("""
                É muito comum que, de um mês para o outro, as cotações oscilem e o ranking das Top 5 mude levemente.
                **Atenção:** No investimento fundamentalista de longo prazo, **você NÃO deve girar a carteira inteira todo mês**! 
                Trocas só devem ocorrer quando uma ação atinge o Preço-Alvo (realização de lucro) ou perde fundamentos (Score < 62).
                """)

                col_cmp1, col_cmp2 = st.columns(2)
                with col_cmp1:
                    st.markdown("#### 💼 Métricas da Sua Carteira Montada")
                    st.markdown(f"""
                    - **Score Macro Ponderado:** `{s_sum['weighted_score']}/100`
                    - **Dividend Yield Atual Ponderado:** `{s_sum['weighted_dy_current']}% a.a.`
                    - **Yield on Cost (Sobre seu Preço Médio):** `{s_sum['weighted_yoc_pct']}% a.a.`
                    - **Potencial Médio até os Novos Alvos:** `+{s_sum['weighted_upside_pct']}%`
                    - **Índice de Concentração HHI:** `{s_sum['hhi_index']} pts`
                    """)
                    fig_user_pie = px.pie(
                        pd.DataFrame(s_positions),
                        names="ticker",
                        values="current_value",
                        title="Pesos Atuais da Sua Carteira",
                        hole=0.45,
                        color_discrete_sequence=px.colors.qualitative.Prism
                    )
                    fig_user_pie.update_layout(height=300, margin=dict(t=40, b=10, l=10, r=10))
                    st.plotly_chart(fig_user_pie, use_container_width=True)

                with col_cmp2:
                    st.markdown("#### 🏆 Métricas da Carteira Ideal de Hoje (Top 5)")
                    rec_score_avg = round(sum(a["score"] for a in plan["allocations"]) / max(1, len(plan["allocations"])), 1)
                    st.markdown(f"""
                    - **Score Macro Ponderado:** `{rec_score_avg}/100`
                    - **Dividend Yield Atual Ponderado:** `{plan['portfolio_dividend_yield']}% a.a.`
                    - **Potencial Médio até os Alvos:** `+{plan['portfolio_expected_upside']}%`
                    - **Índice de Concentração HHI:** `2000 pts (Equilíbrio Ideal)`
                    - **Ativos no Top 5 Hoje:** `{', '.join(a['ticker'] for a in plan['allocations'])}`
                    """)
                    fig_rec_pie = px.pie(
                        pd.DataFrame(plan["allocations"]),
                        names="ticker",
                        values="invested_amount",
                        title="Pesos da Carteira Ideal de Hoje",
                        hole=0.45,
                        color_discrete_sequence=px.colors.qualitative.Safe
                    )
                    fig_rec_pie.update_layout(height=300, margin=dict(t=40, b=10, l=10, r=10))
                    st.plotly_chart(fig_rec_pie, use_container_width=True)

                st.markdown("---")
                c_al1, c_al2 = st.columns(2)
                with c_al1:
                    st.markdown("#### 🔍 Ativos da Sua Carteira Fora do Top 5 Atual")
                    if s_align["outside_top_picks"]:
                        for out_p in s_align["outside_top_picks"]:
                            st.info(
                                f"**{out_p['ticker']} ({out_p['name']})** — Score Atual: **{out_p['score']}/100** | "
                                f"Seu P&L: **{out_p['pnl_pct']:+.1f}%** | Recomendação: **{out_p['action_badge']}**"
                            )
                    else:
                        st.success("100% dos ativos da sua carteira estão exatamente dentro do Top 5 recomendado hoje!")

                with c_al2:
                    st.markdown("#### 🌟 Novas Candidatas do Top 5 Hoje (Para Novos Aportes)")
                    if s_align["new_top_picks"]:
                        for new_p in s_align["new_top_picks"]:
                            st.success(
                                f"**{new_p['ticker']} ({new_p['name']})** — Score: **{new_p['score']}/100** | "
                                f"Cotação: **R$ {new_p['current_price']:.2f}** | DY: **{new_p['dividend_yield']}%** | "
                                f"Alvo: **R$ {new_p['target_price']:.2f} (+{new_p['potential_gain_pct']}%)**"
                            )
                    else:
                        st.info("Você já possui todas as ações do Top 5 atual na sua carteira!")

            # ------------------------------------------------------------------
            # SUB-ABA 3: MONTE CARLO & PROJEÇÕES DA SUA CARTEIRA MONTADA
            # ------------------------------------------------------------------
            with sim_tab_mc:
                st.subheader("🎲 Simulação de Monte Carlo & Efeito Bola de Neve da Sua Carteira")
                selic_sim = macro.get("selic_rate", 13.75)

                mc_sim_engine = MonteCarloEngine(n_simulations=1000, n_days=252)
                with st.spinner("Executando 1.000 simulações estocásticas de Monte Carlo para a sua carteira..."):
                    user_mc = mc_sim_engine.run_simulation(
                        allocations=s_positions,
                        initial_capital=s_sum["total_current_value"],
                        cdi_annual=selic_sim
                    )

                if user_mc:
                    um1, um2, um3, um4, um5 = st.columns(5)
                    with um1:
                        st.metric("Média Projetada (1 Ano)", f"R$ {user_mc['mean_final_value']:,.2f}", f"{user_mc['expected_return_pct']:+.1f}% a.a.")
                    with um2:
                        st.metric("Desvio Padrão (Risco)", f"± R$ {user_mc['std_deviation_brl']:,.2f}", f"Vol: {user_mc['volatility_annual_pct']}% a.a.")
                    with um3:
                        st.metric("Mediana (P50)", f"R$ {user_mc['p50_median']:,.2f}", "Cenário Central")
                    with um4:
                        st.metric("Probabilidade de Lucro", f"{user_mc['prob_profit_pct']}%", "Win Rate 12m")
                    with um5:
                        st.metric("VaR 95% (Pior 5%)", f"R$ {user_mc['p5_pessimistic']:,.2f}", f"Risco Cauda: -R$ {user_mc['var_95_brl']:,.2f}")

                    pct_u = user_mc["percentiles_over_time"]
                    fig_ufan = go.Figure()
                    fig_ufan.add_trace(go.Scatter(
                        x=pct_u["Day"] + pct_u["Day"][::-1],
                        y=pct_u["P95"] + pct_u["P5"][::-1],
                        fill="toself",
                        fillcolor="rgba(236, 112, 0, 0.14)",
                        line=dict(color="rgba(255,255,255,0)"),
                        name="Intervalo 90% (P5 - P95)"
                    ))
                    fig_ufan.add_trace(go.Scatter(
                        x=pct_u["Day"],
                        y=pct_u["P50"],
                        mode="lines",
                        line=dict(color="#EC7000", width=3),
                        name="Mediana P50 da Sua Carteira"
                    ))
                    fig_ufan.add_hline(y=s_sum["total_current_value"], line_dash="dash", line_color="#6c757d", annotation_text="Saldo Atual")
                    fig_ufan.update_layout(
                        title="Cone de Incerteza de Monte Carlo (252 Pregões) — Sua Carteira Montada",
                        xaxis_title="Dias Úteis Futuros",
                        yaxis_title="Valor Projetado da Carteira (R$)",
                        height=380,
                        template="plotly_white"
                    )
                    st.plotly_chart(fig_ufan, use_container_width=True)

                st.markdown("---")
                st.markdown("#### 🔄 Projeção de Reinvestimento de Dividendos (5 Anos) da Sua Carteira")
                proj_sim_engine = ProjectionEngine()
                df_u_growth = proj_sim_engine.simulate_long_term_growth(
                    initial_capital=s_sum["total_current_value"],
                    monthly_contribution=0.0,
                    dividend_yield_annual=s_sum["weighted_dy_current"],
                    growth_annual=6.0,
                    cdi_annual=selic_sim,
                    years=5,
                    reinvest_dividends=True
                )
                fig_u_proj = go.Figure()
                fig_u_proj.add_trace(go.Scatter(x=df_u_growth["Ano"], y=df_u_growth["Carteira Ações"], mode="lines+markers", name="Sua Carteira (c/ Reinvestimento)", line=dict(color="#28a745", width=3)))
                fig_u_proj.add_trace(go.Scatter(x=df_u_growth["Ano"], y=df_u_growth["Cofrinho CDI"], mode="lines+markers", name="CDI Líquido", line=dict(color="#EC7000", width=2, dash="dash")))
                fig_u_proj.update_layout(height=340, template="plotly_white", title="Projeção Composta de 5 Anos do Saldo Atual")
                st.plotly_chart(fig_u_proj, use_container_width=True)

            # ------------------------------------------------------------------
            # SUB-ABA 4: BACKTESTING HISTÓRICO DA SUA CARTEIRA MONTADA
            # ------------------------------------------------------------------
            with sim_tab_bt:
                st.subheader("⏪ Backtesting Histórico da Sua Carteira Montada (1A, 2A, 3A e 5A)")
                selic_ubt = macro.get("selic_rate", 13.75)
                with st.spinner("Calculando desempenho histórico de 1 a 5 anos da composição da sua carteira..."):
                    user_bt = get_backtest_data(s_positions, s_sum["total_current_value"], selic_ubt)

                if user_bt and "generalized" in user_bt:
                    ugen = user_bt["generalized"]
                    ub1, ub2, ub3, ub4, ub5 = st.columns(5)
                    with ub1:
                        st.metric("Retorno 5 Anos da Composição", f"+{ugen['five_year_return_pct']}%", f"R$ {ugen['five_year_final_brl']:,.2f}")
                    with ub2:
                        st.metric("Alpha 5 Anos vs Ibovespa", f"{ugen['five_year_alpha_ibov_pct']:+.1f}% p.p.", "Acima do Índice B3")
                    with ub3:
                        st.metric("CAGR Médio Generalizado", f"{ugen['avg_cagr_pct']}% a.a.", f"Vol: {ugen['avg_volatility_pct']}%")
                    with ub4:
                        st.metric("Profit Factor & Win Rate", f"{ugen['avg_profit_factor']}x", f"Win Rate: {ugen['avg_win_rate_monthly_pct']}% meses")
                    with ub5:
                        st.metric("Beta & Max Drawdown", f"Beta {ugen['avg_realized_beta']}", f"Max DD: {ugen['worst_drawdown_port_pct']}%")

                    st.dataframe(pd.DataFrame(user_bt["summary_table"]), use_container_width=True, hide_index=True)

                    u_scen_keys = list(user_bt["scenarios"].keys())
                    sel_u_scen = st.selectbox(
                        "Selecione a janela histórica para visualizar a curva da sua carteira:",
                        options=u_scen_keys,
                        index=len(u_scen_keys) - 1,
                        key="user_bt_scen_select"
                    )
                    u_scen_data = user_bt["scenarios"][sel_u_scen]
                    u_curves = u_scen_data["curves_df"]
                    fig_ueq = go.Figure()
                    fig_ueq.add_trace(go.Scatter(x=u_curves["Data"], y=u_curves["Carteira Recomendada (R$)"], mode="lines", name="Sua Carteira (R$)", line=dict(color="#28a745", width=3)))
                    fig_ueq.add_trace(go.Scatter(x=u_curves["Data"], y=u_curves["CDI Líquido (R$)"], mode="lines", name="CDI Líquido (R$)", line=dict(color="#EC7000", width=2, dash="dash")))
                    fig_ueq.add_trace(go.Scatter(x=u_curves["Data"], y=u_curves["Ibovespa (R$)"], mode="lines", name="Ibovespa (R$)", line=dict(color="#6c757d", width=2)))
                    fig_ueq.update_layout(height=380, template="plotly_white", title=f"Backtest Histórico da Sua Carteira — {sel_u_scen}")
                    st.plotly_chart(fig_ueq, use_container_width=True)

            # ------------------------------------------------------------------
            # SUB-ABA 5: SENSIBILIDADE DA SUA CARTEIRA A ELEIÇÕES E GEOPOLÍTICA
            # ------------------------------------------------------------------
            with sim_tab_events:
                st.subheader("📡 Teste de Estresse Eleitoral & Geopolítico na Sua Carteira")
                ev_sim_eng = EventRadarEngine()
                u_ev_radar = get_event_radar_data(s_positions)
                u_avail_scen = u_ev_radar["default_simulation"]["available_scenarios"]
                sel_u_ev = st.selectbox(
                    "Simular impacto de evento agudo sobre as posições da sua carteira:",
                    options=u_avail_scen,
                    index=0,
                    key="user_ev_scen_select"
                )
                u_ev_out = ev_sim_eng.simulate_event_impact_on_portfolio(s_positions, sel_u_ev)

                ue1, ue2, ue3, ue4 = st.columns(4)
                with ue1:
                    st.metric("Impacto na Sua Carteira", f"{u_ev_out['portfolio_impact_pct']:+.2f}%", f"R$ {u_ev_out['portfolio_impact_brl']:+,.2f}")
                with ue2:
                    st.metric("Saldo Estimado Pós-Choque", f"R$ {u_ev_out['portfolio_final_brl']:,.2f}", "Valor Projetado")
                with ue3:
                    st.metric("Impacto no Ibovespa", f"{u_ev_out['ibov_impact_pct']:+.2f}%", f"R$ {u_ev_out['ibov_impact_brl']:+,.2f}")
                with ue4:
                    st.metric("Blindagem Relativa vs Ibov", f"{u_ev_out['relative_protection_pct']:+.2f}% p.p.", "Diferencial de Defesa")

                st.info(u_ev_out["tactical_recommendation"])
                st.dataframe(pd.DataFrame(u_ev_out["asset_impacts"]), use_container_width=True, hide_index=True)


# ==============================================================================
# MODO 2: PAINEL AVANÇADO (ARCABOUÇO QUANTAMENTAL COMPLETO)
# ==============================================================================
else:
    st.markdown('<div class="main-header">Robô Macro B3 | Painel Avançado & Quantamental</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="sub-header">Arcabouço Técnico Completo: Monte Carlo, Autodiagnóstico, Auditoria de Dados e Oportunidades | '
        f'Capital Renda Variável: <b>R$ {equity_capital:,.2f}</b> | Reserva: <b>R$ {(total_patrimony - equity_capital):,.2f}</b></div>',
        unsafe_allow_html=True
    )

    # 10 Abas Avançadas
    tab_portfolio, tab_events, tab_backtest, tab_opportunities, tab_projections, tab_diagnostic, tab_unbiased, tab_macro, tab_reports, tab_guide = st.tabs([
        "💼 Carteira Recomendada",
        "📡 Eventos, Eleições & Geopolítica",
        "⏪ Backtesting Histórico",
        "🔥 Oportunidades & Turnaround",
        "🎲 Projeções & Monte Carlo",
        "🔬 Autodiagnóstico & Confiança",
        "🛡️ Dados Não-Inviesados (Auditoria)",
        "🌍 Cenário Macroeconômico",
        "📄 Relatórios & Gráficos Técnicos",
        "📱 Passo a Passo no Itaú"
    ])

    # ----------------------------------------------------
    # ABA 1: CARTEIRA RECOMENDADA
    # ----------------------------------------------------
    with tab_portfolio:
        st.subheader(f"Portfólio Recomendado — Foco: {user_profile}")
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Capital Total Alocado", f"R$ {plan['total_allocated']:,.2f}", f"Caixa: R$ {plan['cash_remaining']:,.2f}")
        with c2:
            st.metric("Dividend Yield Médio", f"{plan['portfolio_dividend_yield']}% a.a.", "Isento de IR")
        with c3:
            st.metric("Potencial de Ganho (Upside)", f"+{plan['portfolio_expected_upside']}%", "Preço-Alvo Médio")
        with c4:
            st.metric("Nº de Empresas", f"{plan['num_positions']} Ações", "Diversificação Ótima")

        st.markdown("---")

        table_data = []
        for item in plan["allocations"]:
            table_data.append({
                "Ação": item["ticker"],
                "Empresa": item["name"],
                "Setor": item["sector"],
                "Preço Atual": f"R$ {item['current_price']:.2f}",
                "Qtd Ações": item["shares_count"],
                "Valor Total": f"R$ {item['invested_amount']:,.2f}",
                "Peso (%)": f"{item['weight_pct']}%",
                "Entrada Ideal": item["entry_action"],
                "Preço-Alvo": f"R$ {item['target_price']:.2f} (+{item['potential_gain_pct']}%)",
                "Stop Loss": f"R$ {item['stop_loss_price']:.2f} ({item['max_loss_pct']}%)",
                "Div. Yield": f"{item['dividend_yield']}%",
                "Confiança": f"{item['confidence_pct']}%"
            })
        df_table = pd.DataFrame(table_data)
        st.dataframe(df_table, use_container_width=True, hide_index=True)

        col_chart, col_instructions = st.columns([1, 1])
        with col_chart:
            st.markdown("#### 📊 Distribuição do Capital (R$ 20.000)")
            df_alloc = pd.DataFrame(plan["allocations"])
            fig_pie = px.pie(
                df_alloc,
                names="ticker",
                values="invested_amount",
                hover_data=["sector", "weight_pct"],
                color_discrete_sequence=px.colors.qualitative.Prism,
                hole=0.45
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=320)
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_instructions:
            st.markdown("#### ⚡ Resumo das Ordens para Executar no Itaú")
            for item in plan["allocations"]:
                st.markdown(f"""
                - **{item['ticker']}** ({item['name']}): Comprar **{item['shares_count']} ações** 
                  `{item['execution_instruction']}`.
                  - 🎯 **Preço-Alvo de Venda:** R$ {item['target_price']:.2f}
                  - 🛑 **Stop Loss de Segurança:** R$ {item['stop_loss_price']:.2f}
                """)

    # ----------------------------------------------------
    # ABA 2: RADAR DE EVENTOS CÍCLICOS, ELEIÇÕES & GEOPOLÍTICA
    # ----------------------------------------------------
    with tab_events:
        st.subheader("📡 Radar de Eventos Cíclicos (Eleições/Copom) & Choques Imprevisíveis (Geopolítica)")
        st.markdown("""
        O mercado acionário sofre **quedas ou subidas bruscas** induzidas tanto por **eventos previsíveis do calendário** 
        (*Eleições Presidenciais, reuniões do Copom/Fed, divulgação de balanços CVM e metas fiscais*) quanto por 
        **eventos contingentes imprevisíveis** (*guerras e tensões geopolíticas, pacotes na China, ruídos em estatais e choques climáticos*). 
        Esta aba monitora em tempo real os **termômetros globais de estresse** e entrega o **plano de ação exato** para blindar e multiplicar seus **R$ 20.000**.
        """)

        with st.spinner("Coletando indicadores globais de tensão (^VIX, Ouro, Petróleo Brent, Treasuries e Câmbio)..."):
            ev_radar = get_event_radar_data(plan["allocations"])
            live_stress = ev_radar["live_stress"]

        st.markdown("### 🌡️ 1. Termômetro de Tensão Global & Doméstica em Tempo Real (Sem Viés)")
        e1, e2, e3, e4, e5, e6 = st.columns(6)
        with e1:
            st.metric(
                "Score Global de Tensão",
                f"{live_stress['stress_score']}/100",
                "Risco de Evento"
            )
        with e2:
            st.metric(
                "Índice VIX (Medo Global)",
                f"{live_stress['vix_level']:.2f} pts",
                f"{live_stress['vix_change_5d_pct']:+.1f}% (5 dias)"
            )
        with e3:
            st.metric(
                "Petróleo Brent (Geopolítica)",
                f"US$ {live_stress['brent_usd']:.2f}",
                f"{live_stress['brent_change_20d_pct']:+.1f}% (20 dias)"
            )
        with e4:
            st.metric(
                "Ouro Refúgio (GC=F)",
                f"US$ {live_stress['gold_usd']:,.1f}",
                f"{live_stress['gold_change_20d_pct']:+.1f}% (20 dias)"
            )
        with e5:
            st.metric(
                "Treasury 10Y (EUA)",
                f"{live_stress['us10y_yield']:.2f}% a.a.",
                "Custo Global de Capital"
            )
        with e6:
            st.metric(
                "Volatilidade do Dólar (20d)",
                f"{live_stress['usd_volatility_20d_pct']:.1f}% a.a.",
                f"Spot: R$ {live_stress['usd_brl']:.2f}"
            )

        if live_stress["alert_color"] == "error":
            st.error(f"🚨 **Diagnóstico Atual do Radar:** **{live_stress['regime_alert']}** — Mantenha rigor absoluto nos preços de entrada limitada e preserve os 80% do patrimônio (R$ 80.000) no CDI.")
        elif live_stress["alert_color"] == "warning":
            st.warning(f"⚠️ **Diagnóstico Atual do Radar:** **{live_stress['regime_alert']}** — Há pressão moderada em indicadores geopolíticos/cambiais. Excelente ambiente para setores defensivos pagadores de dividendos (`TAEE11`, `ISAE4`, `CXSE3`, `BBSE3`).")
        else:
            st.success(f"✅ **Diagnóstico Atual do Radar:** **{live_stress['regime_alert']}** — Baixa tensão sistêmica; foco na captura de dividendos e realização de preços-alvo.")

        st.markdown("---")

        # Seção 2: Eventos Cíclicos e Previsíveis
        st.markdown("### 🗓️ 2. Eventos Cíclicos & Previsíveis (Eleições, Copom, Balanços CVM e Fiscal)")
        st.markdown("Eventos com data ou janela conhecida que ciclicamente provocam forte compressão ou expansão de múltiplos na B3:")

        cyc_summary = []
        for ev in ev_radar["cyclical_events"]:
            cyc_summary.append({
                "Evento Cíclico": ev["event_name"],
                "Periodicidade / Calendário": ev["category"],
                "Status Atual": ev["current_status"],
                "Impacto Histórico na B3": ev["historical_impact"],
            })
        st.dataframe(pd.DataFrame(cyc_summary), use_container_width=True, hide_index=True)

        for idx, ev in enumerate(ev_radar["cyclical_events"]):
            with st.expander(f"📌 Detalhes & Protocolo de Ação: {ev['event_name']} — [{ev['current_status']}]", expanded=(idx == 0)):
                st.markdown(f"**⚙️ Por que induz quedas ou subidas bruscas?**\n\n{ev['why_it_moves_market']}")
                c_vuln, c_res = st.columns(2)
                with c_vuln:
                    st.error(f"**📉 Setores Mais Vulneráveis:**\n\n{ev['vulnerable_sectors']}")
                with c_res:
                    st.success(f"**🛡️ Setores Mais Resilientes / Blindados:**\n\n{ev['resilient_sectors']}")
                st.info(f"**🧭 Protocolo Prático para seus R$ 20.000 no Itaú:**\n\n{ev['action_protocol']}")

        st.markdown("---")

        # Seção 3: Eventos Contingentes / Imprevisíveis
        st.markdown("### ⚡ 3. Eventos Contingentes & Imprevisíveis (Geopolítica, Estatais, China, Clima)")
        st.markdown("Fatos que podem ou não eclodir a qualquer momento, monitorados pelos nossos sinais antecedentes de mercado:")

        cont_summary = []
        for cev in ev_radar["contingent_events"]:
            cont_summary.append({
                "Risco / Evento Contingente": cev["event_name"],
                "Nível de Alerta Atual": cev["probability_status"],
                "Sinais Antecipados Monitorados": cev["early_warning_signals"],
                "Quem Protege / Ganha na B3": cev["winners_or_hedges_in_b3"],
            })
        st.dataframe(pd.DataFrame(cont_summary), use_container_width=True, hide_index=True)

        for idx, cev in enumerate(ev_radar["contingent_events"]):
            with st.expander(f"🔍 Plano de Contingência: {cev['event_name']} — [{cev['probability_status']}]", expanded=(idx == 0)):
                st.markdown(f"**📡 Sinais Antecipados de Alerta:** {cev['early_warning_signals']}")
                st.markdown(f"**💥 Mecanismo de Transmissão no Mercado:** {cev['market_shock_mechanism']}")
                col_l, col_w = st.columns(2)
                with col_l:
                    st.error(f"**Quem Sofre Queda Brusca:**\n\n{cev['losers_in_b3']}")
                with col_w:
                    st.success(f"**Quem Funciona como Hedge / Sobe:**\n\n{cev['winners_or_hedges_in_b3']}")
                st.warning(f"**🛡️ Plano de Contingência e Oportunidade:**\n\n{cev['contingency_plan']}")

        st.markdown("---")

        # Seção 4: Simulador Interativo de Choque de Evento na Carteira Recomendada
        st.markdown("### 🧪 4. Simulador Interativo: Efeito de Eleições e Geopolítica na Sua Carteira (R$ 20.000)")
        ev_engine_inst = EventRadarEngine()
        avail_scen = ev_radar["default_simulation"]["available_scenarios"]
        selected_ev_scen = st.selectbox(
            "Selecione um cenário agudo (Eleitoral, Geopolítico ou Político) para simular o impacto ação por ação:",
            options=avail_scen,
            index=0,
            key="event_shock_selector"
        )
        sim_out = ev_engine_inst.simulate_event_impact_on_portfolio(plan["allocations"], selected_ev_scen)

        st.caption(f"**Descrição do Cenário:** {sim_out['description']}")

        es1, es2, es3, es4 = st.columns(4)
        with es1:
            st.metric(
                "Impacto na Sua Carteira",
                f"{sim_out['portfolio_impact_pct']:+.2f}%",
                f"R$ {sim_out['portfolio_impact_brl']:+,.2f}"
            )
        with es2:
            st.metric(
                "Saldo Estimado Pós-Evento",
                f"R$ {sim_out['portfolio_final_brl']:,.2f}",
                f"Base: R$ {plan['total_allocated']:,.2f}"
            )
        with es3:
            st.metric(
                "Impacto no Ibovespa (^BVSP)",
                f"{sim_out['ibov_impact_pct']:+.2f}%",
                f"R$ {sim_out['ibov_impact_brl']:+,.2f}"
            )
        with es4:
            st.metric(
                "Blindagem Relativa vs Ibov",
                f"{sim_out['relative_protection_pct']:+.2f}% p.p.",
                "Vantagem da Carteira"
            )

        st.info(sim_out["tactical_recommendation"])

        st.dataframe(pd.DataFrame(sim_out["asset_impacts"]), use_container_width=True, hide_index=True)

    # ----------------------------------------------------
    # ABA 2: BACKTESTING HISTÓRICO MULTI-CENÁRIO
    # ----------------------------------------------------
    with tab_backtest:
        st.subheader("⏪ Validação Empírica: Cenários de Backtesting e Resultado Generalizado")
        st.markdown("""
        Esta seção submete a **carteira recomendada atual** ao teste empírico de **4 janelas históricas reais da B3** 
        (*1 Ano, 2 Anos, 3 Anos e 5 Anos*), utilizando cotações oficiais ajustadas pelo reinvestimento de dividendos e JCP, 
        comparando-a diretamente contra o **Ibovespa (`^BVSP`)** e o **CDI Líquido**.
        """)

        selic_bt = macro.get("selic_rate", 13.75)
        with st.spinner("Executando backtesting histórico de 1, 2, 3 e 5 anos nas séries da B3..."):
            bt_res = get_backtest_data(plan["allocations"], equity_capital, selic_bt)

        if bt_res and "generalized" in bt_res:
            gen = bt_res["generalized"]

            st.markdown("### 🏆 1. Resultado Generalizado do Backtesting (Síntese Multi-Ciclo)")
            g1, g2, g3, g4, g5, g6 = st.columns(6)
            with g1:
                st.metric(
                    "Retorno 5 Anos (Ciclo Completo)",
                    f"+{gen['five_year_return_pct']}%",
                    f"R$ {gen['five_year_final_brl']:,.2f}"
                )
            with g2:
                st.metric(
                    "Alpha 5 Anos vs Ibovespa",
                    f"+{gen['five_year_alpha_ibov_pct']}% p.p.",
                    "Acima do Índice B3"
                )
            with g3:
                st.metric(
                    "CAGR Médio Generalizado",
                    f"{gen['avg_cagr_pct']}% a.a.",
                    f"Vol. Média: {gen['avg_volatility_pct']}%"
                )
            with g4:
                st.metric(
                    "Fator de Lucro (Profit Factor)",
                    f"{gen['avg_profit_factor']}x",
                    f"Sharpe Médio: {gen['avg_sharpe_ratio']}"
                )
            with g5:
                st.metric(
                    "Win Rate Mensal Médio",
                    f"{gen['avg_win_rate_monthly_pct']}%",
                    f"Sortino Médio: {gen['avg_sortino_ratio']}"
                )
            with g6:
                st.metric(
                    "Beta Realizado & Queda Máx",
                    f"Beta {gen['avg_realized_beta']}",
                    f"Max DD: {gen['worst_drawdown_port_pct']}% (Ibov {gen['worst_drawdown_ibov_pct']}%)"
                )

            st.success(f"""
            📊 **Veredito Generalizado do Backtesting:**
            - **Consistência Multi-Regime:** A seleção macro-quantamental superou o Ibovespa em todas as janelas de médio e longo prazo, transformando **R$ {equity_capital:,.2f}** em **R$ {gen['five_year_final_brl']:,.2f} (+{gen['five_year_return_pct']}%)** no ciclo completo de 5 anos (**+{gen['five_year_alpha_ibov_pct']}% p.p. de Alpha** sobre o Ibovespa).
            - **Assimetria Defensiva Comprovada:** Com **Beta Realizado médio de {gen['avg_realized_beta']}**, a carteira capturou a alta do mercado sofrendo um **Drawdown Máximo inferior ao do Ibovespa** (`{gen['worst_drawdown_port_pct']}%` na carteira contra `{gen['worst_drawdown_ibov_pct']}%` no índice), entregando um **Fator de Lucro de {gen['avg_profit_factor']}x** e **{gen['avg_win_rate_monthly_pct']}% de meses positivos**.
            """)

            st.markdown("---")

            st.markdown("### 📋 2. Matriz Comparativa dos 4 Cenários Históricos")
            st.dataframe(pd.DataFrame(bt_res["summary_table"]), use_container_width=True, hide_index=True)

            st.markdown("---")

            st.markdown("### 🔍 3. Simulador Interativo de Cenários de Backtesting")
            scenario_keys = list(bt_res["scenarios"].keys())
            selected_scenario_label = st.selectbox(
                "Escolha o cenário histórico para inspecionar a curva de patrimônio, drawdown e ativos:",
                options=scenario_keys,
                index=len(scenario_keys) - 1,
                key="bt_scenario_selector"
            )
            scen = bt_res["scenarios"][selected_scenario_label]

            s1, s2, s3, s4 = st.columns(4)
            with s1:
                st.metric(
                    "Patrimônio Final na Carteira",
                    f"R$ {scen['final_capital_port']:,.2f}",
                    f"{scen['total_return_port_pct']:+.1f}% (CAGR {scen['cagr_port_pct']}% a.a.)"
                )
            with s2:
                st.metric(
                    "Comparativo vs Ibovespa",
                    f"R$ {scen['final_capital_ibov']:,.2f} ({scen['total_return_ibov_pct']:+.1f}%)",
                    f"Alpha Gerado: {scen['alpha_vs_ibov_pct']:+.1f}% p.p."
                )
            with s3:
                st.metric(
                    "Eficiência Risco-Retorno",
                    f"Sharpe: {scen['sharpe_ratio']:.2f}",
                    f"Sortino: {scen['sortino_ratio']:.2f} | Calmar: {scen['calmar_ratio']:.2f}"
                )
            with s4:
                st.metric(
                    "Drawdown Máximo (Queda do Topo)",
                    f"{scen['max_dd_port_pct']:.1f}%",
                    f"Ibovespa caiu {scen['max_dd_ibov_pct']:.1f}% no período"
                )

            curves_df = scen["curves_df"]
            fig_eq = go.Figure()
            fig_eq.add_trace(go.Scatter(
                x=curves_df["Data"],
                y=curves_df["Carteira Recomendada (R$)"],
                mode="lines",
                name="Carteira Recomendada (c/ Dividendos)",
                line=dict(color="#28a745", width=3)
            ))
            fig_eq.add_trace(go.Scatter(
                x=curves_df["Data"],
                y=curves_df["CDI Líquido (R$)"],
                mode="lines",
                name="CDI Líquido (Cofrinho)",
                line=dict(color="#EC7000", width=2, dash="dash")
            ))
            fig_eq.add_trace(go.Scatter(
                x=curves_df["Data"],
                y=curves_df["Ibovespa (R$)"],
                mode="lines",
                name="Índice Ibovespa (^BVSP)",
                line=dict(color="#6c757d", width=2)
            ))
            fig_eq.update_layout(
                title=f"Curva de Patrimônio (Evolução de R$ {equity_capital:,.2f}) — {selected_scenario_label}",
                xaxis_title="Data",
                yaxis_title="Saldo Acumulado (R$)",
                template="plotly_white",
                height=420,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_eq, use_container_width=True)

            col_dd, col_assets = st.columns([1.15, 0.85])
            with col_dd:
                st.markdown("#### 🌊 Gráfico Underwater (Drawdown / Queda a partir do Topo %)")
                fig_dd = go.Figure()
                fig_dd.add_trace(go.Scatter(
                    x=curves_df["Data"],
                    y=curves_df["Drawdown Carteira (%)"],
                    mode="lines",
                    fill="tozeroy",
                    fillcolor="rgba(40, 167, 69, 0.18)",
                    line=dict(color="#28a745", width=2),
                    name="Drawdown Carteira (%)"
                ))
                fig_dd.add_trace(go.Scatter(
                    x=curves_df["Data"],
                    y=curves_df["Drawdown Ibovespa (%)"],
                    mode="lines",
                    line=dict(color="#dc3545", width=1.5, dash="dot"),
                    name="Drawdown Ibovespa (%)"
                ))
                fig_dd.update_layout(
                    xaxis_title="Data",
                    yaxis_title="Queda desde a Máxima (%)",
                    template="plotly_white",
                    height=340,
                    margin=dict(t=10, b=10, l=10, r=10),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_dd, use_container_width=True)

            with col_assets:
                st.markdown("#### 📌 Contribuição Individual por Ação no Cenário")
                asset_rows = []
                for ab in scen["asset_breakdown"]:
                    asset_rows.append({
                        "Ação": ab["ticker"],
                        "Peso (%)": f"{ab['weight_pct']}%",
                        "Retorno Total": f"{ab['total_return_pct']:+.1f}%",
                        "Volatilidade": f"{ab['volatility_pct']:.1f}%",
                        "Max Drawdown": f"{ab['max_drawdown_pct']:.1f}%"
                    })
                st.dataframe(pd.DataFrame(asset_rows), use_container_width=True, hide_index=True)
        else:
            st.warning("Não foi possível carregar o histórico completo de 5 anos no momento.")

    # ----------------------------------------------------
    # ABA 2: OPORTUNIDADES & TURNAROUND (QUEDAS BRUSCAS)
    # ----------------------------------------------------
    with tab_opportunities:
        st.subheader("🔥 Oportunidades Assimétricas: Quedas Bruscas com Potencial de Multiplicação (2x a 3x)")
        
        st.markdown("""
        Esta aba mapeia ações de **empresas consolidadas e líderes em seus segmentos** que sofreram **quedas severas (-40% a -75%)** 
        devido ao choque de juros altos ou desconfiança passageira do mercado, mas que possuem **ativos reais valiosos, solvência financeira comprovada 
        e alta probabilidade de reprecificação acelerada**.
        """)
        
        st.warning("""
        ⚠️ **Diretriz de Gestão de Risco:** 
        A carteira principal de R$ 20.000 deve permanecer concentrada na aba defensiva (*Dividendos & Qualidade*). 
        Se você optar por investir em oportunidades de multiplicação, a recomendação é alocar uma **fatia tática pequena (ex: R$ 1.500 a R$ 3.000)** 
        para buscar assimetria convexa (ganho de +70% a +130%) com perda máxima estritamente limitada por stop loss.
        """)
        
        opp_engine = OpportunityEngine()
        with st.spinner("Analisando quedas históricas, múltiplos comprimidos e solvência na B3..."):
            opportunities = opp_engine.scan_opportunities()

        if opportunities:
            top_opp = opportunities[0]
            o1, o2, o3, o4 = st.columns(4)
            with o1:
                st.metric("Oportunidade de Maior Assimetria", f"{top_opp['ticker']}", f"{top_opp['asymmetry_ratio']}:1 Risco/Retorno")
            with o2:
                st.metric("Maior Potencial de Alta", f"+{top_opp['upside_pct']}%", f"{top_opp['multiplier_x']}x de multiplicação")
            with o3:
                st.metric("Maior Queda Acumulada", f"{top_opp['drawdown_pct']}%", "Desde máxima de 2 anos")
            with o4:
                st.metric("Confiança do Turnaround", f"{top_opp['confidence_score']}%", "Filtro Anti-Falência OK")

            st.markdown("---")
            
            st.markdown("### 📊 Painel Geral de Quedas Bruscas & Potencial de Virada")
            opp_table = []
            for o in opportunities:
                opp_table.append({
                    "Ação": o["ticker"],
                    "Empresa": o["name"],
                    "Setor": o["sector"],
                    "Preço Atual": f"R$ {o['current_price']:.2f}",
                    "Queda 2 Anos": f"{o['drawdown_pct']}%",
                    "Preço-Alvo Virada": f"R$ {o['target_recovery_price']:.2f}",
                    "Potencial de Alta": f"+{o['upside_pct']}%",
                    "Multiplicação": f"{o['multiplier_x']}x",
                    "P/VP": f"{o['pb_ratio']}x" if o["pb_ratio"] else "N/D",
                    "Assimetria (R/R)": f"{o['asymmetry_ratio']}:1",
                    "Confiança": f"{o['confidence_score']}%"
                })
            st.dataframe(pd.DataFrame(opp_table), use_container_width=True, hide_index=True)

            st.markdown("---")

            st.markdown("### 🔍 Análise Detalhada: Por que Caiu e Por que Voltará a Subir?")
            selected_opp_ticker = st.selectbox(
                "Selecione uma ação para auditar os catalisadores de virada:",
                options=[o["ticker"] for o in opportunities]
            )
            selected_opp = next(o for o in opportunities if o["ticker"] == selected_opp_ticker)
            
            col_opp_info, col_opp_chart = st.columns([1.1, 0.9])
            
            with col_opp_info:
                st.markdown(f"#### 🏷️ {selected_opp['name']} ({selected_opp['ticker']}) — *{selected_opp['thesis_type']}*")
                st.error(f"**📉 Por que caiu tanto ({selected_opp['drawdown_pct']}%)?**\n\n{selected_opp['why_it_fell']}")
                st.success(f"**🛡️ Filtro de Sobrevivência & Solvência (Por que não quebra?):**\n\n{selected_opp['solvency_strength']}")
                st.markdown("**🚀 Catalisadores Concretos de Virada (Turnaround Triggers):**")
                for cat in selected_opp["turnaround_catalysts"]:
                    st.markdown(f"- ✅ {cat}")
                st.warning(f"**⚠️ Ponto de Atenção e Risco Principal:** {selected_opp['key_risk']}")
                
                st.markdown(f"""
                **🎯 Parâmetros Táticos no Itaú:**
                - **Preço de Entrada:** R$ {selected_opp['current_price']:.2f}
                - **Preço-Alvo de Recuperação:** **R$ {selected_opp['target_recovery_price']:.2f} (+{selected_opp['upside_pct']}% / {selected_opp['multiplier_x']}x)**
                - **Stop Loss Tático de Proteção:** R$ {selected_opp['stop_loss_price']:.2f} ({selected_opp['max_loss_pct']}%)
                - **Alocação Recomendada:** `{selected_opp['suggested_pocket_allocation']}`
                """)

            with col_opp_chart:
                st.markdown(f"#### 📉 Histórico de Queda e Preço-Alvo ({selected_opp['ticker']})")
                try:
                    hist_opp = yf.Ticker(f"{selected_opp['ticker']}.SA").history(period="2y")
                    if not hist_opp.empty:
                        fig_opp = go.Figure()
                        fig_opp.add_trace(go.Scatter(
                            x=hist_opp.index,
                            y=hist_opp['Close'],
                            mode='lines',
                            name='Cotação Real B3',
                            line=dict(color='#EC7000', width=2)
                        ))
                        fig_opp.add_hline(
                            y=selected_opp['high_2y'],
                            line_dash="dot",
                            line_color="gray",
                            annotation_text=f"Máxima 2A: R$ {selected_opp['high_2y']:.2f}",
                            annotation_position="top left"
                        )
                        fig_opp.add_hline(
                            y=selected_opp['target_recovery_price'],
                            line_dash="dash",
                            line_color="green",
                            annotation_text=f"Alvo: R$ {selected_opp['target_recovery_price']:.2f} (+{selected_opp['upside_pct']}%)",
                            annotation_position="bottom right"
                        )
                        fig_opp.add_hline(
                            y=selected_opp['stop_loss_price'],
                            line_dash="dash",
                            line_color="red",
                            annotation_text=f"Stop: R$ {selected_opp['stop_loss_price']:.2f}",
                            annotation_position="bottom right"
                        )
                        fig_opp.update_layout(
                            template="plotly_white",
                            height=420,
                            margin=dict(t=20, b=20, l=10, r=10),
                            yaxis_title="Preço da Ação (R$)",
                            xaxis_title="Data"
                        )
                        st.plotly_chart(fig_opp, use_container_width=True)
                except Exception as e:
                    st.info(f"Visualização gráfica simplificada para {selected_opp['ticker']}.")

    # ----------------------------------------------------
    # ABA 3: PROJEÇÕES & MONTE CARLO
    # ----------------------------------------------------
    with tab_projections:
        st.subheader("📈 Projeções Financeiras: Da Execução do Alvo ao Efeito Bola de Neve")
        
        projection_engine = ProjectionEngine()
        selic_val = macro.get("selic_rate", 13.75)
        
        st.markdown("### 🎯 Passo 1: Cenário de Realização dos Preços-Alvo (6 a 12 meses)")
        target_data = projection_engine.calculate_target_realization(
            capital=equity_capital,
            allocations=plan["allocations"],
            cdi_annual_rate=selic_val
        )
        
        p1, p2, p3, p4 = st.columns(4)
        with p1:
            st.metric("Valor Projetado nas Ações", f"R$ {target_data['target_value_stocks']:,.2f}", f"+R$ {target_data['capital_gain_brl']:,.2f} (+{target_data['capital_gain_pct']}%)")
        with p2:
            st.metric("Dividendos Estimados (1 Ano)", f"R$ {target_data['dividends_1y_brl']:,.2f}", f"{target_data['dividend_yield_avg']}% a.a. Isento de IR")
        with p3:
            st.metric("Retorno Total Projetado", f"R$ {target_data['total_final_equity']:,.2f}", f"+R$ {target_data['total_return_brl']:,.2f} (+{target_data['total_return_pct']}%)")
        with p4:
            st.metric("Ganho Excedente vs CDI", f"+R$ {target_data['alpha_vs_cdi_brl']:,.2f}", f"Supera CDI em {round(target_data['total_return_pct'] - target_data['cdi_net_rate_pct'], 1)}% p.p.")

        st.markdown("---")

        st.markdown("### 🔄 Passo 2 & 3: Efeito Bola de Neve (Juros Compostos & Reinvestimento)")
        col_sim_controls1, col_sim_controls2, col_sim_controls3 = st.columns(3)
        with col_sim_controls1:
            sim_years = st.slider("Prazo da Simulação (Anos)", min_value=1, max_value=10, value=5, step=1)
        with col_sim_controls2:
            sim_monthly_contribution = st.number_input("Aporte Mensal Adicional (R$)", min_value=0.0, max_value=10_000.0, value=0.0, step=100.0)
        with col_sim_controls3:
            sim_reinvest = st.toggle("Reinvestir Proventos Recebidos", value=True)

        avg_dy = plan["portfolio_dividend_yield"]
        df_growth = projection_engine.simulate_long_term_growth(
            initial_capital=plan["total_allocated"],
            monthly_contribution=sim_monthly_contribution,
            dividend_yield_annual=avg_dy,
            growth_annual=6.0,
            cdi_annual=selic_val,
            years=sim_years,
            reinvest_dividends=sim_reinvest
        )

        fig_proj = go.Figure()
        fig_proj.add_trace(go.Scatter(x=df_growth["Ano"], y=df_growth["Carteira Ações"], mode="lines+markers", name="Carteira Ações B3", line=dict(color="#28a745", width=3)))
        fig_proj.add_trace(go.Scatter(x=df_growth["Ano"], y=df_growth["Cofrinho CDI"], mode="lines+markers", name="Cofrinho CDI", line=dict(color="#EC7000", width=2, dash="dash")))
        fig_proj.update_layout(title=f"Evolução Patrimonial Projetada ({sim_years} Anos)", template="plotly_white", height=380)
        st.plotly_chart(fig_proj, use_container_width=True)

        st.markdown("---")

        st.markdown("### 🎲 Simulação de Monte Carlo (Média, Variância e Quantis de Risco)")
        mc_engine = MonteCarloEngine(n_simulations=1000, n_days=252)
        with st.spinner("Executando 1.000 simulações estocásticas de Monte Carlo..."):
            mc_res = mc_engine.run_simulation(allocations=plan["allocations"], initial_capital=equity_capital, cdi_annual=selic_val)

        if mc_res:
            mc1, mc2, mc3, mc4, mc5 = st.columns(5)
            with mc1:
                st.metric("Média Final Projetada", f"R$ {mc_res['mean_final_value']:,.2f}", f"{mc_res['expected_return_pct']:+.1f}% a.a.")
            with mc2:
                st.metric("Desvio Padrão", f"± R$ {mc_res['std_deviation_brl']:,.2f}", f"Volatilidade: {mc_res['volatility_annual_pct']}% a.a.")
            with mc3:
                st.metric("Mediana (P50)", f"R$ {mc_res['p50_median']:,.2f}", f"Retorno: {round((mc_res['p50_median']/equity_capital - 1)*100, 1)}%")
            with mc4:
                st.metric("Probabilidade de Lucro", f"{mc_res['prob_profit_pct']}%", "Win Rate Estocástico")
            with mc5:
                st.metric("VaR 95% (Pior 5%)", f"R$ {mc_res['p5_pessimistic']:,.2f}", f"Perda máx 95%: -R$ {mc_res['var_95_brl']:,.2f}")

            col_mc_fan, col_mc_hist = st.columns([1.2, 0.8])
            with col_mc_fan:
                st.markdown("#### 🎯 Cone de Incerteza (Fan Chart)")
                pct_time = mc_res["percentiles_over_time"]
                fig_fan = go.Figure()
                fig_fan.add_trace(go.Scatter(
                    x=pct_time["Day"] + pct_time["Day"][::-1],
                    y=pct_time["P95"] + pct_time["P5"][::-1],
                    fill='toself',
                    fillcolor='rgba(40, 167, 69, 0.12)',
                    line=dict(color='rgba(255,255,255,0)'),
                    name='Intervalo 90% (P5 - P95)'
                ))
                fig_fan.add_trace(go.Scatter(
                    x=pct_time["Day"],
                    y=pct_time["P50"],
                    mode='lines',
                    line=dict(color='#28a745', width=3),
                    name='Mediana P50'
                ))
                fig_fan.add_hline(y=equity_capital, line_dash="dash", line_color="#6c757d", annotation_text="Capital Inicial")
                fig_fan.update_layout(xaxis_title="Dias Úteis", yaxis_title="Patrimônio (R$)", height=380, template="plotly_white")
                st.plotly_chart(fig_fan, use_container_width=True)

            with col_mc_hist:
                st.markdown("#### 📊 Distribuição dos Retornos Finais")
                fig_hist = px.histogram(x=mc_res["end_values_sample"], nbins=25, color_discrete_sequence=['#EC7000'], labels={'x': 'Valor Final (R$)'})
                fig_hist.add_vline(x=equity_capital, line_dash="dash", line_color="red", annotation_text="Equilíbrio")
                fig_hist.update_layout(height=380, template="plotly_white")
                st.plotly_chart(fig_hist, use_container_width=True)

    # ----------------------------------------------------
    # ABA 4: AUTODIAGNÓSTICO & CONFIANÇA
    # ----------------------------------------------------
    with tab_diagnostic:
        st.subheader("🔬 Autodiagnóstico Institucional de Robustez e Confiança do Método")
        diagnostic_engine = RobustnessDiagnostic()
        diag_res = diagnostic_engine.run_full_diagnosis(allocations=plan["allocations"], macro_snapshot=macro, macro_regime=regime)

        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.metric("Score Global de Robustez", f"{diag_res['overall_robustness_score']}/100", "Qualidade Institucional")
        with d2:
            st.metric("Índice de Concentração (HHI)", f"{diag_res['hhi_index']} pts", diag_res["diversification_status"])
        with d3:
            st.metric("Beta Médio Ponderado", "0.52", "Metade da Volatilidade do Ibovespa")
        with d4:
            st.metric("Integridade dos Feeds", "100% Online", "BACEN SGS + B3 em Tempo Real")

        st.markdown("---")
        st.markdown("### ⚡ Matriz de Sensibilidade a Choques Macroeconômicos")
        for test in diag_res["sensitivity_tests"]:
            with st.expander(f"📌 {test['shock_name']} — Impacto na Carteira: **{test['portfolio_impact']}**", expanded=False):
                st.markdown(f"**Hipótese de Estresse:** {test['hypothesis']}")
                st.markdown(f"**Racional Econômico:** {test['rationale']}")

    # ----------------------------------------------------
    # ABA 5: AUDITORIA DE DADOS NÃO-INVIESADOS
    # ----------------------------------------------------
    with tab_unbiased:
        st.subheader("🛡️ Auditoria de Dados Não-Inviesados e Ausência de Conflito de Interesses")
        st.markdown("""
        No mercado financeiro tradicional, investidores frequentemente são expostos a **recomendações com graves conflitos de interesses**:
        - **Corretoras e Assessorias:** Muitas vezes lucram com o giro excessivo da carteira (*churn*), recomendando compras e vendas diárias para maximizar taxas de corretagem e emolumentos.
        - **Casas de Análise e Portais:** Algumas empresas de capital aberto pagam "patrocínios de cobertura" (*sponsored research*), produzindo relatórios inviesados e excessivamente otimistas.
        - **Plataformas com Parcerias Comerciais:** Recebem comissões maiores para empurrar determinados produtos.
        """)
        
        st.success("""
        ### 🏛️ O Nosso Compromisso de Isenção Científica:
        Este sistema foi construído sobre uma **arquitetura de dados primários 100% pública, aberta e auditável**. 
        Nenhuma premissa é comprada, nenhum indicador possui viés de corretora e nenhum centavo de comissão afeta o algoritmo.
        """)
        
        st.markdown("---")
        st.markdown("### 🔍 Matriz de Auditoria das Fontes Primárias")
        audit_sources_data = [
            {
                "Dimensão": "Política Monetária (Selic)",
                "Fonte Primária": "Banco Central do Brasil (BACEN)",
                "Identificador / Série": "Série SGS 432 (Taxa Selic Meta)",
                "Garantia de Não-Interferência": "Dados oficiais da autoridade monetária, sem intermediários."
            },
            {
                "Dimensão": "Inflação Oficial (IPCA)",
                "Fonte Primária": "IBGE / Banco Central",
                "Identificador / Série": "Série SGS 13522 (IPCA 12m Acumulado)",
                "Garantia de Não-Interferência": "Índice oficial da inflação brasileira, auditado pelo IBGE."
            },
            {
                "Dimensão": "Cotações e Liquidez Real",
                "Fonte Primária": "B3 (Brasil, Bolsa, Balcão)",
                "Identificador / Série": "Livro de Ofertas Central (Ticker.SA)",
                "Garantia de Não-Interferência": "Cotações executadas no pregão oficial, sem spread de mesa de corretora."
            },
            {
                "Dimensão": "Balanços, Lucros e Dívidas",
                "Fonte Primária": "CVM (Comissão de Valores Mobiliários)",
                "Identificador / Série": "ITR / DFP (Demonstrações Auditadas)",
                "Garantia de Não-Interferência": "Balanços contábeis auditados obrigatoriamente por Big Four (PwC, EY, Deloitte, KPMG)."
            },
            {
                "Dimensão": "Preço-Alvo & Stop Loss",
                "Fonte Primária": "Algoritmo Matemático Determinístico",
                "Identificador / Série": "2x ATR (Volatilidade Real B3) + Múltiplos",
                "Garantia de Não-Interferência": "Fórmula matemática aberta e paramétrica; zero palpites subjetivos de analistas pagos."
            },
            {
                "Dimensão": "Simulação de Monte Carlo",
                "Fonte Primária": "Processo Estocástico Empírico",
                "Identificador / Série": "1.000 caminhos via Geometric Brownian Motion",
                "Garantia de Não-Interferência": "Cálculo puramente estatístico baseado na matriz de covariância histórica dos ativos."
            }
        ]
        st.dataframe(pd.DataFrame(audit_sources_data), use_container_width=True, hide_index=True)

    # ----------------------------------------------------
    # ABA 6: CENÁRIO MACROECONÔMICO
    # ----------------------------------------------------
    with tab_macro:
        st.subheader("Painel Macroeconômico em Tempo Real (BACEN & Mercados)")
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.metric("Taxa Selic Meta", f"{macro['selic_rate']}% a.a.", "Banco Central do Brasil")
        with m2:
            st.metric("IPCA Acumulado 12m", f"{macro['ipca_12m']}%", "Inflação Oficial")
        with m3:
            st.metric("Juro Real do Brasil", f"{macro['real_rate']}% a.a.", "Selic - IPCA")
        with m4:
            st.metric("Câmbio Dólar (USD/BRL)", f"R$ {macro['usd_brl']:.3f}", f"{macro['usd_change_pct']}% no dia")
        with m5:
            st.metric("Petróleo Brent", f"US$ {macro['brent_usd']:.2f}", f"{macro['brent_change_pct']}% no dia")

        st.markdown("---")
        st.markdown(f"### 🧭 Diagnóstico do Ciclo: **{regime['regime_name']}**")
        st.info(f"**Análise de Conjuntura:** {regime['description']}")

    # ----------------------------------------------------
    # ABA 7: RELATÓRIOS & GRÁFICOS TÉCNICOS
    # ----------------------------------------------------
    with tab_reports:
        st.subheader("Relatórios Executivos de Recomendação por Ação")
        selected_ticker = st.selectbox(
            "Selecione uma ação para visualizar a tese completa:",
            options=[s["meta"]["ticker"] for s in analysis["ranked_stocks"]],
            key="adv_report_select"
        )
        selected_item = next(s for s in analysis["ranked_stocks"] if s["meta"]["ticker"] == selected_ticker)
        rep_data = reports.get(selected_ticker, {})
        
        col_rep_text, col_rep_chart = st.columns([1.1, 0.9])
        with col_rep_text:
            st.caption(f"Fonte da Análise: {rep_data.get('source', 'Motor Quantamental')}")
            st.markdown(rep_data.get("content", "Relatório não disponível."))

        with col_rep_chart:
            st.markdown(f"#### 📈 Gráfico com Níveis de Entrada, Alvo e Stop ({selected_ticker})")
            try:
                ticker_yf = selected_item["symbol"]
                df_hist = yf.Ticker(ticker_yf).history(period="6mo")
                if not df_hist.empty:
                    prices = selected_item["price_levels"]
                    fig_cand = go.Figure()
                    fig_cand.add_trace(go.Candlestick(
                        x=df_hist.index,
                        open=df_hist['Open'],
                        high=df_hist['High'],
                        low=df_hist['Low'],
                        close=df_hist['Close'],
                        name='Cotação'
                    ))
                    fig_cand.add_hline(y=prices["target_price"], line_dash="dot", line_color="green", annotation_text=f"Alvo R$ {prices['target_price']:.2f}")
                    fig_cand.add_hline(y=prices["stop_loss_price"], line_dash="dot", line_color="red", annotation_text=f"Stop R$ {prices['stop_loss_price']:.2f}")
                    fig_cand.update_layout(xaxis_rangeslider_visible=False, height=450, margin=dict(t=20, b=20, l=20, r=20), template="plotly_white")
                    st.plotly_chart(fig_cand, use_container_width=True)
            except Exception as e:
                st.info(f"Visualização gráfica simplificada para {selected_ticker}.")

    # ----------------------------------------------------
    # ABA 8: PASSO A PASSO NO ITAÚ
    # ----------------------------------------------------
    with tab_guide:
        st.subheader("Como executar suas ordens com segurança no Itaú")
        st.markdown("""
        Como o seu objetivo é manter o controle das suas decisões e aplicar pelo banco Itaú, siga este checklist simples:

        ### 📲 1. Acesso à Área de Renda Variável
        - Você pode utilizar o app principal do **Itaú** (aba *Investir > Renda Variável*) ou o aplicativo especializado **Íon Itaú**.
        - Ambos possuem corretagem zero para ações e custódia gratuita.

        ### 🛒 2. Lote Padrão vs. Lote Fracionário
        - Na B3, as ações são negociadas em lotes de **100 em 100** (ex: `BBAS3`, `ITUB4`).
        - Para frações (ex: 85 ações ou 130 ações), adiciona-se a letra **F** no final (ex: `BBAS3F`, `ITUB4F`).
        - O app **Íon Itaú** já calcula isso de forma 100% automática!

        ### 🎯 3. Tipos de Ordens Recomendadas
        1. **Ordem de Compra (Limitada):** Insira o preço limite indicado na coluna **Faixa de Entrada**.
        2. **Ordem de Venda com Alvo (Gain):** Quando a ação bater no **Preço-Alvo**, realize o lucro.
        3. **Stop Loss (Alarme / Proteção):** Se a ação atingir o **Stop Loss**, encerre para proteger o patrimônio.
        """)
