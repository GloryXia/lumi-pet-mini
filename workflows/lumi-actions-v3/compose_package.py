"""Replace only the generated jump row in the approved transparent v2 atlas."""
from PIL import Image
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parents[2];run=root/'workflows/lumi-actions-v3';out=root/'assets/pets/lumi-actions-v3'
a=Image.open(root/'assets/pets/lumi-actions-v2/spritesheet.webp').convert('RGBA');base=a.copy()
row=Image.new('RGBA',(1536,208))
for i in range(5):row.paste(Image.open(run/'frames/jumping'/f'{i:02}.png').convert('RGBA'),(i*192,0))
a.paste(row,(0,4*208));a.save(out/'spritesheet.webp',lossless=True,exact=True,method=6)
f=Image.open(out/'spritesheet.webp').convert('RGBA');preserved=[]
for r in range(11):
 if r==4:continue
 box=(0,r*208,1536,(r+1)*208)
 assert f.crop(box).tobytes()==base.crop(box).tobytes()
 preserved.append(r)
(run/'qa/preservation.json').write_text(json.dumps({'ok':True,'pixel_exact_preserved_vs_previous_package':preserved},indent=2))
names=['idle','running-right','running-left','waving','jumping','failed','waiting','running','review'];counts=[6,8,8,4,5,8,6,6,6]
for r,(name,count) in enumerate(zip(names,counts)):
 d=run/'final-frames'/name;d.mkdir(parents=True,exist_ok=True)
 for i in range(count):f.crop((i*192,r*208,(i+1)*192,(r+1)*208)).save(d/f'{i:02}.png')
f.crop((0,0,192,208)).save(out/'lumi-preview.png')
print(json.dumps({'ok':True,'size':f.size,'preserved_rows':preserved,'sha256':hashlib.sha256((out/'spritesheet.webp').read_bytes()).hexdigest()}))
