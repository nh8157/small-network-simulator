import abc
import graph as g
import packet as p


class Middlebox:
    def __init__(self, router_id, nodes_map):
        self.id = router_id
        self.graph = g.Graph(nodes_map)
        self.routing_table = None
        self.neighbor = None
        self.iBGP = {
            'client': [],
            'server': []
        }
        self.iBGP_msg = {}
        self.update_routing_table()

    def get_id(self):
        return self.id

    def update_graph(self, n1, n2, cost):
        if not cost:
            self.graph.destroy_link(n1, n2)
        elif self.graph.has_link(n1, n2):
            self.graph.update_cost(n1, n2, cost)
        self.append_routing_table()
        self.update_routing_table()

    def route(self, packet: p.Packet):
        receiver = packet.get_receiver()
        packet.stamp_packet(self.get_id())
        if receiver != self.get_id():
            # packet has not arrived at the destination
            packet.dec_TTL()
        else:
            packet.terminate_packet()
        try:
            next_hop = self.get_routing_table()[receiver]
            if packet.get_TTL() and not packet.has_terminate():
                if next_hop != None:
                    print("Next hop:", next_hop)
                    return self.get_routing_table()[receiver]
                print("Intra-AS -> Inter-AS")
                packet.terminate_packet()
                return None
            elif packet.get_TTL() and packet.has_terminate():
                print("Destination reached")
                packet.terminate_packet()
                return None
            elif not packet.get_TTL() and not packet.has_terminate():
                packet.terminate_packet()
                print("Forwarding loop detected")
                return None

        except KeyError:
            packet.terminate_packet()
            return "Destination not reachable"

    def update_routing_table(self):
        self.routing_table = self.graph.dijkstra(self.id)

    def append_routing_table(self, dest, gateway) -> None:
        self.routing_table[dest] = gateway

    def remove_routing_table(self, dest) -> None:
        del self.routing_table[dest]

    def get_routing_table(self):
        return self.routing_table

    def get_BGP_session(self):
        return self.iBGP.copy()

    @abc.abstractclassmethod
    def start_iBGP_session(self, *args):
        return NotImplemented

    @abc.abstractclassmethod
    def destroy_iBGP_session(self, *args):
        return NotImplemented

    @abc.abstractclassmethod
    def draft_iBGP_ad(self, update):
        return NotImplemented

    @abc.abstractclassmethod
    def receive_iBGP_ad(self, update):
        return NotImplemented

    def decode_iBGP_ad(self, update: list):
        destinations = update['dest']
        gate = update['gate']
        advertiser = update['advertiser']
        for dest in destinations:
            if dest not in self.iBGP_msg.keys():
                self.iBGP_msg[dest] = [[gate, advertiser]]
            else:
                if self.same_advertiser_exist(dest, advertiser):
                    # print(self.get_id(), "exist same advertiser", gate, advertiser)
                # if the same advertiser advertise different route to the same destination
                # then the route may have altered
                    self.remove_iBGP_ad(self.get_iBGP_ad(dest, advertiser), advertiser)
                if dest not in self.iBGP_msg.keys():
                    self.iBGP_msg[dest] = []
                self.iBGP_msg[dest].append([gate, advertiser])

            self.opt_iBGP_route(dest)

    def remove_iBGP_ad(self, router, advert):
        # called when an iBGP session is down and self is the client
        # print(self.get_id(), self.iBGP_msg, router, advert)
        for dest in self.iBGP_msg.keys():
            for i in self.iBGP_msg[dest]:
                # the router is the advertiser of the iBGP msg or the gateway
                if router == i[0] and advert == i[1]:
                    # if the router is one of the gateway routers to an external dest
                    # print(self.get_id(), "removing", router, advert)
                    self.iBGP_msg[dest].remove(i)
                    if not len(self.iBGP_msg[dest]):
                        del self.iBGP_msg[dest]
                        self.remove_routing_table(dest)
                        return self.iBGP['client'], self.get_id()
                    else:
                        self.opt_iBGP_route(dest)
        # if self is a route reflector then return the list of client so that these clients also remove the ad from their list
        # print(self.get_id(), self.iBGP_msg)
        return self.iBGP['client'], self.get_id()

    def get_iBGP_ad(self, dest, advert):
        for i in self.iBGP_msg[dest]:
            if i[1] == advert:
                return i[0]

    def same_advertiser_exist(self, dest, advert):
        for i in self.iBGP_msg[dest]:
            if i[1] == advert:
                return True
            return False

    def opt_iBGP_route(self, dest) -> None:
        # choose iBGP route from the advertisement received
        # append the next hop of the chosen route into the routing table
        min_cost = float('inf')
        min_gate = None
        # compare the cost to each gateway within the AS
        # acquire the gateway router with the least intra-AS distance
        for i in self.iBGP_msg[dest]:
            if self.graph.get_cost(i[0]) < min_cost:
                min_gate = self.routing_table[i[0]]
                min_cost = self.graph.get_cost(i[0])
        self.append_routing_table(dest, min_gate)


