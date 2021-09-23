import abc
import graph as g


class Middlebox:
    def __init__(self, router_id, nodes_map):
        self.id = router_id
        self.graph = g.Graph(nodes_map)
        self.routing_table = None
        self.neighbor = None
        self.iBGP = None
        self.update_routing_table()

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
    def route(self, packet):
        pass

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
    m0 = Middlebox(0, nodes_map.copy())
    m1 = Middlebox(1, nodes_map.copy())
    m2 = Middlebox(2, nodes_map.copy())
    m3 = Middlebox(3, nodes_map.copy())
    m4 = Middlebox(4, nodes_map.copy())
    m5 = Middlebox(5, nodes_map.copy())

    print(m1.get_routing_table())
    print(m2.get_routing_table())
    print(m3.get_routing_table())