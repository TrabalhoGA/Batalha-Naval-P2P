from typing import List, Optional
from app.game.ship import Ship
from app.utils.ship_loader import carregar_especificacoes_navios

class GameController:
    def __init__(self):
        self.tamanho_grid = None
        self.tabuleiro = []
        self.embarcacoes: List[Ship] = []
        self.hitPoints = None
        self.tabuleiroInimigo = []
        self.hitPointsInimigo = None
        self.tabuleiros_por_jogador = {}  # {ip: [[grid]]} - Rastreia tiros por jogador

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
        embarcacoesInfo, tamanho_grid = carregar_especificacoes_navios()
        self.embarcacoes = [Ship(spec["name"], spec["size"], tamanho_grid=tamanho_grid) for spec in embarcacoesInfo]
        self.tamanho_grid = tamanho_grid
        self.tabuleiro = [[0 for y in range(tamanho_grid)] for x in range(tamanho_grid)]
        self.tabuleiroInimigo = [[0 for y in range(tamanho_grid)] for x in range(tamanho_grid)]
        
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
    
    def registrar_tiro_enviado(self, linha: int, coluna: int, acertou: bool = False):
        """Registra um tiro que fizemos no tabuleiro inimigo visualizado."""
        if 0 <= linha < self.tamanho_grid and 0 <= coluna < self.tamanho_grid:
            if acertou:
                self.tabuleiroInimigo[linha][coluna] = 2  # Acerto (vermelho)
            else:
                if self.tabuleiroInimigo[linha][coluna] == 0:  # Só marca se não tinha nada
                    self.tabuleiroInimigo[linha][coluna] = 3  # Erro (azul claro)
    
    def criar_tabuleiro_para_jogador(self, ip_jogador: str):
        """Cria um tabuleiro específico para rastrear ataques a um jogador."""
        if ip_jogador not in self.tabuleiros_por_jogador:
            self.tabuleiros_por_jogador[ip_jogador] = [[0 for y in range(self.tamanho_grid)] for x in range(self.tamanho_grid)]
    
    def registrar_tiro_para_jogador(self, ip_jogador: str, linha: int, coluna: int, acertou: bool = False):
        """Registra um tiro enviado para um jogador específico."""
        self.criar_tabuleiro_para_jogador(ip_jogador)
        
        if 0 <= linha < self.tamanho_grid and 0 <= coluna < self.tamanho_grid:
            if acertou:
                self.tabuleiros_por_jogador[ip_jogador][linha][coluna] = 2  # Acerto
            else:
                if self.tabuleiros_por_jogador[ip_jogador][linha][coluna] == 0:
                    self.tabuleiros_por_jogador[ip_jogador][linha][coluna] = 3  # Erro

    def reset(self):
        self.tabuleiro = [[0 for y in range(self.tamanho_grid)] for x in range(self.tamanho_grid)]
        self.hitPoints = sum(barco.tamanho for barco in self.embarcacoes)
        self.tabuleiroInimigo = [[0 for y in range(self.tamanho_grid)] for x in range(self.tamanho_grid)]
        self.hitPointsInimigo = sum(barco.tamanho for barco in self.embarcacoes)
        for embarcacao in self.embarcacoes:
            embarcacao.hits.clear()

    def registrar_embarcacoes(self, embarcacoes: Optional[List[Ship]]):
        self.embarcacoes = embarcacoes or []
        self.tabuleiro = [[0 for y in range(self.tamanho_grid)] for x in range(self.tamanho_grid)]
        self.hitPoints = sum(barco.tamanho for barco in self.embarcacoes)
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
        if not (0 <= linha < self.tamanho_grid and 0 <= coluna < self.tamanho_grid):
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