import argparse
import socket


class NetCat:

    def __init__(self, args):
        self.args = args

        # Cria um socket TCP/IP
        self.socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        # Permite reutilizar a porta rapidamente
        self.socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )

    def run(self):

        # Se -l foi utilizado, somos o servidor
        if self.args.listen:
            self.listen()

        # Caso contrário, somos o cliente
        else:
            self.connect()


    # ==========================================================
    # SERVIDOR
    # ==========================================================

    def listen(self):

        # Vincula o socket ao IP e à porta
        self.socket.bind(
            (self.args.target, self.args.port)
        )

        # Coloca o socket em modo de escuta
        self.socket.listen(1)

        print(
            f"[+] Servidor ouvindo em "
            f"{self.args.target}:{self.args.port}"
        )

        print("[+] Aguardando conexão...")

        # Aguarda um cliente se conectar
        client_socket, client_address = self.socket.accept()

        print(
            f"[+] Cliente conectado: "
            f"{client_address[0]}:{client_address[1]}"
        )

        # Começa a comunicação
        self.handle_client(client_socket)


    def handle_client(self, client_socket):

        while True:

            # Recebe uma mensagem do cliente
            data = client_socket.recv(4096)

            # Se não recebeu nada, o cliente fechou a conexão
            if not data:
                print("[!] Cliente encerrou a conexão.")
                break

            # Converte bytes para texto
            message = data.decode("utf-8")

            print(f"\nCliente: {message}")

            # Pergunta ao servidor o que deseja responder
            response = input("Servidor: ")

            # Se o usuário digitar sair, encerra
            if response.lower() == "sair":
                client_socket.send(
                    b"O servidor encerrou a conexao."
                )
                break

            # Envia a resposta
            client_socket.send(
                response.encode("utf-8")
            )

        client_socket.close()
        self.socket.close()

        print("[+] Conexão encerrada.")


    # ==========================================================
    # CLIENTE
    # ==========================================================

    def connect(self):

        print(
            f"[+] Conectando em "
            f"{self.args.target}:{self.args.port}..."
        )

        # Conecta ao servidor
        self.socket.connect(
            (self.args.target, self.args.port)
        )

        print("[+] Conectado ao servidor!")
        print("[+] Digite 'sair' para encerrar.\n")

        # Começa a comunicação
        self.handle_server()


    def handle_server(self):

        while True:

            # Digita uma mensagem
            message = input("Cliente: ")

            # Envia a mensagem para o servidor
            self.socket.send(
                message.encode("utf-8")
            )

            # Se digitou sair, encerra
            if message.lower() == "sair":
                break

            # Aguarda a resposta do servidor
            data = self.socket.recv(4096)

            if not data:
                print("[!] Servidor encerrou a conexão.")
                break

            # Converte bytes para texto
            response = data.decode("utf-8")

            print(f"Servidor: {response}")

        self.socket.close()

        print("[+] Conexão encerrada.")


# ==============================================================
# PROGRAMA PRINCIPAL
# ==============================================================

if __name__ == "__main__":

    # Cria o parser de argumentos
    parser = argparse.ArgumentParser(
        description="NetCat TCP simples para estudo"
    )

    # -l = servidor
    parser.add_argument(
        "-l",
        "--listen",
        action="store_true",
        help="iniciar como servidor"
    )

    # -t = endereço
    parser.add_argument(
        "-t",
        "--target",
        default="127.0.0.1",
        help="endereco IP"
    )

    # -p = porta
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=5555,
        help="porta TCP"
    )

    # Lê os argumentos
    args = parser.parse_args()

    # Cria o objeto NetCat
    nc = NetCat(args)

    # Inicia o programa
    nc.run()