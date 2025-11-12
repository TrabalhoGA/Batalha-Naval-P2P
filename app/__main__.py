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
    print("  - 'tabuleiro' ou 't': Exibir tabuleiros")
    print("  - 'participantes' ou 'p': Listar participantes")
    print("  - 'sair' ou 'q': Sair do jogo")
    print("  - 'score' ou 's': Ver score atual")
    print("Tiros automáticos serão disparados a cada 10 segundos")
    
    # Loop principal do jogo
    try:
        while peer_service.running:
            comando = input("\nComando: ").strip().lower()
            
            if comando in ['sair', 'q', 'quit', 'exit']:
                peer_service.sair()
                break
            elif comando in ['tabuleiro', 't']:
                game_interface.exibir_tabuleiro()
            elif comando in ['participantes', 'p']:
                print(f"\n[PARTICIPANTES] Total: {len(peer_service.peers)}")
                for i, peer in enumerate(peer_service.peers, 1):
                    print(f"  {i}. {peer}")
            elif comando in ['score', 's']:
                print(f"\n[SCORE ATUAL]")
                print(f"  Jogadores atingidos: {len(peer_service.jogadores_atingidos)}")
                print(f"  Vezes atingido: {peer_service.vezes_atingido}")
                print(f"  Score: {len(peer_service.jogadores_atingidos) - peer_service.vezes_atingido}")
            elif comando == '':
                continue
            else:
                print("Comando não reconhecido. Use 'sair', 'tabuleiro', 'participantes' ou 'score'")
                
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
