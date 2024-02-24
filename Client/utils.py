import datetime, random, string


def get_greeting():
    current_hour = datetime.datetime.now().hour
    if current_hour < 12:
        greeting = "Good morning"
    elif 12 <= current_hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"
    return greeting


def create_key(length):
    key = ""
    chars = string.digits + string.ascii_uppercase

    for _ in range(length):
        key += chars[random.randint(0, len(chars) - 1)]

    return key


if __name__ == "__main__":
    print(create_key(7))