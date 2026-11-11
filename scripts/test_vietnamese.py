"""Regression checks for the built Vietnamese review fonts and offline editor.

Run: scratchpad/.venv/bin/python -m unittest discover -s scripts -p test_vietnamese.py -v
"""
from pathlib import Path
import json
import unicodedata as ud
import unittest

import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.basePen import NullPen
from fontTools.svgLib.path import parse_path
from playwright.sync_api import sync_playwright
from shapely.geometry import Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.joinpath('scratchpad/vietnamese')
VN = 'àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ'
VN += VN.upper()


def record(gs, name):
    p = RecordingPen()
    gs[name].draw(p)
    return p.value


def box_of(gs, name):
    p = BoundsPen(gs)
    gs[name].draw(p)
    return p.bounds


def shape(font, text, features=None):
    b = hb.Buffer()
    b.add_str(text)
    b.guess_segment_properties()
    b.language = 'vi'
    hb.shape(font, b, features or {})
    return [(g.codepoint, p.x_advance, p.x_offset, p.y_offset) for g, p in zip(b.glyph_infos, b.glyph_positions)]


def data_folder(ver):
    if ver in ('2', '3'):
        return WORK.joinpath('r' + ver)
    return WORK.joinpath('r1') if ver == '1C' else WORK.joinpath('r1/vers', 'VER ' + ver)


class VietnameseFontTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = TTFont(ROOT.joinpath('public/assets/DepartureMono-1.500.otf'))

    def test_coverage_widths_outlines_and_metrics(self):
        original = self.source.getGlyphSet()
        combining = {self.source.getBestCmap()[cp] for cp in [0x300, 0x301, 0x302, 0x303, 0x306, 0x323]}
        for ver in ('1A', '1B', '1C'):
            with self.subTest(ver=ver):
                f = TTFont(WORK.joinpath('VER ' + ver, 'VFK-DepartureMono.otf'))
                gs, cm = f.getGlyphSet(), f.getBestCmap()
                self.assertEqual(len(set(VN)), 134)
                self.assertTrue(all(ord(ch) in cm for ch in VN))
                for name in self.source.getGlyphOrder():
                    self.assertEqual(record(gs, name), record(original, name), name)
                    if name not in combining:
                        self.assertEqual(f['hmtx'][name], self.source['hmtx'][name], name)
                for ch in VN:
                    b = box_of(gs, cm[ord(ch)])
                    self.assertIsNotNone(b, ch)
                    self.assertEqual(f['hmtx'][cm[ord(ch)]][0], 350, ch)
                    self.assertGreaterEqual(b[0], 0, ch)
                    self.assertLessEqual(b[2], 350, ch)
                    self.assertLessEqual(b[3], f['hhea'].ascent, ch)
                    for op, pts in record(gs, cm[ord(ch)]):
                        self.assertNotIn(op, ('curveTo', 'qCurveTo'), ch)
                        for x, y in pts:
                            self.assertEqual(x % 50, 0, ch)
                            self.assertEqual(y % 50, 0, ch)
                for cp in (0x300, 0x301, 0x302, 0x303, 0x306, 0x309, 0x31b, 0x323):
                    self.assertEqual(f['hmtx'][cm[cp]][0], 0)
                for pair in ('ơư', 'ƠƯ'):
                    self.assertEqual(*[box_of(gs, cm[ord(c)])[3] for c in pair])
                for tag in ('GSUB', 'GPOS'):
                    self.assertEqual([r.FeatureTag for r in f[tag].table.FeatureList.FeatureRecord],
                                     [r.FeatureTag for r in self.source[tag].table.FeatureList.FeatureRecord])
                for name in f.getGlyphOrder():
                    cs = f['CFF '].cff.topDictIndex[0].CharStrings[name]
                    cs.draw(NullPen())
                    self.assertEqual(cs.width, f['hmtx'][name][0], name)
                self.assertEqual(f['post'].isFixedPitch, 1)

    def test_precomposed_and_decomposed_input(self):
        for ver in ('1A', '1B', '1C', '2', '3'):
            font = hb.Font(hb.Face(WORK.joinpath('VER ' + ver, 'VFK-DepartureMono.otf').read_bytes()))
            for ch in VN:
                d = ud.normalize('NFD', ch)
                variants = {ch, d}
                for i in range(1, len(d)):
                    variants.add(ud.normalize('NFC', d[:i]) + d[i:])
                if len(d) == 3:
                    variants.add(d[0] + d[2] + d[1])
                for kern in (True, False):
                    expected = shape(font, ch, {'kern': kern})
                    for text in variants:
                        with self.subTest(ver=ver, ch=ch, text=text, kern=kern):
                            actual = shape(font, text, {'kern': kern})
                            self.assertEqual(actual, expected)
                            self.assertEqual(sum(g[1] for g in actual), 350)
                            self.assertTrue(all(g[0] for g in actual))

    def test_editor_recipes_match_font(self):
        for ver in ('1A', '1B', '1C', '2', '3'):
            folder = data_folder(ver)
            data = json.loads(folder.joinpath('editor.json').read_text())
            self.assertEqual(len(data['recipes']), 134)
            for name, r in data['recipes'].items():
                composed = list(r['s'])
                for mi in r['m']:
                    a, b, c, d, e, f = mi['t']
                    composed += [[[op, [[a*x+c*y+e, b*x+d*y+f] for x, y in pts]] for op, pts in contour] for contour in data['marks'][mi['m']]]
                self.assertEqual(composed, data['glyphs'][name]['c'], name)

    def test_detail_preview_matches_font(self):
        def geometry(ops):
            polys, points = [], []
            for op, pts in ops:
                if op == 'moveTo':
                    points = [pts[0]]
                elif op == 'lineTo':
                    points.append(pts[0])
                elif op == 'closePath':
                    polys.append(Polygon(points))
            return unary_union(polys)
        for ver in ('1A', '1B', '1C', '2', '3'):
            folder = data_folder(ver)
            data = json.loads(folder.joinpath('hornui.json').read_text())
            f = TTFont(WORK.joinpath('VER ' + ver, 'VFK-DepartureMono.otf'))
            gs, cm = f.getGlyphSet(), f.getBestCmap()
            for ch in VN:
                e = data['G'][ch]
                d = e.get('rd', e['d']) + e.get('rh', '') + e.get('rm', e.get('m', ''))
                if 'dot' in e:
                    x = e['dot']
                    d += f'M{x-25} -100L{x-25} -50L{x+25} -50L{x+25} -100Z'
                pen = RecordingPen()
                parse_path(d, pen)
                actual = geometry(pen.value)
                expected = geometry(record(gs, cm[ord(ch)]))
                self.assertLess(actual.symmetric_difference(expected).area, 0.01, (ver, ch))

    def test_round2_changes_only_requested_marks(self):
        old = TTFont(WORK.joinpath('VER 1B/VFK-DepartureMono.otf'))
        new = TTFont(WORK.joinpath('VER 2/VFK-DepartureMono.otf'))
        cm, gs, before = new.getBestCmap(), new.getGlyphSet(), old.getGlyphSet()
        affected = {ch for ch in VN if any(m in ud.normalize('NFD', ch) for m in ('\u0306', '\u0309'))}
        self.assertEqual(len(affected), 34)
        allowed = {cm[ord(ch)] for ch in affected | {'\u0306', '\u0309'}}
        changed = set()
        for name in new.getGlyphOrder():
            if record(gs, name) != record(before, name):
                changed.add(name)
            self.assertEqual(new['hmtx'][name][0], old['hmtx'][name][0], name)
        self.assertEqual(changed, allowed)
        r = json.loads(WORK.joinpath('VER 2/recipes.json').read_text())
        breve, hook = r['marks']['breve'], r['marks']['hook']
        self.assertEqual(len(breve), 3)
        self.assertEqual(len(hook), 3)
        rotated = [[[op, [[100-y, x] for x, y in pts]] for op, pts in contour] for contour in breve]
        self.assertEqual(hook, rotated)
        for ch in affected:
            b = box_of(gs, cm[ord(ch)])
            self.assertGreaterEqual(b[0], 0, ch)
            self.assertLessEqual(b[2], 350, ch)
            self.assertLessEqual(b[3], new['hhea'].ascent, ch)
            recipe = r['glyphs'][cm[ord(ch)]]
            for mi in recipe['marks']:
                if mi['m'] in ('breve', 'hook'):
                    self.assertEqual(mi['t'][:4], [1, 0, 0, 1], ch)
        self.assertEqual(new['hhea'].ascent, old['hhea'].ascent)

    def test_round3_only_lowers_hook_on_lowercase_i(self):
        old = TTFont(WORK.joinpath('VER 2/VFK-DepartureMono.otf'))
        new = TTFont(WORK.joinpath('VER 3/VFK-DepartureMono.otf'))
        cm, gs, before = new.getBestCmap(), new.getGlyphSet(), old.getGlyphSet()
        changed = {n for n in new.getGlyphOrder() if record(gs, n) != record(before, n)}
        self.assertEqual(changed, {cm[ord('ỉ')]})
        self.assertEqual(new['hmtx'].metrics, old['hmtx'].metrics)
        for tag in ('hhea', 'OS/2', 'GPOS', 'GSUB', 'cmap'):
            self.assertEqual(new.getTableData(tag), old.getTableData(tag), tag)
        for ch in 'ảẻỉỏủỷ':
            self.assertEqual(box_of(gs, cm[ord(ch)])[3], 500, ch)
        old_recipes = json.loads(WORK.joinpath('VER 2/recipes.json').read_text())
        new_recipes = json.loads(WORK.joinpath('VER 3/recipes.json').read_text())
        self.assertEqual(new_recipes['marks'], old_recipes['marks'])
        expected = old_recipes['glyphs'][cm[ord('ỉ')]]
        expected['marks'][0]['t'][5] -= 100
        self.assertEqual(new_recipes['glyphs'], old_recipes['glyphs'])


