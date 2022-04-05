from network_simulator.config import Append, ACL, StaticRoute, Update, Config
import network_simulator as ns
import dep_graph as dep
from copy import deepcopy
from typing import List
from policy import *

# order configurations that influences reachability between the two nodes
def path_synthesize(old_route: list, new_route: list, config: list) -> dict:
    # find nodes common to both old and new routes
    common_nodes = find_common_nodes(edge_to_node(old_route), edge_to_node(new_route))
    # find edges that is in the new route only
    new_edges = find_diff_edges(old_route, new_route)
    # find boundary routers
    boundary_routers = find_boundary_routers(common_nodes, new_edges)
    # using boundary routers, find zones
    zones = find_zones(new_edges, boundary_routers)
    # find dependency among configs
    dependency = {}
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

# return zones in the new graph encompassed by boundary routers
def find_zones(new_edges, boundary_routers) -> dict:
    common = None
    zones = {}
    for i in new_edges:
        if i[0] in boundary_routers:
            common = i[0]
            zones[common] = []
        else:
            zones[common].append(i[0])
    return zones

# find boundary routers that encompass disparate zones
def find_boundary_routers(comm, edges) -> list:
    nodes = edge_to_node(edges)
    return find_common_nodes(nodes, comm)

# find nodes that exist in both paths
def find_common_nodes(lst1: list, lst2: list) -> list:
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

# returns a list of configurations that is either on the old path or the new path
def find_relevant_config(old_route, new_route, config) -> list:
    # convert from the edge expression to the node expression
    old_nodes = edge_to_node(old_route)
    new_nodes = edge_to_node(new_route)
    relevant_config = []
    for i in config:
        router = i.get_router()
        if router in old_nodes or router in new_nodes:
            relevant_config.append(i)
    return relevant_config

# finds edges that is unique to lst2
def find_diff_edges(lst1: list, lst2: list) -> list:
    edges = []
    for e in lst2:
        if e not in lst1:
            edges.append(e)
    return edges

# converts a path from a list of edges to a list of nodes
def edge_to_node(l: List[list]) -> list:
    i = 0
    nodes = []
    while i < len(l):
        nodes.append(l[i][0])
        if i == len(l) - 1:
            nodes.append(l[i][1])
        i += 1
    return nodes

# construct a dependency graph based on the dependent relationships given
def construct_dependency_graph(dep_dict: dict) -> list:
    pass

# order configurations according to the 
def synthesize(old_ns: ns.Simulator, config: list, cond: list) -> bool:
    new_ns = deepcopy(old_ns)
    new_ns.apply_config(config)
    reachability = True
    dependency = {}
    for c in cond:
        src, dst = c.a, c.b
        old_route = old_ns.route(src, dst)
        new_route = new_ns.route(src, dst)
        relevant_config = find_relevant_config(old_route, new_route, config)
        dependency[c] = path_synthesize(old_route, new_route, relevant_config)
        for v in dependency[c].values():
            for c in v[0]:
                old_ns.apply_config([c])
                reachability = reachability and old_ns.check_node_reachability(src, dst)
            old_ns.apply_config([c])
            reachability = reachability and old_ns.check_node_reachability(src, dst)
        print(reachability)
    # need a final step here to construct the dependency graph    
    return dependency

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
    config.append(Append(StaticRoute(3, 3), 2))
    s.apply_config(config)
    
    new_config = []
    new_config.append(Update(StaticRoute(1, 4), 3, Config(StaticRoute(1, 2), 3)))
    new_config.append(Append(StaticRoute(1, 2), 4))
    new_config.append(Update(StaticRoute(1, 0), 2, Config(StaticRoute(1, 1), 2)))
    new_config.append(Append(StaticRoute(1, 1), 0))
    new_config.append(Update(StaticRoute(3, 4), 2, Config(StaticRoute(3, 3), 2)))
    new_config.append(Append(StaticRoute(3, 3), 4))

    cond = []

    for i in range(6):
        for j in range(6):
            cond.append(Reachability(i, j))

    dependency = synthesize(s, new_config, cond)
    print(dependency)