#!/usr/bin/env python3


import sys
# Permite acessar argumentos passados pela linha de comando.
# Exemplo:
# python3 proxy.py 127.0.0.1 9000 ftp.sun.ac.za 21 True
#
# Nesse caso, sys.argv conterá esses valores.

import socket
# Biblioteca responsável pela comunicação de rede através de sockets.
#
# É ela que permite:
# - criar conexões TCP;
# - conectar ao servidor;
# - receber dados;
# - enviar dados;
# - abrir uma porta para receber conexões.

import threading
# Permite criar threads.
#
# Isso permite que o proxy atenda vários clientes ao mesmo tempo,
# sem precisar esperar uma conexão terminar para aceitar outra.


# ============================================================
# CONFIGURAÇÃO DO HEXDUMP
# ============================================================

HEX_FILTER = ''.join(
    [(len(repr(chr(i))) == 3) and chr(i) or '.' for i in range(256)]
)

# Essa variável cria uma tabela usada pela função hexdump().
#
# A ideia é:
#
#   bytes imprimíveis -> mostrar o caractere
#   bytes não imprimíveis -> mostrar "."
#
# Por exemplo, uma mensagem como:
#
# b"USER admin\r\n"
#
# poderá ser exibida aproximadamente assim:
#
# 55 53 45 52 20 61 64 6D 69 6E ...
#
# USER admin
#
# Isso é muito útil para observar o que está passando pelo proxy.


# ============================================================
# FUNÇÃO HEXDUMP
# ============================================================

def hexdump(src, length=16, show=True):
    """
    Exibe dados em hexadecimal e caracteres imprimíveis.

    src:
        Dados que queremos visualizar.

    length:
        Quantidade de bytes mostrados por linha.

    show:
        Se True, imprime na tela.
        Se False, retorna uma lista de linhas.
    """

    # --------------------------------------------------------
    # CONVERSÃO DE BYTES PARA STRING
    # --------------------------------------------------------

    if isinstance(src, bytes):

        # Verifica se src é do tipo bytes.
        #
        # Dados recebidos de um socket normalmente são bytes.
        #
        # Exemplo:
        #
        # b"USER anonymous\r\n"

        try:

            # Tenta transformar os bytes em texto.
            #
            # errors="replace" significa:
            # se existir algum byte que não possa ser convertido,
            # ele será substituído por um caractere de substituição
            # em vez de gerar um erro.

            src = src.decode(errors="replace")

        except Exception:

            # Se alguma coisa inesperada acontecer durante
            # a conversão, transforma o objeto em string.

            src = str(src)


    # Lista onde serão armazenadas as linhas do hexdump.

    results = []


    # --------------------------------------------------------
    # PERCORRE OS DADOS EM BLOCOS
    # --------------------------------------------------------

    for i in range(0, len(src), length):

        # Divide os dados em blocos de "length" caracteres.
        #
        # Se length = 16:
        #
        # bloco 1 -> bytes 0-15
        # bloco 2 -> bytes 16-31
        # bloco 3 -> bytes 32-47
        # etc.

        word = str(src[i:i + length])


        # ----------------------------------------------------
        # PARTE ASCII
        # ----------------------------------------------------

        printable = word.translate(HEX_FILTER)

        # Substitui caracteres não imprimíveis por ".".
        #
        # Isso facilita enxergar mensagens de protocolos
        # como FTP, HTTP, etc.


        # ----------------------------------------------------
        # PARTE HEXADECIMAL
        # ----------------------------------------------------

        hexa = ' '.join([f"{ord(c):02X}" for c in word])

        # Converte cada caractere para seu valor hexadecimal.
        #
        # Exemplo:
        #
        # "A" -> 41
        # "B" -> 42
        # " " -> 20
        #
        # Então:
        #
        # "ABC" -> "41 42 43"


        # Define a largura reservada para a coluna hexadecimal.

        hexwidth = length * 3


        # Monta uma linha completa do hexdump.

        results.append(
            f"{i:04x}   {hexa:<{hexwidth}}   {printable}"
        )

        # O resultado terá aproximadamente esta aparência:
        #
        # 0000   55 53 45 52 20 61 64 6D 69 6E   USER admin
        #
        # 0010   ...
        #
        # O número da esquerda representa o offset,
        # ou seja, a posição dentro dos dados.


    # --------------------------------------------------------
    # MOSTRAR O RESULTADO
    # --------------------------------------------------------

    if show:

        # Se show=True, imprime cada linha.

        for line in results:
            print(line)

    else:

        # Se show=False, retorna a lista para quem chamou
        # a função.

        return results


