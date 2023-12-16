import hashlib


def md5hash(plain):
    return hashlib.md5(plain.encode('utf-8')).hexdigest()


def rotate(text, key):
    length = len(text)
    key = key % length  # Adjust key in case it's larger than the length of the string
    rotated_text = text[key:] + text[:key]
    return rotated_text


def rblhash(plain):
    return rotate(md5hash(plain), len(plain))


def compare_rbl(plain, hashed):
    return rblhash(plain) == hashed


if __name__ == "__main__":
    print(rotate("hallelujah", 5))