import socket, re
import DBHandle
import ObjManagement as obj

IP = "127.0.0.1"
PORT = 6010


def adduser(data, client):
    """
    Tries to add a new user to the db
    If is unique and valid, user is added
    :param data: New User info
    :param client: Client object
    :return:
    """
    name, email, password = data.split(":")
    new_name = DBHandle.check_if_new(name)
    new_email = DBHandle.check_if_new(email)
    valid_name = re.match(r'^[a-zA-Z0-9_ ]{4,20}$', name) != None

    client.send(f"{new_name}:{new_email}:{valid_name}".encode())
    if new_name and new_email and valid_name:
        DBHandle.add_new(name, email, password)


def sign_in(data, client):
    """
    Tries to sign in a user to the system
    and sends back the user's name
    If unable to, sends back '@' as name
    :param data: User identifier and password
    :param client: Client object
    :return:
    """
    identifier, password = data.split(":")
    name = DBHandle.sign_in(identifier, password)
    client.send(name.encode())


def register_user(data, client):
    """
    Registers an entry of a user to the system
    :param data: Username and IP
    :param client: Client object
    :return:
    """
    name, ip = data.split(":")
    already_connected = DBHandle.check_if_connected(name)
    if not already_connected:
        DBHandle.add_ip(name, ip)
    client.send(str(already_connected).encode())


def search_addr(data, client):
    """
    Looks for a user that's already connected
    :param data: User IP
    :param client: Client object
    :return:
    """
    user = DBHandle.find_by_addr(data)
    if user:
        client.send(user['name'].encode())
    else:
        client.send("@".encode())

def search_vault(data, client):
    """
    Looks for a vault by its title
    :param data: Vault title
    :param client: Client object
    :return:
    """
    vault = DBHandle.find_by_title(data)
    if vault:
        client.send(str(obj.Vault(vault['title'], vault['user'], vault['description'], vault['type'])).encode())
    else:
        client.send("@".encode())

def remove_ip(data, client):
    """
    Disconnects a user by removing the IP field
    :param data: User to disconnect
    :param client: Client object
    :return:
    """
    ip_address = data
    user = DBHandle.find_by_addr(ip_address)
    if user:
        DBHandle.remove_ip(user['name'])


def get_private_vaults(data, client):
    """
    Passes all private vaults of a certain user
    :param data: User
    :param client: Client object
    :return:
    """
    pvaults = DBHandle.get_private_vaults(data)
    for vault in pvaults:
        vault_obj = obj.Vault(vault['title'], vault['user'], vault['description'], vault['type'])
        client.send(str(vault_obj).encode())
        confirm = client.recv(1024).decode()
        if confirm != "next":
            return
    client.send('@'.encode())


def get_shared_vaults(data, client):
    """
    Passes all shared vaults of a certain user
    :param data: User
    :param client: Client object
    :return:
    """
    pvaults = DBHandle.get_shared_vaults(data)
    for vault in pvaults:
        vault_obj = obj.Vault(vault['title'], vault['user'], vault['description'], vault['type'])
        client.send(str(vault_obj).encode())
        confirm = client.recv(1024).decode()
        if confirm != "next":
            return
    client.send('@'.encode())


def add_vault(data, client):
    """
    Create a new vault for a client
    :param data: vault string obj
    :param client: Client Object
    :return:
    """
    vault = obj.fromstr(data)
    if not DBHandle.check_if_new_vault(vault.title, vault.user):
        client.send("ChangeTitle".encode())

    DBHandle.add_vault(vault)
    client.send("OK".encode())


actions = {"adduser": adduser,
           "sign-in": sign_in,
           "register-user": register_user,
           "get-user-by-addr": search_addr,
           "remove-ip": remove_ip,
           "get-private-vaults": get_private_vaults,
           "get-shared-vaults": get_shared_vaults,
           "add-vault": add_vault,
           "get-vault-by-title": search_vault}


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
    # search_addr("127.0.0.1", 1)
