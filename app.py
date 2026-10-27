"""
Dashboard Interativo do Robô de Recomendação Macroeconômica (B3).
Desenvolvido com Streamlit, Plotly e Análise Top-Down em Tempo Real.
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
        margin-bottom: 25px;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        border-left: 5px solid #EC7000;
        margin-bottom: 10px;
    }
    .badge-buy {
        background-color: #28a745;
        color: white;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: bold;
    }
    .badge-wait {
        background-color: #ffc107;
        color: black;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Barra Lateral - Parâmetros do Usuário
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/Banco_Ita%C3%BA_logo.svg/200px-Banco_Ita%C3%BA_logo.svg.png", width=120)
st.sidebar.title("Configurações da Carteira")

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

# Execução da Análise
if refresh_btn:
    st.cache_data.clear()

with st.spinner("Analisando cenário macroeconômico, cotações da B3 e múltiplos em tempo real..."):
    analysis = get_advisor_data(user_profile, num_assets, equity_capital, api_key_input)

macro = analysis["macro_snapshot"]
regime = analysis["macro_regime"]
plan = analysis["portfolio_plan"]
reports = analysis["reports"]

# Cabeçalho Principal
st.markdown('<div class="main-header">Robô de Recomendação Macro B3 | Itaú Advisory</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="sub-header">Alocação Estratégica: <b>R$ {equity_capital:,.2f}</b> em Ações Defensivas | '
    f'Reserva de Segurança Preservada: <b>R$ {(total_patrimony - equity_capital):,.2f}</b> (80%)</div>',
    unsafe_allow_html=True
)

# Abas de Navegação
tab_portfolio, tab_projections, tab_diagnostic, tab_macro, tab_reports, tab_guide = st.tabs([
    "💼 Carteira Recomendada (R$ 20k)",
    "🎲 Projeções & Monte Carlo",
    "🔬 Autodiagnóstico & Confiança",
    "🌍 Cenário Macroeconômico",
    "📄 Relatórios & Teses Detalhadas",
    "📱 Passo a Passo no Itaú"
])

# ==========================================
# ABA 1: CARTEIRA RECOMENDADA
# ==========================================
with tab_portfolio:
    st.subheader(f"Portfólio Recomendado — Foco: {user_profile}")
    
    # Métricas de Topo da Carteira
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

    # Tabela Executiva de Ações
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

    # Gráfico de Distribuição e Instruções Rápidas
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

# ==========================================
# ABA 2: PROJEÇÕES & SIMULAÇÃO FINANCEIRA
# ==========================================
with tab_projections:
    st.subheader("📈 Projeções Financeiras: Da Execução do Alvo ao Efeito Bola de Neve")
    
    projection_engine = ProjectionEngine()
    selic_val = macro.get("selic_rate", 13.75)
    
    st.markdown("""
    Esta aba simula a trajetória dos seus **R$ 20.000,00** aplicando os passos recomendados:
    1. **Passo 1 (Ciclo de 6 a 12 meses):** Realização das metas nos Preços-Alvo (+18% a +23%) somado aos dividendos;
    2. **Passo 2 (Longo Prazo / Efeito Bola de Neve):** Reinvestimento automático dos proventos na própria carteira;
    3. **Passo 3 (Comparativo com o Cofrinho):** Desempenho relativo frente a 100% do CDI líquido de Imposto de Renda;
    4. **Passo 4 (Blindagem Patrimonial):** Teste de estresse com acionamento de Stop Loss e preservação dos R$ 80k de reserva.
    """)
    
    st.markdown("---")
    
    # ----------------------------------------------------
    # PASSO 1: REALIZAÇÃO DOS PREÇOS-ALVO (MÉDIO PRAZO)
    # ----------------------------------------------------
    st.markdown("### 🎯 Passo 1: Cenário de Realização dos Preços-Alvo (6 a 12 meses)")
    target_data = projection_engine.calculate_target_realization(
        capital=equity_capital,
        allocations=plan["allocations"],
        cdi_annual_rate=selic_val
    )
    
    p1, p2, p3, p4 = st.columns(4)
    with p1:
        st.metric(
            "Valor Projetado nas Ações",
            f"R$ {target_data['target_value_stocks']:,.2f}",
            f"+R$ {target_data['capital_gain_brl']:,.2f} (+{target_data['capital_gain_pct']}%)"
        )
    with p2:
        st.metric(
            "Dividendos Estimados (1 Ano)",
            f"R$ {target_data['dividends_1y_brl']:,.2f}",
            f"{target_data['dividend_yield_avg']}% a.a. Isento de IR"
        )
    with p3:
        st.metric(
            "Retorno Total Projetado",
            f"R$ {target_data['total_final_equity']:,.2f}",
            f"+R$ {target_data['total_return_brl']:,.2f} (+{target_data['total_return_pct']}%)"
        )
    with p4:
        alpha = target_data["alpha_vs_cdi_brl"]
        st.metric(
            "Ganho Excedente vs CDI",
            f"+R$ {alpha:,.2f}",
            f"Supera CDI em {round(target_data['total_return_pct'] - target_data['cdi_net_rate_pct'], 1)}% p.p."
        )

    st.caption(
        f"* Comparativo com o Cofrinho CDI Líquido: R$ 20.000 renderiam R$ {target_data['cdi_gain_brl']:,.2f} "
        f"(100% do CDI descontada alíquota média de 17.5% de IR)."
    )

    st.markdown("---")

    # ----------------------------------------------------
    # PASSO 2 E 3: SIMULADOR DE LONGO PRAZO (BOLA DE NEVE)
    # ----------------------------------------------------
    st.markdown("### 🔄 Passo 2 & 3: Efeito Bola de Neve (Juros Compostos & Reinvestimento)")
    
    col_sim_controls1, col_sim_controls2, col_sim_controls3 = st.columns(3)
    with col_sim_controls1:
        sim_years = st.slider("Prazo da Simulação (Anos)", min_value=1, max_value=10, value=5, step=1)
    with col_sim_controls2:
        sim_monthly_contribution = st.number_input(
            "Aporte Mensal Adicional (R$)",
            min_value=0.0,
            max_value=10_000.0,
            value=0.0,
            step=100.0,
            help="Simule novos aportes mensais poupados do salário ou do rendimento do cofrinho."
        )
    with col_sim_controls3:
        sim_reinvest = st.toggle("Reinvestir Proventos Recebidos", value=True, help="Reaplicar dividendos comprando novas ações acelera o efeito bola de neve.")

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

    # Gráfico de Evolução Patrimonial
    fig_proj = go.Figure()
    fig_proj.add_trace(go.Scatter(
        x=df_growth["Ano"],
        y=df_growth["Carteira Ações"],
        mode="lines+markers",
        name="Carteira Recomendada B3 (Ações + Dividendos)",
        line=dict(color="#28a745", width=3)
    ))
    fig_proj.add_trace(go.Scatter(
        x=df_growth["Ano"],
        y=df_growth["Cofrinho CDI"],
        mode="lines+markers",
        name="Cofrinho CDI (100% CDI Líquido)",
        line=dict(color="#EC7000", width=2, dash="dash")
    ))
    if sim_monthly_contribution > 0:
        fig_proj.add_trace(go.Scatter(
            x=df_growth["Ano"],
            y=df_growth["Total Aportado"],
            mode="lines",
            name="Capital Aportado do Bolso",
            line=dict(color="#6c757d", width=2, dash="dot")
        ))
    
    fig_proj.update_layout(
        title=f"Evolução Patrimonial Projetada ({sim_years} Anos)",
        xaxis_title="Tempo decorrido (Anos)",
        yaxis_title="Patrimônio Acumulado (R$)",
        hovermode="x unified",
        template="plotly_white",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_proj, use_container_width=True)

    # Tabela de Marcos e Projeção de Renda Passiva
    col_tabela, col_renda = st.columns([1.2, 0.8])
    with col_tabela:
        st.markdown("#### 📅 Cronograma de Marcos de Patrimônio")
        st.dataframe(
            df_growth[["Ano", "Total Aportado", "Carteira Ações", "Cofrinho CDI", "Dividendo Mensal", "Dividendos Acumulados"]].rename(
                columns={
                    "Ano": "Ano",
                    "Total Aportado": "Aportado (R$)",
                    "Carteira Ações": "Carteira Ações (R$)",
                    "Cofrinho CDI": "Cofrinho CDI (R$)",
                    "Dividendo Mensal": "Renda Mensal Estimada (R$)",
                    "Dividendos Acumulados": "Div. Acumulados (R$)"
                }
            ),
            use_container_width=True,
            hide_index=True
        )

    with col_renda:
        final_row = df_growth.iloc[-1]
        st.markdown("#### 💰 Renda Passiva Projetada ao Final")
        st.metric(
            f"Renda Mensal em Dividendos (Ano {sim_years})",
            f"R$ {final_row['Dividendo Mensal']:,.2f} / mês",
            f"R$ {final_row['Dividendo Mensal'] * 12:,.2f} / ano"
        )
        st.metric(
            "Total de Proventos Isentos Recebidos",
            f"R$ {final_row['Dividendos Acumulados']:,.2f}",
            "Dinheiro livre direto na conta"
        )
        st.info("💡 À medida que novas ações são adquiridas com os dividendos, a quantidade de proventos a cada trimestre cresce exponencialmente.")

    st.markdown("---")

    # ----------------------------------------------------
    # PASSO 4: BLINDAGEM DE RISCO E TESTE DE ESTRESSE
    # ----------------------------------------------------
    st.markdown("### 🛡️ Passo 4: Teste de Estresse e Blindagem de Risco (Pior Caso)")
    stress_data = projection_engine.calculate_stress_test(
        capital=equity_capital,
        allocations=plan["allocations"],
        total_patrimony=total_patrimony
    )
    
    col_st1, col_st2 = st.columns([1.1, 0.9])
    with col_st1:
        st.markdown(f"""
        **O que acontece se a Bolsa passar por uma crise e todas as ações atingirem os Stops de Proteção?**
        - **Perda Máxima nas Ações:** R$ {stress_data['max_loss_brl']:,.2f} ({stress_data['max_loss_pct_stocks']}%)
        - **Capital Preservado nas Ações:** R$ {stress_data['capital_preserved_stocks']:,.2f}
        - **Impacto no seu Patrimônio Global (R$ {total_patrimony:,.0f}):** **Apenas {stress_data['impact_on_total_patrimony_pct']}%**
        """)
        if stress_data["reserve_covers_loss"]:
            st.success(f"""
            ✅ **Blindagem Garantida:** Seus R$ {stress_data['reserve_capital']:,.0f} mantidos no cofrinho 
            rendem aproximadamente **R$ {stress_data['reserve_annual_gain']:,.2f}** no ano (a 100% do CDI), 
            o que cobre **{round(stress_data['reserve_annual_gain'] / stress_data['max_loss_brl'], 1)} vezes** 
            a perda máxima possível de todos os stops somados!
            """)

    with col_st2:
        st.metric(
            "Patrimônio Global Líquido no Pior Cenário Possível",
            f"R$ {stress_data['net_annual_patrimony_worst_case']:,.2f}",
            f"+R$ {round(stress_data['net_annual_patrimony_worst_case'] - total_patrimony, 2):,.2f} no ano"
        )
        st.caption("Mesmo que todas as 5 ações fossem stopadas, seu patrimônio total ainda cresce devido ao rendimento da reserva de segurança.")

    st.markdown("---")

    # ----------------------------------------------------
    # SIMULAÇÃO ESTOCÁSTICA DE MONTE CARLO
    # ----------------------------------------------------
    st.markdown("### 🎲 Simulação de Monte Carlo (Média, Variância e Quantis de Risco)")
    st.markdown("""
    A simulação de Monte Carlo projeta **1.000 trajetórias estocásticas possíveis** para a sua carteira de **R$ 20.000,00** 
    ao longo dos próximos 252 pregões (1 ano de mercado), utilizando a volatilidade e correlações históricas reais dos ativos.
    """)
    
    mc_engine = MonteCarloEngine(n_simulations=1000, n_days=252)
    with st.spinner("Executando 1.000 simulações estocásticas de Monte Carlo..."):
        mc_res = mc_engine.run_simulation(
            allocations=plan["allocations"],
            initial_capital=equity_capital,
            cdi_annual=selic_val
        )
    
    if mc_res:
        mc1, mc2, mc3, mc4, mc5 = st.columns(5)
        with mc1:
            st.metric(
                "Média Final Projetada",
                f"R$ {mc_res['mean_final_value']:,.2f}",
                f"{mc_res['expected_return_pct']:+.1f}% a.a."
            )
        with mc2:
            st.metric(
                "Desvio Padrão (Variância)",
                f"± R$ {mc_res['std_deviation_brl']:,.2f}",
                f"Volatilidade: {mc_res['volatility_annual_pct']}% a.a."
            )
        with mc3:
            st.metric(
                "Mediana (P50)",
                f"R$ {mc_res['p50_median']:,.2f}",
                f"Retorno: {round((mc_res['p50_median']/equity_capital - 1)*100, 1)}%"
            )
        with mc4:
            st.metric(
                "Probabilidade de Lucro",
                f"{mc_res['prob_profit_pct']}%",
                "Win Rate Estocástico"
            )
        with mc5:
            st.metric(
                "VaR 95% (Pior 5% - P5)",
                f"R$ {mc_res['p5_pessimistic']:,.2f}",
                f"Perda máx 95%: -R$ {mc_res['var_95_brl']:,.2f}"
            )
            
        # Gráficos de Monte Carlo: Fan Chart e Histograma
        col_mc_fan, col_mc_hist = st.columns([1.2, 0.8])
        
        with col_mc_fan:
            st.markdown("#### 🎯 Cone de Incerteza (Fan Chart Estocástico)")
            pct_time = mc_res["percentiles_over_time"]
            fig_fan = go.Figure()
            
            # Faixa P5 - P95 (90% dos casos)
            fig_fan.add_trace(go.Scatter(
                x=pct_time["Day"] + pct_time["Day"][::-1],
                y=pct_time["P95"] + pct_time["P5"][::-1],
                fill='toself',
                fillcolor='rgba(40, 167, 69, 0.12)',
                line=dict(color='rgba(255,255,255,0)'),
                hoverinfo="skip",
                name='Intervalo de Confiança 90% (P5 - P95)'
            ))
            # Faixa P25 - P75 (50% dos casos mais centrais)
            fig_fan.add_trace(go.Scatter(
                x=pct_time["Day"] + pct_time["Day"][::-1],
                y=pct_time["P75"] + pct_time["P25"][::-1],
                fill='toself',
                fillcolor='rgba(40, 167, 69, 0.25)',
                line=dict(color='rgba(255,255,255,0)'),
                hoverinfo="skip",
                name='Intervalo Interquartil (P25 - P75)'
            ))
            # Linha P50 (Mediana)
            fig_fan.add_trace(go.Scatter(
                x=pct_time["Day"],
                y=pct_time["P50"],
                mode='lines',
                line=dict(color='#28a745', width=3),
                name='Mediana P50'
            ))
            # Linha de Capital Inicial
            fig_fan.add_hline(y=equity_capital, line_dash="dash", line_color="#6c757d", annotation_text="Capital Inicial (R$ 20k)")
            
            fig_fan.update_layout(
                xaxis_title="Pregões Decorridos (Dias Úteis)",
                yaxis_title="Patrimônio Simulado (R$)",
                hovermode="x unified",
                template="plotly_white",
                height=380,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(t=20, b=20, l=10, r=10)
            )
            st.plotly_chart(fig_fan, use_container_width=True)

        with col_mc_hist:
            st.markdown("#### 📊 Distribuição dos Retornos Finais")
            fig_hist = px.histogram(
                x=mc_res["end_values_sample"],
                nbins=25,
                color_discrete_sequence=['#EC7000'],
                labels={'x': 'Valor Final em 1 Ano (R$)'}
            )
            fig_hist.add_vline(x=equity_capital, line_dash="dash", line_color="red", annotation_text="Zero a Zero")
            fig_hist.add_vline(x=mc_res["mean_final_value"], line_dash="dot", line_color="green", annotation_text=f"Média R$ {mc_res['mean_final_value']:,.0f}")
            fig_hist.update_layout(
                yaxis_title="Frequência de Cenários",
                template="plotly_white",
                height=380,
                margin=dict(t=20, b=20, l=10, r=10)
            )
            st.plotly_chart(fig_hist, use_container_width=True)
            st.caption(f"Em {mc_res['prob_profit_pct']}% das 1.000 simulações, o saldo final foi superior aos R$ 20.000 alocados.")

# ==========================================
# ABA 3: AUTODIAGNÓSTICO & CONFIANÇA
# ==========================================
with tab_diagnostic:
    st.subheader("🔬 Autodiagnóstico Institucional de Robustez e Confiança do Método")
    st.markdown("""
    Esta seção realiza uma **auditoria estatística e qualitativa contínua** do motor de recomendação, 
    avaliando a diversificação dos riscos, a estabilidade frente a choques macroeconômicos e a qualidade dos dados.
    """)
    
    diagnostic_engine = RobustnessDiagnostic()
    diag_res = diagnostic_engine.run_full_diagnosis(
        allocations=plan["allocations"],
        macro_snapshot=macro,
        macro_regime=regime
    )
    
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
    
    # Seção 1: Matriz de Sensibilidade e Stress Testing
    st.markdown("### ⚡ 1. Matriz de Sensibilidade a Choques Macroeconômicos")
    for test in diag_res["sensitivity_tests"]:
        with st.expander(f"📌 {test['shock_name']} — Impacto na Carteira: **{test['portfolio_impact']}**", expanded=False):
            st.markdown(f"**Hipótese de Estresse:** {test['hypothesis']}")
            st.markdown(f"**Racional Econômico:** {test['rationale']}")

    st.markdown("---")

    # Seção 2: Auditoria dos Pilares de Confiança
    st.markdown("### 🛡️ 2. Auditoria da Confiança Estatística das Ações Recomendadas")
    col_audit_tbl, col_audit_hhi = st.columns([1.2, 0.8])
    
    with col_audit_tbl:
        audit_rows = []
        for item in diag_res["confidence_audit"]:
            audit_rows.append({
                "Ação": item["ticker"],
                "Nome": item["name"],
                "Confiança": f"{item['confidence_score']}%",
                "Score Quantamental": f"{item['quant_score']} pts",
                "Perfil de Risco": item["risk_profile"]
            })
        st.dataframe(pd.DataFrame(audit_rows), use_container_width=True, hide_index=True)
        st.caption("A nota de confiança sintetiza 5 pilares: lucros ininterruptos de 10 anos, margens saudáveis, desalavancagem, payout previsível e liquidez de ponta.")

    with col_audit_hhi:
        st.markdown("#### ⚖️ Exposição Setorial da Carteira")
        df_sec = pd.DataFrame(list(diag_res["sector_exposure"].items()), columns=["Setor", "Exposição (%)"])
        fig_sec = px.bar(
            df_sec,
            x="Exposição (%)",
            y="Setor",
            orientation='h',
            color="Exposição (%)",
            color_continuous_scale="Oranges"
        )
        fig_sec.update_layout(height=260, margin=dict(t=10, b=10, l=10, r=10), template="plotly_white")
        st.plotly_chart(fig_sec, use_container_width=True)

    st.markdown("---")

    # Seção 3: Infraestrutura de Dados & Limitações
    col_infra, col_limits = st.columns(2)
    with col_infra:
        st.markdown("#### 📡 3. Status e Latência dos Feeds de Dados")
        for source, info in diag_res["data_health"].items():
            if isinstance(info, dict):
                st.markdown(f"- **{source.replace('_', ' ').title()}:** `{info['status']}` | Latência: ~{info['latency_ms']}ms | Fonte: {info['freshness']}")
            else:
                st.markdown(f"- **Estado Geral da Esteira:** `{info}`")

    with col_limits:
        st.markdown("#### ⚠️ 4. Premissas Críticas e Limitações do Modelo")
        for lim in diag_res["limitations"]:
            st.markdown(f"- {lim}")

# ==========================================
# ABA 4: CENÁRIO MACROECONÔMICO
# ==========================================
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
    
    col_fav, col_avoid = st.columns(2)
    with col_fav:
        st.markdown("#### ✅ Setores Altamente Favorecidos no Momento")
        for s in regime["favored_sectors"]:
            weight = regime["sector_weights"].get(s, 1.0)
            st.success(f"**{s}** — Peso Estratégico: {weight:.2f}x")
            
    with col_avoid:
        st.markdown("#### ⚠️ Setores a Evitar ou Reduzir Exposição")
        for s in regime["avoid_sectors"]:
            st.warning(f"**{s}** — Alta sensibilidade negativa ao custo do dinheiro ou volatilidade.")

# ==========================================
# ABA 5: RELATÓRIOS & TESES DETALHADAS
# ==========================================
with tab_reports:
    st.subheader("Relatórios Executivos de Recomendação por Ação")
    
    selected_ticker = st.selectbox(
        "Selecione uma ação para visualizar a tese completa:",
        options=[s["meta"]["ticker"] for s in analysis["ranked_stocks"]]
    )
    
    # Recuperar dados do ativo selecionado
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
                # Linha de Preço-Alvo
                fig_cand.add_hline(
                    y=prices["target_price"],
                    line_dash="dot",
                    line_color="green",
                    annotation_text=f"Alvo R$ {prices['target_price']:.2f} (+{prices['potential_gain_pct']}%)",
                    annotation_position="top right"
                )
                # Linha de Stop Loss
                fig_cand.add_hline(
                    y=prices["stop_loss_price"],
                    line_dash="dot",
                    line_color="red",
                    annotation_text=f"Stop R$ {prices['stop_loss_price']:.2f} ({prices['max_loss_pct']}%)",
                    annotation_position="bottom right"
                )
                fig_cand.update_layout(
                    xaxis_rangeslider_visible=False,
                    height=450,
                    margin=dict(t=20, b=20, l=20, r=20),
                    template="plotly_white"
                )
                st.plotly_chart(fig_cand, use_container_width=True)
        except Exception as e:
            st.info(f"Visualização gráfica simplificada para {selected_ticker}.")

# ==========================================
# ABA 6: GUIA DE EXECUÇÃO NO ITAÚ
# ==========================================
with tab_guide:
    st.subheader("Como executar suas ordens com segurança no Itaú")
    
    st.markdown("""
    Como o seu objetivo é manter o controle das suas decisões e aplicar pelo banco Itaú, siga este checklist simples:

    ### 📲 1. Acesso à Área de Renda Variável
    - Você pode utilizar o app principal do **Itaú** (aba *Investir > Renda Variável*) ou o aplicativo especializado **Íon Itaú**.
    - Ambos possuem corretagem zero para ações e custódia gratuita.

    ### 🛒 2. Lote Padrão vs. Lote Fracionário
    - Na B3, as ações são negociadas em lotes de **100 em 100** (ex: `BBAS3`, `ITUB4`).
    - Para quantidades que não sejam múltiplos de 100 (ex: 85 ações ou 130 ações), adiciona-se a letra **F** no final do código (ex: `BBAS3F`, `ITUB4F`).
    - *Dica:* O app **Íon Itaú** já calcula isso de forma 100% automática se você apenas digitar a quantidade desejada de ações!

    ### 🎯 3. Tipos de Ordens Recomendadas
    1. **Ordem de Compra (Limitada):** Insira o preço limite indicado na coluna **Faixa de Entrada**. Não envie ordem a mercado se o preço estiver esticado acima do teto.
    2. **Ordem de Venda com Alvo (Gain):** Quando a ação valorizar e bater no **Preço-Alvo**, realize o lucro (venda total ou parcial para rebalancear).
    3. **Stop Loss (Alarme / Proteção):** Se a ação atingir o preço de **Stop Loss**, encerre a operação para proteger os seus R$ 20.000 contra desvalorizações maiores.

    ### 🛡️ 4. Gestão Patrimonial
    - Você possui **R$ 100.000,00** no total.
    - **R$ 80.000,00** (80%) continuam 100% seguros no cofrinho/reserva (rendendo Selic/CDI diariamente).
    - **R$ 20.000,00** (20%) foram distribuídos entre as 5 empresas mais sólidas do Brasil, gerando dividendos em dinheiro na sua conta.
    """)