# ============================================================
# RECEBER DADOS DO SOCKET
# ============================================================

def receive_from(connection, timeout=5):
    """
    Recebe dados de um socket até ocorrer timeout
    ou até o outro lado fechar a conexão.
    """

    # Começamos com um buffer vazio.

    buffer = b""


    # Define quanto tempo o socket pode ficar esperando
    # por dados antes de gerar socket.timeout.

    connection.settimeout(timeout)


    try:

        # Continua recebendo dados.

        while True:

            # Tenta receber até 4096 bytes.

            data = connection.recv(4096)


            # Se recv() retornar bytes vazios,
            # significa que o outro lado encerrou a conexão.

            if not data:
                break


            # Adiciona os dados recebidos ao buffer.

            buffer += data


    except socket.timeout:

        # O tempo limite acabou.
        #
        # Isso não necessariamente significa que houve erro.
        #
        # O proxy simplesmente para de esperar novos dados.

        pass


    except ConnectionError as e:

        # Erros relacionados à conexão.

        print(f"[!] Erro recebendo dados: {e}")


    except OSError as e:

        # Outros erros relacionados ao socket.

        print(f"[!] Erro no socket: {e}")


    # Retorna tudo que foi recebido.

    return buffer


# ============================================================
# MODIFICAR REQUISIÇÕES DO CLIENTE
# ============================================================

def request_handler(buffer):
    """
    Função responsável por modificar dados enviados
    pelo cliente antes de chegarem ao servidor.
    """

    # Atualmente não modifica nada.

    return buffer

    # Futuramente você poderia colocar alguma lógica aqui.
    #
    # Exemplo conceitual:
    #
    # buffer = buffer.replace(...)
    #
    # return buffer


# ============================================================
# MODIFICAR RESPOSTAS DO SERVIDOR
# ============================================================

def response_handler(buffer):
    """
    Função responsável por modificar dados enviados
    pelo servidor antes de chegarem ao cliente.
    """

    # Atualmente também não modifica nada.

    return buffer


# ============================================================
# FUNÇÃO PRINCIPAL DO PROXY
# ============================================================

