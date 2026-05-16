"""
config.txt parsing 용도 

"""

def parse_config(path="config.txt"):
    address_dict = {}
    with open(path) as file:
        for addresses in file:
            addresses = addresses.strip()
            node_name, add = addresses.split("=", 1)
            ip, port = add.strip().split(":", 1)
            address_dict[node_name.strip()] = (ip.strip(), int(port.strip()))
    return address_dict