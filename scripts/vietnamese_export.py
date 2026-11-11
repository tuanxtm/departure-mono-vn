"""Export approved VER 3 in four formats, with original names and no kit branding."""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import shutil
import subprocess
import sys
import unicodedata
import zipfile

from fontTools.ttLib import TTFont, newTable
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.joinpath('public/assets/DepartureMono-1.500.otf')
APPROVED = ROOT.joinpath('scratchpad/vietnamese/VER 3/VFK-DepartureMono.otf')
OUTPUT = ROOT.joinpath('vietnamese/release')
STEM = 'DepartureMono-Regular'


def clean_font():
    font, source = TTFont(APPROVED), TTFont(SOURCE)
    # Restore the complete original naming table, including author, license,
    # website and feature labels. Only version and unique ID identify this build.
    font['name'] = copy.deepcopy(source['name'])
    for record in list(font['name'].names):
        if record.nameID == 3:
            font['name'].setName('1.003;UKWN;DepartureMono-Regular', 3, record.platformID, record.platEncID, record.langID)
        elif record.nameID == 5:
            font['name'].setName('Version 1.003', 5, record.platformID, record.platEncID, record.langID)
    font['head'].fontRevision = 1.003
    cff = font['CFF '].cff
    cff.fontNames = [STEM]
    top = cff.topDictIndex[0]
    top.FullName = source['name'].getDebugName(4)
    top.FamilyName = source['name'].getDebugName(1)
    top.version = '1.003'
    return font


def to_truetype(font):
    """The approved font uses only straight pixel contours; preserve them exactly."""
    gs = font.getGlyphSet()
    order = font.getGlyphOrder()
    glyf = newTable('glyf')
    glyf.glyphs = {}
    glyf.glyphOrder = order
    for name in order:
        pen = TTGlyphPen(None)
        gs[name].draw(Cu2QuPen(pen, max_err=1, reverse_direction=True))
        glyf.glyphs[name] = pen.glyph()
    font['glyf'] = glyf
    font['loca'] = newTable('loca')
    maxp = newTable('maxp')
    maxp.tableVersion = 0x00010000
    maxp.numGlyphs = len(order)
    for field in ('maxPoints', 'maxContours', 'maxCompositePoints', 'maxCompositeContours', 'maxZones', 'maxTwilightPoints', 'maxStorage', 'maxFunctionDefs', 'maxInstructionDefs', 'maxStackElements', 'maxSizeOfInstructions', 'maxComponentElements', 'maxComponentDepth'):
        setattr(maxp, field, 0)
    maxp.maxZones = 1
    font['maxp'] = maxp
    font['post'].formatType = 2.0
    font['post'].extraNames = []
    font['post'].mapping = {}
    font['post'].glyphOrder = order
    del font['CFF ']
    font.sfntVersion = '\x00\x01\x00\x00'
    font['head'].glyphDataFormat = 0
    for name in order:
        glyph = glyf[name]
        if glyph.numberOfContours:
            glyph.recalcBounds(glyf)
            font['hmtx'].metrics[name] = (font['hmtx'][name][0], glyph.xMin)
    maxp.recalc(font)
    return font


