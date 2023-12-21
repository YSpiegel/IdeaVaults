
class Vault:
    def __init__(self, name, user, description):
        self.name = name
        self.user = user
        self.description = description

    def __str__(self):
        return f"{self.name}|||{self.user}|||{self.description}"


def fromstr(str):
    return Vault(*str.split("|||"))
