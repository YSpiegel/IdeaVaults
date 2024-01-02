from pymongo import MongoClient
import ObjManagement as obj

uri = "mongodb+srv://yoavsp:y0avdb7@cluster1.jebb6i6.mongodb.net/?retryWrites=true&w=majority"


def sign_in_method(identifier):
    return 'email' if "@" in identifier else 'name'


def check_if_new(identifier):
    with MongoClient(uri) as cluster:
        users = cluster['IdeaVaults']['Users']
        exists = bool(users.find_one({sign_in_method(identifier): identifier}))
        return not exists


def check_if_connected(name):
    with MongoClient(uri) as cluster:
        users = cluster['IdeaVaults']['Users']
        user = users.find_one({"name": name})
        try:
            return bool(user['ip'])
        except:
            return False


def add_new(name, email, password):
    with MongoClient(uri) as cluster:
        users = cluster['IdeaVaults']['Users']
        users.insert_one({"name":name, "email":email, "password":password})


def sign_in(identifier, password):
    with MongoClient(uri) as cluster:
        users = cluster['IdeaVaults']['Users']
        obj = users.find_one({sign_in_method(identifier): identifier})
        if obj and obj['password'] == password:
            return obj['name']
        return '@'


def add_ip(name, ip):
    with MongoClient(uri) as cluster:
        users = cluster['IdeaVaults']['Users']
        users.update_one({'name': name}, {"$set": {"ip":ip}})


def find_by_addr(addr):
    with MongoClient(uri) as cluster:
        users = cluster['IdeaVaults']['Users']
        return users.find_one({'ip':addr})


def find_by_title(title):
    with MongoClient(uri) as cluster:
        users = cluster['IdeaVaults']['Vaults']
        return users.find_one({'title':title})


def remove_ip(name):
    with MongoClient(uri) as cluster:
        users = cluster['IdeaVaults']['Users']
        users.update_one({'name': name}, {"$unset": {"ip": ""}})


def get_private_vaults(user):
    with MongoClient(uri) as cluster:
        vaults = cluster['IdeaVaults']['Vaults']
        return list(vaults.find({'user': user, 'type': "private"}))


def get_shared_vaults(user):
    with MongoClient(uri) as cluster:
        vaults = cluster['IdeaVaults']['Vaults']
        return list(vaults.find({'user': user, 'type': "shared"}))


def check_if_new_vault(vault_title, user):
    with MongoClient(uri) as cluster:
        vaults = cluster['IdeaVaults']['Vaults']
        exists = bool(vaults.find_one({'title': vault_title,
                                      'user': user}))
        return not exists


def add_vault(vault):
    with MongoClient(uri) as cluster:
        vaults = cluster['IdeaVaults']['Vaults']
        vaults.insert_one({'title': vault.title, 'description': vault.description,
                           'user': vault.user, 'type': vault.type})


if __name__ == "__main__":
    print(bool("False"))