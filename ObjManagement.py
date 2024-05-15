import ctypes, string, random, datetime, hashlib, re, base64, pickle


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


class UserInfo:
    def __init__(self, name):
        self.name = name

    def private_vaults(self):
        return []

    def shared_vaults(self):
        return []


class Vault:
    def __init__(self, title, owner, description, type, collaborators=None, pending=None):
        self.title = title
        self.owner = owner
        self.description = description
        self.type = type
        if collaborators is not None:
            self.collaborators = collaborators
        if pending is not None:
            self.pending = pending

    def is_in_vault(self, user):
        if not getattr(self, 'collaborators', None):
            return user == self.owner
        return user == self.owner or user in self.collaborators['guest'] or \
            user in self.collaborators['contributor'] or user in self.collaborators['coowner']


class Gem:
    def __init__(self, vault, user, title, content, lastedit=None):
        self.vault = vault
        self.user = user
        self.title = title
        self.content = content
        self.idtitle = self.title.replace(' ', '_')
        if lastedit:
            self.lastedit = lastedit
        self.preview = string_preview(self.content, 14, 21)


class Utils:
    def __init__(self):
        self.keylength = 7
        self.endingequals = r'(=+)$'
        self.baserot = 2

    def get_greeting(self):
        current_hour = datetime.datetime.now().hour
        if current_hour < 12:
            greeting = "Good morning"
        elif 12 <= current_hour < 18:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        return greeting

    def create_key(self):
        key = ""
        chars = string.digits + string.ascii_uppercase

        for _ in range(self.keylength):
            key += chars[random.randint(0, len(chars) - 1)]

        return key

    def md5hash(self, plain):
        return hashlib.md5(plain.encode('utf-8')).hexdigest()

    def rotate(self, text, key):
        length = len(text)
        key = key % length
        rotated_text = text[key:] + text[:key]
        return rotated_text

    def rblhash(self, plain):
        return self.rotate(self.md5hash(plain), len(plain))

    def compare_rbl(self, plain, hashed):
        return self.rblhash(plain) == hashed

    def flipbase(self, msg, action):
        if action == 'e':
            if isinstance(msg, str):
                msg = msg.encode('utf-8')
            msg = base64.b64encode(msg)

        msg = msg.decode('utf-8')

        match = re.search(self.endingequals, msg)
        if match:
            endingequals = match.group(1)
            msg = msg[:-len(endingequals)]
        else:
            endingequals = ""

        switched_text = ""
        for i in range(0, len(msg), 2 * self.baserot):
            if i + 2 * self.baserot <= len(msg):
                switched_text += msg[i + self.baserot:i + 2 * self.baserot] + msg[i:i + self.baserot]
            else:
                switched_text += msg[i:][::-1]
        switched_text += endingequals

        if action == 'd':
            decoded_bytes = base64.b64decode(switched_text)
            if decoded_bytes.startswith(b'\x80'):
                return pickle.loads(decoded_bytes)
            switched_text = decoded_bytes.decode('utf-8')
        else:
            return switched_text.encode()

        return switched_text


if __name__ == "__main__":
    util = Utils()
    encrypted = util.flipbase('@', 'e')
    print(encrypted)
    print(util.flipbase(encrypted, 'd'))