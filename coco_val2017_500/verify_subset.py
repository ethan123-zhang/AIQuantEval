# -*- coding: utf-8 -*-
"""Final integrity verification of the COCO val2017 500-image subset."""
import os, json, glob

BASE = r'E:\Simulator\coco_val2017_500'
IMG_DIR = os.path.join(BASE, 'images', 'val2017')
ANN_SUB = os.path.join(BASE, 'annotations', 'instances_val2017_sub500.json')
TXT = os.path.join(BASE, 'val2017_sub500.txt')

log = open(os.path.join(BASE, '_tmp', 'verify.log'), 'w', encoding='utf-8')
def p(*a): print(*a, file=log, flush=True)

# 1) files on disk
files = glob.glob(os.path.join(IMG_DIR, '*.jpg'))
p('disk jpg files:', len(files))
zero = [f for f in files if os.path.getsize(f) == 0]
p('zero-size files:', len(zero))

# 2) JPEG magic check for all
bad = []
for f in files:
    with open(f, 'rb') as fh:
        magic = fh.read(3)
    if magic != b'\xff\xd8\xff':
        bad.append(os.path.basename(f))
p('bad JPEG magic:', len(bad), bad[:10])

# 3) subset json structure
d = json.load(open(ANN_SUB, encoding='utf-8'))
p('subset json images:', len(d['images']))
p('subset json annotations:', len(d['annotations']))
p('subset json categories:', len(d['categories']))

# 4) json images <-> disk coverage
disk_names = {os.path.basename(f) for f in files}
json_names = {im['file_name'] for im in d['images']}
p('json images missing on disk:', len(json_names - disk_names))
p('disk files not in json:', len(disk_names - json_names))

# 5) annotation coverage: every json image has >=0 anns, count anns per image
from collections import Counter
cnt = Counter(a['image_id'] for a in d['annotations'])
img_ids = {im['id'] for im in d['images']}
ann_img_ids = set(cnt)
p('annotated images:', len(ann_img_ids), '/', len(img_ids))
p('images with 0 annotations:', len(img_ids - ann_img_ids))
p('max anns on one image:', max(cnt.values()))
p('total bbox fields ok:', all(len(a.get('bbox', [])) == 4 for a in d['annotations']))

# 6) txt list
with open(TXT, encoding='utf-8') as f:
    lines = [l.strip() for l in f if l.strip()]
p('txt lines:', len(lines))
p('txt paths exist:', sum(1 for l in lines if os.path.exists(l.replace('/', '\\'))))
p('txt matches json order:', [im['file_name'] for im in d['images']] == [l.rsplit('/', 1)[-1] for l in lines])

# 7) sizes
tot = sum(os.path.getsize(f) for f in files)
p('images total: %.1f MB' % (tot / 1048576))
p('json size: %.1f MB' % (os.path.getsize(ANN_SUB) / 1048576))
p('VERIFY_DONE')
log.close()
