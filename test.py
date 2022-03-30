from network_simulator.config import ACL, Append, Config, LinkWeight, Remove, StaticRoute, Update
import network_simulator as ns

if __name__ == '__main__':
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

    acl_config = []

    for i in graph_config.keys():
        for a in graph_config.keys():
            for b in graph_config.keys():
                acl_config.append(Append(ACL(True, a, b), i))

    s.apply_config(acl_config)

    # before switching to static route
    p = s.route_packet(1, 3)
    assert p == [[1, 3]]

    # after switching to static route
    c1 = [Append(StaticRoute(3, 0), 1)]
    s.apply_config(c1)
    # s.add_static_route(1, 3, 0)
    p = s.route_packet(1, 3)
    assert p == [[1, 0], [0, 3]]

    c2 = [Append(StaticRoute(3, 2), 1)]
    s.apply_config(c2)
    # s.del_static_route(1, 3)
    # s.switch_route_mode(1, 3)
    p = s.route_packet(1, 3)
    assert p == [[1, 2], [2, 3]]

    c3 = [Remove(ACL(True, 1, 3), 2)]
    s.apply_config(c3)
    p = s.route_packet(1, 3)
    assert p == [[1, 2]]
    
    print("Test complete")