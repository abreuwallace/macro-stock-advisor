"""
Motor de Monetização, Controle de Acesso (Freemium / Pro / Fundador),
Vitrine de Afiliados Éticos e Simulador de Receita SaaS (MRR, ARR, LTV, CAC).
"""
from typing import Dict, Any, List


class SaaSMonetizationEngine:
    """
    Gerencia a camada comercial do produto:
    - Regras de Paywall Freemium vs. Assinante Pro vs. Modo Fundador
    - Validação de chaves de acesso Pro
    - Slots de anúncios nativos éticos / afiliados educacionais
    - Projeção financeira de receita recorrente (MRR/ARR) e funil de conversão
    """

    VALID_PRO_CODES = {
        "PRO-VIP-2026",
        "ALPHAMACRO-PRO",
        "FUNDADOR-MASTER",
        "ITAU-VIP",
    }

    PLANS_CATALOG = {
        "free": {
            "name": "Plano Gratuito (Iniciante)",
            "price_monthly": 0.0,
            "price_annual": 0.0,
            "badge": "🔓 Visitante Gratuito",
            "features": [
                "Acesso ao Guia 'Começar a Investir do Zero' e Calculadora de Reserva",
                "Painel Macroeconômico BACEN em tempo real",
                "Visualização das 3 primeiras ações da Carteira Recomendada",
                "Simulador de Carteira limitado a até 3 ações",
                "Exibição de vitrine educacional e parceiros",
            ],
        },
        "pro": {
            "name": "Assinante AlphaMacro PRO",
            "price_monthly": 29.90,
            "price_annual": 249.00,
            "badge": "💎 Assinante PRO",
            "features": [
                "Carteira Recomendada Completa (5 a 6 ações) com Faixa de Entrada, Alvo e Stop",
                "Painel Simulação ILIMITADO ('Como Atuar Agora' na sua carteira anterior + salvamento em nuvem)",
                "Painel Avançado Completo: Monte Carlo (1.000 cenários) + Backtesting 5 Anos",
                "Radar de Eventos Cíclicos (Eleições/Copom) & Tensões Geopolíticas",
                "Aba de Oportunidades Assimétricas (Turnaround 2x a 3x)",
                "Exportação de Relatórios Executivos em HTML/PDF Imprimível e Planilha CSV",
                "Zero anúncios",
            ],
        },
        "founder": {
            "name": "Modo Fundador / Admin Master",
            "price_monthly": 0.0,
            "price_annual": 0.0,
            "badge": "👑 Modo Fundador (Admin)",
            "features": [
                "100% dos recursos PRO desbloqueados para uso pessoal irrestrito",
                "Painel de Gestão de Negócio & Monetização SaaS (MRR, ARR, LTV, Leads)",
                "Gerador de Chaves VIP e Configuração de Gateways (PIX / Stripe / Kiwify / Asaas)",
                "Exportação completa da base de Leads e Clientes em CSV",
            ],
        },
    }

    def get_tier_permissions(self, tier_code: str) -> Dict[str, Any]:
        """Retorna as permissões exatas de cada nível de usuário."""
        tier = tier_code.lower().strip()
        if tier in ("founder", "pro"):
            return {
                "tier": tier,
                "is_premium": True,
                "is_founder": (tier == "founder"),
                "max_visible_recommendations": 10,
                "max_simulator_stocks": 20,
                "can_access_advanced_tabs": True,
                "can_export_reports": True,
                "can_save_cloud_portfolio": True,
                "show_ethical_ads": False,
            }
        return {
            "tier": "free",
            "is_premium": False,
            "is_founder": False,
            "max_visible_recommendations": 3,
            "max_simulator_stocks": 3,
            "can_access_advanced_tabs": False,
            "can_export_reports": False,
            "can_save_cloud_portfolio": False,
            "show_ethical_ads": True,
        }

    def validate_access_code(self, code: str) -> bool:
        """Verifica se um código promocional ou chave de assinatura é válido."""
        if not code:
            return False
        return code.strip().upper() in self.VALID_PRO_CODES

    def get_ethical_affiliate_slots(self) -> List[Dict[str, str]]:
        """
        Retorna slots de monetização ética (afiliados educacionais / livros / ferramentas).
        100% separados do motor matemático de ações para jamais comprometer a isenção.
        """
        return [
            {
                "category": "📚 Leitura Essencial (Amazon Afiliados)",
                "title": "Faça Fortuna com Ações — Décio Bazin",
                "description": "O clássico brasileiro sobre investimento em dividendos e segurança que inspirou grandes investidores da B3.",
                "cta_label": "Ver Livro na Amazon →",
                "url": "https://www.amazon.com.br/s?k=faca+fortuna+com+acoes+decio+bazin",
                "revenue_model": "Comissão de 8% a 10% por venda (Amazon Associados)",
            },
            {
                "category": "📘 Clássico Global (Amazon Afiliados)",
                "title": "O Investidor Inteligente — Benjamin Graham",
                "description": "A bíblia do Value Investing e da Margem de Segurança (mentor de Warren Buffett).",
                "cta_label": "Ver Livro na Amazon →",
                "url": "https://www.amazon.com.br/s?k=o+investidor+inteligente+benjamin+graham",
                "revenue_model": "Comissão de 8% a 10% por venda (Amazon Associados)",
            },
            {
                "category": "🏦 Comparativo de Corretoras Taxa Zero",
                "title": "Invista com Corretagem R$ 0,00 para Ações",
                "description": "Compare os aplicativos Itaú Íon, Toro, Rico, Clear, Inter e Nubank para não pagar taxa por ordem emitida.",
                "cta_label": "Comparar Corretoras no Guia →",
                "url": "#guia-corretoras",
                "revenue_model": "Parceria CPA / Indicação (R$ 30 a R$ 120 por conta aberta)",
            },
        ]

    def calculate_saas_unit_economics(
        self,
        monthly_visitors: int = 5000,
        lead_conversion_pct: float = 8.0,
        pro_conversion_pct: float = 3.0,
        monthly_price_brl: float = 29.90,
        annual_plan_share_pct: float = 35.0,
        annual_price_brl: float = 249.00,
        affiliate_arpu_brl: float = 0.45,
        infra_cost_brl: float = 65.00,
        gateway_fee_pct: float = 2.49,
    ) -> Dict[str, Any]:
        """
        Calcula a viabilidade econômica, MRR, ARR, Receita de Afiliados/Ads e Lucro Líquido
        para o Painel de Gestão do Fundador.
        """
        new_leads_month = int(round(monthly_visitors * (lead_conversion_pct / 100.0)))
        paying_subscribers = int(round(monthly_visitors * (pro_conversion_pct / 100.0)))

        annual_subs = int(round(paying_subscribers * (annual_plan_share_pct / 100.0)))
        monthly_subs = paying_subscribers - annual_subs

        mrr_from_monthly = monthly_subs * monthly_price_brl
        mrr_from_annual = annual_subs * (annual_price_brl / 12.0)
        subscription_mrr = round(mrr_from_monthly + mrr_from_annual, 2)

        # Receita complementar de Afiliados / Ads éticos sobre visitantes gratuitos
        free_visitors = max(0, monthly_visitors - paying_subscribers)
        affiliate_ad_revenue_month = round(free_visitors * affiliate_arpu_brl, 2)

        gross_monthly_revenue = round(subscription_mrr + affiliate_ad_revenue_month, 2)
        gateway_fees = round(subscription_mrr * (gateway_fee_pct / 100.0), 2)
        net_monthly_profit = round(gross_monthly_revenue - gateway_fees - infra_cost_brl, 2)
        arr_projected = round(gross_monthly_revenue * 12.0, 2)
        net_annual_profit = round(net_monthly_profit * 12.0, 2)

        # Projeção de crescimento acumulado em 12 meses (assumindo retenção mensal de 92% / churn de 8%)
        retention_rate = 0.92
        projection_12m = []
        active_subs = 0
        for m in range(1, 13):
            active_subs = int(round(active_subs * retention_rate + paying_subscribers * 0.35))
            if m == 1:
                active_subs = paying_subscribers
            m_sub_rev = round(active_subs * ((monthly_price_brl * 0.65) + ((annual_price_brl / 12.0) * 0.35)), 2)
            m_aff_rev = affiliate_ad_revenue_month
            m_total = round(m_sub_rev + m_aff_rev, 2)
            m_net = round(m_total * (1.0 - gateway_fee_pct / 100.0) - infra_cost_brl, 2)
            projection_12m.append({
                "Mês": f"Mês {m}",
                "Assinantes Ativos": active_subs,
                "Receita Assinaturas (R$)": m_sub_rev,
                "Receita Afiliados/Ads (R$)": m_aff_rev,
                "Faturamento Total (R$)": m_total,
                "Lucro Líquido (R$)": m_net,
            })

        avg_ticket = round(subscription_mrr / max(1, paying_subscribers), 2)
        ltv_estimated = round(avg_ticket * 12.5, 2)  # ~12.5 meses de retenção média

        return {
            "monthly_visitors": monthly_visitors,
            "new_leads_month": new_leads_month,
            "paying_subscribers": paying_subscribers,
            "subscription_mrr": subscription_mrr,
            "affiliate_ad_revenue_month": affiliate_ad_revenue_month,
            "gross_monthly_revenue": gross_monthly_revenue,
            "gateway_fees_brl": gateway_fees,
            "infra_cost_brl": infra_cost_brl,
            "net_monthly_profit": net_monthly_profit,
            "arr_projected": arr_projected,
            "net_annual_profit": net_annual_profit,
            "avg_ticket_brl": avg_ticket,
            "ltv_brl": ltv_estimated,
            "projection_12m": projection_12m,
        }

