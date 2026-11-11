"""Build pixel-grid Vietnamese review fonts without replacing the upstream release.

Run with a Python environment containing fonttools, brotli, uharfbuzz, shapely.
Only review WOFF2 data is embedded in the review page until a VER is approved.
"""
from pathlib import Path
import argparse
import json
import subprocess
import sys
import unicodedata as ud

import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.basePen import NullPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.joinpath('public/assets/DepartureMono-1.500.otf')
WORK = ROOT.joinpath('scratchpad/vietnamese')
REVIEW = WORK.joinpath('r1')
LOWER = 'àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ'
VN = LOWER + LOWER.upper()
TONES = {'\u0300': 'grave', '\u0301': 'acute', '\u0309': 'hook', '\u0303': 'tilde', '\u0323': 'dot'}
MODS = {'\u0302': 'circ', '\u0306': 'breve', '\u031b': 'horn'}


def draw(ops, pen):
    for op, pts in ops:
        getattr(pen, op)(*pts)


def bounds(ops):
    p = BoundsPen(None)
    draw(ops, p)
    return p.bounds


def move(ops, dx=0, dy=0):
    return [(op, [(x + dx, y + dy) for x, y in pts]) for op, pts in ops]


def contours(ops):
    out = []
    for op, pts in ops:
        if op == 'moveTo':
            out.append([])
        out[-1].append((op, pts))
    return out


def outline(gs, name):
    p = RecordingPen()
    gs[name].draw(p)
    return p.value


def polygon_ops(geometry):
    """Turn unions of the original square pixels back into CFF line contours."""
    from shapely.geometry.polygon import orient
    geometry = geometry.simplify(0)
    out = []
    polys = list(geometry.geoms) if geometry.geom_type == 'MultiPolygon' else [geometry]
    for poly in polys:
        poly = orient(poly, sign=-1)
        for ring in [poly.exterior, *poly.interiors]:
            pts = list(ring.coords)[:-1]
            out += [('moveTo', [pts[0]])] + [('lineTo', [p]) for p in pts[1:]] + [('closePath', [])]
    return out


def question_hook(gs, half):
    # Retain the upper bowl and neck of ?, drop dot and lower stem. Collapse
    # redundant columns, rather than scaling its 50-unit strokes into thin ones.
    shapes = []
    xmap = {50: 0, 100: 0, 150: 50, 200: 50, 250: 100}
    for c in contours(outline(gs, 'question')):
        poly = Polygon([p for op, pts in c for p in pts])
        for x in range(50, 300, 50):
            for y in range(300 if half else 200, 400, 50):
                if poly.covers(box(x, y, x + 50, y + 50).centroid):
                    xx = xmap[x]
                    yy = y - (300 if half else 200)
                    shapes.append(box(xx, yy, xx + 50, yy + 50))
    return polygon_ops(unary_union(shapes))


def add_ccmp(font, cmap):
    """Prepend Vietnamese composition while retaining all upstream OT features."""
    rules = {}
    for ch in VN:
        d = ud.normalize('NFD', ch)
        if len(d) < 2:
            continue
        rules[tuple(cmap[ord(c)] for c in d)] = cmap[ord(ch)]
        # Also compose a previously composed vowel followed by its final mark.
        for k in range(1, len(d)):
            prefix = ud.normalize('NFC', d[:k])
            if len(prefix) == 1 and ord(prefix) in cmap:
                rules[tuple([cmap[ord(prefix)], *[cmap[ord(c)] for c in d[k:]]])] = cmap[ord(ch)]
        if len(d) == 3:
            # Vietnamese input methods also emit shape-before-tone for dot below.
            alt = d[0] + d[2] + d[1]
            rules[tuple(cmap[ord(c)] for c in alt)] = cmap[ord(ch)]
            prefix = ud.normalize('NFC', alt[:2])
            if len(prefix) == 1 and ord(prefix) in cmap:
                rules[(cmap[ord(prefix)], cmap[ord(alt[2])])] = cmap[ord(ch)]
    fea = 'languagesystem DFLT dflt; feature ccmp {\n'
    for seq, target in sorted(rules.items(), key=lambda r: (-len(r[0]), r[0])):
        fea += 'sub ' + ' '.join(seq) + ' by ' + target + ';\n'
    fea += '} ccmp;'
    temp = TTFont()
    temp.setGlyphOrder(font.getGlyphOrder())
    addOpenTypeFeaturesFromString(temp, fea)
    table = font['GSUB'].table
    added = temp['GSUB'].table.LookupList.Lookup
    count = len(added)
    for rec in table.FeatureList.FeatureRecord:
        rec.Feature.LookupListIndex = [i + count for i in rec.Feature.LookupListIndex]
    table.LookupList.Lookup = added + table.LookupList.Lookup
    table.LookupList.LookupCount += count
    for rec in table.FeatureList.FeatureRecord:
        if rec.FeatureTag == 'ccmp':
            rec.Feature.LookupListIndex = list(range(count)) + rec.Feature.LookupListIndex
            rec.Feature.LookupCount = len(rec.Feature.LookupListIndex)
    return len(rules)


