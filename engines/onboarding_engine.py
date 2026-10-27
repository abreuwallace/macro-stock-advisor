"""
Motor Educacional, Calculadora de Reserva de Emergência, Suitability e
Adaptador Universal Multi-Corretora (Itaú, XP, BTG, Nubank, Inter, Clear/Rico, Ágora).
Desenhado para acolher usuários de todas as origens (do completo iniciante ao avançado).
"""
from typing import Dict, Any, List


class OnboardingEngine:
    """
    Auxilia pessoas que estão começando a investir ou validando seu planejamento financeiro
    a definir sua Reserva de Emergência, seu Perfil de Risco (Suitability) e a operar em qualquer corretora.
    """

    BROKER_GUIDES: Dict[str, Dict[str, Any]] = {
        "Itaú / Íon Itaú": {
            "broker_name": "Itaú / Íon Itaú",
            "brokerage_fee": "R$ 0,00 (Corretagem Zero para Ações e FIIs)",
            "app_menu_path": "App Íon Itaú > Aba 'Investir' > 'Renda Variável' > 'Ações' (ou App Itaú > Investimentos)",
            "fractional_rule": "Automático no Íon (ou adicione a letra 'F' no final do código no Home Broker, ex: BBAS3F).",
            "step_by_step": [
                "Abra o aplicativo **Íon Itaú** ou o app principal do **Itaú**.",
                "Toque em **Investir > Renda Variável > Buscar Ativo** e digite o código da ação (ex: `TAEE11` ou `BBAS3`).",
                "Escolha **Comprar**, informe a quantidade exata calculada pelo sistema e selecione **Ordem Limitada**.",
                "Digite o valor limite da **Faixa de Entrada Ideal** e confirme com sua senha/biometria.",
                "Ative os alertas de preço para o **Preço-Alvo (Gain)** e **Stop Loss (Proteção)**.",
            ],
            "pro_tip": "O Itaú permite integrar os proventos diretamente na conta corrente ou no Cofrinho 100% CDI para reinvestimento automático.",
        },
        "XP Investimentos": {
            "broker_name": "XP Investimentos",
            "brokerage_fee": "R$ 4,90 por ordem no autoatendimento (ou variável conforme assessoria)",
            "app_menu_path": "App XP > Aba 'Bolsa' > 'Buscar Ativo' > 'Negociar'",
            "fractional_rule": "Para quantidades menores que 100 ações, digite o ticker com 'F' no final (ex: `TAEE11F`, `CXSE3F`).",
            "step_by_step": [
                "Abra o aplicativo **XP Investimentos** e acesse a aba **Bolsa** no menu inferior.",
                "Toque na lupa de busca e digite o ticker da ação (adicione **F** no final se não for múltiplo de 100).",
                "Clique em **Comprar** e mude o tipo de ordem de 'A Mercado' para **Limitada**.",
                "Preencha o preço da **Faixa de Entrada Ideal** e a validade da ordem (`Até Cancelar / VAC`).",
                "Na aba de ordens, você também pode deixar agendada uma ordem **Stop Gain / Stop Loss**.",
            ],
            "pro_tip": "Como a XP cobra corretagem por ordem no plano padrão, evite picotar compras pequenas no mesmo mês; agrupe o aporte mensal em 1 ou 2 ativos da carteira.",
        },
        "BTG Pactual": {
            "broker_name": "BTG Pactual Digital",
            "brokerage_fee": "Variável / Regressiva (Zero em planos promocionais ou fidelidade)",
            "app_menu_path": "App BTG Investimentos > 'Renda Variável' > 'Home Broker / Negociação'",
            "fractional_rule": "Use o sufixo 'F' para lotes fracionários de 1 a 99 ações (ex: `BBSE3F`).",
            "step_by_step": [
                "Acesse o app **BTG Pactual Investimentos** e entre em **Renda Variável**.",
                "Busque pelo código da ação recomendada e selecione **Comprar**.",
                "Escolha a opção **Ordem Limitada**, inserindo o preço máximo indicado na coluna **Faixa de Entrada**.",
                "Configure uma ordem **Stop Simultâneo (Gain + Loss)** utilizando os níveis calculados pelo nosso motor.",
            ],
            "pro_tip": "O Home Broker do BTG possui ordem OCO (One-Cancels-the-Other) nativa: você já pode deixar o Preço-Alvo e o Stop Loss armados simultaneamente.",
        },
        "Nubank / NuInvest": {
            "broker_name": "Nubank",
            "brokerage_fee": "R$ 0,00 (Corretagem Zero)",
            "app_menu_path": "App Nubank > Aba 'Investimentos' (cifrão $) > 'Investir' > 'Bolsa de Valores'",
            "fractional_rule": "100% automático! O app Nubank compra lote padrão ou fracionário sem precisar digitar a letra 'F'.",
            "step_by_step": [
                "No app do **Nubank**, toque no ícone de **Planejamento / Investimentos ($)** na barra inferior.",
                "Vá em **Investir > Bolsa de Valores > Ações Brasileiras** e busque a empresa pelo nome ou código.",
                "Clique em **Comprar** e verifique o preço exibido na tela em comparação à nossa **Faixa de Entrada Ideal**.",
                "Informe a quantidade de ações recomendada e confirme com sua senha de 4 dígitos.",
            ],
            "pro_tip": "Ideal para quem está começando com pouco dinheiro: corretagem zero permite comprar até mesmo 1 única ação no mercado fracionário sem custo de taxa.",
        },
        "Banco Inter": {
            "broker_name": "Banco Inter (Inter Invest)",
            "brokerage_fee": "R$ 0,00 (Corretagem Zero)",
            "app_menu_path": "Super App Inter > 'Investir' > 'Renda Variável / Home Broker'",
            "fractional_rule": "No Home Broker Inter, adicione 'F' para quantidades de 1 a 99 ações (ex: `ISAE4F`).",
            "step_by_step": [
                "Abra o **Super App Inter**, toque em **Investir** e selecione **Renda Variável**.",
                "Digite o ticker da ação (com **F** no final se for menos de 100 ações).",
                "Selecione **Ordem Limitada**, informe a quantidade e o preço da **Faixa de Entrada Ideal**.",
                "Confira na carteira do Inter o calendário automático de proventos que cairão na sua conta.",
            ],
            "pro_tip": "Com corretagem zero no Inter, você pode reinvestir os dividendos recebidos imediatamente comprando ações fracionárias (`F`).",
        },
        "Clear / Rico": {
            "broker_name": "Clear / Rico Corretora",
            "brokerage_fee": "R$ 0,00 (Corretagem Zero)",
            "app_menu_path": "App Rico ou Clear > 'Renda Variável' > 'Boleta de Compra'",
            "fractional_rule": "Utilize o sufixo 'F' para lotes de 1 a 99 ações (ex: `BBAS3F`).",
            "step_by_step": [
                "Acesse o aplicativo da **Rico** ou **Clear** e adicione o ativo na sua lista de acompanhamento.",
                "Abra a boleta de **Compra**, selecione **Ordem Limitada** e preencha a quantidade e o preço de entrada.",
                "Em seguida, abra a aba **Stop** para configurar o Preço-Alvo (Gain) e o Stop Loss.",
            ],
            "pro_tip": "Excelente para ordens limitadas e stops automáticos sem custo de corretagem.",
        },
        "Bradesco / Ágora": {
            "broker_name": "Ágora Investimentos / Bradesco",
            "brokerage_fee": "R$ 0,00 para ações no plano Ágora / Bradesco",
            "app_menu_path": "App Ágora > 'Renda Variável' > 'Home Broker'",
            "fractional_rule": "Adicione 'F' ao código do ativo para quantidades inferiores a 100 ações.",
            "step_by_step": [
                "Abra o app **Ágora Investimentos** e entre no menu **Renda Variável**.",
                "Selecione o ativo recomendado, defina a quantidade e o preço limite da **Faixa de Entrada Ideal**.",
                "Monitore a liquidação financeira (D+2) diretamente na sua conta.",
            ],
            "pro_tip": "Permite débito direto integrado com a conta corrente do Bradesco em D+2.",
        },
    }

    FINANCIAL_GLOSSARY: List[Dict[str, str]] = [
        {
            "term": "🛡️ Reserva de Emergência (Cofrinho / Tesouro Selic / CDB 100% CDI)",
            "simple_explanation": (
                "É o dinheiro da sua paz de espírito (6 a 12 meses do seu custo de vida). Deve ficar em Renda Fixa "
                "com liquidez diária (pode sacar a qualquer hora sem perder valor). Você SÓ investe em ações na Bolsa "
                "o dinheiro que está acima da sua Reserva de Emergência!"
            ),
        },
        {
            "term": "📈 O que é uma Ação (ON / PN / Unit — final 3, 4 ou 11)?",
            "simple_explanation": (
                "Comprar uma ação significa se tornar sócio de uma empresa real (como Banco do Brasil, Itaú, Taesa). "
                "Código final `3` (ex: BBAS3) é ação ordinária com direito a voto; final `4` (ex: ITUB4, ISAE4) tem "
                "prioridade no recebimento de dividendos; final `11` (ex: TAEE11) é um pacote (Unit) que junta as duas."
            ),
        },
        {
            "term": "🧩 Lote Padrão (100 ações) vs. Mercado Fracionário (Letra 'F')",
            "simple_explanation": (
                "Na B3, o lote padrão negocia de 100 em 100 ações. Mas você NÃO precisa comprar 100 ações de uma vez! "
                "Basta colocar a letra **F** no final do código (ex: `TAEE11F`, `BBAS3F`) para comprar de 1 em 1 ação "
                "(com apenas R$ 20 ou R$ 40 você já consegue começar)."
            ),
        },
        {
            "term": "💰 Dividendos e Dividend Yield (DY % a.a.)",
            "simple_explanation": (
                "Dividendos são a parte do lucro que a empresa deposita em dinheiro vivo direto na sua conta da corretora, "
                "**livres de Imposto de Renda** para pessoa física! Se uma ação custa R$ 20 e paga R$ 2 por ano de dividendos, "
                "o Dividend Yield (DY) dela é de **10% ao ano**."
            ),
        },
        {
            "term": "🎯 Faixa de Entrada, Preço-Alvo (Gain) e Stop Loss (Proteção)",
            "simple_explanation": (
                "- **Faixa de Entrada:** O preço máximo até onde vale a pena comprar a ação sem pagar caro.\n"
                "- **Preço-Alvo (Gain):** O preço justo onde a ação já subiu bastante (+15% a +25%) e vale vender para embolsar o lucro.\n"
                "- **Stop Loss:** O 'seguro contra incêndio' — se algo grave acontecer e a ação cair até esse valor (máx -8%), você vende para proteger seu patrimônio."
            ),
        },
        {
            "term": "⚖️ P/L (Preço/Lucro) e ROE (Retorno sobre Patrimônio)",
            "simple_explanation": (
                "- **P/L:** Quantos anos de lucro a empresa leva para 'se pagar'. Um P/L de 5x a 8x indica uma empresa barata.\n"
                "- **ROE:** Mede a eficiência da empresa em gerar lucro com o próprio dinheiro. ROE acima de 15% a 20% indica empresa altamente lucrativa."
            ),
        },
        {
            "term": "🏛️ Isenção de Imposto de Renda até R$ 20.000/mês na B3",
            "simple_explanation": (
                "No Brasil, se a soma total das suas **vendas** de ações no mês for menor que **R$ 20.000,00** (operações comuns / Swing Trade), "
                "todo o lucro obtido na venda é **100% ISENTO de Imposto de Renda**!"
            ),
        },
    ]

    def calculate_financial_plan(
        self,
        monthly_income: float,
        monthly_expenses: float,
        total_patrimony: float,
        job_stability: str = "Moderada (CLT Privado / Profissional Liberal)",
        experience_level: str = "Iniciante (Já tenho Renda Fixa)",
    ) -> Dict[str, Any]:
        """
        Calcula quanto o usuário precisa ter de Reserva de Emergência, quanto já pode investir
        em Renda Variável (B3) hoje e qual o aporte mensal ideal.
        """
        if "Estável" in job_stability:
            months_reserve = 6
        elif "Autônomo" in job_stability or "Variável" in job_stability:
            months_reserve = 12
        else:
            months_reserve = 6

        ideal_emergency_reserve = round(monthly_expenses * months_reserve, 2)
        monthly_savings_capacity = max(0.0, round(monthly_income - monthly_expenses, 2))

        # Quanto do patrimônio atual excede a reserva de emergência
        surplus_above_reserve = max(0.0, round(total_patrimony - ideal_emergency_reserve, 2))
        reserve_coverage_pct = round(min(100.0, (total_patrimony / max(1.0, ideal_emergency_reserve)) * 100.0), 1)

        # Definir percentual prudente do excedente para ações conforme experiência
        if "Nunca" in experience_level:
            equity_share_of_surplus = 0.20
            recommended_profile = "Segura / Dividendos & Qualidade"
        elif "Iniciante" in experience_level:
            equity_share_of_surplus = 0.30
            recommended_profile = "Segura / Dividendos & Qualidade"
        else:
            equity_share_of_surplus = 0.45
            recommended_profile = "Moderada (Dividendos + Crescimento)"

        # Se a pessoa já tem patrimônio sólido (ex: R$ 100k) e custo de vida compatível, sugere alocação segura
        suggested_equity_capital = round(surplus_above_reserve * equity_share_of_surplus, 2)
        # Se ainda está formando a reserva, sugere começar com valor pedagógico simbólico (ex: R$ 200 a R$ 500) enquanto foca 90% na reserva
        if surplus_above_reserve <= 0:
            suggested_equity_capital = 0.0
            suggested_monthly_stocks = round(monthly_savings_capacity * 0.10, 2)
            readiness_status = "🟡 Fase 1: Construção da Reserva de Emergência Prioritária"
            readiness_advice = (
                f"Sua meta número 1 é acumular **R$ {ideal_emergency_reserve:,.2f}** ({months_reserve} meses do seu custo de vida) "
                f"no Cofrinho 100% CDI ou Tesouro Selic. Hoje você já cobriu **{reserve_coverage_pct}%** dessa reserva. "
                f"Destine 90% da sua poupança mensal para o CDI e, se desejar aprender na prática, use apenas "
                f"**R$ {suggested_monthly_stocks:,.2f}/mês** no mercado fracionário (`F`) em ações hiper-defensivas."
            )
        else:
            suggested_monthly_stocks = round(monthly_savings_capacity * 0.35, 2)
            readiness_status = "🟢 Fase 2: Reserva Completa — Pronto para Multiplicar na B3 com Segurança!"
            readiness_advice = (
                f"Parabéns! Sua Reserva de Emergência de **R$ {ideal_emergency_reserve:,.2f}** ({months_reserve} meses) está **100% protegida**! "
                f"Do seu patrimônio excedente (**R$ {surplus_above_reserve:,.2f}**), recomendamos alocar de forma prudente "
                f"**R$ {suggested_equity_capital:,.2f}** na Carteira Recomendada da B3 e manter o restante rendendo 100% do CDI."
            )

        safe_fixed_income_kept = round(total_patrimony - suggested_equity_capital, 2)

        return {
            "months_reserve_required": months_reserve,
            "ideal_emergency_reserve_brl": ideal_emergency_reserve,
            "reserve_coverage_pct": reserve_coverage_pct,
            "surplus_above_reserve_brl": surplus_above_reserve,
            "suggested_equity_capital_brl": suggested_equity_capital,
            "safe_fixed_income_kept_brl": safe_fixed_income_kept,
            "monthly_savings_capacity_brl": monthly_savings_capacity,
            "suggested_monthly_stocks_brl": suggested_monthly_stocks,
            "recommended_profile": recommended_profile,
            "readiness_status": readiness_status,
            "readiness_advice": readiness_advice,
        }

    def get_broker_guide(self, broker_name: str) -> Dict[str, Any]:
        """Retorna o guia específico da corretora selecionada pelo usuário."""
        return self.BROKER_GUIDES.get(broker_name, self.BROKER_GUIDES["Itaú / Íon Itaú"])

    def format_broker_order_ticket(self, item: Dict[str, Any], broker_name: str) -> str:
        """Adapta a instrução de compra para a corretora específica do usuário."""
        ticker = item["ticker"]
        shares = int(item["shares_count"])
        if "Nubank" in broker_name or "Íon" in broker_name:
            return f"No app {broker_name}: buscar '{ticker}', digitar {shares} ações (o app ajusta lote padrão/fracionário automaticamente)."
        lotes = shares // 100
        frac = shares % 100
        if lotes > 0 and frac > 0:
            return f"No Home Broker {broker_name}: {lotes} lote(s) de {ticker} ({lotes * 100} ações) + {frac} ações no fracionário ({ticker}F)."
        if lotes > 0:
            return f"No Home Broker {broker_name}: {lotes} lote(s) padrão de {ticker} ({shares} ações)."
        return f"No Home Broker {broker_name}: comprar {shares} ações no código fracionário {ticker}F."
