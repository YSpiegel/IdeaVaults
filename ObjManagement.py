
class Vault:
    def __init__(self, title, user, description, type):
        self.title = title
        self.user = user
        self.description = description
        self.type = type

    def __str__(self):
        return f"{self.title}|||{self.user}|||{self.description}|||{self.type}"


def vaultfromstr(str):
    return Vault(*str.split("|||"))


class Gem:
    def __init__(self, vault, user, title, content):
        self.vault = vault
        self.user = user
        self.title = title
        self.content = content

    def __str__(self):
        return f"{self.vault}|||{self.user}|||{self.title}|||{self.content}"


def gemfromstr(str):
    return Gem(*str.split("|||"))