"""Replace only the two approved running rows, preserving the v3 atlas elsewhere."""
from pathlib import Path
import hashlib
import json
import shutil
from PIL import Image,ImageDraw,ImageFont

RUN=Path(__file__).resolve().parent
ROOT=RUN.parents[1]
BASE=ROOT/'assets/pets/lumi-actions-v3'
OUT=ROOT/'assets/pets/lumi-actions-v4'
STATES=[('idle',6),('running-right',8),('running-left',8),('waving',4),('jumping',5),('failed',8),('waiting',6),('running',6),('review',6)]
DURATIONS=[120]*7+[220]


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    base=Image.open(BASE/'spritesheet.webp').convert('RGBA');sheet=base.copy()
    for row,state in [(1,'running-right'),(2,'running-left')]:
        for col in range(8):
            image=Image.open(RUN/f'frames/{state}/{col:02}.png').convert('RGBA')
            if image.size!=(192,208):raise ValueError('Incorrect native frame dimensions')
            sheet.paste(image,(col*192,row*208))
    sheet.save(OUT/'spritesheet.webp',lossless=True,exact=True,method=6)
    encoded=Image.open(OUT/'spritesheet.webp').convert('RGBA')
    preserved=[]
    for row in range(11):
        box=(0,row*208,1536,(row+1)*208)
        if row not in (1,2):
            if encoded.crop(box).tobytes()!=base.crop(box).tobytes():raise ValueError(f'Preserved row changed: {row}')
            preserved.append(row)
    shutil.copy2(BASE/'pet.json',OUT/'pet.json')
    shutil.copy2(BASE/'spritesheet.webp',OUT/'spritesheet-before-update.webp')
    encoded.crop((0,0,192,208)).save(OUT/'lumi-preview.png')
    for row,(state,count) in enumerate(STATES):
        dest=RUN/'final-frames'/state;dest.mkdir(parents=True,exist_ok=True)
        for col in range(count):encoded.crop((col*192,row*208,(col+1)*192,(row+1)*208)).save(dest/f'{col:02}.png')
    previews=RUN/'qa/previews';previews.mkdir(parents=True,exist_ok=True)
    font=ImageFont.load_default(size=17)
    for state in ('running-right','running-left'):
        frames=[Image.open(RUN/f'final-frames/{state}/{i:02}.png').convert('RGBA') for i in range(8)]
        # GIFs are review artifacts on a white matte; final native art keeps its RGBA alpha.
        gif_frames=[]
        contact=Image.new('RGB',(864,512),'#f6f7fa');d=ImageDraw.Draw(contact)
        for i,frame in enumerate(frames):
            matte=Image.new('RGBA',frame.size,'white');matte.alpha_composite(frame)
            gif_frames.append(matte.convert('RGB'))
            x=16+(i%4)*208;y=16+(i//4)*240
            d.rounded_rectangle((x,y,x+200,y+232),radius=8,fill='white',outline='#dbe0e6')
            contact.paste(frame,(x+4,y+4),frame)
            d.text((x+8,y+210),f'{i+1:02} / {DURATIONS[i]}ms',font=font,fill='#46505a')
        contact.save(previews/f'{state}-frames.png')
        gif_frames[0].save(previews/f'{state}.gif',save_all=True,append_images=gif_frames[1:],duration=DURATIONS,loop=0,optimize=False)
        shutil.copy2(previews/f'{state}.gif',OUT/f'{state}.gif')
    report={'ok':True,'changed_rows':[1,2],'pixel_exact_preserved_rows':preserved,
            'preservation_base':'assets/pets/lumi-actions-v3','sha256':hashlib.sha256((OUT/'spritesheet.webp').read_bytes()).hexdigest(),
            'timing_ms':DURATIONS,'cycle_ms':sum(DURATIONS)}
    (RUN/'qa/preservation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
