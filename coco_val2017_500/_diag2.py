import socket, ssl

log = open(r'E:\Simulator\coco_val2017_500\_diag2.log', 'w', encoding='utf-8')
def p(*a):
    print(*a, file=log, flush=True)

# 1) what cert is served at the polluted IP
ip = '16.15.230.214'
try:
    ctx = ssl._create_unverified_context()
    with socket.create_connection((ip, 443), timeout=10) as s:
        with ctx.wrap_socket(s, server_hostname='images.cocodataset.org') as ss:
            cert = ss.getpeercert()
            p('cert subject:', cert.get('subject'))
            p('cert SAN:', cert.get('subjectAltName'))
            p('cert issuer:', cert.get('issuer'))
except Exception as e:
    p('cert fetch fail:', repr(e))

# 2) resolve via common public resolvers using UDP
import struct, random

def dns_query(domain, server):
    tid = random.randint(0, 65535)
    header = struct.pack('>HHHHHH', tid, 0x0100, 1, 0, 0, 0)
    q = b''.join(bytes([len(x)]) + x.encode() for x in domain.split('.')) + b'\x00'
    q += struct.pack('>HH', 1, 1)
    pkt = header + q
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(5)
    s.sendto(pkt, (server, 53))
    data, _ = s.recvfrom(4096)
    s.close()
    # parse answer section (skip question)
    idx = 12
    while data[idx] != 0:
        idx += 1 + data[idx]
    idx += 5
    answers = []
    ancount = struct.unpack('>H', data[6:8])[0]
    for _ in range(ancount):
        # skip name (compressed)
        while True:
            l = data[idx]
            if l & 0xC0 == 0xC0:
                idx += 2
                break
            elif l == 0:
                idx += 1
                break
            else:
                idx += 1 + l
        rtype, rclass, ttl, rdlen = struct.unpack('>HHIH', data[idx:idx+10])
        idx += 10
        if rtype == 1 and rdlen == 4:
            answers.append('.'.join(str(b) for b in data[idx:idx+4]))
        idx += rdlen
    return answers

for server in ['8.8.8.8', '1.1.1.1', '223.5.5.5', '119.29.29.29']:
    try:
        p(server, '->', dns_query('images.cocodataset.org', server))
    except Exception as e:
        p(server, '-> fail:', repr(e))

log.close()
