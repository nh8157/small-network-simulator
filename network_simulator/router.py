import abc
import network_simulator.graph as g
import network_simulator.packet as p

# base class of all router types
class Middlebox:
    def __init__(self, router_id, nodes_map):
        self.id = router_id
        self.graph = g.Graph(nodes_map)
        # IGP config
        self.routing_table = None
        # all routes are dynamic by default
        # call dynamic_to_static to switch to static mode
        self.static_route = []
        # BGP config
        self.neighbor = None
        self.iBGP_msg = {}
        self.iBGP = {
            'client': [],
            'server': []
        }
        # Access-control configs stored in a list of dictionaries
        self.acl = []   # if no match till the end of the list, then denied
        # update routing table upon initialization
        self.update_routing_table()

    def get_id(self):
        return self.id

    def update_graph(self, n1, n2, cost):
        # destroys the link when the cost is 0
        if not cost:
            self.graph.destroy_link(n1, n2)
        elif self.graph.has_link(n1, n2):
            self.graph.update_cost(n1, n2, cost)
        self.append_routing_table()
        self.update_routing_table()

    def route(self, packet: p.Packet):
        # get the receiver of this packet
        # then track put self.id on the packet
        receiver = packet.get_receiver()
        # if the packet is not allowed by the acl
        if not self.check_acl(packet.get_sender(), packet.get_receiver()):
            print("Packet denied")
            packet.terminate_packet()
            return None
        packet.stamp_packet(self.get_id())
        # self is not the receipient of this packet
        if receiver != self.get_id():
            # packet has not arrived at the destination
            packet.dec_TTL()
        else:
            # successfully received the packet
            packet.terminate_packet()
            return None
        try:
            next_hop = self.get_routing_table()[receiver]
            # TTL is still valid and packet not yet terminated
            if packet.get_TTL() > 0 and not packet.has_terminate():
                if next_hop != None:
                    return next_hop
                # packet has reached boundary router
                print("Intra-AS -> Inter-AS")
                packet.terminate_packet()
                return None
            # TTL reaches 0, packet dropped
            elif not packet.get_TTL() and not packet.has_terminate():
                packet.terminate_packet()
                print("Forwarding loop detected")
                return None

        except KeyError:
            packet.terminate_packet()
            print("Destination not reachable")
            return None

    def update_routing_table(self):
        new_table = self.graph.dijkstra(self.id)
        # swap the next hop for static route with the one in the old dictionary
        for i in self.static_route:
            new_table[i] = self.routing_table[i]
        self.routing_table = new_table

    def append_routing_table(self, dest, gateway) -> None:
        self.routing_table[dest] = gateway

    def remove_routing_table(self, dest) -> None:
        del self.routing_table[dest]

    def get_routing_table(self):
        return self.routing_table.copy()

    def get_next_hop(self, dst):
        return self.get_routing_table()[dst]

    # adds a static route to the current routing table
    def add_static_route(self, dst, nh) -> bool:
        # check if the route is in static route mode
        if dst in self.static_route:
            # check if the next hop is self's neighbor
            if not self.graph.has_link(self.id, nh):
                print("No link between", self.id, nh)
                return False
            # overwrites the existing entry (if any exists)
            self.routing_table[dst] = nh
            return True
        return False

    # removes a static route from the current routing table
    def remove_static_route(self, dst) -> bool:
        # first checks if there is a static route
        if dst not in self.static_route:
            print("Not a static route")
            return False
        # removes this route from the routing table and the static route entry
        # once a static entry is deleted, the link automatically 
        del self.routing_table[dst]
        return True

    # changes a route's state from dynamic to static    
    def dynamic_to_static(self, dst) -> bool:
        # the route was not set as static route
        if dst not in self.static_route:
            self.static_route.append(dst)
            # remove the dynamic route in the routing table
            try:
                del self.routing_table[dst]
            except KeyError:
                print("Unknown destination")
            return True
        # the route was already set as static route
        return False

    # changes a route's state from static to dynamic
    def static_to_dynamic(self, dst) -> bool:
        # the route was set as static
        if dst in self.static_route:
            self.static_route.remove(dst)
            # runs graph algo to recalculate the path
            self.update_routing_table()
            return True
        # the route was not set as static
        return False

    # get the list of routes that are configured statically
    def get_static_route(self) -> list:
        return self.static_route.copy()

    # get whether the route is configured statically or dynamically
    def get_route_mode(self, dst) -> bool:
        # returns true if the route is static, false otherwise
        return dst in self.static_route
    
    # check whether a packet is accepted by the router
    def check_acl(self, src, dst) -> bool:
        for i in self.acl:
            if i["src"] == src and i["dst"] == dst:
                return i["act"]
        return False

    # add a rule into ACL list
    def add_acl(self, act, src, dst, pos=-1) -> bool:
        acl = self.init_acl(act, src, dst)
        if acl not in self.acl:
            if pos == -1:
                self.acl.append(acl)
            else:
                self.acl.insert(pos, acl)
            return True
        else:
            return False

    # remove a rule from the ACL list
    def remove_acl(self, act, src, dst) -> bool:
        acl = self.init_acl(act, src, dst)
        try:
            self.acl.remove(acl)
            return True
        except ValueError:
            return False

    # return a new acl rule
    def init_acl(self, act, src, dst) -> dict:
        return  {
                "act": act,
                "src": src,
                "dst": dst
                }

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
        # print(self.get_id(), router, advert)
        for dest in self.iBGP_msg.keys():
            for i in self.iBGP_msg[dest]:
                # the router is the advertiser of the iBGP msg or the gateway
                # print(self.get_id(), "IBG_msg", i)
                if router == i[0] and advert == i[1]:
                    # if the router is one of the gateway routers to an external dest
                    # print(self.get_id(), "removing", router, advert)
                    # print("route removed")
                    self.iBGP_msg[dest].remove(i)
                    if not len(self.iBGP_msg[dest]):
                        del self.iBGP_msg[dest]
                        self.remove_routing_table(dest)
                        return self.iBGP['client'], self.get_id(), None
                    else:
                        self.opt_iBGP_route(dest)
                        router = self.routing_table[dest]
                        ad = {
                            'dest': [dest],
                            'gate': router,
                            'advertiser': self.get_id()
                        }
        # if self is a route reflector then return the list of client so that these clients also remove the ad from their list
        return self.iBGP['client'], self.get_id(), ad

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
                return self.remove_iBGP_ad(i, args[1])
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
        return None

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
        0: {1: 1, 3: 1},
        1: {0: 1, 3: 1, 2: 1},
        2: {1: 1, 3: 1},
        3: {0: 1, 1: 1, 2: 1},
    }

    routers = [Router(i, graph_config) for i in range(4)]
    pk = p.Packet(1, 3)

    for r in routers:
        for i in range(len(routers)):
            for j in range(len(routers)):
                r.add_acl(True, i, j)
    
    # before changing to static route
    routers[1].route(pk)

    # change to static route
    routers[1].dynamic_to_static(3)
    routers[1].add_static_route(3, 0)

    routers[1].route(pk)

    # change back to dynamic route
    routers[1].remove_static_route(3)
    routers[1].static_to_dynamic(3)
    
    routers[1].route(pk)

    # deny access on router 0
    print(routers[0].remove_acl(True, 1, 3))

    routers[0].route(pk) 

    # routers[0].dynamic_to_static(2)
    # routers[0].add_static_route(2, 2)
    # r0.start_iBGP_session(ibgp_config)
    # r1.start_iBGP_session(ibgp_config)
    # r2.start_iBGP_session(ibgp_config)

    # ad = r0.draft_iBGP_ad(4)
    # r = r0.get_iBGP_client()
    # print(r)

    # argv = r1.receive_iBGP_ad(ad)
    # print(argv)

    # r = argv[1]

    # argv = r2.receive_iBGP_ad(argv[0])
    # print(argv)
    # r1.receive_iBGP_ad({"dest": 4, "gate": 0, "advertiser": 0})
    # r1.receive_iBGP_ad({"dest": 4, "gate": 2, "advertiser": 2})

    # pk = p.Packet(1, 4)

    # print(r1.route(pk))
    # r1.destroy_iBGP_session(0)
    # print(r1.route(pk))
    # r1.destroy_iBGP_session(2)
    # print(r1.route(pk))
