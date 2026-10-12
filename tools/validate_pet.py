"""Validate the packaged v3 pet against the approved frames."""
from pathlib import Path
import hashlib
import json
import re
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PROJECT = json.loads((ROOT / 'native/project.json').read_text())
PACKAGE = ROOT / PROJECT.get('asset_package_directory', 'assets/pets/lumi-actions-v3')
WORKFLOW = ROOT / PROJECT.get('workflow_directory', 'workflows/lumi-actions-v3')
STATES = [('idle', 6), ('running-right', 8), ('running-left', 8),
          ('waving', 4), ('jumping', 5), ('failed', 8),
          ('waiting', 6), ('running', 6), ('review', 6)]


def validate_structure(package=PACKAGE):
    package = Path(package)
    manifest = json.loads((package / 'pet.json').read_text())
    if not isinstance(manifest, dict):
        raise ValueError('Pet manifest must be an object')
    pet_id = manifest.get('id')
    if not isinstance(pet_id, str) or not re.fullmatch(r'lumi(?:-project)?', pet_id) or manifest.get('spriteVersionNumber') != 2:
        raise ValueError('Unexpected pet identity or sprite version')
    sprite_path = manifest.get('spritesheetPath')
    if not isinstance(sprite_path, str) or not sprite_path.strip():
        raise ValueError('Sprite path must be a non-empty string')
    sheet_path = package / sprite_path
    if sheet_path.resolve().parent != package.resolve():
        raise ValueError('Sprite path must stay within the package')
    with Image.open(sheet_path) as image:
        if image.format != 'WEBP' or image.mode != 'RGBA' or image.size != (1536, 2288):
            raise ValueError('Expected a 1536 × 2288 RGBA WebP atlas')
        sheet = image.copy()
    if not isinstance(manifest.get('displayName'), str) or not manifest['displayName'].strip():
        raise ValueError('Pet displayName must be a non-empty string')
    if sheet.getchannel('A').getextrema() != (0, 255):
        raise ValueError('Atlas must contain transparent and opaque pixels')
    return {'ok': True, 'id': manifest['id'],
            'sha256': hashlib.sha256(sheet_path.read_bytes()).hexdigest()}, sheet


def validate(package=PACKAGE):
    report, sheet = validate_structure(package)
    approval = json.loads((WORKFLOW / 'qa/package-check.json').read_text())
    digest = report['sha256']
    if not approval.get('ok') or approval.get('visual_qa') != 'pass' or digest != approval['sha256']:
        raise ValueError('Atlas differs from the visually approved package')
    base_directory = approval.get('preservation_base', 'assets/pets/lumi-actions-v2')
    changed_rows = approval.get('changed_rows', [4])
    base = Image.open(ROOT / base_directory / 'spritesheet.webp').convert('RGBA')
    for row in range(11):
        box = (0, row * 208, 1536, (row + 1) * 208)
        if row not in changed_rows and sheet.crop(box).tobytes() != base.crop(box).tobytes():
            raise ValueError(f'Unexpected change in preserved row {row}')
    for row, (name, count) in enumerate(STATES):
        for col in range(8):
            frame = sheet.crop((col * 192, row * 208, (col + 1) * 192, (row + 1) * 208))
            if col < count:
                expected = Image.open(WORKFLOW / f'final-frames/{name}/{col:02}.png').convert('RGBA')
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
    return {**report,
            'animation_states': len(STATES), 'look_directions': 16}


if __name__ == '__main__':
    print(json.dumps(validate(), ensure_ascii=False, indent=2))
