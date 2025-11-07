import socket
import threading

# Função para receber mensagens
def receber(conexao):
    while True:
        try:
            msg = conexao.recv(1024).decode()
            if not msg:
                break
            print(f"\n[Peer] {msg}")
        except:
            break

def main():
    mode = input("Deseja hospedar ou conectar-se a um servidor? (h/c): ")

    if mode.lower() == 'h':
        # Modo Servidor
        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servidor.bind(("0.0.0.0", 5000))
        servidor.listen(1)
        print("Aguardando conexões na porta 5000...")
        conexao, endereco = servidor.accept()   
        print(f"Conectado a {endereco}")
    else:
        # Modo Cliente
        ip = input("Digite o IP do servidor: ")
        conexao = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conexao.connect((ip, 5000))
        print(f"Conectado ao servidor {ip}:5000")

    threading.Thread(target=receber, args=(conexao,), daemon=True).start()

    # Enviar mensagens
    while True:
        msg = input("Você: ")
        if msg.lower() == "/sair":
            break
        conexao.send(msg.encode())

    conexao.close()

if __name__ == "__main__":
    main()