def proxy_handler(client_socket, remote_host, remote_port, receive_first):
    """
    Faz a intermediação:

        CLIENTE
           |
           v
         PROXY
           |
           v
       SERVIDOR

    E também no sentido contrário.
    """

    # --------------------------------------------------------
    # CRIA SOCKET PARA O SERVIDOR REMOTO
    # --------------------------------------------------------

    remote_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    # socket.AF_INET
    #
    # Indica que estamos usando IPv4.
    #
    #
    # socket.SOCK_STREAM
    #
    # Indica TCP.


    try:

        # ----------------------------------------------------
        # CONECTA AO SERVIDOR REMOTO
        # ----------------------------------------------------

        print(
            f"[*] Conectando ao servidor remoto "
            f"{remote_host}:{remote_port}"
        )

        # Faz a conexão TCP com o servidor remoto.

        remote_socket.connect(
            (remote_host, remote_port)
        )

        print("[*] Conectado ao servidor remoto.")


        # ----------------------------------------------------
        # RECEIVE FIRST
        # ----------------------------------------------------

        if receive_first:

            # Alguns protocolos fazem o servidor enviar dados
            # imediatamente após a conexão.
            #
            # O FTP é um exemplo.
            #
            # Ao conectar em um servidor FTP, normalmente
            # recebemos algo semelhante a:
            #
            # 220 Welcome to ...
            #
            # Nesse caso precisamos receber essa mensagem
            # antes de esperar o cliente enviar alguma coisa.

            remote_buffer = receive_from(remote_socket)


            # Se recebemos alguma coisa:

            if remote_buffer:

                print(
                    f"[<==] Recebido "
                    f"{len(remote_buffer)} bytes "
                    f"do servidor remoto."
                )


                # Mostra os dados recebidos em hexadecimal
                # e ASCII.

                hexdump(remote_buffer)


                # Passa a resposta pela função que poderia
                # modificar os dados.

                remote_buffer = response_handler(remote_buffer)


                # Se ainda existem dados depois do processamento:

                if remote_buffer:

                    # Envia os dados para o cliente.

                    client_socket.sendall(remote_buffer)

                    print("[<==] Enviado para o cliente.")


        # ====================================================
        # LOOP PRINCIPAL
        # ====================================================

        while True:

            # ------------------------------------------------
            # 1. RECEBE DADOS DO CLIENTE
            # ------------------------------------------------

            local_buffer = receive_from(client_socket)


            # Se não recebeu nada:

            if not local_buffer:

                print(
                    "[*] Cliente encerrou a conexão."
                )

                break


            # Mostra quantos bytes chegaram.

            print(
                f"[==>] Recebido "
                f"{len(local_buffer)} bytes do cliente."
            )


            # Mostra os dados em hexadecimal.

            hexdump(local_buffer)


            # ------------------------------------------------
            # 2. PROCESSA A REQUISIÇÃO
            # ------------------------------------------------

            local_buffer = request_handler(local_buffer)

            # Aqui poderíamos modificar a requisição
            # antes de enviá-la ao servidor.


            # ------------------------------------------------
            # 3. ENVIA PARA O SERVIDOR
            # ------------------------------------------------

            if local_buffer:

                remote_socket.sendall(local_buffer)

                print(
                    "[==>] Enviado para o servidor remoto."
                )


            # ------------------------------------------------
            # 4. RECEBE RESPOSTA DO SERVIDOR
            # ------------------------------------------------

            remote_buffer = receive_from(remote_socket)


            # Se o servidor não enviou nada:

            if not remote_buffer:

                print(
                    "[*] Servidor remoto encerrou a conexão."
                )

                break


            # Mostra quantos bytes foram recebidos.

            print(
                f"[<==] Recebido "
                f"{len(remote_buffer)} bytes "
                f"do servidor remoto."
            )


            # Mostra os dados em hexadecimal.

            hexdump(remote_buffer)


            # ------------------------------------------------
            # 5. PROCESSA A RESPOSTA
            # ------------------------------------------------

            remote_buffer = response_handler(remote_buffer)


            # ------------------------------------------------
            # 6. ENVIA A RESPOSTA PARA O CLIENTE
            # ------------------------------------------------

            if remote_buffer:

                client_socket.sendall(remote_buffer)

                print(
                    "[<==] Enviado para o cliente."
                )


    # ========================================================
    # TRATAMENTO DE ERROS
    # ========================================================

    except ConnectionRefusedError:

        # O servidor recusou a conexão.

        print(
            f"[!!] Conexão recusada por "
            f"{remote_host}:{remote_port}"
        )


    except socket.gaierror as e:

        # O Python não conseguiu resolver o hostname.
        #
        # Exemplo:
        #
        # ftp.sun.ac.za
        #
        # precisa ser convertido para um endereço IP.

        print(
            f"[!!] Não foi possível resolver "
            f"'{remote_host}': {e}"
        )


    except socket.timeout:

        # Timeout durante a comunicação.

        print(
            f"[!!] Timeout conectando a "
            f"{remote_host}:{remote_port}"
        )


    except OSError as e:

        # Outros erros relacionados ao sistema/socket.

        print(
            f"[!!] Erro de socket: {e}"
        )


    except Exception as e:

        # Captura outros erros que não foram previstos.

        print(
            f"[!!] Erro no proxy: {e}"
        )


    finally:

        # ====================================================
        # FECHAMENTO DOS SOCKETS
        # ====================================================

        try:

            # Fecha conexão com o cliente.

            client_socket.close()

        except Exception:

            pass


        try:

            # Fecha conexão com o servidor remoto.

            remote_socket.close()

        except Exception:

            pass


        print("[*] Conexões encerradas.")


# ============================================================
# SERVIDOR DO PROXY
# ============================================================

