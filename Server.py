import socket
import threading
import DBHandle
import re

IP = "192.168.1.113"
PORT = 5900



def adduser(data, client):
    name, email, password = data.split(":")
    new_name = DBHandle.check_if_new(name)
    new_email = DBHandle.check_if_new(email)
    valid_name = re.match(r'^[a-zA-Z0-9_]{4,20}$', name) != None

    client.send(f"{new_name}:{new_email}:{valid_name}".encode())
    if new_name and new_email and valid_name:
        DBHandle.add_new(name, email, password)


def sign_in(data, client):
    identifier, password = data.split(":")
    name = DBHandle.sign_in(identifier, password)
    client.send(name.encode())


def register_user(data, client):
    name, ip = data.split(":")
    DBHandle.add_ip(name, ip)


def search_addr(data, client):
    user = DBHandle.find_by_addr(data)
    if user:
        client.send(user['name'].encode())
    else:
        client.send("@".encode())


def remove_ip(data, client):
    ip_address = data
    user = DBHandle.find_by_addr(ip_address)
    if user:
        DBHandle.remove_ip(user['name'])


actions = {"adduser": adduser,
           "sign-in": sign_in,
           "register-user": register_user,
           "get-user-by-addr": search_addr,
           "remove-ip": remove_ip}


def main():
    server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server_socket.bind((IP,PORT))
    server_socket.listen()

    while True:
        client, ip = server_socket.accept()
        action, data = client.recv(1024).decode().split(';')
        actions[action](data, client)


if __name__ == "__main__":
    main()
    #search_addr("127.0.0.1", 1)