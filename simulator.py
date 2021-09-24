import router as r
import packet as p

nodes_map = {
    0: {1: 4, 2: 2},
    1: {0: 4, 2: 1, 3: 5},
    2: {0: 2, 1: 1, 3: 8, 4: 10},
    3: {1: 5, 2: 8, 4: 2, 5: 6},
    4: {2: 10, 3: 2, 5: 5},
    5: {3: 6, 4: 5}
}


def main():
    # define a new packet
    sender = 0
    receiver = 3

    pk = p.Packet(sender, receiver)

    routers = [r.Router(i, nodes_map.copy())
                for i in range(len(nodes_map.keys()))]

    while (pk.get_TTL() and not pk.has_terminate()):
        print(sender)
        sender = routers[sender].route(pk)
        print(pk.get_path())


main()
