
class Vault:
    def __init__(self, name, user):
        self.name = name
        self.user = user

    def __str__(self):
        return f"{self.name}|||{self.user}"

def fromstr(str):
    name, user = str.split("|||")
    return Vault(name, user)