import sys
import time
from app.game.gameInterface import GameInterface
from app.game.gameController import GameController
from app.network.peerService import PeerService


def main():
    print("="*50)
    print("BEM-VINDO AO BATALHA NAVAL P2P")
    print("="*50)
    
    # Inicializa o controlador do jogo
    game_controller = GameController()
    game_interface = GameInterface(game_controller)
    
    # Primeiro: Carrega as especificações das embarcações no controller
    game_controller.carregar_embarcacoes()
    
    # Segundo: Posiciona as embarcações no tabuleiro
    game_interface.posicionar_todas_embarcacoes()
    
    # Inicializa o serviço P2P
    peer_service = PeerService(game_controller)
    peer_service.start()

    print("Jogo iniciado! Comandos disponíveis:")
    print("  - 'tabuleiro' ou 't': Exibir tabuleiro consolidado")
    print("  - 'todos' ou 'a': Exibir todos os tabuleiros (por jogador)")
    print("  - 'participantes' ou 'p': Listar participantes")
    print("  - 'sair' ou 'q': Sair do jogo")
    print("  - 'score' ou 's': Ver score atual")
    print("\n[INFO] O jogo atacará automaticamente a cada 10 segundos.")
    print("[INFO] Quando for seu turno, você terá 10s para escolher o alvo.")
    print("[INFO] Pressione Enter a qualquer momento para ver o menu.\n")
        
    # Loop principal do jogo
    try:
        while peer_service.running:
            # Usa um try para não travar se o usuário não digitar nada
            try:
                comando = input("\nComando (ou Enter para continuar): ").strip().lower()
            except EOFError:
                continue
            except KeyboardInterrupt:
                raise
            
            if not comando:
                continue
            
            if comando in ['sair', 'q', 'quit', 'exit']:
                peer_service.sair()
                break
            elif comando in ['tabuleiro', 't']:
                game_interface.exibir_tabuleiro()
            elif comando in ['todos', 'a', 'all']:
                game_interface.exibir_tabuleiros_por_jogador(peer_service.peers)
            elif comando in ['participantes', 'p']:
                print(f"\n[PARTICIPANTES] Total: {len(peer_service.peers)}")
                for i, peer in enumerate(peer_service.peers, 1):
                    tiros = len(peer_service.tiros_por_jogador.get(peer, []))
                    print(f"  {i}. {peer} (Tiros realizados: {tiros})")
            elif comando in ['score', 's']:
                print(f"\n[SCORE ATUAL]")
                print(f"  Jogadores atingidos: {len(peer_service.jogadores_atingidos)}")
                for jogador in peer_service.jogadores_atingidos:
                    print(f"    - {jogador}")
                print(f"  Vezes atingido: {peer_service.vezes_atingido}")
                print(f"  Score: {len(peer_service.jogadores_atingidos) - peer_service.vezes_atingido}")
            else:
                print("Comando não reconhecido.")
                print("Use: 'sair', 'tabuleiro', 'todos', 'participantes' ou 'score'")
                
            # Verifica se perdeu
            if game_controller.perdeu():
                print("\nTodas as suas embarcações foram destruídas!")
                peer_service._broadcast_lost()
                time.sleep(2)
                peer_service.sair()
                break
                
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário")
        peer_service.sair()
    except Exception as e:
        print(f"\nErro inesperado: {e}")
        peer_service.sair()
    
    sys.exit(0)


if __name__ == "__main__":
    main()
