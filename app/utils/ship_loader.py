import json
import os
from typing import List

def carregar_especificacoes_navios(caminho_arquivo: str = None) -> List[dict]:
    if caminho_arquivo is None:
        dir_atual = os.path.dirname(os.path.abspath(__file__))
        caminho_arquivo = os.path.join(dir_atual, "..", "config", "ships.json")
    
    if not os.path.exists(caminho_arquivo):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")
    
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            navios = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Erro ao decodificar JSON: {e}")
    
    if not isinstance(navios, list):
        raise ValueError("O arquivo JSON deve conter uma lista de navios.")
    
    if len(navios) == 0:
        raise ValueError("A lista de navios está vazia.")
    
    for i, navio in enumerate(navios):
        if not isinstance(navio, dict):
            raise ValueError(f"Navio na posição {i} não é um dicionário.")
        if "name" not in navio:
            raise ValueError(f"Navio na posição {i} não possui o campo 'name'.")
        if "size" not in navio:
            raise ValueError(f"Navio na posição {i} não possui o campo 'size'.")
        if not isinstance(navio["size"], int) or navio["size"] <= 0:
            raise ValueError(f"Navio '{navio.get('name', '?')}' possui tamanho inválido.")
    
    return navios