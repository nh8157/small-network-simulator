import router as r
import packet as p


class Simulator:
    def __init__(self, graph_config: dict, ibgp_config: dict):
        self.graph_config = graph_config
        self.ibgp_config = ibgp_config
        self.routers = {}
        self.configure_routers()

    def configure_routers(self):
        for i in self.ibgp_config.keys():
            if self.ibgp_config[i]["type"] == 1:
                # regular routers
                self.routers[i] = r.Router(i, self.graph_config.copy())
            elif self.ibgp_config[i]["type"] == 2:
                # route reflector
                self.routers[i] = r.RR(i, self.graph_config.copy())
            else:
                self.routers[i] = r.Border(i, self.graph_config.copy())
            self.routers[i].start_iBGP_session(self.ibgp_config.copy())

    def route_packet(self, sender, receiver):
        pk = p.Packet(sender, receiver)
        router = sender
        while not pk.has_terminate():
            # print(self.routers[router].get_routing_table())
            print("########## Packet at router", router, "##########")
            router = self.routers[router].route(pk)

    def insert_eBGP(self, prefix, gateway):
        ad = self.routers[gateway].insert_eBGP(prefix)
        client = self.routers[gateway].get_iBGP_client()
        
        for c in client:
            self.update_iBGP_recursive(c, ad)
        # while len(client):
        #     nc = []
        #     for c in client:
        #         argv = self.routers[c].receive_iBGP_ad(ad)
        #         if argv != None:
        #             nad = argv[0]
        #             nc += argv[1]
        #     ad = nad
        #     client = nc
        # for i in self.routers.keys():
        #     print(self.routers[i].get_id(), self.routers[i].get_routing_table())

    def start_iBGP(self, server, client):
        ibgp_update = {}
        ibgp_update[server] = {'client': [client], 'server': []}
        ibgp_update[client] = {'server': [server], 'client': []}
        self.routers[server].start_iBGP_session(ibgp_update)
        self.routers[client].start_iBGP_session(ibgp_update)
        # advertise the new client the route
        client = [client]
        ad = self.routers[server].draft_iBGP_ad()
        for c in client:
            self.update_iBGP_recursive(c, ad)
        # for i in self.routers.keys():
        #     print(self.routers[i].get_id(), self.routers[i].get_routing_table())

    def update_iBGP_recursive(self, client, ad):
        argv = self.routers[client].receive_iBGP_ad(ad)
        if argv != None:
            for i in argv[1]:
                self.update_iBGP_recursive(i, argv[0])

    def delete_iBGP(self, server, client):
        self.routers[server].destroy_iBGP_session()
        advert = server
        client = self.routers[client].destroy_iBGP_session([server], advert, 'client')
        if client != None and client[0] != None:
            for c in client[0]:
                self.del_iBGP_recursive(c, server, advert)
        # while client != None and len(client):
        #     nc = []
        #     if client != None:
        #         for c in client:
        #             nc += self.routers[c].remove_iBGP_ad(server)
        #     client = nc
        # for i in self.routers.keys():
        #     print(self.routers[i].get_id(), self.routers[i].get_routing_table())

    def del_iBGP_recursive(self, client, router, advert):
        argv = self.routers[client].remove_iBGP_ad(router, advert)
        if argv != None:
            for i in argv[0]:
                self.del_iBGP_recursive(i, router, argv[1])

    def update_link_cost(self, l1, l2, cost):
        for i in self.routers.values():
            i.update_graph(l1, l2, cost)

    def get_routers(self):
        return self.routers.copy()


def main():
    # define a new packet
    graph_config = {
        0: {3: 1, 4: 1},
        1: {2: 1, 5: 1},
        2: {1: 1, 3: 1},
        3: {0: 1, 2: 1},
        4: {0: 1, 5: 1},
        5: {1: 1, 4: 1}
    }

    ibgp_config = {
        0: {"client": [2, 4], "server": [], "type": 3},
        1: {"client": [2, 3, 5], "server": [], "type": 3},
        2: {"client": [4], "server": [0, 1], "type": 2},
        3: {"client": [5], "server": [1], "type": 2},
        4: {"client": [], "server": [0, 2], "type": 1},
        5: {"client": [], "server": [1, 3], "type": 1}
    }

    s = Simulator(graph_config, ibgp_config)

    s.insert_eBGP(6, 0)
        
    s.insert_eBGP(6, 1)
    
    s.delete_iBGP(0, 4)
    s.delete_iBGP(1, 5)
    s.start_iBGP(0, 3)
    # s.delete_iBGP(1, 2)
    
    s.route_packet(5, 6)


main()