def export_editor(font, recipes, destination):
    """Export exact separate pixel components, including corner-touching horns.

    The kit's outline reclassifier assumes a horn union reduces contour count;
    these source pixel horns touch at corners and remain separate contours.
    Exporting the known composition avoids losing those correct recipes.
    """
    codes = {'moveTo': 'M', 'lineTo': 'L', 'curveTo': 'C', 'qCurveTo': 'Q'}
    def convert(cs):
        return [[[codes[op], pts] for op, pts in c if op in codes] for c in cs]
    gs = font.getGlyphSet()
    glyphs = {n: {'u': cp, 'w': font['hmtx'][n][0], 'c': convert(contours(outline(gs, n)))} for cp, n in font.getBestCmap().items()}
    o = font['OS/2']
    data = {'upm': 550, 'xh': 300, 'cap': 400, 'asc': o.sTypoAscender, 'desc': o.sTypoDescender,
            'lbAsc': font['hhea'].ascent, 'lbDesc': font['hhea'].descent, 'tildeW': 50, 'axis': 0,
            'glyphs': glyphs, 'marks': {k: convert(v) for k, v in recipes['marks'].items()}, 'kern': {},
            'recipes': {n: {'u': r['u'], 'w': r['w'], 's': convert(r['static']), 'm': r['marks'], 'sax': r['sax']} for n, r in recipes['glyphs'].items()}}
    destination.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')))
    print('export_editor: 134 exact recipes; dropped 0')


