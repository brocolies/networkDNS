"""
dns_rqst(abCDN url을 달고 옴)가 들어왔을 때, 적절한 manifest file을 반환하는지

"""
import socket
from core.protocol import pack, unpack
from core.config_utils import parse_config

config = parse_config()
abcdn_dns_addr = config["abCDN_dns_server"]

query = {
    "type": "dns_rqst",
    "url": index.
}