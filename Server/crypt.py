import hashlib as hash


def md5hash(plain):
    return hash.md5(plain)


def compareto_md5hash(plain, hashed):
    return hash.md5(plain) == hashed