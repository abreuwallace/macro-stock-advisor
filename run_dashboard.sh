#!/usr/bin/env bash
# Script para iniciar o Dashboard do Robô de Recomendação Macro B3
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=========================================================="
echo "  Iniciando Robô de Recomendação Macro B3 (Itaú Advisory)"
echo "=========================================================="

"$DIR/.venv/bin/streamlit" run app.py --server.port=8501 --server.headless=true

