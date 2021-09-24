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

    def update_routing_table(self):
        self.routing_table = self.graph.dijkstra(self.id)

    def append_routing_table(self, dest, gateway) -> None:
        self.routing_table[dest] = gateway

    def remove_routing_table(self, dest) -> None:
        del self.routing_table[dest]

    def get_routing_table(self):
        return self.routing_table

    @abc.abstractclassmethod
    def route(self, packet):
        return NotImplemented

    @abc.abstractclassmethod
    def start_iBGP_session(self, *args):
        return NotImplemented

    @abc.abstractclassmethod
    def destroy_iBGP_session(self, *args):
        return NotImplemented

    @abc.abstractclassmethod
    def send_iBGP_ad(self, update):
        return NotImplemented

    @abc.abstractclassmethod
    def receive_iBGP_ad(self, update):
        return NotImplemented

    def remove_iBGP_ad(self, router):
        self.iBGP['server'].remove(router)
        for dest in self.iBGP_msg.keys():
            if router in self.iBGP_msg[dest]:
                # if the router is one of the gateway routers to an external dest
                self.iBGP_msg[dest].remove(router)
                if not len(self.iBGP_msg[dest]):
                    del self.iBGP_msg[dest]
                    self.remove_routing_table(dest)
                    break
                else:
                    self.opt_iBGP_route(dest)

    def opt_iBGP_route(self, dest) -> None:
        min_cost = float('inf')
        min_gate = None
        # compare the cost to each gateway within the AS
        # acquire the gateway router with the least intra-AS distance
        for i in self.iBGP_msg[dest]:
            if self.graph.get_cost(i) < min_cost:
                min_gate = i
                min_cost = self.graph.get_cost(i)
        # append the next hop of this route to the routing table
        self.append_routing_table(dest, min_gate)


class Router(Middlebox):
    def __init__(self, router_id, nodes_map):
        super().__init__(router_id, nodes_map)

    # ordinary router without any special function
    def route(self, packet: p.Packet):
        receiver = packet.get_receiver()
        packet.stamp_packet(self.get_id())
        if receiver != self.get_id():
            # packet has not arrived at the destination
            packet.dec_TTL()
        else:
            packet.terminate_packet()
        try:
            return self.get_routing_table()[receiver]
        except KeyError:
            packet.terminate_packet()
            return "Destination not reachable"

    def start_iBGP_session(self, sessions: dict):
        # one server opens up iBGP session with the client
        self.iBGP['server'] += [i for i in sessions[self.get_id()]['server']]

    def destroy_iBGP_session(self, *args):
        for router in args:
            # remove the server from the iBGP server table
            # locate the associated path
            self.remove_iBGP_ad(router)

    def receive_iBGP_ad(self, update: dict):
        dest = update['dest']
        gate = update['gate']
        if dest not in self.iBGP_msg.keys():
            self.iBGP_msg[dest] = [gate]
        else:
            self.iBGP_msg[dest].append(gate)
        self.opt_iBGP_route(dest)


class RR(Middlebox):
    def __init__(self, router_id, graph=None, client=None):
        super().__init__(router_id, graph=graph)
        self.client = client
        self.preference = None

    def reflect_iBGP():
        pass

    def start_iBGP_session(self, sessions):
        self.iBGP['server'] += [i for i in sessions[self.get_id()]['server']]
        self.iBGP['client'] += [i for i in sessions[self.get_id()]['client']]

    def destroy_iBGP_session(self, *args):
        pass

    def get_iBGP_client(self):
        return self.iBGP['client'].copy()


class Border(Middlebox):
    def __init__(self, router_id, graph):
        super().__init__(router_id, graph)

    def start_iBGP_session(self, sessions: dict):
        self.iBGP['server'] += [i for i in sessions[self.get_id()]['server']]
        self.iBGP['client'] += [i for i in sessions[self.get_id()]['client']]

    def destroy_iBGP_session(self, *args):
        for i in args:
            self.iBGP['client'].remove(i)

    def get_iBGP_client(self):
        return self.iBGP['client'].copy()


if __name__ == '__main__':
    graph_config = {
        0: {1: 1},
        1: {0: 1, 2: 10},
        2: {1: 10}
    }

    ibgp_config = {
        0: {"client": [1], "server": []},
        1: {"client": [], "server": [0, 2]},
        2: {"client": [1], "server": []}
    }

    r0 = Border(0, graph_config)
    r1 = Router(1, graph_config)
    r2 = Border(2, graph_config)

    r0.start_iBGP_session(ibgp_config)
    r1.start_iBGP_session(ibgp_config)
    r2.start_iBGP_session(ibgp_config)

    print(r0.get_iBGP_client())
    r1.receive_iBGP_ad({"dest": 4, "gate": 0})
    r1.receive_iBGP_ad({"dest": 4, "gate": 2})

    pk = p.Packet(1, 4)

    print(r1.route(pk))
    r1.destroy_iBGP_session(0)
    print(r1.route(pk))
    r1.destroy_iBGP_session(2)
    print(r1.route(pk))
