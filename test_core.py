"""
protocol, time_utils, log_utils 테스트

"""

from core.protocol import pack, unpack
from core.time_utils import now_time, time_to_ms, elapsed_time
from core.log_utils import get_logger

def test_protocol():
    test_msg = [
        {"type": "info_rqst", "movie_id": 1},
        {"type": "info_rsp", "movie_id": 1, "index_url": "https://index.netplus.com/1234"},
        
        {"type": "dns_rqst", "url_name": "index.netplus.com/1234", "txid": 42},
        {"type": "dns_rsp", "url_name_echo": "index.netplus.com/1234", "txid": 42, "answer": "abCDN.net/"},
        # manifest
        {"type": "dns_rsp", "url_name_echo": "abCDN.net/", "txid": 99,
         "answer": {"HQ": "127.0.0.1:50000", "MQ": "127.0.0.1:50001", "LQ": "127.0.0.1:50002"}},
        
        {"type": "chunk_rqst", "movie_id": 1, "encoding_type": "HQ", "chunk_index": 0,
         "last_watched_time": "00:00:00:000"},
        {"type": "chunk_rsp", "movie_id": 1, "encoding_type": "HQ", "chunk_index": 0,
         "start_time": "00:00:00:000", "end_time": "00:00:04:000", "payload_size": 1024},
    ]

    for i in test_msg:
        assert unpack(pack(i)) == i, f"FAIL: {i}"
    print("protocol roundtrip OK")

test_protocol()