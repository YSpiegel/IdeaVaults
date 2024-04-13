import socket, pickle, re
import DBHandle
import ObjManagement as obj
import threading as th

IP = "192.168.1.113"
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
    :param data: Username and MAC
    :param client: Client object
    :return:
    """
    name, mac = data
    already_connected = DBHandle.check_if_connected(name)
    if not already_connected:
        DBHandle.add_mac(name, mac)
    client.send(str(already_connected).encode())


def search_addr(user_mac, client):
    """
    Looks for a user that's already connected
    :param user_mac: User MAC
    :param client: Client object
    :return:
    """
    user = DBHandle.find_by_addr(user_mac)
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
        if vault['type'] == 'shared':
            if 'pending' in vault:
                vault_obj = obj.Vault(vault['title'], vault['owner'], vault['description'], vault['type'],
                                      vault['collaborators'], vault['pending'])
            else:
                vault_obj = obj.Vault(vault['title'], vault['owner'], vault['description'], vault['type'],
                                      vault['collaborators'])
        else:
            vault_obj = obj.Vault(vault['title'], vault['owner'], vault['description'], vault['type'])
        client.send(pickle.dumps(vault_obj))
    else:
        client.send("@".encode())


def remove_mac(mac, client):
    """
    Disconnects a user by removing the MAC field
    :param mac: address to disconnect
    :param client: Client object
    :return:
    """
    user = DBHandle.find_by_addr(mac)
    if user:
        DBHandle.remove_mac(user['name'])
    client.send('Done'.encode())


def get_vaults_by_type(data, client):
    """
    Passes all private vaults of a certain user
    :param data: user and type
    :param client: Client object
    :return:
    """
    pvaults = DBHandle.get_vaults_by_type(*data)
    for vault in pvaults:
        if vault['type'] == 'shared':
            vault_obj = obj.Vault(vault['title'], vault['owner'], vault['description'], vault['type'],
                              vault['collaborators'])
        else:
            vault_obj = obj.Vault(vault['title'], vault['owner'], vault['description'], vault['type'])
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


def gem_title_validation(data, client):
    if DBHandle.check_if_existing_gem(*data):
        client.send("409".encode())
        return
    if re.match(r'^[A-Za-z0-9\-:. ]*$', data[-1]) == None:
        client.send("1001".encode())
        return
    client.send("200".encode())


def delete_gem_from_vault(data, client):
    DBHandle.delete_gem(*data)


def make_public(data, client):
    DBHandle.make_public(data)


def produce_key(data, client):
    vault_title, key = data
    DBHandle.add_key_to_vault(vault_title, key)


def key_check_and_pend(data, client):
    key, user = data
    if DBHandle.check_if_key_exists(key):
        DBHandle.register_by_key(key, user)
        client.send("200".encode())
    else:
        client.send("409".encode())


def remove_pend_add_collab(data, client):
    DBHandle.remove_pend_add_collab(*data)


def delete_pending(data, client):
    DBHandle.delete_pending(*data)


def act(action, data, client):
    actions = {"adduser": adduser,
               "sign-in": sign_in,
               "register-user": register_user,
               "get-user-by-addr": search_addr,
               "remove-mac": remove_mac,
               "get-vaults-by-type": get_vaults_by_type,
               "add-vault": add_vault,
               "get-vault-by-title": search_vault,
               "update-vault-desc": update_description,
               "find-desc": get_desc,
               "get-gems-by-vault": gems_by_vault,
               "delete-gem-from-vault": delete_gem_from_vault,
               "add-gem-to-vault": add_gem_to_vault,
               "gem-title-validation": gem_title_validation,
               "make-public": make_public,
               "produce-shared-key": produce_key,
               "check-key-and-pend-request": key_check_and_pend,
               "pending-to-collaborator": remove_pend_add_collab,
               "delete-pending": delete_pending}

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
