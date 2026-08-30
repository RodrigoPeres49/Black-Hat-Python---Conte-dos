import socket 

target_host = "www.google.com"
target_port = 80

# CRIAR O OBJETO SOCKET COM OS PARÂMETROS AF_INET (indica que utilizaremos um endereço ou nome de host IPv4) E SOCK_STREAM (indica que será um cliente TCP)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#CONECTAR O CLIENTE
client.connect((target_host,target_port))

# ENVIAR ALGUNS DADOS
client.send(b"GET / HTTP/1.1\r\nHost: google.com\r\n\r\n")

# RECEBER ALGUNS DADOS
response = client.recv(4096)

print(response.decode())
client.close