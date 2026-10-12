"""Slice AI-rendered 4×2 run grids and register them in native 192×208 cells."""
from pathlib import Path
import argparse
import hashlib
import json
import statistics
from PIL import Image

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[1]


def head_box(image, box):
    left, top, right, bottom = box
    band = image.crop((left, top, right, min(bottom, top + round((bottom-top)*0.44))))
    raw = band.tobytes()
    mask = bytearray(band.width*band.height)
    for i in range(len(mask)):
        r,g,b,a = raw[i*4:i*4+4]
        mask[i] = 255 if a>100 and r<110 and g<125 and b<165 else 0
    b = Image.frombytes('L',band.size,bytes(mask)).getbbox()
    if b is None:
        raise ValueError('Cannot find navy hair for registration')
    return left+b[0], top+b[1], left+b[2], top+b[3]


def extract(state, source):
    source = Path(source)
    image = Image.open(source).convert('RGBA')
    if image.getchannel('A').histogram()[0] < image.width*image.height*0.12:
        raise ValueError('Source must have genuine alpha transparency')
    slots, boxes, heads = [], [], []
    for i in range(8):
        x0=round((i%4)*image.width/4);x1=round(((i%4)+1)*image.width/4)
        y0=round((i//4)*image.height/2);y1=round(((i//4)+1)*image.height/2)
        slot=image.crop((x0,y0,x1,y1))
        box=slot.getchannel('A').point(lambda a:255 if a>32 else 0).getbbox()
        if box is None:
            raise ValueError(f'Empty pose {i}')
        if box[0]<4 or box[1]<4 or box[2]>slot.width-4 or box[3]>slot.height-4:
            raise ValueError(f'Pose {i} too close to source boundary: {box}')
        slots.append(slot);boxes.append(box);heads.append(head_box(slot,box))
    references=[Image.open(ROOT/f'workflows/lumi-actions-v3/final-frames/{state}/{i:02}.png').convert('RGBA') for i in range(8)]
    ref_boxes=[im.getchannel('A').point(lambda a:255 if a>32 else 0).getbbox() for im in references]
    ref_heads=[head_box(im,b) for im,b in zip(references,ref_boxes)]
    target_head_width=statistics.median(b[2]-b[0] for b in ref_heads)
    scale=min(target_head_width/statistics.median(b[2]-b[0] for b in heads),
              182/max(b[2]-b[0]+8 for b in boxes),
              188/max(b[3]-b[1]+8 for b in boxes))
    head_top=round(statistics.median(b[1] for b in ref_heads))
    bob=[0,2,0,-2,0,2,0,0]
    dest=RUN/'frames'/state;dest.mkdir(parents=True,exist_ok=True)
    report=[]
    for i,(slot,box,head) in enumerate(zip(slots,boxes,heads)):
        padded=(box[0]-4,box[1]-4,box[2]+4,box[3]+4)
        view=slot.crop(padded)
        view=view.resize((round(view.width*scale),round(view.height*scale)),Image.Resampling.LANCZOS)
        x=96-round(((head[0]+head[2])/2-padded[0])*scale)
        y=head_top+bob[i]-round((head[1]-padded[1])*scale)
        if x<2 or y<2 or x+view.width>190 or y+view.height>206:
            raise ValueError(f'Pose {i} registration would clip: {(x,y,view.size)}')
        frame=Image.new('RGBA',(192,208));frame.paste(view,(x,y))
        data=bytearray(frame.tobytes())
        for j in range(0,len(data),4):
            if data[j+3]==0:data[j:j+3]=b'\0\0\0'
        frame=Image.frombytes('RGBA',frame.size,bytes(data))
        frame.save(dest/f'{i:02}.png')
        report.append({'frame':i,'source_bbox':box,'head_bbox':head,'position':[x,y],
                       'final_bbox':frame.getchannel('A').getbbox()})
    result={'state':state,'source':source.name,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'source_size':image.size,'shared_scale':scale,'target_head_width':target_head_width,
            'frames':report,'timing_ms':[120]*7+[220]}
    (RUN/'qa'/f'extraction-{state}.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('state',choices=['running-right','running-left'])
    p.add_argument('source',type=Path)
    args=p.parse_args();extract(args.state,args.source)
