"""Deterministic pose-group slicing and row-wide registration of transparent art."""
from pathlib import Path
import json
from PIL import Image
p=Path(__file__).resolve().parent
src=Image.open(p/'decoded/jumping.png').convert('RGBA');a=src.getchannel('A')
hist=a.histogram();w,h=src.size
if hist[0]<w*h*.1: raise SystemExit('Source lacks sufficient actual alpha transparency')
data=a.tobytes()
used=[sum(data[y*w+x]>16 for y in range(h))>=3 for x in range(w)]
runs=[];start=None
for x,val in enumerate(used+[False]):
 if val and start is None: start=x
 if not val and start is not None:
  if x-start>=10:runs.append((start,x))
  start=None
if len(runs)!=5:raise SystemExit(f'Expected5 separated pose groups, got{runs}')
boundaries=[0]+[(runs[i][1]+runs[i+1][0])//2 for i in range(4)]+[w]
slots=[];boxes=[];edge_info=[]
for i in range(5):
 im=src.crop((boundaries[i],0,boundaries[i+1],h));aa=im.getchannel('A');core=aa.point(lambda v:255 if v>1 else 0).getbbox();box=(max(0,core[0]-8),max(0,core[1]-8),min(im.width,core[2]+8),min(h,core[3]+8)) if core else None
 if not box:raise SystemExit(f'Empty generated pose{i}')
 side=max(aa.crop((0,0,1,h)).getextrema()[1],aa.crop((im.width-1,0,im.width,h)).getextrema()[1])
 if side>16:raise SystemExit(f'Visible clipping at pose{i}:side_alpha{side}')
 slots.append(im);boxes.append(box);edge_info.append(side)
top=min(b[1] for b in boxes);bottom=max(b[3] for b in boxes)
width=max(b[2]-b[0] for b in boxes);height=bottom-top
scale=min(182/width,198/height,1)
frame_dir=p/'frames/jumping';frame_dir.mkdir(parents=True,exist_ok=True)
info=[]
for i,(im,b) in enumerate(zip(slots,boxes)):
 view=Image.new('RGBA',(width,height))
 view.paste(im.crop((b[0],top,b[2],bottom)),((width-(b[2]-b[0]))//2,0))
 view=view.resize((round(width*scale),round(height*scale)),Image.Resampling.LANCZOS)
 frame=Image.new('RGBA',(192,208));frame.paste(view,((192-view.width)//2,(208-view.height)//2))
 raw=bytearray(frame.tobytes())
 for j in range(0,len(raw),4):
  if raw[j+3]==0:raw[j:j+3]=b'\0\0\0'
 frame=Image.frombytes('RGBA',frame.size,bytes(raw));frame.save(frame_dir/f'{i:02}.png')
 info.append({'slot':i,'source_bbox':b,'final_bbox':frame.getbbox(),'source_boundary_max_alpha':edge_info[i]})
report={'ok':True,'source_size':src.size,'pose_group_boundaries':boundaries,'transparent_pixels':hist[0],'partial_alpha_pixels':sum(hist[1:255]),'shared_scale':scale,'alpha_cleanup':'Generated alpha preserved within registered viewport; bbox based on alpha>1 plus8px padding excludes remote1/255 noise; hidden RGB cleared. Faint boundary alpha requires visual review.','frames':info}
(p/'qa/extraction.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