class ReviewBrowserTests(unittest.TestCase):
    def test_offline_review(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
            page = browser.new_page(viewport={'width': 1280, 'height': 900})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            # No external resources are needed to review the fonts.
            page.route('https://**', lambda route: route.abort())
            page.goto(WORK.joinpath('host-review.html').as_uri())
            page.wait_for_function('window.__FV_VERS && window.__FV_VERS.length === 2')
            page.evaluate('document.fonts.ready')
            self.assertEqual(page.locator('.vk-ver').count(), 2)
            self.assertEqual(page.evaluate('window.__FV_VER'), 'VER 3')
            for ver, family in [('VER 2', 'FV-v2'), ('VER 3', 'Font VN')]:
                page.locator('.vk-ver', has_text=ver).click()
                self.assertTrue(page.evaluate('(family) => document.fonts.check(`55px "${family}"`, "ẤậƠưỵ")', family))
                self.assertEqual(page.evaluate('window.__FV_VER'), ver)
            page.locator('[data-tab="chinh"]').click()
            page.locator('.vb-tabs [data-k="hook"]').click()
            current = page.locator('.vb-rows').inner_html()
            self.assertGreater(page.locator('.vb-rows path.gh').count(), 0)
            page.locator('.vk-ver', has_text='VER 2').click()
            self.assertNotEqual(page.locator('.vb-rows').inner_html(), current)
            page.locator('.vk-ver', has_text='VER 3').click()
            self.assertEqual(page.locator('.vb-rows').inner_html(), current)
            for width in (1280, 800, 390):
                page.set_viewport_size({'width': width, 'height': 900})
                for theme in ('light', 'dark'):
                    page.evaluate('(theme) => document.documentElement.dataset.theme=theme', theme)
                    for tab in ('xem', 'chinh', 've', 'kn', 'huongdan', 'nguon'):
                        page.locator('[data-tab="' + tab + '"]').click()
                        page.wait_for_timeout(180)
                        self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), width + 1, (width, theme, tab))
                        page.screenshot(path=str(WORK.joinpath(f'review-{width}-{theme}-{tab}.png')))
            page.set_viewport_size({'width': 1280, 'height': 900})
            page.locator('[data-tab="xem"]').click()
            page.set_input_files('#vk-file', str(ROOT.joinpath('public/assets/DepartureMono-1.500.otf')))
            page.wait_for_function('!document.querySelector(".vk-refon").hidden')
            self.assertEqual(errors, [])
            browser.close()


if __name__ == '__main__':
    unittest.main()
