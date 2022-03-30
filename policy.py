class Policy:
    def __init__(self, a, b):
        self.a = a
        self.b = b
    def get_policy(self):
        return self.a, self.b

class Reachability(Policy):
    def __init__(self, a, b):
        super().__init__(a, b)
    def __str__(self):
        return "Reachability"

class Isolation(Policy):
    def __init__(self, a, b):
        super().__init__(a, b)
    def __str__(self):
        return "Isolation"

class Waypointing(Policy):
    def __init__(self, a, b, c):
        super().__init__(a, b)
        self.c = c
    def get_policy(self):
        return self.a, self.b, self.c
    def __str__(self):
        return "Waypointing"
    
if __name__ == '__main__':
    w = Waypointing(0, 1, 2)
    i = Isolation(0, 1)
    print(w)