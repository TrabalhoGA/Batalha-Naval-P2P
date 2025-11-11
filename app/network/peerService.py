import socket
import threading
import time
import json
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

    def _handle_destroyed(self, sender_ip):
        """Processa confirmação de embarcação destruída."""
        print(f"[DESTRUÍDO] Você destruiu uma embarcação de {sender_ip}!")
        self.jogadores_atingidos.add(sender_ip)

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

    def _start_shooting_timer(self):
        """Inicia timer para enviar tiros a cada 10 segundos."""
        def shooting_loop():
            while self.running:
                time.sleep(10)
                if self.running and self.peers:
                    self._shoot_at_all_peers()
        
        self.timer_thread = threading.Thread(target=shooting_loop, daemon=True)
        self.timer_thread.start()
        print("[INFO] Timer de tiros iniciado (10 segundos)")

    def _shoot_at_all_peers(self):
        """Envia um tiro para cada participante."""
        import random
        
        for peer_ip in list(self.peers):  # Cria cópia da lista
            try:
                # Inicializa lista de tiros para este jogador se necessário
                if peer_ip not in self.tiros_por_jogador:
                    self.tiros_por_jogador[peer_ip] = []
                
                # Gera posição aleatória que ainda não foi tentada
                posicoes_disponiveis = [(x, y) for x in range(10) for y in range(10) 
                                       if (x, y) not in self.tiros_por_jogador[peer_ip]]
                
                if not posicoes_disponiveis:
                    print(f"[INFO] Todas as posições de {peer_ip} já foram tentadas")
                    continue
                
                x, y = random.choice(posicoes_disponiveis)
                self.tiros_por_jogador[peer_ip].append((x, y))
                
                # Envia tiro via UDP
                shot_msg = f"shot:{x},{y}"
                self.udp_connection.send(shot_msg, peer_ip, self.udp_port)
                print(f"[TIRO] Atirando em {peer_ip} na posição ({x},{y})")
                
            except Exception as e:
                print(f"[ERRO] Falha ao atirar em {peer_ip}: {e}")

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