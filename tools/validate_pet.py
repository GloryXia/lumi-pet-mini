"""Validate the packaged v3 pet against the approved frames."""
from pathlib import Path
import hashlib
import json
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'assets/pets/lumi-actions-v3'
STATES = [('idle', 6), ('running-right', 8), ('running-left', 8),
          ('waving', 4), ('jumping', 5), ('failed', 8),
          ('waiting', 6), ('running', 6), ('review', 6)]


def validate(package=PACKAGE):
    package = Path(package)
    manifest = json.loads((package / 'pet.json').read_text())
    if manifest.get('id') != 'lumi' or manifest.get('spriteVersionNumber') != 2:
        raise ValueError('Unexpected pet identity or sprite version')
    sheet_path = package / manifest['spritesheetPath']
    if sheet_path.resolve().parent != package.resolve():
        raise ValueError('Sprite path must stay within the package')
    with Image.open(sheet_path) as image:
        if image.format != 'WEBP' or image.mode != 'RGBA' or image.size != (1536, 2288):
            raise ValueError('Expected a 1536 × 2288 RGBA WebP atlas')
        sheet = image.copy()
    if sheet.getchannel('A').getextrema() != (0, 255):
        raise ValueError('Atlas must contain transparent and opaque pixels')
    approval = json.loads((ROOT / 'workflows/lumi-actions-v3/qa/package-check.json').read_text())
    digest = hashlib.sha256(sheet_path.read_bytes()).hexdigest()
    if not approval.get('ok') or approval.get('visual_qa') != 'pass' or digest != approval['sha256']:
        raise ValueError('Atlas differs from the visually approved package')
    base = Image.open(ROOT / 'assets/pets/lumi-actions-v2/spritesheet.webp').convert('RGBA')
    for row in range(11):
        box = (0, row * 208, 1536, (row + 1) * 208)
        if row != 4 and sheet.crop(box).tobytes() != base.crop(box).tobytes():
            raise ValueError(f'Unexpected change in preserved row {row}')
    for row, (name, count) in enumerate(STATES):
        for col in range(8):
            frame = sheet.crop((col * 192, row * 208, (col + 1) * 192, (row + 1) * 208))
            if col < count:
                expected = Image.open(ROOT / f'workflows/lumi-actions-v3/final-frames/{name}/{col:02}.png').convert('RGBA')
                if frame.tobytes() != expected.tobytes():
                    raise ValueError(f'Frame mismatch: {name}/{col:02}')
            elif row == 0 and col == 6:
                if not frame.getchannel('A').getbbox():
                    raise ValueError('Missing neutral look frame')
            elif frame.getchannel('A').getbbox():
                raise ValueError(f'Unused cell is visible: {row}/{col}')
    for row in (9, 10):
        for col in range(8):
            if not sheet.crop((col * 192, row * 208, (col + 1) * 192, (row + 1) * 208)).getchannel('A').getbbox():
                raise ValueError('Missing look direction')
    return {'ok': True, 'id': manifest['id'], 'sha256': digest,
            'animation_states': len(STATES), 'look_directions': 16}


if __name__ == '__main__':
    print(json.dumps(validate(), ensure_ascii=False, indent=2))
