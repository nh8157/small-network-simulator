from mimetypes import init
import network_simulator.router as r
import network_simulator.packet as p

class Simulator:
    def __init__(self, graph_config: dict, ibgp_config: dict):
        self.graph_config = graph_config
        self.ibgp_config = ibgp_config
        # routers indexed by distinct router id
        self.routers = {}
        self.configure_routers()
        # no eBGP is considered at the moment
        # self.init_eBGP()
        
    def configure_routers(self):
        # configure routers based on the ibgp_config dictionary
        for i in self.ibgp_config.keys():
            if self.ibgp_config[i]["type"] == 1:
                # regular routers
                self.routers[i] = r.Router(i, self.graph_config.copy())
            elif self.ibgp_config[i]["type"] == 2:
                # route reflector
                self.routers[i] = r.RR(i, self.graph_config.copy())
            else:
                # boarder router
                self.routers[i] = r.Border(i, self.graph_config.copy())
            # start bgp sessions based on the input configuration file
            # could be skipped when only considering igp
            # self.routers[i].start_iBGP_session(self.ibgp_config.copy())

    def get_router(self, router_id):
        return self.routers[router_id]

    def route_packet(self, sender, receiver):
        # initialize a new packet
        pk = p.Packet(sender, receiver)
        router = sender
        # stops when the packet is terminated
        while not pk.has_terminate() and router != None:
            print("########## Packet at router", router, "##########")
            # gets the router id for the next hop
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
        # print("server", server)
        nclient = self.routers[client].destroy_iBGP_session([server], advert, 'client')
        # print("router", client, nclient)
        if nclient != None and nclient[0] != None:
            for c in nclient[0]:
                self.del_iBGP_recursive(c, server, nclient[1])
                print("Router", nclient)
                if nclient[2] != None:
                    self.update_iBGP_recursive(c, nclient[2])
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
        # print(client, argv)
        if argv != None:
            for i in argv[0]:
                self.del_iBGP_recursive(i, router, argv[1])

    def update_link_cost(self, l1, l2, cost):
        for i in self.routers.values():
            i.update_graph(l1, l2, cost)

    # add a static route to the graph
    def add_static_route(self, src, dst, nh):
        router = self.routers[src]
        # first check if the route is in static mode
        if not router.get_route_mode(dst):
            router.dynamic_to_static(dst)
        router.add_static_route(dst, nh)

    # delete a static route from the graph
    def del_static_route(self, src, dst):
        router = self.routers[src]
        # first check if the route is in static mode
        if router.get_route_mode(dst):
            router.remove_static_route(dst)

    # switch route mode to dynamic
    def switch_route_mode(self, src, dst):
        router = self.routers[src]
        # first checks if the router is under static mode
        if router.get_route_mode(dst):
            router.static_to_dynamic(dst)

    # add an acl rule to a router
    def add_acl(self, router_id, act, src, dst, pos=-1) -> bool:
        router = self.get_router(router_id)
        return router.add_acl(act, src, dst, pos)

    # remove an acl rule from a router
    def remove_acl(self, router_id, act, src, dst) -> bool:
        router = self.get_router(router_id)
        return router.remove_acl(act, src, dst)

    def get_routers(self):
        return self.routers.copy()
    
    def init_eBGP(self):
        self.insert_eBGP(6, 0)    
        self.insert_eBGP(6, 1)

def init_bgp_config(client, server, router_type) -> dict:
    return {"client": client, "server": server, "type": router_type}

def main():
    # define a new packet
    # graph_config = {
    #     0: {3: 1, 4: 1},
    #     1: {2: 1, 5: 1},
    #     2: {1: 1, 3: 1},
    #     3: {0: 1, 2: 1},
    #     4: {0: 1, 5: 1},
    #     5: {1: 1, 4: 1}
    # }
    
    # ibgp_config = {
    #     0: {"client": [2, 4], "server": [], "type": 3},
    #     1: {"client": [2, 3, 5], "server": [], "type": 3},
    #     2: {"client": [4], "server": [0, 1], "type": 2},
    #     3: {"client": [5], "server": [1], "type": 2},
    #     4: {"client": [], "server": [0, 2], "type": 1},
    #     5: {"client": [], "server": [1, 3], "type": 1}
    # }

    graph_config = {
        0: {1: 1, 3: 1},
        1: {0: 1, 3: 1, 2: 1},
        2: {1: 1, 3: 1},
        3: {0: 1, 1: 1, 2: 1},
    }

    ibgp_config = {
        0: init_bgp_config([], [], 1),
        1: init_bgp_config([], [], 1),
        2: init_bgp_config([], [], 1),
        3: init_bgp_config([], [], 1)
    }
    
    s = Simulator(graph_config, ibgp_config)

    # before switching to static route
    print("\nDynamic mode")
    s.route_packet(1, 3)

    # after switching to static route
    print("\nStatic mode")
    s.add_static_route(1, 3, 0)
    s.route_packet(1, 3)

    print("\nDynamic mode")
    s.del_static_route(1, 3)
    s.switch_route_mode(1, 3)
    s.route_packet(1, 3)
    
    """
    a: s.delete_iBGP(0, 4)
    b: s.delete_iBGP(1, 5)
    c: s.delete_iBGP(1, 2)
    d: s.start_iBGP(0, 3)
    """

    # while True:
    #     ins = int(input("Please type in command (1: start iBGP, 2: delete iBGP, 3: route packet): "))
    #     if ins == 1 or ins == 2:
    #         server = int(input("Please type in server index: "))
    #         client = int(input("Please type in client index: "))
    #         if ins == 1:
    #             s.start_iBGP(server, client)
    #         else:
    #             s.delete_iBGP(server, client)
    #         print("Changes applied successfully")
    #     else:
    #         server = int(input("Please type in sender index: "))
    #         client = int(input("Please type in receipient index: "))
    #         s.route_packet(server, client)

if __name__ == '__main__':
    main()
