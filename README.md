# Small Network Simulator

This is a small network simulator that supports configuring link weight, static route, Boarder Gateway Protocol, Access Control List.

## Usage
```python
import network_simulator as ns

# Initialize a graph using dictionary.
# In the dictionary, key refers to router ID, each value it corresponds to 
# is its neighbors and the link weight associated.
graph_config = {
    0: {1: 1, 3: 1},
    1: {0: 1, 3: 1, 2: 1},
    2: {1: 1, 3: 1},
    3: {0: 1, 1: 1, 2: 1},
}

# Initialize BGP settings of the graph
# If no BGP is incurred, use the setting below and change the key to 
# router ID
ibgp_config = {
    0: ns.init_bgp_config([], [], 1),
    1: ns.init_bgp_config([], [], 1),
    2: ns.init_bgp_config([], [], 1),
    3: ns.init_bgp_config([], [], 1)
}

# creates a new simulator object using the graph and BGP settings
s = ns.Simulator(graph_config, ibgp_config)

# given router IDs, route packets between two hosts in the graph
s.route(1, 3)

# change link weight between two hosts
# first and second arguments specifies the router ID, third argument
# specifies the final link weight
s.update_link_cost(1, 3, 5)

# to be continued
```