def export_detail(font, recipes, destination):
    """Use the actual outline in every detail preview; retain full multi-pixel marks."""
    gs = font.getGlyphSet()
    cm = font.getBestCmap()
    def svg(ops):
        p = SVGPathPen(None)
        draw(ops, p)
        return p.getCommands()
    tone_keys = {'acute': 's', 'grave': 'f', 'hook': 'r', 'tilde': 'x'}
    G = {}
    for cp, name in cm.items():
        ch = chr(cp)
        if cp < 32 or cp > 0xFFFF:
            continue
        ops = outline(gs, name)
        r = recipes['glyphs'].get(name)
        e = {'w': font['hmtx'][name][0], 'd': svg(ops), 'lp': [None] * 103}
        if r and ch not in 'đĐ':
            d = ud.normalize('NFD', ch)
            body = [op for c in r['static'] for op in c]
            above, horn, dot = [], [], []
            for mi in r['marks']:
                mk = move([op for c in recipes['marks'][mi['m']] for op in c], mi['t'][4], mi['t'][5])
                if mi['m'].startswith('horn'):
                    horn += mk
                elif mi['m'] == 'dot':
                    dot += mk
                elif mi['m'] in tone_keys:
                    e['t'] = tone_keys[mi['m']]
                    above += mk
                else:
                    body += mk
            # Untouched original glyphs have static recipes: split by source body height.
            if not r['marks']:
                bt = 400 if ch.isupper() else (400 if d[0] == 'i' and '\u0323' in d else 300)
                tone = next((TONES[m] for m in d[1:] if m in TONES), None)
                if tone:
                    parts = contours(ops)
                    dot = [op for c in parts if bounds(c)[3] < 0 for op in c] if tone == 'dot' else []
                    above = [op for c in parts if bounds(c)[1] > bt for op in c] if tone != 'dot' else []
                    body = [op for c in parts if not ((tone == 'dot' and bounds(c)[3] < 0) or (tone != 'dot' and bounds(c)[1] > bt)) for op in c]
                    if tone in tone_keys:
                        e['t'] = tone_keys[tone]
                if '\u031b' in d:
                    parts = contours(body)
                    horn = [op for c in parts if bounds(c)[1] >= bt for op in c]
                    body = [op for c in parts if bounds(c)[1] < bt for op in c]
            e['d'] = svg(body)
            if above:
                e['m'] = svg(above)
                e['mp'] = [p for op, pts in above for p in pts]
            if dot:
                e['dot'] = sum(bounds(dot)[::2]) * 0.5
            if '\u031b' in d:
                e.update(h=d[0], rd=svg(body), rh=svg(horn), rw=350, rp=[None] * 103)
                if above:
                    e['rm'] = svg(above)
        G[ch] = e
    plain = {}
    for ch in 'UOuo':
        ops = outline(gs, cm[ord(ch)])
        top = 400 if ch.isupper() else 300
        plain[ch] = {'d': svg(ops), 'w': 350, 'x0': 300, 'top': top, 'oy': [top - 150, top - 1], 'ox': [300] * 150}
    hook = recipes['marks']['hook']
    height = bounds([op for c in hook for op in c])[3]
    data = {'all': {'reach': 50, 'rise': 100, 'thin': 50, 'head': 50, 'p': 1, 't0': 0, 'dyO': 0, 'dyU': 0},
            'lc_ratio': 0.5, 'lc_wratio': 1, 'g': plain, 'G': G, 'space': 350, 'band': [-320, 16, 103], 'slant': 0,
            'tone_gap': 50, 'ndot': {'d': 'M-25 -25L-25 25L25 25L25 -25Z', 'w': 50, 'h': 50}, 'period': [50, 50],
            'guide': [[450, 450 + height], [350, 350 + height]],
            'hook': {'mode': 'taper', 'h': height, 'thick': 50, 'thin': 50, 'ball': 50, 'neck': 50, 'foot': 50, 'cut': 0,
                     'path': [[25, 100], [25, 150], [125, 150], [125, 100], [125, 50], [75, 50], [75, 0]]}}
    destination.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')))


