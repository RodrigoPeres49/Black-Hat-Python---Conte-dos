import socket 

target_host = "127.0.0.1"
target_port = 9997

# CRIAR UM OBJETO SOCKET

client = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

# ENVIAR ALGUNS DADOS

client.bind(("127.0.0.1", 9997))

print("Servidor UDP aguardando dados...")

client.sendto(b"AAABBBCCC",(target_host,target_port))

# RECEBER ALGUNS DADOS

data, addr = client.recvfrom(4096)

print("Recebi:", data.decode())
print("De:", addr)

client.sendto(b"Mensagem recebida!", addr)

print(data.decode())
client.close()