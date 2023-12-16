import hashlib as hash


def md5hash(plain):
    return hash.md5(plain.encode('utf-8')).hexdigest()


def compareto_md5hash(plain, hashed):
    return md5hash(plain) == hashed
