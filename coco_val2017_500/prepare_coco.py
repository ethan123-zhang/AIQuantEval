# -*- coding: utf-8 -*-
"""Prepare COCO val2017 subset: pick 500 images, download via proxy, build filtered annotations."""
import os, json, random, urllib.request, concurrent.futures, time

BASE = r'E:\Simulator\coco_val2017_500'
ANN_FULL = os.path.join(BASE, 'annotations', 'instances_val2017.json')
IMG_DIR = os.path.join(BASE, 'images', 'val2017')
TMP = os.path.join(BASE, '_tmp')
SEL_IDS = os.path.join(TMP, 'selected_image_ids.txt')
ANN_SUB = os.path.join(BASE, 'annotations', 'instances_val2017_sub500.json')
TXT_LIST = os.path.join(BASE, 'val2017_sub500.txt')
PROG = os.path.join(TMP, 'img_progress.txt')
N_SELECT = 500
SEED = 42
WORKERS = 16
PROXY = 'http://127.0.0.1:10090'

os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(TMP, exist_ok=True)
handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
opener = urllib.request.build_opener(handler)

with open(ANN_FULL, 'r', encoding='utf-8') as f:
    data = json.load(f)
all_images = data['images']
print('total val2017 images in json:', len(all_images))

rng = random.Random(SEED)
selected = rng.sample(all_images, N_SELECT)
selected.sort(key=lambda im: im['id'])
with open(SEL_IDS, 'w', encoding='utf-8') as f:
    for im in selected:
        f.write(str(im['id']) + '\n')
print('selected', len(selected), 'image ids')

def download(im):
    fn = im['file_name']
    dest = os.path.join(IMG_DIR, fn)
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        return fn, 'exists'
    url = 'http://images.cocodataset.org/val2017/' + fn
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with opener.open(req, timeout=180) as r:
                buf = r.read()
            if len(buf) < 1000 or buf[:3] != b'\xff\xd8\xff':
                return fn, 'bad-jpeg(%d)' % len(buf)
            with open(dest, 'wb') as f:
                f.write(buf)
            with open(PROG, 'a', encoding='utf-8') as f:
                f.write('%s ok\n' % fn)
            return fn, 'ok'
        except Exception as e:
            with open(PROG, 'a', encoding='utf-8') as f:
                f.write('%s attempt%d %s\n' % (fn, attempt, repr(e)[:60]))
            time.sleep(1)
    return fn, 'err'

ok = fail = 0
with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as ex:
    for fn, status in ex.map(download, selected):
        if status in ('ok', 'exists'):
            ok += 1
        else:
            fail += 1
            print('FAIL', fn, status)
print('images ok/exists:', ok, 'failed:', fail)

sel_ids = {im['id'] for im in selected}
anns = [a for a in data['annotations'] if a['image_id'] in sel_ids]
subset = {
    'info': data.get('info'),
    'licenses': data.get('licenses'),
    'images': selected,
    'annotations': anns,
    'categories': data['categories'],
}
with open(ANN_SUB, 'w', encoding='utf-8') as f:
    json.dump(subset, f)
print('subset annotations:', len(anns))

with open(TXT_LIST, 'w', encoding='utf-8') as f:
    for im in selected:
        f.write(os.path.join(IMG_DIR, im['file_name']).replace('\\', '/') + '\n')
print('image list ->', TXT_LIST)
print('DONE')