def assert_clean(path):
    font = TTFont(path)
    for record in font['name'].names:
        assert 'vfk' not in record.toUnicode().casefold(), (path, record.nameID)
    if 'CFF ' in font:
        cff = font['CFF '].cff
        # Include unused entries in the String INDEX, not just displayed names.
        values = [*cff.fontNames, *cff.strings.strings]
        assert all('vfk' not in str(value).casefold() for value in values), path
    if font.flavorData is not None:
        assert not getattr(font.flavorData, 'metaData', None), path
    return font


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kit', required=True, type=Path)
    parser.add_argument('--package-only', action='store_true', help='Refresh release documentation and ZIP without rebuilding approved fonts')
    args = parser.parse_args()
    kit = args.kit.resolve()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if not args.package_only:
        clean_font().save(OUTPUT.joinpath(STEM + '.otf'))
        to_truetype(clean_font()).save(OUTPUT.joinpath(STEM + '.ttf'))
        for flavor in ('woff', 'woff2'):
            font = clean_font()
            font.flavor = flavor
            font.save(OUTPUT.joinpath(STEM + '.' + flavor))
    paths = [OUTPUT.joinpath(STEM + '.' + ext) for ext in ('otf', 'ttf', 'woff', 'woff2')]
    log = subprocess.run([sys.executable, '-I', str(kit.joinpath('tools/kiemword.py')), *map(str, paths), *([] if args.package_only else ['--fix'])], capture_output=True, text=True, check=True)
    OUTPUT.joinpath('validation-word.txt').write_text(log.stdout)
    print(log.stdout)
    assert log.stdout.count('KIỂM WORD: ĐẠT') == 4
    for path in paths:
        assert_clean(path)
    shutil.copy2(ROOT.joinpath('public/assets/LICENSE'), OUTPUT.joinpath('LICENSE.txt'))
    text = ('Departure Mono Regular · VER 3 · Version 1.003\n'
            'Vietnamese adaptation by tuantm. Original font by Helena Zhang.\n'
            'Install either OTF or TTF; only one desktop format is needed.\n'
            'Close applications, uninstall an older Departure Mono build, install, then reopen.\n'
            'WOFF and WOFF2 are for websites. Use multiples of 11 px for pixel alignment.\n\n'
            '1. Stacked accents\n'
            'ẦẤẨẪẬ ẰẮẲẴẶ ỀẾỂỄỆ ỒỐỔỖỘ ỜỚỞỠỢ ỪỨỬỮỰ ỲÝỶỸỴ ÌÍỈĨỊ\n'
            'ầấẩẫậ ằắẳẵặ ềếểễệ ồốổỗộ ờớởỡợ ừứửữự ỳýỷỹỵ ìíỉĩị\n\n'
            '2. Vietnamese character coverage\n'
            'aàáảãạ ăằắẳẵặ âầấẩẫậ eèéẻẽẹ êềếểễệ iìíỉĩị oòóỏõọ ôồốổỗộ ơờớởỡợ uùúủũụ ưừứửữự yỳýỷỹỵ đ\n'
            'AÀÁẢÃẠ ĂẰẮẲẴẶ ÂẦẤẨẪẬ EÈÉẺẼẸ ÊỀẾỂỄỆ IÌÍỈĨỊ OÒÓỎÕỌ ÔỒỐỔỖỘ ƠỜỚỞỠỢ UÙÚỦŨỤ ƯỪỨỬỮỰ YỲÝỶỸỴ Đ\n\n'
            '3. Sample text\n'
            'ả ẻ ỉ ỏ ủ ỷ · nghỉ, tỉ mỉ, kỉ niệm · uppercase: Ỉ\n'
            'Người ươn ưa, cửa, TƯƠNG LAI · thưởng thức, mười, ưu tú, ƯỚC MƠ\n'
            'Phố cổ, “cổ,” ấm áp, ồn ào · ẨM THỰC · ủy ban, ỦY BAN · đã ĐƯỢC ghi nhận\n\n'
            '4. Line metrics\n'
            'Character advance: 350 units; combining marks: 0; pixel: 50; UPM: 550.\n'
            'Ascent / descent: 800 / 150. Highest ink: 750 (Ẳ Ẩ Ể Ổ); lowest ink in the full font: -150.\n'
            'Default lines are 35.7% taller than upstream to fit stacked accents, as approved in VER 3.\n\n'
            '5. Precomposed Unicode (NFC)\nNgười chỉ nghỉ ở cửa.\n\n'
            '6. Decomposed Unicode (NFD), should look identical to section 5\n'
            + unicodedata.normalize('NFD', 'Người chỉ nghỉ ở cửa.') + '\n')
    OUTPUT.joinpath('test-tieng-viet.txt').write_text(text)
    release_readme = '''Departure Mono VN — v1.003

Vietnamese adaptation by tuantm: https://github.com/tuanxtm
Project: https://github.com/tuanxtm/departure-mono-vn

Original Departure Mono typeface by Helena Zhang: https://helenazhang.com
Original source: https://github.com/rektdeckard/departure-mono
Original specimen website by Helena Zhang and Tobias Fried.

Based on upstream Departure Mono 1.500. This release adds 76 missing Vietnamese
letters and two combining marks, for 134 Vietnamese-specific precomposed
characters and 1,264 total glyphs. Precomposed and decomposed input is supported.

Install one of the OTF or TTF files for desktop use. Use WOFF/WOFF2 on the web.
The installed family name remains Departure Mono; uninstall an older build first.
The Vietnamese release number is independent of the upstream version number.

The font and its modifications are licensed under SIL OFL 1.1; see LICENSE.txt.
Original copyright and license metadata are preserved. This is a derivative
adaptation, not an official upstream release.

test-tieng-viet.txt contains sample text with English instructions.
validation-word.txt contains the compatibility tool's original diagnostic output.
build.json records the build information and SHA-256 checksums for all fonts.
'''
    OUTPUT.joinpath('README.txt').write_text(release_readme)
    report = {'approved_version': 'VER 3', 'font_version': '1.003', 'family': 'Departure Mono',
              'postscript_name': STEM, 'formats': [p.suffix[1:] for p in paths], 'vietnamese_characters': 134,
              'word_gate': 'passed for all four files', 'kit_branding_in_metadata': False,
              'sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    OUTPUT.joinpath('build.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    archive = ROOT.joinpath('vietnamese/DepartureMono-Vietnamese-1.003.zip')
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as zip_file:
        for path in [*paths, OUTPUT.joinpath('LICENSE.txt'), OUTPUT.joinpath('README.txt'), OUTPUT.joinpath('test-tieng-viet.txt'), OUTPUT.joinpath('validation-word.txt'), OUTPUT.joinpath('build.json')]:
            zip_file.write(path, arcname=path.name)
    print(archive)


if __name__ == '__main__':
    main()
