"""Validate the final four font formats independently of the export implementation."""
from pathlib import Path
import io
import hashlib
import json
import shutil
import unicodedata
import unittest
import zipfile

from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from playwright.sync_api import sync_playwright
import uharfbuzz as hb

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.joinpath('vietnamese/release')
STEM = 'DepartureMono-Regular'
VN = 'àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ'
VN += VN.upper()


def rings(font, name):
    pen = RecordingPen()
    font.getGlyphSet()[name].draw(pen)
    result = []
    points = []
    for op, pts in pen.value:
        if op == 'moveTo':
            points = [pts[0]]
        elif op == 'lineTo':
            points.extend(pts)
        elif op == 'closePath':
            if points[-1] == points[0]:
                points.pop()
            # TrueType reverses contour direction and may rotate the start point.
            forward, backward = tuple(points), tuple(reversed(points))
            result.append(min(r[i:] + r[:i] for r in (forward, backward) for i in range(len(r))))
        else:
            raise AssertionError('Unexpected non-pixel outline operation: ' + op)
    return sorted(result)


def shape(font, text):
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    buffer.language = 'vi'
    hb.shape(font, buffer)
    return [(g.codepoint, p.x_advance, p.x_offset, p.y_offset) for g, p in zip(buffer.glyph_infos, buffer.glyph_positions)]


class ExportTests(unittest.TestCase):
    def test_all_formats_preserve_approved_outlines_and_shaping(self):
        working_reference = ROOT.joinpath('scratchpad/vietnamese/VER 3/VFK-DepartureMono.otf')
        approved = TTFont(working_reference if working_reference.exists() else OUT.joinpath(STEM + '.otf'))
        for ext in ('otf', 'ttf', 'woff', 'woff2'):
            f = TTFont(OUT.joinpath(STEM + '.' + ext))
            self.assertEqual(f.getBestCmap(), approved.getBestCmap(), ext)
            self.assertEqual(f.getGlyphOrder(), approved.getGlyphOrder(), ext)
            self.assertEqual(f['post'].isFixedPitch, 1)
            self.assertGreaterEqual(f['hhea'].ascent, f['head'].yMax)
            self.assertGreaterEqual(f['OS/2'].usWinAscent, f['head'].yMax)
            self.assertGreaterEqual(f['OS/2'].usWinDescent, -f['head'].yMin)
            self.assertTrue(f['OS/2'].ulCodePageRange1 & (1 << 8))
            for name in f.getGlyphOrder():
                self.assertEqual(rings(f, name), rings(approved, name), (ext, name))
                self.assertEqual(f['hmtx'][name][0], approved['hmtx'][name][0], (ext, name))
            for tag in ('hhea', 'OS/2', 'GPOS', 'GSUB'):
                self.assertEqual(f.getTableData(tag), approved.getTableData(tag), (ext, tag))
            # HarfBuzz accepts SFNT bytes; unwrap web containers before shaping.
            f.flavor = None
            sfnt = io.BytesIO()
            f.save(sfnt)
            hfont = hb.Font(hb.Face(sfnt.getvalue()))
            for ch in VN:
                nfc = shape(hfont, ch)
                self.assertEqual(nfc, shape(hfont, unicodedata.normalize('NFD', ch)), (ext, ch))
                self.assertEqual(sum(g[1] for g in nfc), 350, (ext, ch))
                self.assertTrue(all(g[0] for g in nfc))

    def test_metadata_and_package(self):
        source = TTFont(ROOT.joinpath('public/assets/DepartureMono-1.500.otf'))
        checksums = json.loads(OUT.joinpath('build.json').read_text())['sha256']
        for ext in ('otf', 'ttf', 'woff', 'woff2'):
            path = OUT.joinpath(STEM + '.' + ext)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), checksums[path.name])
            font = TTFont(path)
            xml = io.StringIO()
            font.saveXML(xml)
            self.assertNotIn('vfk', xml.getvalue().casefold(), ext)
            self.assertEqual(font['name'].getDebugName(1), 'Departure Mono')
            self.assertEqual(font['name'].getDebugName(6), STEM)
            self.assertEqual(font['name'].getDebugName(5), 'Version 1.003')
            for name_id in (0, 9, 10, 12, 13, 14):
                self.assertEqual(font['name'].getDebugName(name_id), source['name'].getDebugName(name_id), (ext, name_id))
            if 'CFF ' in font:
                strings = font['CFF '].cff.strings.strings
                self.assertTrue(all('vfk' not in str(s).casefold() for s in strings), ext)
        archive = ROOT.joinpath('vietnamese/DepartureMono-Vietnamese-1.003.zip')
        with zipfile.ZipFile(archive) as z:
            self.assertIsNone(z.testzip())
            self.assertEqual(len(z.namelist()), 9)
            self.assertIn('Vietnamese adaptation by tuantm', z.read('README.txt').decode())
            self.assertEqual(z.read('LICENSE.txt'), ROOT.joinpath('public/assets/LICENSE').read_bytes())
            self.assertEqual(z.read('validation-word.txt').decode().count('KIỂM WORD: ĐẠT'), 4)

    def test_chromium_loads_every_format(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=shutil.which('chromium'), headless=True, args=['--no-sandbox'])
            page = browser.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.set_content('<!doctype html><html lang="en"><title>Font validation</title></html>')
            for ext in ('otf', 'ttf', 'woff', 'woff2'):
                data = list(OUT.joinpath(STEM + '.' + ext).read_bytes())
                status = page.evaluate('''async ({ext, data}) => {
                    const font = new FontFace('Final-' + ext, new Uint8Array(data));
                    await font.load(); document.fonts.add(font);
                    return font.status;
                }''', {'ext': ext, 'data': data})
                self.assertEqual(status, 'loaded', ext)
            self.assertEqual(errors, [])
            browser.close()


if __name__ == '__main__':
    unittest.main()
