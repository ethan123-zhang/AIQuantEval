# -*- coding: utf-8 -*-
"""Parallel range download of annotations_trainval2017.zip via local proxy (127.0.0.1:10090),
then extract only annotations/instances_val2017.json."""
import os, sys, urllib.request, concurrent.futures, time, zipfile

BASE = r'E:\Simulator\coco_val2017_500'
TMP = os.path.join(BASE, '_tmp')
ZIP_PATH = os.path.join(TMP, 'annotations_trainval2017.zip')
URL = 'http://images.cocodataset.org/annotations/annotations_trainval2017.zip'
TOTAL = 252907541
CHUNKS = 12
PROXY = 'http://127.0.0.1:10090'
UA = {'User-Agent': 'Mozilla/5.0'}
OUT_JSON = os.path.join(BASE, 'annotations', 'instances_val2017.json')
PROG = os.path.join(TMP, 'zip_progress.txt')

os.makedirs(TMP, exist_ok=True)
handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
opener = urllib.request.build_opener(handler)

def fetch_range(i):
    start = i * (TOTAL // CHUNKS)
    end = (i + 1) * (TOTAL // CHUNKS) - 1 if i < CHUNKS - 1 else TOTAL - 1
    part = os.path.join(TMP, 'part_%02d.bin' % i)
    if os.path.exists(part) and os.path.getsize(part) == end - start + 1:
        return i, 'exists'
    for attempt in range(6):
        req = urllib.request.Request(URL, headers=dict(UA, Range='bytes=%d-%d' % (start, end)))
        try:
            with opener.open(req, timeout=300) as r:
                buf = r.read()
            if len(buf) != end - start + 1:
                return i, 'short(%d/%d)' % (len(buf), end - start + 1)
            with open(part, 'wb') as f:
                f.write(buf)
            with open(PROG, 'a', encoding='utf-8') as f:
                f.write('chunk %d ok %s\n' % (i, time.strftime('%H:%M:%S')))
            return i, 'ok'
        except Exception as e:
            with open(PROG, 'a', encoding='utf-8') as f:
                f.write('chunk %d attempt%d %s\n' % (i, attempt, repr(e)[:60]))
            time.sleep(3)
    return i, 'err'

results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=CHUNKS) as ex:
    for i, st in ex.map(fetch_range, range(CHUNKS)):
        results.append((i, st))

bad = [r for r in results if r[1] != 'ok']
if bad:
    print('FAILED chunks:', bad)
    sys.exit(1)

with open(ZIP_PATH, 'wb') as out:
    for i in range(CHUNKS):
        with open(os.path.join(TMP, 'part_%02d.bin' % i), 'rb') as f:
            out.write(f.read())
print('zip size:', os.path.getsize(ZIP_PATH))

z = zipfile.ZipFile(ZIP_PATH)
names = z.namelist()
print('entries:', len(names))
target = 'annotations/instances_val2017.json'
assert target in names, 'target missing'
os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
with z.open(target) as src, open(OUT_JSON, 'wb') as dst:
    dst.write(src.read())
print('extracted ->', OUT_JSON, os.path.getsize(OUT_JSON))
print('ALL_OK')
