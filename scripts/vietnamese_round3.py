"""Lower only the hook on ỉ, preserving every other VER 2 glyph and metric."""
from pathlib import Path
import argparse
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.joinpath('scripts')))
from vietnamese import WORK, draw, move, export_editor, export_detail
from fontTools.ttLib import TTFont
from fontTools.pens.t2CharStringPen import T2CharStringPen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kit', required=True, type=Path)
    args = parser.parse_args()
    kit = args.kit.resolve()
    baseline = WORK.joinpath('VER 2/VFK-DepartureMono.otf')
    font = TTFont(baseline)
    recipes = json.loads(WORK.joinpath('VER 2/recipes.json').read_text())
    name = font.getBestCmap()[ord('ỉ')]
    recipe = recipes['glyphs'][name]
    hook = next(mark for mark in recipe['marks'] if mark['m'] == 'hook')
    assert hook['t'][5] == 450
    hook['t'][5] = 350
    ops = [op for contour in recipe['static'] for op in contour]
    for mark in recipe['marks']:
        ops += move([op for contour in recipes['marks'][mark['m']] for op in contour], mark['t'][4], mark['t'][5])
    cff = font['CFF '].cff
    top = cff.topDictIndex[0]
    pen = T2CharStringPen(font['hmtx'][name][0] - getattr(top.Private, 'nominalWidthX', 0), None)
    draw(ops, pen)
    top.CharStrings.charStringsIndex[top.CharStrings.charStrings[name]] = pen.getCharString(private=top.Private, globalSubrs=cff.GlobalSubrs)
    folder = WORK.joinpath('VER 3')
    folder.mkdir(exist_ok=True)
    path = folder.joinpath('VFK-DepartureMono.otf')
    font.save(path)
    folder.joinpath('recipes.json').write_text(json.dumps(recipes, ensure_ascii=False))
    folder.joinpath('metrics.json').write_text(json.dumps({'version': '3', 'base': '2', 'changed_letters': 1, 'letters': 'ỉ', 'hook_dy': -100, 'width_changes': 0, 'line_ascent': font['hhea'].ascent}, ensure_ascii=False, indent=2))
    for script, extra in [('stamp.py', ['1.003', '3']), ('winfix.py', []), ('kiemword.py', ['--fix'])]:
        subprocess.run([sys.executable, '-I', str(kit.joinpath('tools', script)), str(path), *extra], check=True)
    diff = subprocess.run([sys.executable, '-I', str(kit.joinpath('tools/glyphdiff.py')), str(baseline), str(path), '--expect', 'ỉ'], check=True, capture_output=True, text=True)
    folder.joinpath('glyphdiff.txt').write_text(diff.stdout)
    print(diff.stdout)
    if 'NGOÀI yêu cầu (0)' not in diff.stdout or 'đúng yêu cầu (1)' not in diff.stdout:
        raise RuntimeError('Expected exactly one changed character: ỉ')
    data = WORK.joinpath('r3')
    data.mkdir(exist_ok=True)
    font = TTFont(path)
    export_editor(font, recipes, data.joinpath('editor.json'))
    export_detail(font, recipes, data.joinpath('hornui.json'))
    subprocess.run([sys.executable, '-I', str(kit.joinpath('tools/export_batch.py')), str(path), str(data.joinpath('batch.json'))], check=True)
    font.flavor = 'woff2'
    font.save(data.joinpath('A.woff2'))
    old = data.joinpath('vers/VER 2')
    old.mkdir(parents=True, exist_ok=True)
    for filename in ('editor.json', 'hornui.json', 'batch.json'):
        shutil.copy2(WORK.joinpath('r2', filename), old.joinpath(filename))
    shutil.copy2(WORK.joinpath('r2/A.woff2'), data.joinpath('v2.woff2'))
    # Discard round-2 comparison hints from the copied reference data, preserving outlines.
    old_batch = json.loads(old.joinpath('batch.json').read_text())
    for ch in old_batch['chars']:
        for mark in ch['m']:
            mark.pop('old_d', None)
    old.joinpath('batch.json').write_text(json.dumps(old_batch, ensure_ascii=False, separators=(',', ':')))
    previous = next(ch for ch in old_batch['chars'] if ch['ch'] == 'ỉ')
    old_hook = next(mark for mark in previous['m'] if mark['k'] == 'hook')
    batch = json.loads(data.joinpath('batch.json').read_text())
    current = next(ch for ch in batch['chars'] if ch['ch'] == 'ỉ')
    next(mark for mark in current['m'] if mark['k'] == 'hook')['old_d'] = old_hook['d']
    data.joinpath('batch.json').write_text(json.dumps(batch, ensure_ascii=False, separators=(',', ':')))


if __name__ == '__main__':
    main()
