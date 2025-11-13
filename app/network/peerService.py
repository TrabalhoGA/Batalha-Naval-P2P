import socket
import threading
import time
import json
import random
import os
import platform
from app.network.TCPConnection import TCPConnection
from app.network.UDPConnection import UDPConnection
from app.game.gameInterface import GameInterface

def limpar_terminal():
    """Limpa o terminal conforme o SO (Windows/Unix)."""
    if platform.system().lower().startswith("win"):
        os.system("cls")
    else:
        os.system("clear")

class PeerService:
    def __init__(self, game_controller):
        self.hostname = socket.gethostname()
        self.ip_address = socket.gethostbyname(self.hostname)
        self.udp_port = 5000
        self.tcp_port = 5001
        self.udp_connection = UDPConnection("0.0.0.0", self.udp_port)
        self.tcp_connection = TCPConnection("0.0.0.0", self.tcp_port)
        self.peers = []  # Lista de IPs dos participantes
        self.game_controller = game_controller
        self.running = True
        self.timer_thread = None
        
        # Controle de score
        self.jogadores_atingidos = set()  # IPs únicos de jogadores atingidos
        self.vezes_atingido = 0  # Quantas vezes fui atingido
        self.tiros_por_jogador = {}  # Dicionário {ip: [posições já tentadas]}
        
        # Controle de turno de ataque
        self.input_escolhido = None
        self.input_lock = threading.Lock()
        self.aguardando_input = False
        self.em_turno_ataque = False  # Nova flag para indicar se está em turno
        
    def start(self):
        """Inicia o serviço P2P."""
        # Inicia listeners
        self.udp_connection.listen(self._handle_udp_message)
        self.tcp_connection.listen(self._handle_tcp_message)
        
        # Aguarda um pouco para garantir que os sockets estão prontos
        time.sleep(1)
        
        # Envia broadcast de conexão
        self._broadcast_conectando()
        
        # Aguarda receber respostas
        time.sleep(2)
        
        # Inicia timer de tiros
        self._start_shooting_timer()
        
    def _broadcast_conectando(self):
        """Envia mensagem Conectando via UDP para descobrir peers na rede."""
        print("Enviando broadcast 'Conectando'...")
        try:
            self.udp_connection.send("Conectando", "255.255.255.255", self.udp_port)
        except Exception as e:
            print(f"[ERRO] Falha ao enviar broadcast: {e}")

    def _handle_udp_message(self, message, addr):
        """Processa mensagens UDP recebidas."""
        sender_ip = addr[0]
        
        # Ignora mensagens de si mesmo
        if sender_ip == self.ip_address or sender_ip == "127.0.0.1":
            return
            
        try:
            if message == "Conectando":
                self._handle_conectando(sender_ip)
            elif message.startswith("shot:"):
                self._handle_shot(message, sender_ip)
            elif message == "lost":
                self._handle_lost(sender_ip)
            elif message == "saindo":
                self._handle_saindo(sender_ip)
        except Exception as e:
            print(f"[ERRO] Erro ao processar mensagem UDP de {sender_ip}: {e}")

    def _handle_tcp_message(self, message, addr):
        """Processa mensagens TCP recebidas."""
        sender_ip = addr[0]
        
        # Ignora mensagens de si mesmo
        if sender_ip == self.ip_address or sender_ip == "127.0.0.1":
            return
            
        try:
            if message.startswith("participantes:"):
                self._handle_participantes(message, sender_ip)
            elif message == "hit":
                self._handle_hit(sender_ip)
            elif message == "destroyed":
                self._handle_destroyed(sender_ip)
            elif message == "miss":
                self._handle_miss(sender_ip)
        except Exception as e:
            print(f"[ERRO] Erro ao processar mensagem TCP de {sender_ip}: {e}")

    def _handle_conectando(self, sender_ip):
        """Processa mensagem Conectando."""
        if sender_ip not in self.peers:
            print(f"[INFO] Novo participante detectado: {sender_ip}")
            self.peers.append(sender_ip)
            
            # Responde via TCP com lista de participantes
            participantes_msg = f"participantes:{json.dumps(self.peers)}"
            try:
                self.tcp_connection.send(participantes_msg, sender_ip, self.tcp_port)
            except Exception as e:
                print(f"[ERRO] Falha ao enviar lista de participantes para {sender_ip}: {e}")

    def _handle_participantes(self, message, sender_ip):
        """Processa lista de participantes recebida."""
        try:
            # Extrai lista de IPs da mensagem
            lista_str = message.replace("participantes:", "")
            lista_ips = json.loads(lista_str)
            
            # Adiciona novos participantes
            for ip in lista_ips:
                if ip not in self.peers and ip != self.ip_address and ip != "127.0.0.1":
                    print(f"Adicionando participante da lista: {ip}")
                    self.peers.append(ip)
                    
            # Adiciona o remetente se não estiver na lista
            if sender_ip not in self.peers:
                print(f"Adicionando remetente: {sender_ip}")
                self.peers.append(sender_ip)
                
        except Exception as e:
            print(f"Erro ao processar lista de participantes: {e}")

    def _handle_shot(self, message, sender_ip):
        """Processa tiro recebido."""
        try:
            # Adiciona o remetente aos peers se não estiver na lista
            if sender_ip not in self.peers:
                print(f"[INFO] Adicionando {sender_ip} aos oponentes (recebeu tiro)")
                self.peers.append(sender_ip)
            
            # Extrai coordenadas: "shot:x,y"
            coords = message.replace("shot:", "").split(",")
            x = int(coords[0])
            y = int(coords[1])
            
            print(f"\nRecebido tiro em ({x},{y}) de {sender_ip}")
            
            # Verifica se acertou
            resultado = self.game_controller.processar_tiro_recebido(x, y)
            
            if resultado["hit"]:
                self.vezes_atingido += 1
                print(f"\nSua embarcação foi atingida! Total de hits: {self.vezes_atingido}")
                self.tcp_connection.send("hit", sender_ip, self.tcp_port)
                
                if resultado["destroyed"]:
                    print(f"\nUma de suas embarcações foi destruída!")
                    self.tcp_connection.send("destroyed", sender_ip, self.tcp_port)
                    
                    if resultado["fleet_destroyed"]:
                        print(f"\nTodas as suas embarcações foram destruídas!")
                        self._broadcast_lost()
            else:
                print(f"\nO tiro de {sender_ip} errou!")
                # Envia confirmação de erro
                self.tcp_connection.send("miss", sender_ip, self.tcp_port)
                
        except Exception as e:
            print(f"Erro ao processar tiro: {e}")

    def _handle_hit(self, sender_ip):
        """Processa confirmação de acerto."""
        print(f"Você atingiu uma embarcação de {sender_ip}!")
        self.jogadores_atingidos.add(sender_ip)
        
        # Atualiza o tabuleiro visual com o acerto se possível
        if sender_ip in self.tiros_por_jogador and self.tiros_por_jogador[sender_ip]:
            ultimo_tiro = self.tiros_por_jogador[sender_ip][-1]
            self.game_controller.registrar_tiro_enviado(ultimo_tiro[0], ultimo_tiro[1], acertou=True)
            # Também registra no tabuleiro específico do jogador
            self.game_controller.registrar_tiro_para_jogador(sender_ip, ultimo_tiro[0], ultimo_tiro[1], acertou=True)

    def _handle_destroyed(self, sender_ip):
        """Processa confirmação de embarcação destruída."""
        print(f"Você destruiu uma embarcação de {sender_ip}!")
        self.jogadores_atingidos.add(sender_ip)
        
        # Atualiza o tabuleiro visual com o acerto
        if sender_ip in self.tiros_por_jogador and self.tiros_por_jogador[sender_ip]:
            ultimo_tiro = self.tiros_por_jogador[sender_ip][-1]
            self.game_controller.registrar_tiro_enviado(ultimo_tiro[0], ultimo_tiro[1], acertou=True)
            # Também registra no tabuleiro específico do jogador
            self.game_controller.registrar_tiro_para_jogador(sender_ip, ultimo_tiro[0], ultimo_tiro[1], acertou=True)

    def _handle_miss(self, sender_ip):
        """Processa confirmação de erro (miss)."""
        print(f"\nSeu tiro em {sender_ip} caiu na água!")

    def _handle_lost(self, sender_ip):
        """Processa mensagem de derrota de um jogador."""
        print(f"\nJogador {sender_ip} foi derrotado e saiu do jogo!")
        if sender_ip in self.peers:
            self.peers.remove(sender_ip)

    def _handle_saindo(self, sender_ip):
        """Processa mensagem de saída de um jogador."""
        print(f"\nJogador {sender_ip} saiu do jogo.")
        if sender_ip in self.peers:
            self.peers.remove(sender_ip)

    def _broadcast_lost(self):
        """Envia mensagem de derrota para todos."""
        print("\nEnviando mensagem 'lost' para todos os participantes...")
        for peer_ip in list(self.peers):
            try:
                self.udp_connection.send("lost", peer_ip, self.udp_port)
            except Exception as e:
                print(f"\nFalha ao enviar 'lost' para {peer_ip}: {e}")

    def sair(self):
        """Sai do jogo e envia mensagem para todos."""
        print("\nSaindo do jogo...")
        self.running = False
        
        # Envia mensagem de saída para todos
        for peer_ip in list(self.peers):
            try:
                self.udp_connection.send("saindo", peer_ip, self.udp_port)
            except Exception as e:
                print(f"\nFalha ao enviar 'saindo' para {peer_ip}: {e}")
        
        # Exibe score final
        self._exibir_score()
        
        # Aguarda um pouco para garantir que as mensagens foram enviadas
        time.sleep(1)

    def _exibir_score(self):
        """Exibe o score final."""
        print("\n" + "="*50)
        print("SCORE FINAL")
        print("="*50)
        print(f"Jogadores únicos atingidos: {len(self.jogadores_atingidos)}")
        print(f"Jogadores: {list(self.jogadores_atingidos)}")
        print(f"Vezes que fui atingido: {self.vezes_atingido}")
        
        score_final = len(self.jogadores_atingidos) - self.vezes_atingido
        print(f"\nSCORE: {score_final}")
        print("="*50 + "\n")

    def _start_shooting_timer(self):
        """Inicia o timer que dispara a cada 10 segundos."""
        def _timer_loop():
            print("[INFO] Timer de disparos iniciado - Ataque a cada 10 segundos")
            while self.running:
                
                time.sleep(10)  # Aguarda 10 segundos
                
                if not self.running:
                    break
                    
                if not self.peers:
                    # Só mostra mensagem se também não recebemos nenhum tiro ainda
                    if self.vezes_atingido == 0:
                        print("\n[INFO] Nenhum oponente conectado. Aguardando jogadores...")
                    continue
                
                # Verifica se já perdeu
                if self.game_controller.perdeu():
                    print("\n[GAME OVER] Você não pode mais atacar.")
                    break
                
                # Realiza o ataque
                self._realizar_turno_ataque()
        
        self.timer_thread = threading.Thread(target=_timer_loop, daemon=True)
        self.timer_thread.start()

    def _realizar_turno_ataque(self):
        """Realiza um turno de ataque, perguntando ao jogador ou escolhendo automaticamente."""
        # Lista os oponentes
        for i, peer_ip in enumerate(self.peers, 1):
            tiros_feitos = len(self.tiros_por_jogador.get(peer_ip, []))
            print(f"  {i}. {peer_ip} (Tiros feitos: {tiros_feitos})")
        
        # Marca que está em turno de ataque
        with self.input_lock:
            self.em_turno_ataque = True
            self.input_escolhido = None
            self.aguardando_input = True
        
        print(f"\nDigite uma posição para atacar (ex: a5)")

        # Cria um GameInterface temporário para exibir os tabuleiros (apenas uma vez)
        try:
            gi = GameInterface(self.game_controller)
        except Exception:
            gi = None

        # Exibe os tabuleiros UMA única vez e informa tempo estático — sem atualizar/limpar o terminal
        try:
            print(f"\n[TURNO DE ATAQUE] Você tem 10 segundos para escolher uma posição\n")
            if gi:
                gi.exibir_tabuleiro()
                if self.peers:
                    print("\n--- Tabuleiros dos inimigos (consolidado) ---\n")
                    display_peers = [p.split(":", 1)[0] if ":" in p else p for p in self.peers]
                    gi.exibir_tabuleiros_por_jogador(display_peers)
            else:
                # Fallback simples se GameInterface não puder ser instanciado
                print("Tabuleiros não disponíveis no momento.")
        except Exception:
            # Não deixar que a exibição quebre o fluxo
            pass

        # Aguarda input por 10 segundos (sem refrescar a tela para evitar piscar/interromper digitação)
        inicio = time.time()
        while time.time() - inicio < 10:
            with self.input_lock:
                if self.input_escolhido is not None:
                    break
            # Dorme um curto período para permanecer responsivo, sem imprimir nada
            time.sleep(0.1)

        # Finaliza período de input
        with self.input_lock:
            self.aguardando_input = False
            self.em_turno_ataque = False
            escolha_usuario = self.input_escolhido
            self.input_escolhido = None
        
        # Processa escolha
        posicao_escolhida = None
        
        if escolha_usuario:
            # Tenta decodificar como posição
            try:
                pos_decodificada = self._decodificar_posicao(escolha_usuario)
                linha, coluna = pos_decodificada
                print(f" Você escolheu atacar na posição: {escolha_usuario.upper()}")
                posicao_escolhida = (linha, coluna)
            except:
                # Não é uma posição válida, ignora
                print(f"Aviso! '{escolha_usuario}' não é uma posição válida. Escolhendo automaticamente...")
                posicao_escolhida = self._escolher_posicao_automatica_geral()
        else:
            # Escolha automática
            print("Tempo esgotado! Escolhendo posição automaticamente...")
            posicao_escolhida = self._escolher_posicao_automatica_geral()
        
        if not posicao_escolhida:
            print("Nenhuma posição escolhida.")
            return
        
        # Aplica o ataque para cada oponente
        for peer_ip in list(self.peers):
            if not self.running or self.game_controller.perdeu():
                break
                
            print(f"\n→ Atacando {peer_ip} na posição escolhida...")
            self._enviar_tiro(peer_ip, posicao_escolhida)
    
    def processar_input(self, comando):
        """Processa input do usuário, seja comando ou posição de ataque."""
        with self.input_lock:
            if self.aguardando_input and self.em_turno_ataque:
                # Durante turno de ataque, guarda o input
                self.input_escolhido = comando
                return True  # Input foi processado no contexto de ataque
            else:
                return False  # Input não é para ataque, processar como comando normal

    def _decodificar_posicao(self, posicao):
        """Decodifica uma posição no formato 'a5' para (linha, coluna)."""
        if len(posicao) < 2:
            raise ValueError("Posição muito curta")
        
        letra_posicao = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, 
                        "f": 5, "g": 6, "h": 7, "i": 8, "j": 9}
        
        letra = posicao[0].lower()
        numero = posicao[1:]
        
        if letra not in letra_posicao:
            raise ValueError(f"Letra inválida: {letra}")
        
        linha = letra_posicao[letra]
        coluna = int(numero)
        
        if not (0 <= coluna < self.game_controller.tamanho_grid):
            raise ValueError(f"Coluna inválida: {coluna}")
        
        return (linha, coluna)

    def _escolher_posicao_automatica(self, peer_ip):
        """Escolhe automaticamente uma posição que ainda não foi atacada para um jogador específico."""
        tamanho_grid = self.game_controller.tamanho_grid
        
        # Inicializa lista de tiros se não existir
        if peer_ip not in self.tiros_por_jogador:
            self.tiros_por_jogador[peer_ip] = []
        
        tiros_feitos = self.tiros_por_jogador[peer_ip]
        
        # Gera todas as posições possíveis
        todas_posicoes = [(x, y) for x in range(tamanho_grid) for y in range(tamanho_grid)]
        
        # Filtra posições não atacadas
        posicoes_disponiveis = [pos for pos in todas_posicoes if pos not in tiros_feitos]
        
        if not posicoes_disponiveis:
            print(f"Todas as posições de {peer_ip} já foram atacadas!")
            return None
        
        # Escolhe aleatoriamente
        posicao_escolhida = random.choice(posicoes_disponiveis)
        
        # Converte para formato legível
        letra_posicao = {0: "a", 1: "b", 2: "c", 3: "d", 4: "e", 
                        5: "f", 6: "g", 7: "h", 8: "i", 9: "j"}
        posicao_str = f"{letra_posicao[posicao_escolhida[0]]}{posicao_escolhida[1]}"
        
        print(f"Posição escolhida automaticamente: {posicao_str}")
        return posicao_escolhida

    def _escolher_posicao_automatica_geral(self):
        """Escolhe automaticamente uma posição aleatória do grid."""
        tamanho_grid = self.game_controller.tamanho_grid
        
        # Gera todas as posições possíveis
        todas_posicoes = [(x, y) for x in range(tamanho_grid) for y in range(tamanho_grid)]
        
        # Escolhe aleatoriamente
        posicao_escolhida = random.choice(todas_posicoes)
        
        # Converte para formato legível
        letra_posicao = {0: "a", 1: "b", 2: "c", 3: "d", 4: "e", 
                        5: "f", 6: "g", 7: "h", 8: "i", 9: "j"}
        posicao_str = f"{letra_posicao[posicao_escolhida[0]]}{posicao_escolhida[1]}"
        
        print(f"Posição escolhida automaticamente: {posicao_str.upper()}")
        return posicao_escolhida

    def _enviar_tiro(self, peer_ip, posicao):
        """Envia um tiro para o peer especificado."""
        if posicao is None:
            return
        
        linha, coluna = posicao
        
        # Converte para formato legível
        letra_posicao = {0: "a", 1: "b", 2: "c", 3: "d", 4: "e", 
                        5: "f", 6: "g", 7: "h", 8: "i", 9: "j"}
        posicao_str = f"{letra_posicao[linha]}{coluna}"
        
        # Registra o tiro
        if peer_ip not in self.tiros_por_jogador:
            self.tiros_por_jogador[peer_ip] = []
        self.tiros_por_jogador[peer_ip].append(posicao)
        
        # Marca no tabuleiro visual consolidado (será atualizado se acertar)
        self.game_controller.registrar_tiro_enviado(linha, coluna, acertou=False)
        
        # Marca no tabuleiro específico do jogador
        self.game_controller.registrar_tiro_para_jogador(peer_ip, linha, coluna, acertou=False)
        
        # Envia mensagem UDP
        mensagem = f"shot:{linha},{coluna}"
        try:
            self.udp_connection.send(mensagem, peer_ip, self.udp_port)
        except Exception as e:
            pass