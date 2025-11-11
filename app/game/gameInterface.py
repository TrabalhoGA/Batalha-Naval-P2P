from typing import List, Dict
from colorama import init, Fore
from app.game.ship import Ship
from app.game.gameController import GameController

# Inicializa colorama
init(autoreset=True)

class GameInterface:
    def __init__(self, game_controller: GameController):
        self.game_controller = game_controller

    def load_posicoes_embarcacoes(self) -> List[Ship]:
        if not self.game_controller.embarcacoes:
            raise ValueError("Nenhuma embarcação foi carregada no GameController. Execute game_controller.carregar_embarcacoes() primeiro.")
        
        embarcacoes_posicionadas: Dict[str, Ship] = {}
        posicaoValida = False

        for embarcacao in self.game_controller.embarcacoes:
            embarcacaoNome = embarcacao.nome
            embarcacaoTamanho = embarcacao.tamanho

            # Mostrar tabuleiro
            self.carregar_tabuleiro_proprio()

            while not posicaoValida:
                direcao = input(f"\nVocê deseja posicionar seu {embarcacaoNome} de tamanho {embarcacaoTamanho} na horizontal ou vertical? (h/v): ").lower()
                posicao = input(f"As embarcações serão posicionadas a partir da parte mais à esquerda ou da parte mais acima.\nOnde você deseja posicionar seu {embarcacaoNome}? (ex: a1): ").lower()
            
                try:
                    pos_decodificada = self.game_controller._decodificar_posicao(posicao)
                    # Criar nova embarcação com posições
                    embarcacao_posicionada = Ship(embarcacaoNome, embarcacaoTamanho, [pos_decodificada, direcao])
                    posicaoValida = embarcacao_posicionada.pode_posicionar(list(embarcacoes_posicionadas.values()))
                
                except Exception as e:
                    print(f"[ERRO] Posição inválida: {e}")
                    posicaoValida = False
                
                if posicaoValida:
                    embarcacoes_posicionadas[embarcacaoNome] = embarcacao_posicionada
                    print(f"[OK] O {embarcacaoNome} foi posicionado com sucesso!\n")
                    self.game_controller._posicionar_embarcacao(embarcacao_posicionada)
                else:
                    print("[ERRO] Posição inválida, tente novamente.\n")

            posicaoValida = False
        
        # Atualizar as embarcações no controller com as posições
        self.game_controller.embarcacoes = list(embarcacoes_posicionadas.values())
        return self.game_controller.embarcacoes

    def carregar_tabuleiro_proprio(self):
        novoTabuleiro = [row[:] for row in self.game_controller.tabuleiro]
        posLaterais = ["a","b","c","d","e","f","g","h","i","j"]

        # Mostrar os números horizontais
        print("\n   ", end="")
        for num in range(len(self.game_controller.tabuleiro)):
            print(f"{num}  ", end="")
        print()

        for y in range(len(novoTabuleiro)):
            for x in range(len(novoTabuleiro[y])):
                if novoTabuleiro[y][x] == 0:
                    novoTabuleiro[y][x] = Fore.BLUE + " ~ " + Fore.RESET
                elif novoTabuleiro[y][x] == 1:
                    novoTabuleiro[y][x] = Fore.GREEN + " ■ " + Fore.RESET
                elif novoTabuleiro[y][x] == 2:
                    novoTabuleiro[y][x] = Fore.RED + " X " + Fore.RESET
                elif novoTabuleiro[y][x] == 3:
                    novoTabuleiro[y][x] = Fore.CYAN + " o " + Fore.RESET

        for i in range(len(novoTabuleiro)):
            row = novoTabuleiro[i]
            line = posLaterais[i] + " "
            for index in range(len(row)):
                line += f"{row[index]}"
            print(line)

    def carregar_tabuleiro_inimigo(self):
        novoTabuleiro = [row[:] for row in self.game_controller.tabuleiroInimigo]
        posLaterais = ["a","b","c","d","e","f","g","h","i","j"]

        # Mostrar os números horizontais
        print("\n   ", end="")
        for num in range(len(self.game_controller.tabuleiro)):
            print(f"{num}  ", end="")
        print()

        for y in range(len(novoTabuleiro)):
            for x in range(len(novoTabuleiro[y])):
                if novoTabuleiro[y][x] == 0:
                    novoTabuleiro[y][x] = Fore.CYAN + " ? " + Fore.RESET
                elif novoTabuleiro[y][x] == 1:
                    novoTabuleiro[y][x] = Fore.CYAN + " ? " + Fore.RESET
                elif novoTabuleiro[y][x] == 2:
                    novoTabuleiro[y][x] = Fore.RED + " X " + Fore.RESET
                elif novoTabuleiro[y][x] == 3:
                    novoTabuleiro[y][x] = Fore.BLUE + " o " + Fore.RESET

        for i in range(len(novoTabuleiro)):
            row = novoTabuleiro[i]
            line = posLaterais[i] + " "
            for index in range(len(row)):
                line += f"{row[index]}"
            print(line)
                    
    def exibir_tabuleiro(self):
        print(f"\n{'='*40}")
        print(f"SEU TABULEIRO:")
        print(f"{'='*40}")
        self.carregar_tabuleiro_proprio()

        print(f"\n{'='*40}")
        print(f"TABULEIRO INIMIGO:")
        print(f"{'='*40}")
        self.carregar_tabuleiro_inimigo()
        print()
