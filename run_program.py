"""
전체 실행
"""

import subprocess 
import time

server_list = [
    ["dns.netplus_dns"],
    ["dns.abcdn_dns"],
    ["dns.local_dns"],
    ["server.netplus_web"],
    ["server.streaming", "HQ"],
    ["server.streaming", "MQ"],
    ["server.streaming", "LQ"],
]

processes = []
try:
    for node in server_list:
        processes.append(subprocess.Popen(["python", "-m"] + node))
    time.sleep(2)

    client = subprocess.Popen(["python", "-m", "client.client"])
    processes.append(client)
    client.wait()
finally:
    for p in processes:
        p.terminate()