def server_loop(
    local_host,
    local_port,
    remote_host,
    remote_port,
    receive_first
):
    """
    Cria o socket que ficará aguardando conexões
    dos clientes.
    """

    # --------------------------------------------------------
    # CRIA SOCKET DO SERVIDOR
    # --------------------------------------------------------

    server = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    # Novamente:
    #
    # AF_INET    -> IPv4
    # SOCK_STREAM -> TCP


    # --------------------------------------------------------
    # SO_REUSEADDR
    # --------------------------------------------------------

    server.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    # Permite reutilizar a porta rapidamente depois
    # de o programa ser encerrado.
    #
    # Isso é útil durante testes.
    #
    # Sem essa opção, às vezes o sistema pode manter
    # a porta temporariamente em estado TIME_WAIT.


    try:

        # ----------------------------------------------------
        # VINCULA O SOCKET AO IP E PORTA
        # ----------------------------------------------------

        server.bind(
            (local_host, local_port)
        )

        # Exemplo:
        #
        # local_host = 127.0.0.1
        # local_port = 9000
        #
        # O proxy ficará ouvindo:
        #
        # 127.0.0.1:9000


        # ----------------------------------------------------
        # COMEÇA A OUVIR
        # ----------------------------------------------------

        server.listen(5)

        # O número 5 indica o tamanho do backlog.
        #
        # É a quantidade de conexões que podem ficar
        # aguardando para serem aceitas.


    except PermissionError:

        # Geralmente acontece quando tentamos abrir
        # uma porta privilegiada (< 1024) sem permissão.

        print(
            f"[!!] Permissão negada ao abrir "
            f"{local_host}:{local_port}."
        )

        print(
            "[!!] Portas abaixo de 1024 normalmente "
            "exigem sudo."
        )

        sys.exit(1)


    except OSError as e:

        # Outros problemas ao abrir a porta.

        print(
            f"[!!] Falha ao ouvir em "
            f"{local_host}:{local_port}"
        )

        print(
            f"[!!] Motivo: {e}"
        )

        print(
            "[!!] Verifique se o IP pertence a esta "
            "máquina e se a porta está livre."
        )

        sys.exit(1)


    # --------------------------------------------------------
    # INFORMAÇÕES DO PROXY
    # --------------------------------------------------------

    print(
        f"[*] Ouvindo em "
        f"{local_host}:{local_port}"
    )

    print(
        f"[*] Encaminhando para "
        f"{remote_host}:{remote_port}"
    )

    print(
        f"[*] receive_first = {receive_first}"
    )

    print(
        "[*] Aguardando uma conexão...\n"
    )


    # ========================================================
    # ACEITAR CLIENTES
    # ========================================================

    try:

        while True:

            # ------------------------------------------------
            # ESPERA UM CLIENTE
            # ------------------------------------------------

            client_socket, addr = server.accept()

            # server.accept() fica bloqueado esperando alguém
            # se conectar.
            #
            # Quando alguém conecta, retorna:
            #
            # client_socket -> socket daquela conexão
            # addr          -> IP e porta do cliente
            #
            # Exemplo:
            #
            # ('192.168.1.50', 54321)


            print(
                f"[+] Conexão de entrada recebida "
                f"de {addr[0]}:{addr[1]}"
            )


            # ------------------------------------------------
            # CRIA UMA THREAD PARA O CLIENTE
            # ------------------------------------------------

            proxy_thread = threading.Thread(
                target=proxy_handler,

                args=(
                    client_socket,
                    remote_host,
                    remote_port,
                    receive_first
                ),

                daemon=True
            )

            # target=proxy_handler
            #
            # Diz qual função a thread deverá executar.
            #
            #
            # args=(...)
            #
            # São os argumentos enviados para proxy_handler().
            #
            #
            # daemon=True
            #
            # Faz a thread ser encerrada quando o programa
            # principal terminar.


            # Inicia a thread.

            proxy_thread.start()


    except KeyboardInterrupt:

        # Permite encerrar o proxy usando:
        #
        # CTRL + C

        print(
            "\n[*] Proxy encerrado pelo usuário."
        )


    finally:

        # Fecha o socket que estava aceitando conexões.

        server.close()


