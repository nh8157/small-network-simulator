import abc
import graph as g
import packet as p


class Middlebox:
    def __init__(self, router_id, nodes_map):
        self.id = router_id
        self.graph = g.Graph(nodes_map)
        self.routing_table = None
        self.neighbor = None
        self.iBGP = None
        self.update_routing_table()

    def get_id(self):
        return self.id

    def update_graph(self, n1, n2, cost):
        if not cost:
            self.graph.destroy_link(n1, n2)
        elif self.graph.has_link(n1, n2):
            self.graph.update_cost(n1, n2, cost)
        self.update_routing_table()

    def update_routing_table(self):
        self.routing_table = self.graph.dijkstra(self.id)

    def get_routing_table(self):
        return self.routing_table

    @abc.abstractclassmethod
    def route(self, packet):
        return NotImplemented

    @abc.abstractclassmethod
    def start_iBGP(self, *args):
        return NotImplemented

    @abc.abstractclassmethod
    def destroy_iBGP(self, *args):
        return NotImplemented


class Router(Middlebox):
    # ordinary router without any special function
    def route(self, packet: p.Packet):
        receiver = packet.get_receiver()
        packet.stamp_packet(self.get_id())
        if receiver != self.get_id():
            # packet has not arrived at the destination
            packet.dec_TTL()
        else:
            packet.terminate_packet()
        return self.get_routing_table()[receiver]

    def start_iBGP(self, *args):
        pass

    def destroy_iBGP(self, *args):
        pass

class RR(Middlebox):
    def __init__(self, router_id, graph=None, client=None):
        super().__init__(router_id, graph=graph)
        self.client = client
        self.preference = None

    def reflect_iBGP():
        pass

class Border(Middlebox):
    def __init__(self, router_id, graph=None):
        super().__init__(router_id, graph=graph)

if __name__ == '__main__':
    nodes_map = {
        0: {1: 4, 2: 2},
        1: {0: 4, 2: 1, 3: 5},
        2: {0: 2, 1: 1, 3: 8, 4: 10},
        3: {1: 5, 2: 8, 4: 2, 5: 6},
        4: {2: 10, 3: 2, 5: 5},
		5: {3: 6, 4: 5}
    }
    
    pk = p.Packet(0, 5)
    
    m0 = Router(0, nodes_map.copy())
    m1 = Router(1, nodes_map.copy())
    m2 = Router(2, nodes_map.copy())
    m3 = Router(3, nodes_map.copy())
    m4 = Router(4, nodes_map.copy())
    m5 = Router(5, nodes_map.copy())

    print(m0.get_routing_table())
    print(m2.get_routing_table())
    print(m3.get_routing_table())
    
    print(m0.route(pk))
    
    print(pk.get_TTL())