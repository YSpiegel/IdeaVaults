
class Vault:
    def __init__(self, title, user, description):
        self.title = title
        self.user = user
        self.description = description

    def __str__(self):
        return f"{self.title}|||{self.user}|||{self.description}"


def fromstr(str):
    return Vault(*str.split("|||"))