# ============================================================
# FUNÇÃO MAIN
# ============================================================

def main():

    # A função main() é responsável por interpretar
    # os argumentos da linha de comando.


    # --------------------------------------------------------
    # PEGA OS ARGUMENTOS
    # --------------------------------------------------------

    args = sys.argv[1:]

    # sys.argv contém:
    #
    # [0] -> nome do programa
    # [1] -> primeiro argumento
    # [2] -> segundo argumento
    # etc.
    #
    # Como não queremos o nome do programa,
    # usamos [1:].


    # ========================================================
    # FORMA COM 4 ARGUMENTOS
    # ========================================================

    if len(args) == 4:

        local_host = args[0]

        local_port = args[1]

        remote_host = args[2]

        # Quando são fornecidos apenas 4 argumentos,
        # assumimos que o servidor remoto usa FTP na porta 21.

        remote_port = "21"

        receive_first = args[3]


    # ========================================================
    # FORMA COM 5 ARGUMENTOS
    # ========================================================

    elif len(args) == 5:

        local_host = args[0]

        local_port = args[1]

        remote_host = args[2]

        remote_port = args[3]

        receive_first = args[4]


    # ========================================================
    # QUANTIDADE INCORRETA DE ARGUMENTOS
    # ========================================================

    else:

        print("Uso:")

        print(
            "  sudo python3 proxy.py "
            "LOCAL_IP LOCAL_PORT REMOTE_HOST "
            "REMOTE_PORT TRUE/FALSE"
        )

        print()

        print(
            "Ou, para FTP na porta 21:"
        )

        print(
            "  sudo python3 proxy.py "
            "LOCAL_IP LOCAL_PORT REMOTE_HOST TRUE/FALSE"
        )

        print()

        print("Exemplos:")

        print(
            "  sudo python3 proxy.py "
            "127.0.0.1 9000 ftp.sun.ac.za 21 True"
        )

        print(
            "  sudo python3 proxy.py "
            "192.168.1.203 21 ftp.sun.ac.za 21 True"
        )

        print(
            "  sudo python3 proxy.py "
            "192.168.1.203 21 ftp.sun.ac.za True"
        )

        # Encerra o programa informando erro.

        sys.exit(1)


    # ========================================================
    # CONVERTER PORTAS PARA INTEGER
    # ========================================================

    try:

        local_port = int(local_port)

        remote_port = int(remote_port)

        # Os argumentos da linha de comando sempre chegam
        # como strings.
        #
        # Exemplo:
        #
        # "21"
        #
        # Precisamos transformar em:
        #
        # 21
        #
        # porque socket utiliza números para representar portas.


    except ValueError:

        # Caso alguém coloque algo como:
        #
        # abc
        #
        # em vez de:
        #
        # 21

        print(
            "[!!] LOCAL_PORT e REMOTE_PORT "
            "precisam ser números."
        )

        sys.exit(1)


    # ========================================================
    # CONVERTE TRUE/FALSE PARA BOOLEAN
    # ========================================================

    receive_first = receive_first.lower() in (
        "true",
        "1",
        "yes",
        "sim"
    )

    # Aqui transformamos strings em True ou False.
    #
    # Exemplos:
    #
    # "True"  -> True
    # "true"  -> True
    # "1"     -> True
    # "yes"   -> True
    # "sim"   -> True
    #
    # Qualquer outra coisa:
    #
    # "false" -> False
    # "abc"   -> False


    # ========================================================
    # INICIA O SERVIDOR DO PROXY
    # ========================================================

    server_loop(
        local_host,
        local_port,
        remote_host,
        remote_port,
        receive_first
    )

    # Aqui finalmente iniciamos o proxy.


# ============================================================
# PONTO DE ENTRADA DO PROGRAMA
# ============================================================

if __name__ == "__main__":

    # Essa condição verifica se o arquivo foi executado
    # diretamente.
    #
    # Exemplo:
    #
    # python3 proxy.py ...
    #
    # Nesse caso:
    #
    # __name__ == "__main__"
    #
    # será verdadeiro.
    #
    # Então chamamos main().

    main()