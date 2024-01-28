import ctypes


# Windows API text measurement
class Size(ctypes.Structure):
    _fields_ = [("cx", ctypes.c_long), ("cy", ctypes.c_long)]


hdc = ctypes.windll.user32.GetDC(0)
GetTextExtentPoint32 = ctypes.windll.gdi32.GetTextExtentPoint32W


def string_preview(text, max_width_rems, font_height_pixels):
    fontsize = font_height_pixels / 1.5
    max_width_pixels = max_width_rems * fontsize

    # Gradually remove characters until preview fits width
    preview = text
    while len(preview) > 1:
        csize = Size()
        GetTextExtentPoint32(hdc, preview, len(preview), ctypes.byref(csize))

        if csize.cx < max_width_pixels:
            break

        preview = preview[:-1]

    # Throw last space
    if preview[-1] == " ":
        preview = preview[:-1]

    # Add ellipses
    if preview != text:
        preview += '...'

    return preview


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
        self.idtitle = self.title.replace(' ', '_')

        self.preview = string_preview(self.content, 14, 21)

    def __str__(self):
        return f"{self.vault}|||{self.user}|||{self.title}|||{self.content}"


def gemfromstr(str):
    return Gem(*str.split("|||"))