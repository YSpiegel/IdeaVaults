from pymongo import MongoClient
import ObjManagement as obj
import time

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
        return list(vaults.find({
            '$or': [
                {'owner': user},
                {'collaborators.coowner': {'$in': [user]}},
                {'collaborators.contributor': {'$in': [user]}},
                {'collaborators.guest': {'$in': [user]}}
            ],
            'type': type
        }))


def check_if_new_vault(vault):
    with MongoClient(uri) as cluster:
        vaults = cluster['IdeaVaults']['Vaults']
        exists = bool(vaults.find_one({'title': vault.title,
                                      'owner': vault.owner}))
        return not exists


def add_vault(vault):
    with MongoClient(uri) as cluster:
        vaults = cluster['IdeaVaults']['Vaults']
        if vault.type == "shared":
            vaults.insert_one({'title': vault.title, 'description': vault.description,
                               'owner': vault.owner, 'type': vault.type,
                               'collaborators': {'coowner': [], 'contributor': [], 'guest': []}})
        else:
            vaults.insert_one({'title': vault.title, 'description': vault.description,
                           'owner': vault.owner, 'type': vault.type})


def update_description(user, title, description):
    with MongoClient(uri) as cluster:
        vaults = cluster['IdeaVaults']['Vaults']
        vaults.update_one({'owner':user, 'title':title}, {'$set':{'description':description}})
        return vaults.find_one({'owner':user, 'title':title})


def get_vault(user, title):
    with MongoClient(uri) as cluster:
        vaults = cluster['IdeaVaults']['Vaults']
        return vaults.find_one({'owner':user, 'title':title})


def get_gems(vault):
    with MongoClient(uri) as cluster:
        gems = cluster['IdeaVaults']['Gems']
        return list(gems.find({'vault': vault.title, 'user': vault.owner}))


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
        vaults.update_one({'title': vault},
                          {'$set': {'type': "shared",
                                      'collaborators': {'coowner': [], 'contributor': [], 'guest': []}}})


def add_key_to_vault(vault_title, key):
    with MongoClient(uri) as cluster:
        vaults = cluster['IdeaVaults']['Vaults']
        vaults.update_one({'title': vault_title}, {'$set': {'key': key}})
        time.sleep(180)
        vaults.update_one({'title': vault_title}, {'$unset': {'key': ""}})


def check_if_key_exists(key):
    with MongoClient(uri) as cluster:
        vaults = cluster['IdeaVaults']['Vaults']
        return bool(vaults.find_one({'key': key}))


def register_by_key(key, user):
    with MongoClient(uri) as cluster:
        vaults = cluster['IdeaVaults']['Vaults']
        if 'pending' in vaults.find_one({'key': key}):
            if user not in vaults.find_one({'key': key})['pending']:
                vaults.update_one({'key': key}, {'$push': {'pending': user}})
        else:
            vaults.update_one({'key': key}, {'$set': {'pending': [user]}})


def remove_pend_add_collab(user, rank, vault):
    with MongoClient(uri) as cluster:
        vaults = cluster['IdeaVaults']['Vaults']
        vaults.update_one({'title': vault},
                          {'$push': {f'collaborators.{rank}': user}, "$pull": {'pending': user}})


def delete_pending(user, vault):
    with MongoClient(uri) as cluster:
        vaults = cluster['IdeaVaults']['Vaults']
        vaults.update_one({'title': vault}, {"$pull": {'pending': user}})


if __name__ == "__main__":
    with MongoClient(uri) as cluster:
        vaults = cluster['IdeaVaults']['Vaults']
        vaults.update_many({'type': 'shared'},
                           {'$set': {'collaborators': {'coowner': [], 'contributor': [], 'guest': []}}})