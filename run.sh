#!/bin/bash

# Verifica se o virtualenv existe, se não, cria
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

# Ativa o virtualenv
source .venv/bin/activate

# Instala dependências
if [ -f "requirements.txt" ]; then
  pip install -r requirements.txt
fi

# Roda o app
python -m app