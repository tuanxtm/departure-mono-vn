"""Apply the requested compact breve and rotated hook to the approved VER 1B base."""
from pathlib import Path
import argparse
import json
import shutil
import subprocess
import sys
import unicodedata as ud

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.joinpath('scripts')))
from vietnamese import WORK, SOURCE, VN, outline, bounds, move, contours, draw, export_editor, export_detail
from fontTools.ttLib import TTFont
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.basePen import NullPen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kit', required=True, type=Path)
    args = parser.parse_args()
    kit = args.kit.resolve()
    baseline = WORK.joinpath('VER 1B/VFK-DepartureMono.otf')
    font = TTFont(baseline)
    source = TTFont(SOURCE)
    gs, cm = font.getGlyphSet(), font.getBestCmap()
    recipes = json.loads(WORK.joinpath('VER 1B/recipes.json').read_text())
    # The supplied screenshot is the original font's 3-square caron: 150 x 100.
    breve = outline(source.getGlyphSet(), source.getBestCmap()[0x2C7])
    breve = move(breve, -bounds(breve)[0], -bounds(breve)[1])
    # Rotate the same pixels 90 degrees counterclockwise: the compact right-facing hook.
    hook = [(op, [(-y, x) for x, y in pts]) for op, pts in breve]
    hook = move(hook, -bounds(hook)[0], -bounds(hook)[1])
    recipes['marks']['breve'] = contours(breve)
    recipes['marks']['hook'] = contours(hook)
    cff = font['CFF '].cff
    top = cff.topDictIndex[0]

    def put(name, ops):
        width = font['hmtx'][name][0]
        pen = T2CharStringPen(width - getattr(top.Private, 'nominalWidthX', 0), None)
        draw(ops, pen)
        top.CharStrings.charStringsIndex[top.CharStrings.charStrings[name]] = pen.getCharString(private=top.Private, globalSubrs=cff.GlobalSubrs)
        font['hmtx'].metrics[name] = (width, round(bounds(ops)[0]))

    affected = [ch for ch in VN if any(mark in ud.normalize('NFD', ch) for mark in ('\u0306', '\u0309'))]
    for ch in affected:
        name = cm[ord(ch)]
        r = recipes['glyphs'][name]
        if not r['marks']:
            # ă/Ă were upstream outlines, so split off only their original breve.
            base = ud.normalize('NFD', ch)[0]
            body = outline(gs, cm[ord(base)])
            r['static'] = contours(body)
            r['marks'] = [{'m': 'breve', 't': [1, 0, 0, 1, 100, bounds(body)[3] + 50]}]
        else:
            for mi in r['marks']:
                if mi['m'] == 'breve':
                    mi['t'][4] = 100
                elif mi['m'] == 'hook':
                    base = ud.normalize('NFD', ch)[0]
                    mi['t'][4] = 100 if base in 'oO' and '\u031b' in ud.normalize('NFD', ch) else 150
        ops = [op for c in r['static'] for op in c]
        for mi in r['marks']:
            ops += move([op for c in recipes['marks'][mi['m']] for op in c], mi['t'][4], mi['t'][5])
        put(name, ops)
    # Align decomposed forms with the newly composed Vietnamese glyphs.
    put(cm[0x306], move(breve, 100, 350))
    put(cm[0x309], move(hook, 150, 350))
    for name in font.getGlyphOrder():
        cs = top.CharStrings[name]
        cs.draw(NullPen())
        assert cs.width == font['hmtx'][name][0], name
    folder = WORK.joinpath('VER 2')
    folder.mkdir(exist_ok=True)
    path = folder.joinpath('VFK-DepartureMono.otf')
    font.save(path)
    folder.joinpath('recipes.json').write_text(json.dumps(recipes, ensure_ascii=False))
    folder.joinpath('config.json').write_text(json.dumps({'base': 'VER 1B', 'breve_source': 'caron', 'hook_source': 'caron rotated 90 CCW', 'stack_place': 'top', 'pixel_grid': 50}))
    expected = ''.join(affected) + '\u0306\u0309'
    for script, extra in [('stamp.py', ['1.002', '2']), ('winfix.py', []), ('kiemword.py', ['--fix'])]:
        subprocess.run([sys.executable, '-I', str(kit.joinpath('tools', script)), str(path), *extra], check=True)
    result = subprocess.run([sys.executable, '-I', str(kit.joinpath('tools/glyphdiff.py')), str(baseline), str(path), '--expect', expected], check=True, capture_output=True, text=True)
    folder.joinpath('glyphdiff.txt').write_text(result.stdout)
    print(result.stdout)
    if 'NGOÀI yêu cầu (0)' not in result.stdout:
        raise RuntimeError('Unexpected glyph changes: preserve the baseline and review the diff before publishing')
    metrics = {'version': '2', 'base': '1B', 'changed_letters': len(affected), 'letters': ''.join(affected), 'width_changes': 0,
               'breve_size': [150, 100], 'hook_size': [100, 150], 'line_ascent': font['hhea'].ascent,
               'max_ink': max(bounds(outline(font.getGlyphSet(), cm[ord(ch)]))[3] for ch in VN)}
    folder.joinpath('metrics.json').write_text(json.dumps(metrics, ensure_ascii=False, indent=2))
    review = WORK.joinpath('r2')
    review.mkdir(exist_ok=True)
    font = TTFont(path)
    export_editor(font, recipes, review.joinpath('editor.json'))
    export_detail(font, recipes, review.joinpath('hornui.json'))
    subprocess.run([sys.executable, '-I', str(kit.joinpath('tools/export_batch.py')), str(path), str(review.joinpath('batch.json'))], check=True)
    font.flavor = 'woff2'
    font.save(review.joinpath('A.woff2'))
    old = review.joinpath('vers/VER 1B')
    old.mkdir(parents=True, exist_ok=True)
    for filename in ('editor.json', 'hornui.json', 'batch.json'):
        shutil.copy2(WORK.joinpath('r1/vers/VER 1B', filename), old.joinpath(filename))
    shutil.copy2(WORK.joinpath('r1/v1b.woff2'), review.joinpath('v1b.woff2'))
    # Dashed outlines in Batch show the actual VER 1B marks, even before a slider moves.
    previous = {c['ch']: c for c in json.loads(old.joinpath('batch.json').read_text())['chars']}
    batch = json.loads(review.joinpath('batch.json').read_text())
    for char in batch['chars']:
        before = {m['k']: m for m in previous[char['ch']]['m']}
        for mark in char['m']:
            if mark['k'] in before and mark['d'] != before[mark['k']]['d']:
                mark['old_d'] = before[mark['k']]['d']
    review.joinpath('batch.json').write_text(json.dumps(batch, ensure_ascii=False, separators=(',', ':')))
    print('VER 2:', len(affected), 'letters updated; no advance changes')


if __name__ == '__main__':
    main()
