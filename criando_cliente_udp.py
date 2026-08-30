import socket 

target_host = "127.0.0.1"
target_port = 9997

# CRIAR UM OBJETO SOCKET UTILIZANDO AGORA O SOCK_DGRAM PARA UTILIZARMOS O SOCKET UDP COM O AF_INET UTLIZANDO O IPV4

client = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

# ASSOCIANDO O SOCKET A PORTA 9997

client.bind((target_host, target_port))

# ENVIAR ALGUNS DADOS

print("Servidor UDP aguardando dados...")

client.sendto(b"AAABBBCCC",(target_host,target_port))

# RECEBER ALGUNS DADOS

data, addr = client.recvfrom(4096)

print("Recebi:", data.decode())
print("De:", addr)

client.sendto(b"Mensagem recebida!", addr)

print(data.decode())
client.close()