class Router(Middlebox):
    def __init__(self, router_id, nodes_map):
        super().__init__(router_id, nodes_map)

    def start_iBGP_session(self, sessions: dict):
        # one server opens up iBGP session with the client
        self.iBGP['server'] += [i for i in sessions[self.get_id()]['server']]

    def destroy_iBGP_session(self, *args):
        for router in args[0]:
            # remove the server from the iBGP server table
            # locate the associated path
            self.iBGP['server'].remove(router)
            self.remove_iBGP_ad(router, args[1])

    def receive_iBGP_ad(self, update: dict) -> None:
        self.decode_iBGP_ad(update)
        return None


class RR(Middlebox):
    def __init__(self, router_id, graph):
        super().__init__(router_id, graph)

    def receive_iBGP_ad(self, update: dict) -> tuple:
        self.decode_iBGP_ad(update)
        # propagate this update to all clients
        # return all clients subscribed
        # modify the advertiser of the update
        client = self.get_iBGP_client()
        if update['advertiser'] in client:
            client.remove(update['advertiser'])
        return self.draft_iBGP_ad(update), client

    def start_iBGP_session(self, sessions):
        self.iBGP['server'] += [i for i in sessions[self.get_id()]['server']]
        self.iBGP['client'] += [i for i in sessions[self.get_id()]['client']]

    def destroy_iBGP_session(self, *args):
        # route reflector also needs to ask the client to remove the route
        if args[2] == "client":
            for i in args[0]:
                self.iBGP['server'].remove(i)
                self.remove_iBGP_ad(i, args[1])
                return self.iBGP['client'], self.get_id()
        else:
            for i in args[0]:
                self.iBGP['client'].remove(i)
                return None

    def get_iBGP_client(self):
        return self.iBGP['client'].copy()

    def draft_iBGP_ad(self, update) -> dict:
        update = update.copy()
        update['advertiser'] = self.get_id()
        return update


class Border(Middlebox):
    def __init__(self, router_id, graph):
        super().__init__(router_id, graph)
        self.eBGP_sessions = []

    def start_iBGP_session(self, sessions: dict):
        self.iBGP['server'] += [i for i in sessions[self.get_id()]['server']]
        self.iBGP['client'] += [i for i in sessions[self.get_id()]['client']]

    def destroy_iBGP_session(self, *args):
        for i in args:
            self.iBGP['client'].remove(i)

    def get_iBGP_client(self) -> list:
        return self.iBGP['client'].copy()

    def insert_eBGP(self, prefix):
        self.append_routing_table(prefix, None)
        self.eBGP_sessions.append(prefix)
        return self.draft_iBGP_ad()

    def draft_iBGP_ad(self) -> tuple:
        return {"dest": [i for i in self.eBGP_sessions], "gate": self.get_id(), "advertiser": self.get_id()}

    def receive_iBGP_ad(self, update: dict) -> None:
        self.decode_iBGP_ad(update)
        return None


if __name__ == '__main__':
    graph_config = {
        0: {1: 1},
        1: {0: 1, 2: 2},
        2: {1: 2}
    }

    ibgp_config = {
        0: {"client": [1], "server": [1]},
        1: {"client": [0, 2], "server": [0, 2]},
        2: {"client": [1], "server": [1]}
    }

    r0 = Border(0, graph_config)
    r1 = RR(1, graph_config)
    r2 = Border(2, graph_config)

    r0.start_iBGP_session(ibgp_config)
    r1.start_iBGP_session(ibgp_config)
    r2.start_iBGP_session(ibgp_config)

    ad = r0.draft_iBGP_ad(4)
    r = r0.get_iBGP_client()
    print(r)

    argv = r1.receive_iBGP_ad(ad)
    print(argv)

    r = argv[1]

    argv = r2.receive_iBGP_ad(argv[0])
    print(argv)
    # r1.receive_iBGP_ad({"dest": 4, "gate": 0, "advertiser": 0})
    # r1.receive_iBGP_ad({"dest": 4, "gate": 2, "advertiser": 2})

    # pk = p.Packet(1, 4)

    # print(r1.route(pk))
    # r1.destroy_iBGP_session(0)
    # print(r1.route(pk))
    # r1.destroy_iBGP_session(2)
    # print(r1.route(pk))
