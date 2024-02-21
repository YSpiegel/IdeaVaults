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
            return bool(user['mac'])
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


def add_mac(name, mac):
    with MongoClient(uri) as cluster:
        users = cluster['IdeaVaults']['Users']
        users.update_one({'name': name}, {"$set": {"mac":mac}})


def find_by_addr(addr):
    with MongoClient(uri) as cluster:
        users = cluster['IdeaVaults']['Users']
        return users.find_one({'mac':addr})


def find_by_title(title):
    with MongoClient(uri) as cluster:
        users = cluster['IdeaVaults']['Vaults']
        return users.find_one({'title':title})


def remove_mac(name):
    with MongoClient(uri) as cluster:
        users = cluster['IdeaVaults']['Users']
        users.update_one({'name': name}, {"$unset": {"mac": ""}})


def get_vaults_by_type(user, type):
    with MongoClient(uri) as cluster:
        vaults = cluster['IdeaVaults']['Vaults']
        return list(vaults.find({'host': user, 'type': type}))


def check_if_new_vault(vault):
    with MongoClient(uri) as cluster:
        vaults = cluster['IdeaVaults']['Vaults']
        exists = bool(vaults.find_one({'title': vault.title,
                                      'host': vault.host}))
        return not exists


def add_vault(vault):
    with MongoClient(uri) as cluster:
        vaults = cluster['IdeaVaults']['Vaults']
        vaults.insert_one({'title': vault.title, 'description': vault.description,
                           'host': vault.host, 'type': vault.type})


def update_description(user, title, description):
    with MongoClient(uri) as cluster:
        vaults = cluster['IdeaVaults']['Vaults']
        vaults.update_one({'host':user, 'title':title}, {'$set':{'description':description}})
        return vaults.find_one({'host':user, 'title':title})


def get_vault(user, title):
    with MongoClient(uri) as cluster:
        vaults = cluster['IdeaVaults']['Vaults']
        return vaults.find_one({'host':user, 'title':title})


def get_gems(vault):
    with MongoClient(uri) as cluster:
        gems = cluster['IdeaVaults']['Gems']
        return list(gems.find({'vault': vault.title, 'user': vault.host}))


def check_if_existing_gem(user, vault, title):
    with MongoClient(uri) as cluster:
        gems = cluster['IdeaVaults']['Gems']
        return bool(gems.find_one({'vault': vault, 'title': title}))


def add_new_gem(user, vault, title, content):
    with MongoClient(uri) as cluster:
        gems = cluster['IdeaVaults']['Gems']
        gems.insert_one({'user': user, 'vault': vault, 'title': title, 'content': content})

    #return obj.Gem(vault, user, title, content)


def delete_gem(gem, vault):
    with MongoClient(uri) as cluster:
        gems = cluster['IdeaVaults']['Gems']
        gems.delete_one({'title': gem, 'vault':vault})


def make_public(vault):
    with MongoClient(uri) as cluster:
        vaults = cluster['IdeaVaults']['Vaults']
        vaults.update_one({'title': vault}, {'$set': {'type': "shared", 'collaborators': []}})


if __name__ == "__main__":
    with MongoClient(uri) as cluster:
        vaults = cluster['IdeaVaults']['Vaults']
        vaults.update_many({'type':'shared'}, {'$set': {'collaborators': []}})