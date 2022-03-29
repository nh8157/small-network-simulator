import network_simulator as ns
graph_config = {
        0: {1: 1, 3: 1},
        1: {0: 1, 3: 1, 2: 1},
        2: {1: 1, 3: 1},
        3: {0: 1, 1: 1, 2: 1},
    }

ibgp_config = {
        0: ns.init_bgp_config([], [], 1),
        1: ns.init_bgp_config([], [], 1),
        2: ns.init_bgp_config([], [], 1),
        3: ns.init_bgp_config([], [], 1)
}

s = ns.Simulator(graph_config, ibgp_config)

for i in graph_config.keys():
    for a in graph_config.keys():
        for b in graph_config.keys():
            s.add_acl(i, True, a, b)

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

print()

paths = s.generate_possible_paths(2, 3)
print(paths)
for p in paths:
    print(p)
    print(s.check_path_reachability(p))

print()
print(s.check_node_reachability(2, 3))
print(s.check_node_reachability(2, 0))