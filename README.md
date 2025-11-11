# Batalha Naval P2P

Projeto desenvolvido para a disciplina **Redes de Computadores: Aplicação e Transporte**.  
Implementa uma **versão distribuída** do clássico jogo *Batalha Naval* utilizando **sockets TCP e UDP**, em um modelo **peer-to-peer (P2P)**.

---

## Objetivo

O objetivo é aplicar os conceitos de **camadas de aplicação e transporte**, utilizando **protocolo UDP** para mensagens de broadcast e tiros, e **TCP** para confirmações de acerto, destruição e sincronização entre jogadores.

---

## Estrutura do Projeto
```
Batalha-Naval-P2P/
│
├── app/
│   ├── __init__.py
│   ├── main.py                    # Ponto de entrada da aplicação
│   │
│   ├── config/
│   │   └── ships.json             # Especificações dos navios
│   │
│   ├── network/
│   │   ├── __init__.py
│   │   ├── connection.py          # Interface de conexão
│   │   ├── tcpConnection.py       # Implementação TCP
│   │   ├── udpConnection.py       # Implementação UDP
│   │   └── peerService.py         # Serviço P2P principal
│   │
│   ├── game/
│   │   ├── __init__.py
│   │   ├── ship.py                # Classe Ship
│   │   ├── gameController.py      # Lógica do jogo
│   │   └── gameInterface.py       # Interface do usuário
│   │
│   └── utils/
│       ├── __init__.py
│       └── ship_loader.py         # Carregador de especificações de navios
│   
├── README.md
└── requirements.txt
```
---

## Funcionalidades

- Criação automática de sockets UDP (porta `5000`) e TCP (porta `5001`)
- Broadcast UDP de **conexão inicial**
- Envio e recebimento de mensagens no formato:
  - `shot:{x},{y}`
  - `hit`
  - `destroyed`
  - `lost`
  - `saindo`
- Atualização dinâmica da lista de jogadores conectados
- Controle da **grid 10x10**, com posicionamento manual ou aleatório dos navios
- Exibição formatada do tabuleiro e do placar no terminal
- Loop automático enviando tiros a cada 10 segundos

---

