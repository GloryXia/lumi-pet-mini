"""Copy the current approved atlas into the native deployment package."""
from pathlib import Path
import json
import shutil
from validate_pet import ROOT, PACKAGE, validate

report = validate(PACKAGE)
target = ROOT / 'native/lumi-project'
target.mkdir(parents=True, exist_ok=True)
shutil.copy2(PACKAGE / 'spritesheet.webp', target / 'spritesheet.webp')
print(json.dumps(validate(target), ensure_ascii=False, indent=2))
