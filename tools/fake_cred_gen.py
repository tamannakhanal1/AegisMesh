import random, string
USERNAMES = ["admin", "root", "test", "user", "administrator", "webadmin"]
DOMAINS = ["acme.local", "corp.example"]
def gen_password(length=10):
    chars = string.ascii_letters + string.digits + "!@#$%^&*()"
    return "".join(random.choice(chars) for _ in range(length))
def gen_cred():
    user = random.choice(USERNAMES)
    return {"username": f"{user}", "password": gen_password(12)}
if __name__ == "__main__":
    for i in range(5):
        print(gen_cred())
