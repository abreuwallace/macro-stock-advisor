"""
Coletor de Expectativas de Mercado do Relatório Focus (Banco Central do Brasil - BACEN).
Conecta-se diretamente à API pública e aberta do BACEN Olinda para capturar
a mediana das projeções de mercado para Selic, IPCA e PIB dos próximos anos.
Permite antecipar ciclos de corte ou aperto monetário antes que ocorram na prática.
"""
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class FocusCollector:
    """Coleta as expectativas do Relatório Focus via API pública do BACEN."""

    OLINDA_URL = (
        "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/ExpectativasMercadoAnuais"
        "?$top=40&$orderby=Data%20desc&$filter=Indicador%20eq%20%27Selic%27%20or%20Indicador%20eq%20%27IPCA%27%20or%20Indicador%20eq%20%27PIB%20Total%27&$format=json"
    )

    def __init__(self, timeout: int = 5):
        self.timeout = timeout

    def get_focus_expectations(self) -> Dict[str, Any]:
        """
        Retorna a mediana das projeções do Focus para os próximos 3 anos
        e calcula o impulso de ciclo monetário.
        """
        # Valores conservadores de fallback
        expectations = {
            "selic_2026": 13.25,
            "selic_2027": 11.75,
            "selic_2028": 10.00,
            "ipca_2026": 5.19,
            "ipca_2027": 4.34,
            "ipca_2028": 3.75,
            "pib_2026": 1.80,
            "pib_2027": 1.35,
            "pib_2028": 1.80,
            "reference_date": "Outubro/2026",
            "is_live_data": False,
        }

        try:
            resp = requests.get(self.OLINDA_URL, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json().get("value", [])
                found_keys = set()
                for item in data:
                    indicador = item.get("Indicador")
                    data_ref = str(item.get("DataReferencia"))
                    mediana = item.get("Mediana")
                    data_coleta = item.get("Data", "")

                    if mediana is not None:
                        if indicador == "Selic":
                            key = f"selic_{data_ref}"
                            if key not in found_keys and key in expectations:
                                expectations[key] = float(mediana)
                                found_keys.add(key)
                        elif indicador == "IPCA":
                            key = f"ipca_{data_ref}"
                            if key not in found_keys and key in expectations:
                                expectations[key] = float(mediana)
                                found_keys.add(key)
                        elif indicador == "PIB Total":
                            key = f"pib_{data_ref}"
                            if key not in found_keys and key in expectations:
                                expectations[key] = float(mediana)
                                found_keys.add(key)

                    if data_coleta and not expectations.get("is_live_data"):
                        expectations["reference_date"] = data_coleta
                        expectations["is_live_data"] = True

        except Exception as e:
            logger.warning(f"Falha na coleta do Relatório Focus (usando projeções padrão): {e}")

        # Cálculo do ciclo monetário projetado
        selic_26 = expectations["selic_2026"]
        selic_27 = expectations["selic_2027"]
        selic_delta_26_27 = round(selic_27 - selic_26, 2)

        if selic_delta_26_27 <= -1.0:
            monetary_impulse = "Ciclo de Afrouxamento / Queda de Juros Projetado (Forte Vento a Favor para Ações)"
            impulse_color = "success"
        elif selic_delta_26_27 >= 1.0:
            monetary_impulse = "Ciclo de Aperto / Alta de Juros (Defesa em Utilities e Seguros Prioritária)"
            impulse_color = "warning"
        else:
            monetary_impulse = "Ciclo Estável / Manutenção de Juros Altos no Horizonte"
            impulse_color = "info"

        expectations["selic_delta_26_27"] = selic_delta_26_27
        expectations["monetary_impulse"] = monetary_impulse
        expectations["impulse_color"] = impulse_color
        return expectations


if __name__ == "__main__":
    focus = FocusCollector()
    res = focus.get_focus_expectations()
    print("Relatório Focus BACEN:", res)
