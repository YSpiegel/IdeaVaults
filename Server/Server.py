import socket, pickle, re
import DBHandle
import ObjManagement as obj
import threading as th

IP = "127.0.0.1"
PORT = 7891


def adduser(data, client):
    """
    Tries to add a new user to the db
    If is unique and valid, user is added
    :param data: New User info
    :param client: Client object
    :return:
    """
    name, email, password = data
    new_name = DBHandle.check_if_new(name)
    new_email = DBHandle.check_if_new(email)
    valid_name = re.match(r'^[a-zA-Z0-9_ ]{4,20}$', name) != None

    client.send(pickle.dumps((new_name, new_email, valid_name)))
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
    identifier, password = data
    name = DBHandle.sign_in(identifier, password)
    client.send(name.encode())


def register_user(data, client):
    """
    Registers an entry of a user to the system
    :param data: Username and IP
    :param client: Client object
    :return:
    """
    name, ip = data
    already_connected = DBHandle.check_if_connected(name)
    if not already_connected:
        DBHandle.add_ip(name, ip)
    client.send(str(already_connected).encode())


def search_addr(user_ip, client):
    """
    Looks for a user that's already connected
    :param user_ip: User IP
    :param client: Client object
    :return:
    """
    user = DBHandle.find_by_addr(user_ip)
    if user:
        client.send(user['name'].encode())
    else:
        client.send("@".encode())


def search_vault(vault_title, client):
    """
    Looks for a vault by its title
    :param data: Vault title
    :param client: Client object
    :return:
    """
    vault = DBHandle.find_by_title(vault_title)
    if vault:
        client.send(pickle.dumps(obj.Vault(vault['title'], vault['user'], vault['description'], vault['type'])))
    else:
        client.send("@".encode())


def remove_ip(ip, client):
    """
    Disconnects a user by removing the IP field
    :param ip: address to disconnect
    :param client: Client object
    :return:
    """
    user = DBHandle.find_by_addr(ip)
    if user:
        DBHandle.remove_ip(user['name'])


def get_vaults_by_type(data, client):
    """
    Passes all private vaults of a certain user
    :param data: user and type
    :param client: Client object
    :return:
    """
    pvaults = DBHandle.get_vaults_by_type(*data)
    for vault in pvaults:
        vault_obj = obj.Vault(vault['title'], vault['user'], vault['description'], vault['type'])
        client.send(pickle.dumps(vault_obj))
        confirm = client.recv(1024).decode()
        if confirm != "next":
            return
    client.send(b'@')


def add_vault(vault, client):
    """
    Create a new vault for a client
    :param vault: vault obj
    :param client: Client Object
    :return:
    """
    if not DBHandle.check_if_new_vault(vault):
        client.send("ChangeTitle".encode())

    DBHandle.add_vault(vault)
    client.send("OK".encode())


def update_description(data, client):
    DBHandle.update_description(*data)


def get_desc(data, client):
    vault = DBHandle.get_vault(*data)
    client.send(vault['description'].encode())


def gems_by_vault(vault, client):
    gems = DBHandle.get_gems(vault)
    for gem in gems:
        gem_obj = obj.Gem(gem['vault'], gem['user'], gem['title'], gem['content'])
        client.send(pickle.dumps(gem_obj))
        confirm = client.recv(1024).decode()
        if confirm != "next":
            return
    client.send(b'@')


def add_gem_to_vault(data, client):
    DBHandle.add_new_gem(*data)
    #client.send(pickle.dumps(new_gem))


def check_new_gem_title(data, client):
    response = '200' if DBHandle.check_if_new_gem(*data) else '409'
    client.send(response.encode())


def delete_gem_from_vault(data, client):
    pass


def act(action, data, client):
    actions = {"adduser": adduser,
               "sign-in": sign_in,
               "register-user": register_user,
               "get-user-by-addr": search_addr,
               "remove-ip": remove_ip,
               "get-vaults-by-type": get_vaults_by_type,
               "add-vault": add_vault,
               "get-vault-by-title": search_vault,
               "update-vault-desc": update_description,
               "find-desc": get_desc,
               "get-gems-by-vault": gems_by_vault,
               "delete-gem-from-vault": delete_gem_from_vault,
               "add-gem-to-vault": add_gem_to_vault,
               "check-new-gem-title": check_new_gem_title}

    actions[action](data, client)


def main():
    server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server_socket.bind((IP,PORT))
    server_socket.listen()

    while True:
        client, ip = server_socket.accept()
        action, data = pickle.loads(client.recv(1024))
        thread = th.Thread(target=act, args=(action, data, client))
        thread.start()


if __name__ == "__main__":
    main()
    # search_addr("127.0.0.1", 1)
