from pymongo import MongoClient

uri = "mongodb+srv://yoavsp:y0avdb7@cluster1.jebb6i6.mongodb.net/?retryWrites=true&w=majority"


def method(identifier):
    return 'email' if "@" in identifier else 'name'


def check_if_new(identifier):
    with MongoClient(uri) as cluster:
        users = cluster['IdeaVaults']['Users']
        exists = bool(users.find_one({method(identifier): identifier}))
        return not exists


def add_new(name, email, password):
    with MongoClient(uri) as cluster:
        users = cluster['IdeaVaults']['Users']
        users.insert_one({"name":name, "email":email, "password":password})


def sign_in(identifier, password):
    with MongoClient(uri) as cluster:
        users = cluster['IdeaVaults']['Users']
        obj = users.find_one({method(identifier): identifier})
        if obj and obj['password'] == password:
            return obj['name']
        return ''


def add_ip(name, ip):
    with MongoClient(uri) as cluster:
        users = cluster['IdeaVaults']['Users']
        users.update_one({'name': name}, {"$set": {"ip":ip}})


def find_by_addr(addr):
    with MongoClient(uri) as cluster:
        users = cluster['IdeaVaults']['Users']
        return users.find_one({'ip':addr})


def remove_ip(name):
    with MongoClient(uri) as cluster:
        users = cluster['IdeaVaults']['Users']
        users.update_one({'name': name}, {"$unset": {"ip": ""}})


if __name__ == "__main__":
    print(bool("False"))