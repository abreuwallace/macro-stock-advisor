"""
Exportador de Relatórios Executivos (HTML/PDF Imprimível e Planilha CSV).
Gera documentos profissionais para assinantes Pro e para o Fundador,
incluindo o aviso regulatório oficial da Resolução CVM nº 20.
"""
import datetime
from typing import Dict, Any, List
import pandas as pd


class ReportExporter:
    """Exporta carteiras recomendadas e carteiras simuladas em formatos CSV e HTML/PDF."""

    @staticmethod
    def export_allocations_to_csv(allocations: List[Dict[str, Any]]) -> str:
        """Converte lista de alocações ou posições simuladas para string CSV UTF-8."""
        if not allocations:
            return ""
        df = pd.DataFrame(allocations)
        cols_exclude = {"reasons", "score_breakdown"}
        keep_cols = [c for c in df.columns if c not in cols_exclude]
        return df[keep_cols].to_csv(index=False, encoding="utf-8-sig")

    @staticmethod
    def generate_printable_html_report(
        title: str,
        broker_name: str,
        macro_snapshot: Dict[str, Any],
        macro_regime: Dict[str, Any],
        rows: List[Dict[str, Any]],
        is_simulation: bool = False
    ) -> str:
        """
        Gera um Relatório Executivo HTML estilizado (pronto para 'Imprimir / Salvar como PDF' no navegador)
        com cabeçalho institucional, resumo macroeconômico, tabela de posições e disclaimer CVM.
        """
        now_str = datetime.datetime.now().strftime("%d/%m/%Y às %H:%M")
        selic = macro_snapshot.get("selic_rate", 13.75)
        ipca = macro_snapshot.get("ipca_12m", 4.5)
        real_rate = macro_snapshot.get("real_rate", 9.25)
        usd = macro_snapshot.get("usd_brl", 5.40)
        regime_name = macro_regime.get("regime_name", "Juros Reais Elevados")

        table_headers = ""
        table_body = ""
        if is_simulation:
            table_headers = """
                <th>Ação</th>
                <th>Empresa</th>
                <th>Qtd</th>
                <th>Preço Médio</th>
                <th>Preço Atual</th>
                <th>Saldo Atual</th>
                <th>Lucro/Prej (%)</th>
                <th>Yield on Cost</th>
                <th>Score Macro</th>
                <th>Novo Alvo</th>
                <th>Stop Proteção</th>
                <th>Recomendação de Atuação</th>
            """
            for r in rows:
                table_body += f"""
                <tr>
                    <td><b>{r.get('ticker', '')}</b></td>
                    <td>{r.get('name', '')}</td>
                    <td>{r.get('shares_count', 0)}</td>
                    <td>R$ {r.get('avg_price', 0):.2f}</td>
                    <td>R$ {r.get('current_price', 0):.2f}</td>
                    <td>R$ {r.get('current_value', 0):,.2f}</td>
                    <td><b>{r.get('pnl_pct', 0):+.2f}%</b></td>
                    <td>{r.get('yield_on_cost_pct', 0):.2f}%</td>
                    <td>{r.get('score', 0):.1f}/100</td>
                    <td>R$ {r.get('target_price', 0):.2f}</td>
                    <td>R$ {r.get('stop_loss_price', 0):.2f}</td>
                    <td><b>{r.get('action_badge', '')}</b><br><small>{r.get('summary_command', '')}</small></td>
                </tr>
                """
        else:
            table_headers = """
                <th>Ação</th>
                <th>Empresa</th>
                <th>Setor</th>
                <th>Preço Atual</th>
                <th>Qtd Ações</th>
                <th>Valor Alocado</th>
                <th>Faixa de Entrada</th>
                <th>Preço-Alvo (Gain)</th>
                <th>Stop Loss</th>
                <th>Div. Yield</th>
                <th>Confiança</th>
            """
            for r in rows:
                table_body += f"""
                <tr>
                    <td><b>{r.get('ticker', '')}</b></td>
                    <td>{r.get('name', '')}</td>
                    <td>{r.get('sector', '')}</td>
                    <td>R$ {r.get('current_price', 0):.2f}</td>
                    <td>{r.get('shares_count', 0)}</td>
                    <td>R$ {r.get('invested_amount', 0):,.2f}</td>
                    <td>{r.get('entry_action', '')}</td>
                    <td>R$ {r.get('target_price', 0):.2f} (+{r.get('potential_gain_pct', 0)}%)</td>
                    <td>R$ {r.get('stop_loss_price', 0):.2f} ({r.get('max_loss_pct', 0)}%)</td>
                    <td>{r.get('dividend_yield', 0)}%</td>
                    <td>{r.get('confidence_pct', 0)}%</td>
                </tr>
                """

        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>{title} — AlphaMacro B3</title>
    <style>
        body {{ font-family: 'Segoe UI', Roboto, Arial, sans-serif; color: #1e293b; margin: 32px; line-height: 1.5; }}
        .header {{ border-bottom: 4px solid #EC7000; padding-bottom: 16px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; }}
        .brand {{ font-size: 24px; font-weight: 800; color: #0f172a; }}
        .brand span {{ color: #EC7000; }}
        .meta {{ font-size: 13px; color: #64748b; text-align: right; }}
        .macro-box {{ background: #f8fafc; border: 1px solid #e2e8f0; border-left: 5px solid #0284c7; padding: 14px 18px; border-radius: 8px; margin-bottom: 24px; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 28px; font-size: 13px; }}
        th {{ background: #0f172a; color: #ffffff; text-align: left; padding: 10px; }}
        td {{ border-bottom: 1px solid #e2e8f0; padding: 10px; vertical-align: top; }}
        tr:nth-child(even) {{ background: #f8fafc; }}
        .footer {{ margin-top: 36px; padding-top: 16px; border-top: 1px solid #cbd5e1; font-size: 11px; color: #64748b; text-align: justify; }}
        @media print {{
            body {{ margin: 12px; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <div class="brand">Alpha<span>Macro</span> B3 | Inteligência Quantamental Independente</div>
            <div>Relatório Executivo: <b>{title}</b> | Corretora Selecionada: <b>{broker_name}</b></div>
        </div>
        <div class="meta">
            Gerado em: {now_str}<br>
            Dados Oficiais: BACEN SGS, CVM & B3
        </div>
    </div>

    <div class="macro-box">
        <b>Panorama Macroeconômico Oficial (BACEN):</b>
        Taxa Selic Meta: <b>{selic}% a.a.</b> | IPCA 12m: <b>{ipca}%</b> | Juro Real: <b>{real_rate}% a.a.</b> |
        Câmbio USD/BRL: <b>R$ {usd:.2f}</b> | Regime Identificado: <b>{regime_name}</b>
    </div>

    <table>
        <thead>
            <tr>{table_headers}</tr>
        </thead>
        <tbody>
            {table_body}
        </tbody>
    </table>

    <div class="footer">
        <b>AVISO LEGAL E CONFORMIDADE REGULATÓRIA (RESOLUÇÃO CVM Nº 20):</b>
        Este documento foi gerado automaticamente por algoritmos matemáticos e estatísticos da plataforma AlphaMacro B3,
        utilizando exclusivamente dados públicos oficiais do Banco Central do Brasil (BACEN), da Comissão de Valores Mobiliários (CVM)
        e da B3 S.A. As informações aqui apresentadas têm caráter estritamente educacional, informativo e quantitativo,
        não constituindo consultoria individualizada de valores mobiliários, promessa de rentabilidade futura ou oferta de compra/venda.
        Rentabilidade passada não representa garantia de rentabilidade futura. O investidor é integralmente responsável pela execução de suas ordens em sua corretora.
    </div>
</body>
</html>"""
