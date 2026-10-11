import socket, ssl, urllib.request

log = open(r'E:\Simulator\coco_val2017_500\_diag3.log', 'w', encoding='utf-8')
def p(*a):
    print(*a, file=log, flush=True)

host = 'images.cocodataset.org'
ips = ['52.216.27.88', '16.15.253.45', '52.217.118.218', '16.15.247.13', '16.15.236.117', '54.231.131.82', '54.231.170.194']

for ip in ips:
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((ip, 443), timeout=8) as s:
            with ctx.wrap_socket(s, server_hostname=host) as ss:
                p(ip, 'TLS-VERIFIED-OK', ss.version())
    except Exception as e:
        p(ip, 'fail:', type(e).__name__, str(e)[:80])

# plain HTTP test
for url in ['http://images.cocodataset.org/val2017/000000000139.jpg',
            'http://images.cocodataset.org/annotations/instances_val2017.json']:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            p('HTTP', url, '->', r.status, r.headers.get('Content-Length'), r.headers.get('Content-Type'))
    except Exception as e:
        p('HTTP', url, '-> fail:', repr(e))

log.close()
