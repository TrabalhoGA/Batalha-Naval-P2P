import socket
import threading
import time
import json
import random
from app.network.tcpConnection import TCPConnection
from app.network.udpConnection import UDPConnection

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
        
    def start(self):
        """Inicia o serviço P2P."""
        print(f"[INFO] Iniciando serviço P2P - IP: {self.ip_address}")
        print(f"[INFO] Escutando UDP na porta {self.udp_port}")
        print(f"[INFO] Escutando TCP na porta {self.tcp_port}")
        
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
        print("[INFO] Enviando broadcast 'Conectando'...")
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
                    print(f"[INFO] Adicionando participante da lista: {ip}")
                    self.peers.append(ip)
                    
            # Adiciona o remetente se não estiver na lista
            if sender_ip not in self.peers:
                print(f"[INFO] Adicionando remetente: {sender_ip}")
                self.peers.append(sender_ip)
                
        except Exception as e:
            print(f"[ERRO] Erro ao processar lista de participantes: {e}")

    def _handle_shot(self, message, sender_ip):
        """Processa tiro recebido."""
        try:
            # Extrai coordenadas: "shot:x,y"
            coords = message.replace("shot:", "").split(",")
            x = int(coords[0])
            y = int(coords[1])
            
            print(f"\n[ATAQUE] Recebido tiro em ({x},{y}) de {sender_ip}")
            
            # Verifica se acertou
            resultado = self.game_controller.processar_tiro_recebido(x, y)
            
            if resultado["hit"]:
                self.vezes_atingido += 1
                print(f"[HIT] Sua embarcação foi atingida! Total de hits: {self.vezes_atingido}")
                self.tcp_connection.send("hit", sender_ip, self.tcp_port)
                
                if resultado["destroyed"]:
                    print(f"[DESTROYED] Uma de suas embarcações foi destruída!")
                    self.tcp_connection.send("destroyed", sender_ip, self.tcp_port)
                    
                    if resultado["fleet_destroyed"]:
                        print(f"\n[GAME OVER] Todas as suas embarcações foram destruídas!")
                        self._broadcast_lost()
            else:
                print(f"[MISS] O tiro de {sender_ip} errou!")
                
        except Exception as e:
            print(f"[ERRO] Erro ao processar tiro: {e}")

    def _handle_hit(self, sender_ip):
        """Processa confirmação de acerto."""
        print(f"[ACERTO] Você acertou uma embarcação de {sender_ip}!")
        self.jogadores_atingidos.add(sender_ip)
        
        # Atualiza o tabuleiro visual com o acerto se possível
        if sender_ip in self.tiros_por_jogador and self.tiros_por_jogador[sender_ip]:
            ultimo_tiro = self.tiros_por_jogador[sender_ip][-1]
            self.game_controller.registrar_tiro_enviado(ultimo_tiro[0], ultimo_tiro[1], acertou=True)
            # Também registra no tabuleiro específico do jogador
            self.game_controller.registrar_tiro_para_jogador(sender_ip, ultimo_tiro[0], ultimo_tiro[1], acertou=True)

    def _handle_destroyed(self, sender_ip):
        """Processa confirmação de embarcação destruída."""
        print(f"[DESTRUÍDO] Você destruiu uma embarcação de {sender_ip}!")
        self.jogadores_atingidos.add(sender_ip)
        
        # Atualiza o tabuleiro visual com o acerto
        if sender_ip in self.tiros_por_jogador and self.tiros_por_jogador[sender_ip]:
            ultimo_tiro = self.tiros_por_jogador[sender_ip][-1]
            self.game_controller.registrar_tiro_enviado(ultimo_tiro[0], ultimo_tiro[1], acertou=True)
            # Também registra no tabuleiro específico do jogador
            self.game_controller.registrar_tiro_para_jogador(sender_ip, ultimo_tiro[0], ultimo_tiro[1], acertou=True)

    def _handle_lost(self, sender_ip):
        """Processa mensagem de derrota de um jogador."""
        print(f"\n[INFO] Jogador {sender_ip} foi derrotado e saiu do jogo!")
        if sender_ip in self.peers:
            self.peers.remove(sender_ip)

    def _handle_saindo(self, sender_ip):
        """Processa mensagem de saída de um jogador."""
        print(f"\n[INFO] Jogador {sender_ip} saiu do jogo.")
        if sender_ip in self.peers:
            self.peers.remove(sender_ip)

    def _broadcast_lost(self):
        """Envia mensagem de derrota para todos."""
        print("[INFO] Enviando mensagem 'lost' para todos os participantes...")
        for peer_ip in list(self.peers):
            try:
                self.udp_connection.send("lost", peer_ip, self.udp_port)
            except Exception as e:
                print(f"[ERRO] Falha ao enviar 'lost' para {peer_ip}: {e}")

    def sair(self):
        """Sai do jogo e envia mensagem para todos."""
        print("\n[INFO] Saindo do jogo...")
        self.running = False
        
        # Envia mensagem de saída para todos
        for peer_ip in list(self.peers):
            try:
                self.udp_connection.send("saindo", peer_ip, self.udp_port)
            except Exception as e:
                print(f"[ERRO] Falha ao enviar 'saindo' para {peer_ip}: {e}")
        
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
        print("\n" + "="*50)
        print("TURNO DE ATAQUE")
        print("="*50)
        print(f"Oponentes disponíveis: {len(self.peers)}")
        
        # Lista os oponentes
        for i, peer_ip in enumerate(self.peers, 1):
            tiros_feitos = len(self.tiros_por_jogador.get(peer_ip, []))
            print(f"  {i}. {peer_ip} (Tiros feitos: {tiros_feitos})")
        
        # Escolhe UMA posição para atacar TODOS os jogadores
        print(f"\n[INPUT] Escolha UMA posição para atacar TODOS os oponentes (ex: a5)")
        print(f"[INPUT] Você tem 10 segundos para decidir...")
        posicao_escolhida = self._escolher_alvo_com_timeout(timeout=10)
        
        if not posicao_escolhida:
            print("[INFO] Nenhuma posição escolhida.")
            return
        
        # Aplica o ataque para cada oponente
        for peer_ip in list(self.peers):
            if not self.running or self.game_controller.perdeu():
                break
                
            print(f"\n→ Atacando {peer_ip} na posição escolhida...")
            self._enviar_tiro(peer_ip, posicao_escolhida)

    def _escolher_alvo_com_timeout(self, timeout=10):
        """
        Permite ao usuário escolher um alvo em até 'timeout' segundos.
        Se não escolher, seleciona automaticamente.
        Retorna uma tupla (linha, coluna) ou None.
        """
        # Reseta estado
        with self.input_lock:
            self.input_escolhido = None
            self.aguardando_input = True
        
        # Thread para capturar input do usuário
        def _capturar_input():
            try:
                escolha = input("Digite a posição (ou deixe vazio para auto): ").strip().lower()
                with self.input_lock:
                    if self.aguardando_input:
                        self.input_escolhido = escolha if escolha else None
            except:
                pass
        
        input_thread = threading.Thread(target=_capturar_input, daemon=True)
        input_thread.start()
        
        # Aguarda timeout
        input_thread.join(timeout=timeout)
        
        # Finaliza período de input
        with self.input_lock:
            self.aguardando_input = False
            escolha_usuario = self.input_escolhido
        
        # Se usuário escolheu e é válido
        if escolha_usuario:
            try:
                pos_decodificada = self._decodificar_posicao(escolha_usuario)
                linha, coluna = pos_decodificada
                
                print(f"[OK] Você escolheu atacar na posição: {escolha_usuario.upper()}")
                return (linha, coluna)
            except Exception as e:
                print(f"[ERRO] Posição inválida: {e}. Escolhendo automaticamente...")
                return self._escolher_posicao_automatica_geral()
        
        # Escolha automática se não digitou nada ou timeout
        print("[AUTO] Tempo esgotado! Escolhendo posição automaticamente...")
        return self._escolher_posicao_automatica_geral()

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
            print(f"[INFO] Todas as posições de {peer_ip} já foram atacadas!")
            return None
        
        # Escolhe aleatoriamente
        posicao_escolhida = random.choice(posicoes_disponiveis)
        
        # Converte para formato legível
        letra_posicao = {0: "a", 1: "b", 2: "c", 3: "d", 4: "e", 
                        5: "f", 6: "g", 7: "h", 8: "i", 9: "j"}
        posicao_str = f"{letra_posicao[posicao_escolhida[0]]}{posicao_escolhida[1]}"
        
        print(f"[AUTO] Posição escolhida automaticamente: {posicao_str}")
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
        
        print(f"[AUTO] Posição escolhida automaticamente: {posicao_str.upper()}")
        return posicao_escolhida

    def _enviar_tiro(self, peer_ip, posicao):
        """Envia um tiro para o peer especificado."""
        if posicao is None:
            return
        
        linha, coluna = posicao
        
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
            print(f"[TIRO] Disparado em ({linha},{coluna}) para {peer_ip}")
        except Exception as e:
            print(f"[ERRO] Falha ao enviar tiro para {peer_ip}: {e}")