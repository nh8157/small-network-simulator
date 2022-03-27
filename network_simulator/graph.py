class Graph:
    def __init__(self, nodes_map) -> None:
        self.nb_nodes = len(nodes_map.keys())
        self.table = None
        self.map = nodes_map

    def dijkstra(self, source) -> dict:
        visited = 0
        routing = {}
        table = {i: {'dist': float("inf"), 'pred': None, 'visited': False}
                for i in self.map.keys()}
        table[source]['dist'] = 0
        while visited < self.nb_nodes:
            # obtain the node with the least total distance
            min_node = None
            min_cost = float("inf")
            for i in table.keys():
                if table[i]['dist'] < min_cost and not table[i]['visited']:
                    min_node = i
                    min_cost = table[i]['dist']
            # explore neighbors through links
            for n in self.map[min_node].keys():
                if not table[n]['visited']:
                    dist = self.map[min_node][n] + min_cost
                    if dist < table[n]['dist']:
                        table[n]['dist'] = dist
                        table[n]['pred'] = min_node
            visited += 1
            table[min_node]['visited'] = True
        # construct the routing table, given the dijkstra table
        self.table = table
        # do we need another field to specify whether the route is static or dynamic?
        routing = {dst: self.get_next_hop(table, source, dst) for dst in self.map.keys()}
        return routing

    def get_next_hop(self, table, source, dst):
        if table[dst]["pred"] == source:
            return dst
        elif dst == source:
            return None
        return self.get_next_hop(table, source, table[dst]['pred'])
    
    def get_cost(self, dest) -> int:
        return self.table[dest]['dist']

    def has_link(self, n1, n2) -> bool:
        return n1 in self.map[n2].keys() and n2 in self.map[n1].keys()

    def create_link(self, n1, n2, cost=1) -> None:
        if n2 not in self.map[n1].keys() and n1 not in self.map[n2].keys():
            self.map[n1][n2] = cost
            self.map[n2][n1] = cost

    def update_cost(self, n1, n2, cost) -> None:
        if n2 in self.map[n1].keys() and n1 in self.map[n2].keys():
            self.map[n1][n2] = cost
            self.map[n2][n1] = cost
        else:
            self.create_link(n1, n2, cost)

    def destroy_link(self, n1, n2) -> None:
        if n2 in self.map[n1].keys() and n1 in self.map[n2].keys():
            del self.map[n1][n2]
            del self.map[n2][n1]

    def get_map(self) -> dict:
        return self.map.copy()
    
    def get_table(self) -> dict:
        return self.table.copy()


if __name__ == '__main__':
    # creates a graph with link cost default to zero
    nodes_map = {
        0: {1: 4, 2: 2},
        1: {0: 4, 2: 1, 3: 5},
        2: {0: 2, 1: 1, 3: 8, 4: 10},
        3: {1: 5, 2: 8, 4: 2, 5: 6},
        4: {2: 10, 3: 2, 5: 5},
		5: {3: 6, 4: 5}
    }
    g = Graph(nodes_map)
    print(g.get_map())
    print(g.dijkstra(0))