# defines ACL configuration
class ACL:
    def __init__(self, act: bool, src, dst):
        self.act = act
        self.src = src
        self.dst = dst
    def __str__(self) -> str:
        return "ACL"

# defines link weight configuration
class LinkWeight:
    def __init__(self, a, b, weight):
        self.a = a
        self.b = b
        self.weight = weight
    def __str__(self) -> str:
        return "LinkWeight"

# defines static route configuration
class StaticRoute:
    def __init__(self, dst, nh):
        self.dst = dst
        self.nh = nh
    def __str__(self) -> str:
        return "StaticRoute"


# superclass for configurations above
class Config:
    def __init__(self, config_type, router):
        self.config_type = config_type
        self.router = router
    def get_router(self):
        return self.router
    def get_config(self):
        return self.config_type
    def __str__(self) -> str:
        return str(self.config_type)

# actions of a configuration
class Append(Config):
    def __init__(self, config_type, router):
        super().__init__(config_type, router)
    
    def __str__(self) -> str:
        return "Append"

class Remove(Config):
    def __init__(self, config_type, router):
        super().__init__(config_type, router)
    
    def __str__(self) -> str:
        return "Remove"

class Update(Config):
    def __init__(self, config_type, router, old_config):
        super().__init__(config_type, router)
        self.old_config = old_config

    def get_old_config(self):
        return self.old_config

    def __str__(self) -> str:
        return "Update"

if __name__ == "__main__":
    s = StaticRoute(0, 1)
    a = Append(s, 0)
    print(str(a.get_config()))