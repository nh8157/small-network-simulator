class Packet:
    def __init__(self, sender, receiver):
        self.sender = sender
        self.receiver = receiver
        self.status = False
        self.TTL = 16
        self.path = []

    def get_sender(self):
        return self.sender

    def get_receiver(self):
        return self.receiver

    def stamp_packet(self, router):
        self.path.append(router)

    def get_path(self):
        return self.path.copy()
    
    def get_TTL(self):
        return self.TTL
    
    def dec_TTL(self):
        self.TTL -= 1

    def terminate_packet(self):
        if not self.status:
            self.status = True
            
    def has_terminate(self):
        return self.status

if __name__ == '__main__':
    p = Packet(1, 2)