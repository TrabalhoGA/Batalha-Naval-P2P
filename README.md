# Batalha Naval P2P

Projeto desenvolvido para a disciplina **Redes de Computadores: Aplicação e Transporte**.  
Implementa uma **versão distribuída** do clássico jogo *Batalha Naval* utilizando **sockets TCP e UDP**, em um modelo **peer-to-peer (P2P)**.

---

## Objetivo

O objetivo é aplicar os conceitos de **camadas de aplicação e transporte**, utilizando **protocolo UDP** para mensagens de broadcast e tiros, e **TCP** para confirmações de acerto, destruição e sincronização entre jogadores.

---

## Estrutura do Projeto
```
batalha_naval/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── network/
│   │   ├── __init__.py
│   │   ├── Connection.py
│   │   ├── TCPConnection.py
│   │   ├── UDPConnection.py
│   │   ├── messageService.py
│   │   └── peerService.py
│   │
│   └── game/
│       ├── __init__.py
│       ├── board.py
│       ├── ship.py
│       ├── player.py
│       ├── gameController.py
│       └── gameInterface.py
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

