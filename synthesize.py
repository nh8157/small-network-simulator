from network_simulator.config import Append, ACL, StaticRoute, Update, Config
import network_simulator as ns
from copy import deepcopy
from typing import List
from policy import *

# return nodes that is in the new path 
def path_synthesize(a, b, ns_old: ns.Simulator, ns_new: ns.Simulator, config: list):
    # get old and new routes
    old_route = ns_old.route_packet(a, b)
    new_route = ns_new.route_packet(a, b)
    # find nodes common to both old and new routes
    common_nodes = find_common_nodes(edge_to_node(old_route), edge_to_node(new_route))
    # find edges that is in the new route only
    new_edges = find_diff_edges(old_route, new_route)
    # find boundary routers
    boundary_routers = find_boundary_routers(common_nodes, new_edges)
    # using boundary routers, find zones
    zones = find_zones(new_edges, boundary_routers)
    dependency = {}
    # find dependency among configs
    for c in config:
        router = c.get_router()
        for i, j in zones.items():
            # if the configuration is applied to a router in zone
            if router in j:
                try:
                    dependency[i][0].append(c)
                except KeyError:
                    dependency[i] = [[c], None, []]
            # else if the router is boundary router
            elif router == i:
                if str(c.get_config()) == "StaticRoute":
                    try:
                        dependency[i][1] = c
                    except KeyError:
                        dependency[i] = [[], c, []]
    return dependency

def find_zones(new_edges, common_nodes) -> dict:
    common = None
    zones = {}
    for i in new_edges:
        if i[0] in common_nodes:
            common = i[0]
            zones[common] = []
        else:
            zones[common].append(i[0])
    return zones

def find_boundary_routers(comm, edges):
    nodes = edge_to_node(edges)
    return find_common_nodes(nodes, comm)

def find_common_nodes(lst1: list, lst2: list):
    if len(lst1) == 0 or len(lst2) == 0:
        return []
        
    if lst1[0] == lst2[0]:
        return [lst1[0]] + find_common_nodes(lst1[1:], lst2[1:])
    else:
        c1 = find_common_nodes(lst1[1:], lst2)
        c2 = find_common_nodes(lst1, lst2[1:])
        if len(c1) > len(c2):
            return c1
        return c2

def find_diff_edges(lst1: list, lst2: list):
    edges = []
    for e in lst2:
        if e not in lst1:
            edges.append(e)
    return edges

def edge_to_node(l: List[list]):
    i = 0
    nodes = []
    while i < len(l):
        nodes.append(l[i][0])
        if i == len(l) - 1:
            nodes.append(l[i][1])
        i += 1
    return nodes

def synthesize(ns: ns.Simulator, config: list, cond: list):
    new_ns = deepcopy(ns)
    new_ns.apply_config(config)
    reachability = True
    for c in cond:
        src = c.a
        dst = c.b
        old_route = ns.route_packet(src, dst)
        new_route = new_ns.route_packet(src, dst)
        old_nodes = edge_to_node(old_route)
        new_nodes = edge_to_node(new_route)
        # needs a function to determine if a configuration would influence reachability
        relevant_config = []
        for i in config:
            router = i.get_router()
            if router in old_nodes or router in new_nodes:
                relevant_config.append(i)
        dependency = path_synthesize(src, dst, ns, new_ns, relevant_config)
        for v in dependency.values():
            for c in v[0]:
                ns.apply_config([c])
                reachability = reachability and ns.check_node_reachability(src, dst)
            ns.apply_config([c])
            reachability = reachability and ns.check_node_reachability(src, dst)

    return reachability

if __name__ == '__main__':
    graph = {
        0: {1: 1, 2: 1},
        1: {0: 1, 2: 1, 3: 1, 4: 1},
        2: {0: 1, 1: 1, 3: 1, 4: 1},
        3: {1: 1, 2: 1, 4: 1, 5: 1},
        4: {1: 1, 2: 1, 3: 1, 5: 1},
        5: {3: 1, 4: 1}
    }
    ibgp = {}
    for i in range(6):
        ibgp[i] = ns.init_bgp_config([], [], 1)

    s = ns.Simulator(graph, ibgp)

    config = []
    for i in graph.keys():
        for a in graph.keys():
            for b in graph.keys():
                config.append(Append(ACL(True, a, b), i))
    config.append(Append(StaticRoute(1, 2), 3))
    config.append(Append(StaticRoute(1, 1), 2))
    s.apply_config(config)
    # assert s.route_packet(0, 1) == [[0, 2], [2, 1]]
    
    new_config = []
    new_config.append(Update(StaticRoute(1, 4), 3, Config(StaticRoute(1, 2), 3)))
    new_config.append(Append(StaticRoute(1, 2), 4))
    new_config.append(Update(StaticRoute(1, 0), 2, Config(StaticRoute(1, 1), 2)))
    new_config.append(Append(StaticRoute(1, 1), 0))

    cond = [Reachability(5, 1)]

    reachability = synthesize(s, new_config, cond)
    assert reachability == True