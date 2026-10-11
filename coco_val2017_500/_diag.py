import socket, ssl, urllib.request, sys

log = open(r'E:\Simulator\coco_val2017_500\_diag.log', 'w', encoding='utf-8')
def p(*a):
    print(*a, file=log, flush=True)

host = 'images.cocodataset.org'
try:
    p('local resolve:', socket.gethostbyname(host))
except Exception as e:
    p('resolve fail:', repr(e))

try:
    ctx = ssl.create_default_context()
    with socket.create_connection((host, 443), timeout=10) as s:
        with ctx.wrap_socket(s, server_hostname=host) as ss:
            p('TLS ok:', ss.version())
            cert = ss.getpeercert()
            p('subject:', cert.get('subject'))
            p('issuer:', cert.get('issuer'))
except Exception as e:
    p('TLS fail:', repr(e))

for url in ['https://www.baidu.com', 'https://github.com', 'https://images.cocodataset.org/val2017/000000000139.jpg']:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            p(url, '->', r.status, r.headers.get('Content-Length'))
    except Exception as e:
        p(url, '-> fail:', repr(e))

log.close()
