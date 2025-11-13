from typing import List, Dict
from colorama import init, Fore
import random
from app.game.ship import Ship
from app.game.gameController import GameController

# Inicializa colorama
init(autoreset=True)

class GameInterface:
    def __init__(self, game_controller: GameController):
        self.game_controller = game_controller

    def posicionar_todas_embarcacoes(self) -> List[Ship]:
        if not self.game_controller.embarcacoes:
            raise ValueError("Nenhuma embarcação foi carregada no GameController. Execute game_controller.carregar_embarcacoes() primeiro.")
        
        # Pergunta se quer posicionar manualmente ou automaticamente
        print("\n" + "="*50)
        print("POSICIONAMENTO DE EMBARCAÇÕES")
        print("="*50)
        escolha = input("Deseja posicionar as embarcações manualmente ou automaticamente? (m/a): ").lower().strip()
        
        if escolha == 'a':
            return self._posicionar_automaticamente()
        else:
            return self._posicionar_manualmente()
    
    def _posicionar_automaticamente(self) -> List[Ship]:
        """Posiciona todas as embarcações automaticamente de forma aleatória."""
        print("\n[AUTO] Posicionando embarcações automaticamente...")
        
        embarcacoes_posicionadas: Dict[str, Ship] = {}
        
        for embarcacao in self.game_controller.embarcacoes:
            embarcacaoNome = embarcacao.nome
            embarcacaoTamanho = embarcacao.tamanho
            
            posicaoValida = False
            tentativas = 0
            max_tentativas = 100
            
            while not posicaoValida and tentativas < max_tentativas:
                tentativas += 1
                
                # Escolhe direção aleatória
                direcao = random.choice(['h', 'v'])
                
                # Escolhe posição aleatória
                linha = random.randint(0, self.game_controller.tamanho_grid - 1)
                coluna = random.randint(0, self.game_controller.tamanho_grid - 1)
                pos_inicial = (linha, coluna)
                
                try:
                    # Criar nova embarcação com posições
                    embarcacao_posicionada = Ship(
                        embarcacaoNome, 
                        embarcacaoTamanho, 
                        [pos_inicial, direcao], 
                        tamanho_grid=self.game_controller.tamanho_grid
                    )
                    posicaoValida = embarcacao_posicionada.pode_posicionar(list(embarcacoes_posicionadas.values()))
                    
                    if posicaoValida:
                        embarcacoes_posicionadas[embarcacaoNome] = embarcacao_posicionada
                        self.game_controller._posicionar_embarcacao(embarcacao_posicionada)
                        
                        # Converte para formato legível
                        letra_posicao = {0: "a", 1: "b", 2: "c", 3: "d", 4: "e", 
                                       5: "f", 6: "g", 7: "h", 8: "i", 9: "j"}
                        pos_str = f"{letra_posicao[linha]}{coluna}"
                        dir_str = "horizontal" if direcao == 'h' else "vertical"
                        
                        print(f"[OK] {embarcacaoNome} posicionado em {pos_str} ({dir_str})")
                        
                except Exception:
                    posicaoValida = False
            
            if not posicaoValida:
                print(f"[ERRO] Não foi possível posicionar {embarcacaoNome}. Tentando novamente...")
                return self._posicionar_automaticamente()
        
        # Mostra tabuleiro final
        print("\n[INFO] Todas as embarcações foram posicionadas:")
        self.carregar_tabuleiro_proprio()
        
        # Atualizar as embarcações no controller com as posições
        self.game_controller.embarcacoes = list(embarcacoes_posicionadas.values())
        return self.game_controller.embarcacoes
    
    def _posicionar_manualmente(self) -> List[Ship]:
        """Posiciona todas as embarcações manualmente."""
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
                    embarcacao_posicionada = Ship(embarcacaoNome, embarcacaoTamanho, [pos_decodificada, direcao], tamanho_grid=self.game_controller.tamanho_grid)
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
                    novoTabuleiro[y][x] = Fore.BLUE + " 0 " + Fore.RESET
                elif novoTabuleiro[y][x] == 1:
                    novoTabuleiro[y][x] = Fore.GREEN + " 1 " + Fore.RESET
                elif novoTabuleiro[y][x] == 2:
                    novoTabuleiro[y][x] = Fore.RED + " X " + Fore.RESET
                elif novoTabuleiro[y][x] == 3:
                    novoTabuleiro[y][x] = Fore.CYAN + " - " + Fore.RESET

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
                    novoTabuleiro[y][x] = Fore.CYAN + " 0 " + Fore.RESET
                elif novoTabuleiro[y][x] == 1:
                    novoTabuleiro[y][x] = Fore.CYAN + " 0 " + Fore.RESET
                elif novoTabuleiro[y][x] == 2:
                    novoTabuleiro[y][x] = Fore.RED + " X " + Fore.RESET
                elif novoTabuleiro[y][x] == 3:
                    novoTabuleiro[y][x] = Fore.BLUE + " - " + Fore.RESET

        for i in range(len(novoTabuleiro)):
            row = novoTabuleiro[i]
            line = posLaterais[i] + " "
            for index in range(len(row)):
                line += f"{row[index]}"
            print(line)
                    
    def exibir_tabuleiro(self):
        # título centralizado com cor
        largura = 40
        print(Fore.YELLOW + "=" * largura + Fore.RESET)
        titulo = "SEU TABULEIRO"
        print(Fore.YELLOW + titulo.center(largura) + Fore.RESET)
        print(Fore.YELLOW + "=" * largura + Fore.RESET)
        self.carregar_tabuleiro_proprio()

        print()  # separador
        print(Fore.YELLOW + "=" * largura + Fore.RESET)
        titulo2 = "TABULEIRO INIMIGO (Consolidado)"
        print(Fore.YELLOW + titulo2.center(largura) + Fore.RESET)
        print(Fore.YELLOW + "=" * largura + Fore.RESET)
        self.carregar_tabuleiro_inimigo()
        print()

        # legenda
        print("Legenda: " + Fore.GREEN + "1=Navio" + Fore.RESET + " " +
              Fore.RED + "X=Atingido" + Fore.RESET + " " +
              Fore.CYAN + "-=Tiro (Água)" + Fore.RESET)
    
    def exibir_tabuleiros_por_jogador(self, peers: list):
        """Exibe tabuleiros individuais para cada jogador."""
        print(f"\n{'='*40}")
        print(f"SEU TABULEIRO:")
        print(f"{'='*40}")
        self.carregar_tabuleiro_proprio()
        
        # Exibe um tabuleiro para cada jogador
        for peer_ip in peers:
            if peer_ip in self.game_controller.tabuleiros_por_jogador:
                print(f"\n{'='*40}")
                print(f"TABULEIRO - {peer_ip}:")
                print(f"{'='*40}")
                self._carregar_tabuleiro_especifico(self.game_controller.tabuleiros_por_jogador[peer_ip])
        
        print()
    
    def _carregar_tabuleiro_especifico(self, tabuleiro):
        """Carrega e exibe um tabuleiro específico."""
        novoTabuleiro = [row[:] for row in tabuleiro]
        posLaterais = ["a","b","c","d","e","f","g","h","i","j"]

        # Mostrar os números horizontais
        print("\n   ", end="")
        for num in range(len(tabuleiro)):
            print(f"{num}  ", end="")
        print()

        for y in range(len(novoTabuleiro)):
            for x in range(len(novoTabuleiro[y])):
                if novoTabuleiro[y][x] == 0:
                    novoTabuleiro[y][x] = Fore.CYAN + " 0 " + Fore.RESET
                elif novoTabuleiro[y][x] == 1:
                    novoTabuleiro[y][x] = Fore.CYAN + " 0 " + Fore.RESET
                elif novoTabuleiro[y][x] == 2:
                    novoTabuleiro[y][x] = Fore.RED + " X " + Fore.RESET
                elif novoTabuleiro[y][x] == 3:
                    novoTabuleiro[y][x] = Fore.BLUE + " - " + Fore.RESET

        for i in range(len(novoTabuleiro)):
            row = novoTabuleiro[i]
            line = posLaterais[i] + " "
            for index in range(len(row)):
                line += f"{row[index]}"
            print(line)