def build(label):
    font = TTFont(SOURCE)
    source_cmap = font.getBestCmap()
    cmap = dict(source_cmap)
    gs = font.getGlyphSet()
    cff = font['CFF '].cff
    top = cff.topDictIndex[0]
    cs = top.CharStrings
    order = list(font.getGlyphOrder())
    source_hb = hb.Font(hb.Face(SOURCE.read_bytes()))
    marks = {k: outline(gs, cmap[cp]) for k, cp in
             [('acute', 0x301), ('grave', 0x300), ('tilde', 0x303), ('circ', 0x302), ('breve', 0x306), ('dot', 0x323)]}
    # Normalize mark coordinate origins, retaining the exact original pixels.
    marks = {k: move(v, -bounds(v)[0], -bounds(v)[1]) for k, v in marks.items()}
    marks['hook'] = question_hook(gs, label == '1C')
    marks['horn'] = move(outline(gs, 'uhorn')[-5:], -300, -300)
    recipes = {'tilde_w': 50, 'axis': 0, 'marks': {k: contours(v) for k, v in marks.items()}, 'glyphs': {}}
    metrics = {'version': label, 'missing_before': sum(ord(c) not in cmap for c in VN), 'changed_original': [], 'width_changes': 0}

    def put(name, ops, width):
        pen = T2CharStringPen(width - getattr(top.Private, 'nominalWidthX', 0), None)
        draw(ops, pen)
        charstring = pen.getCharString(private=top.Private, globalSubrs=cff.GlobalSubrs)
        if name in cs.charStrings:
            cs.charStringsIndex[cs.charStrings[name]] = charstring
        else:
            cs.charStrings[name] = len(cs.charStringsIndex)
            cs.charStringsIndex.append(charstring)
            order.append(name)
            if name not in top.charset:
                top.charset.append(name)
        font['hmtx'].metrics[name] = (width, round(bounds(ops)[0]))

    for cp, kind in [(0x309, 'hook'), (0x31b, 'horn')]:
        name = 'uni%04X' % cp
        cmap[cp] = name
        put(name, move(marks[kind], 100, 350) if kind == 'hook' else move(marks[kind], 250, 300), 0)
    # Combining marks are zero-advance; source GPOS positioning is retained.
    for cp in [0x300, 0x301, 0x302, 0x303, 0x306, 0x309, 0x31b, 0x323]:
        n = cmap[cp]
        font['hmtx'].metrics[n] = (0, font['hmtx'].metrics[n][1])
        if cp not in (0x309, 0x31b):
            put(n, outline(gs, n), 0)

    for ch in VN:
        name = cmap.get(ord(ch), 'uni%04X' % ord(ch))
        cmap[ord(ch)] = name
        d = ud.normalize('NFD', ch)
        if ch in 'đĐ':
            body = outline(gs, source_cmap[ord(ch)])
            instances = []
        else:
            base = d[0]
            above = [m for m in d[1:] if m in TONES and m != '\u0323']
            # The dot of i remains in ị, but disappears for every upper accent.
            bn = source_cmap[0x131] if base == 'i' and above else source_cmap[ord(base)]
            body = outline(gs, bn)
            bt = bounds(body)[3]
            instances = []
            modifier = next((MODS[m] for m in d[1:] if m in MODS), None)
            tone = next((TONES[m] for m in d[1:] if m in TONES), None)
            if modifier == 'horn':
                # Same source horn and same top for each case; O attaches at its
                # top-right corner, U at its right stem. No advance expansion.
                horn = marks['horn']
                if base.isupper():
                    horn = [(op, [(x, y * 2) for x, y in pts]) for op, pts in horn]
                key = 'horn_uc' if base.isupper() else 'horn'
                marks[key] = horn
                recipes['marks'][key] = contours(horn)
                instances.append({'m': key, 't': [1, 0, 0, 1, 250 if base in 'oO' else 300, bt]})
            elif modifier:
                instances.append({'m': modifier, 't': [1, 0, 0, 1, 100 if modifier == 'circ' else 50, bt + 50]})
            if tone:
                mk = marks[tone]
                mw = bounds(mk)[2]
                x = {'acute': 150, 'grave': 100, 'tilde': 100, 'dot': 150}.get(tone, 100)
                y = -100 if tone == 'dot' else (400 if base == 'i' else bt) + 50
                if modifier in ('circ', 'breve') and tone != 'dot':
                    # VER 1B follows the source's measured 150-unit stack step.
                    y = bt + 200
                    if label != '1B' and tone != 'tilde':
                        x = 350 - mw
                        y = bt + (150 if modifier == 'circ' else 200)
                    elif tone == 'hook':
                        x = 100
                if modifier == 'horn' and tone != 'dot':
                    # Keep a complete pixel gap to the existing horn.
                    x = min(x, (200 if base in 'oO' else 250) - mw)
                if base == 'y' and tone == 'dot':
                    # Place beside, rather than through, y's descender.
                    x = 250
                instances.append({'m': tone, 't': [1, 0, 0, 1, x, y]})
        ops = body[:]
        for mi in instances:
            ops += move(marks[mi['m']], mi['t'][4], mi['t'][5])
        # Preserve every existing precomposed outline unless it needs a new tone.
        if ord(ch) in source_cmap and not (any(m in d for m in ('\u0309', '\u031b')) and len(d) > 2):
            ops = outline(gs, source_cmap[ord(ch)])
            # Use an exact static recipe for untouched original glyphs.
            recipe_body, recipe_instances = ops, []
        else:
            recipe_body, recipe_instances = body, instances
        if ord(ch) in source_cmap and ops != outline(gs, source_cmap[ord(ch)]):
            metrics['changed_original'].append(ch)
        put(name, ops, 350)
        recipes['glyphs'][name] = {'u': ord(ch), 'w': 350, 'static': contours(recipe_body), 'marks': recipe_instances, 'sax': [175, 0]}
    font.setGlyphOrder(order)
    font['maxp'].numGlyphs = len(order)
    for table in font['cmap'].tables:
        if table.isUnicode() and table.format in (4, 12):
            table.cmap.update({cp: n for cp, n in cmap.items() if table.format == 12 or cp <= 0xFFFF})
    # The new combining marks need to participate in GDEF mark filtering.
    if 'GDEF' in font:
        classes = font['GDEF'].table.GlyphClassDef.classDefs
        for cp in [0x309, 0x31b]:
            classes[cmap[cp]] = 3
    metrics['composition_rules'] = add_ccmp(font, cmap)
    font['OS/2'].ulCodePageRange1 |= 1 << 8
    font['OS/2'].recalcUnicodeRanges(font)
    # Keep the real fixed-pitch flags: this font really is monospaced.
    font['post'].isFixedPitch = 1
    top.isFixedPitch = 1
    ink_top = max(bounds(outline(font.getGlyphSet(), n))[3] for n in order if bounds(outline(font.getGlyphSet(), n)))
    font['hhea'].ascent = round(ink_top)
    font['OS/2'].sTypoAscender = round(ink_top)
    font['OS/2'].usWinAscent = round(ink_top)
    for n in order:
        cs[n].draw(NullPen())
        assert cs[n].width == font['hmtx'].metrics[n][0], n
    folder = WORK.joinpath('VER ' + label)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder.joinpath('VFK-DepartureMono.otf')
    font.save(path)
    (folder.joinpath('recipes.json')).write_text(json.dumps(recipes, ensure_ascii=False))
    (folder.joinpath('config.json')).write_text(json.dumps({'anchor_marks': {}, 'stack_place': 'top' if label == '1B' else 'right', 'hook_src': 'half' if label == '1C' else 'neck', 'pixel_grid': 50}))
    metrics['bounds'] = [min(bounds(outline(font.getGlyphSet(), n))[1] for n in order if bounds(outline(font.getGlyphSet(), n))), max(bounds(outline(font.getGlyphSet(), n))[3] for n in order if bounds(outline(font.getGlyphSet(), n)))]
    (folder.joinpath('metrics.json')).write_text(json.dumps(metrics, ensure_ascii=False, indent=2))
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kit', type=Path, required=True, help='Installed viet-hoa-font skill directory')
    args = parser.parse_args()
    kit = args.kit.resolve()
    REVIEW.mkdir(parents=True, exist_ok=True)
    for label in ('1A', '1B', '1C'):
        path = build(label)
        for script, extra in [('stamp.py', ['1.001', label]), ('winfix.py', []), ('kiemword.py', ['--fix'])]:
            subprocess.run([sys.executable, '-I', str(kit.joinpath('tools', script)), str(path), *extra], check=True)
        font = TTFont(path)
        font.flavor = 'woff2'
        font.save(REVIEW.joinpath('v' + label.lower() + '.woff2'))
        folder = REVIEW if label == '1C' else REVIEW.joinpath('vers', 'VER ' + label)
        folder.mkdir(parents=True, exist_ok=True)
        recipes = json.loads(path.parent.joinpath('recipes.json').read_text())
        export_editor(font, recipes, folder.joinpath('editor.json'))
        export_detail(font, recipes, folder.joinpath('hornui.json'))
        subprocess.run([sys.executable, '-I', str(kit.joinpath('tools/export_batch.py')), str(path), str(folder.joinpath('batch.json'))], check=True)
    (REVIEW.joinpath('A.woff2')).write_bytes((REVIEW.joinpath('v1c.woff2')).read_bytes())


if __name__ == '__main__':
    main()
