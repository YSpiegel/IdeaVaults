
class Vault:
    def __init__(self, title, user, description, type):
        self.title = title
        self.user = user
        self.description = description
        self.type = type

    def __str__(self):
        return f"{self.title}|||{self.user}|||{self.description}|||{self.type}"


def fromstr(str):
    print(str)
    print(str.split("|||"))
    return Vault(*str.split("|||"))
