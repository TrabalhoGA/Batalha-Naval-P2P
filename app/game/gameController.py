from typing import List, Optional, Tuple
from app.game.ship import Ship
from app.utils.ship_loader import carregar_especificacoes_navios

class GameController:
    def __init__(self):
        self.tabuleiro = [[0 for y in range(10)] for x in range(10)]
        self.embarcacoes: List[Ship] = []
        self.hitPoints = None
        self.tabuleiroInimigo = [[0 for y in range(10)] for x in range(10)]
        self.hitPointsInimigo = None

    def _posicionar_embarcacao(self, embarcacao: Ship):
        alcanceEmbarcacao = embarcacao.get_alcance()
        for pos in alcanceEmbarcacao:
            self.tabuleiro[pos[0]][pos[1]] = 1

    def _decodificar_posicao(self, posicao):
        letraPosicao = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7, "i": 8, "j": 9}
        linha = int(letraPosicao[posicao[0]])
        coluna = int(posicao[1])

        return (linha, coluna)
    
    def carregar_embarcacoes(self):
        embarcacoesInfo = carregar_especificacoes_navios()
        self.embarcacoes = [Ship(spec["name"], spec["size"]) for spec in embarcacoesInfo]
        
        # Calcular hitPoints total baseado no tamanho de todas as embarcações
        self.hitPoints = sum(barco.tamanho for barco in self.embarcacoes)
        self.hitPointsInimigo = self.hitPoints
        
        return self.embarcacoes
    
    def carregar_posicoes_inimigo(self, posEmbarcacaoInimigaStr):
        embarcacoesInimigo = posEmbarcacaoInimigaStr.split(" ")
        posEmbarcacaoInimiga = []
        for pos in embarcacoesInimigo:
            posEmbarcacaoInimiga.append(pos.split(","))

        for pos in posEmbarcacaoInimiga:
            linha = int(pos[0])
            coluna = int(pos[1])
            self.tabuleiroInimigo[linha][coluna] = 1

    def enviar_posicoes_embarcacoes(self) -> str:
        posEmbarcacoes = []
        for embarcacao in self.embarcacoes:
            for pos in embarcacao.get_alcance():
                posEmbarcacoes.append(f"{pos[0]},{pos[1]} ")
        return posEmbarcacoes[:len(posEmbarcacoes)-1]
    
    def atacar_inimigo(self, posicao: str):
        pos = self._decodificar_posicao(posicao)
        row = pos[0]
        col = pos[1]
        if self.tabuleiroInimigo[row][col] == 1:
            print("ACERTOU EM CHEIO!")
            self.tabuleiroInimigo[row][col] = 2
            self.hitPointsInimigo -= 1

        elif self.tabuleiroInimigo[row][col] == 2 or self.tabuleiroInimigo[row][col] == 3:
            print("Posição já atacada anteriormente, que tal tentar outra na próxima?")

        else:
            print("Você errou o ataque, mas não desanime, o próximo pode ser o certo!")
            self.tabuleiroInimigo[row][col] = 3

    def sofrer_ataque(self, posicao: str):
        pos = self._decodificar_posicao(posicao)
        row = pos[0]
        col = pos[1]
        if self.tabuleiro[row][col] == 1:
            print("SEU NAVIO FOI ATINGIDO!")
            self.tabuleiro[row][col] = 2
            self.hitPoints -= 1

        elif self.tabuleiro[row][col] == 2 or self.tabuleiro[row][col] == 3:
            print("O inimigo está perdido! Atacou uma posição já atingida anteriormente.")

        else:
            print("Passou de raspão! O inimigo errou o ataque.")
            self.tabuleiro[row][col] = 3
    
    def perdeu(self) -> bool:
        return self.hitPoints <= 0
    
    def venceu(self) -> bool:
        return self.hitPointsInimigo <= 0

    def reset(self):
        self.tabuleiro = [[0 for y in range(10)] for x in range(10)]
        self.hitPoints = 5 + 4 + 3 + 3 + 2
        self.tabuleiroInimigo = [[0 for y in range(10)] for x in range(10)]
        self.hitPointsInimigo = 5 + 4 + 3 + 3 + 2
        for embarcacao in self.embarcacoes:
            embarcacao.hits.clear()

    def registrar_embarcacoes(self, embarcacoes: Optional[List[Ship]]):
        self.embarcacoes = embarcacoes or []
        self.tabuleiro = [[0 for y in range(10)] for x in range(10)]
        self.hitPoints = sum(barco.tamanho for barco in self.embarcacoes) or (5 + 4 + 3 + 3 + 2)
        for barco in self.embarcacoes:
            self._posicionar_embarcacao(barco)

    def _encontrar_embarcacao_por_posicao(self, linha: int, coluna: int) -> Optional[Ship]:
        for barco in self.embarcacoes:
            try:
                if (linha, coluna) in barco.get_alcance():
                    return barco
            except (IndexError, TypeError):
                continue
        return None

    def processar_tiro_recebido(self, linha: int, coluna: int) -> dict:
        resultado = {"hit": False, "destroyed": False, "fleet_destroyed": False}
        if not (0 <= linha < 10 and 0 <= coluna < 10):
            return resultado

        celula = self.tabuleiro[linha][coluna]
        if celula == 1:
            resultado["hit"] = True
            self.tabuleiro[linha][coluna] = 2
            self.hitPoints -= 1

            barco = self._encontrar_embarcacao_por_posicao(linha, coluna)
            if barco is not None:
                barco.hits.add((linha, coluna))
                if barco.foi_destruido():
                    resultado["destroyed"] = True

            if self.perdeu():
                resultado["fleet_destroyed"] = True
        elif celula == 0:
            self.tabuleiro[linha][coluna] = 3

        return resultado