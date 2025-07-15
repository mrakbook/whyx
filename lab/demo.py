class User:
    def __init__(self):
        self.age = 0

def increment(u):
    u.age += 2
    return u.age

def workflow():
    u = User()
    a1 = increment(u)
    a2 = increment(u)
    return a1 + a2

if __name__ == "__main__":
    print(workflow())