"""Assemble the skill's offline review UI using this project's exact pixel data."""
from pathlib import Path
import argparse
import html
import json
import os
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kit', required=True, type=Path)
    parser.add_argument('--round', type=int, choices=(1, 2, 3), default=3)
    args = parser.parse_args()
    kit = args.kit.resolve()
    work = ROOT.joinpath('scratchpad/vietnamese')
    data = work.joinpath('r' + str(args.round))
    output = ROOT.joinpath('vietnamese/review.html')
    output.parent.mkdir(exist_ok=True)
    template = kit.joinpath('tools/content_template.py').read_text()
    template = template.replace('<slug-font>', 'departure-mono').replace('<Tên font gốc>', 'Departure Mono')
    template = template.replace('OUT_STYLE, OUT_EXT = "Regular", ".ttf"', 'OUT_STYLE, OUT_EXT = "Regular", ".otf"')
    previous_tag = 'VER 1B' if args.round == 2 else 'VER 2'
    current_tag = 'VER ' + str(args.round)
    previous_family = 'FV-v1b' if args.round == 2 else 'FV-v2'
    if args.round >= 2:
        template = template.replace('ROUND = 1', 'ROUND = ' + str(args.round)).replace('VER_LABEL = "vòng 1"', 'VER_LABEL = "vòng ' + str(args.round) + '"').replace('VER_BASE = "VER 1C"', 'VER_BASE = "' + current_tag + '"')
        start = template.index('VERS = [')
        end = template.index('\nTEXT =', start)
        versions = [(previous_tag, '1.001' if args.round == 2 else '1.002', previous_family, 'Bản nền được giữ để so sánh.'),
                    (current_tag, '1.002' if args.round == 2 else '1.003', 'Font VN', 'Dấu ă ba ô pixel theo ảnh; dấu hỏi là cùng dấu xoay dọc.' if args.round == 2 else 'Chỉ hạ dấu hỏi của ỉ 100 đơn vị, ngang với ả/ẻ/ỏ/ủ/ỷ.')]
        template = template[:start] + 'VERS = ' + repr(versions) + template[end:]
    text = ('ẦẤẨẪẬ ẰẮẲẴẶ ỀẾỂỄỆ ỒỐỔỖỘ\n'
            'ầấẩẫậ ằắẳẵặ ềếểễệ ồốổỗộ\n'
            'ỜỚỞỠỢ ỪỨỬỮỰ ỲÝỶỸỴ ÌÍỈĨỊ\n'
            'ờớởỡợ ừứửữự ỳýỷỹỵ ìíỉĩị\n'
            'NGƯỜI ƯỚC MƠ · TƯƠNG LAI · ĐẦU TƯ\n'
            'Người, ố ấ ồ Ố Ấ, ẩ ể ổ Ẩ, ở ử, “cổ,” ƯT ƯƠ TƯƠNG ươ\n'
            'àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩị\n'
            'òóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ\n'
            'ÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊ\n'
            'ÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ')
    start = template.index('TEXT = (')
    end = template.index('\nNEWS =', start)
    template = template[:start] + 'TEXT = ' + repr(text) + template[end:]
    news = [
        'Bổ sung 76 tổ hợp còn thiếu; giữ nguyên nét 58 chữ Việt có sẵn. Dấu sắc, huyền, ngã, mũ, trăng và chấm lấy từ font gốc.',
        'Giữ ô rộng 350 đơn vị và nét pixel 50 đơn vị. Không chữ nào tăng độ rộng. Râu lấy từ ư / Ư; dấu hỏi lấy từ phần trên của ?.',
        'VER 1A: dấu bên phải · 1B: dấu trên đỉnh theo bước neo gốc · 1C: dấu hỏi ngắn hơn. Đỉnh dòng 800 / 800 / 700 (gốc 550); dòng tăng 36% / 36% / 21%. Xuất OTF, TTF, WOFF, WOFF2 sau khi chốt VER.'
    ]
    if args.round == 2:
        text = ('ă ằ ắ ẳ ẵ ặ   Ă Ằ Ắ Ẳ Ẵ Ặ\n'
                'ả ẳ ẩ ẻ ể ỉ ỏ ổ ở ủ ử ỷ\n'
                'Ả Ẳ Ẩ Ẻ Ể Ỉ Ỏ Ổ Ở Ủ Ử Ỷ\n'
                'Chẳng, khẳng, khỏe, cửa, người, nở, hỏi\n') + text
        start = template.index('TEXT = ')
        end = template.index('\nNEWS =', start)
        template = template[:start] + 'TEXT = ' + repr(text) + template[end:]
        news = [
            'Giữ VER 1B làm nền. Nhóm ă/Ă dùng nguyên dấu caron ba ô pixel của font, đúng dáng ảnh: 150 × 100 đơn vị, cùng cỡ cho hoa và thường.',
            'Dấu hỏi là cùng dấu xoay 90° sang chiều dọc: 100 × 150 đơn vị; áp dụng cả dấu hỏi đơn và chồng. Tổng cộng 34 chữ đổi, không chữ nào đổi độ rộng.',
            'Các chữ ngoài hai nhóm giữ nguyên. Chọn VER 1B để so; viền đứt ở Chỉnh dấu và Bàn vẽ là nét cũ. Mở sẵn VER 2 để gõ thử.'
        ]
    elif args.round == 3:
        text = ('ả ẻ ỉ ỏ ủ ỷ\n'
                'ả ẳ ẩ ẻ ể ỉ ỏ ổ ở ủ ử ỷ\n'
                'ỉ ỉ ỉ   Ỉ Ỉ Ỉ\n'
                'Chỉ một chữ: nghỉ, tỉ mỉ, kỉ niệm\n') + text
        start = template.index('TEXT = ')
        end = template.index('\nNEWS =', start)
        template = template[:start] + 'TEXT = ' + repr(text) + template[end:]
        news = [
            'Chỉ sửa chữ ỉ: dấu hỏi hạ 100 đơn vị (2 ô pixel), đáy 450 → 350, ngang với ả/ẻ/ỏ/ủ/ỷ.',
            'Giữ nguyên dáng dấu, vị trí ngang, chữ Ỉ và toàn bộ chữ khác của VER 2. Độ rộng và giãn dòng không đổi.',
            'Mở sẵn VER 3; chọn VER 2 để so. Viền đứt ở Chỉnh dấu và Bàn vẽ là vị trí dấu cũ.'
        ]
    template = re.sub(r'^NEWS = .*$', 'NEWS = ' + repr(news), template, flags=re.M)
    template = template.replace('VK.preview(VERS, TEXT, 48, MEAS', 'VK.preview(VERS, TEXT, 55, MEAS')
    template = re.sub(r'^EXTRA_HEAD = .*$', "EXTRA_HEAD = ''", template, flags=re.M)
    license_html = ('<details><summary>Departure Mono · SIL Open Font License 1.1</summary><pre style="white-space:pre-wrap">'
                    + html.escape(ROOT.joinpath('public/assets/LICENSE').read_text()) + '</pre></details>')
    template = template.replace("sources_html() + '</div>'", "sources_html() + " + repr(license_html) + " + '</div>'")
    content = work.joinpath('content_r' + str(args.round) + '.py')
    content.write_text(template)
    slider = kit.joinpath('tools/slider_ui.html').read_text()
    # This source's dot top is -50; the generic kit assumes -40.
    slider = slider.replace('(-40 - ph / 2 + T.ny)', '(-50 - ph / 2 + T.ny)')
    work.joinpath('slider_ui.html').write_text(slider)
    env = dict(os.environ, HOST_OUT=str(work.joinpath('host-review.html')))
    subprocess.run([sys.executable, '-I', str(kit.joinpath('tools/build_page.py')), str(kit.joinpath('tools/tpl')), str(data), str(output), str(content)], check=True, env=env)
    # The font and editing data are embedded; UI fonts use local fallbacks offline.
    for path in [output, work.joinpath('host-review.html')]:
        page = path.read_text()
        page = re.sub(r'<link[^>]+(?:fonts\.googleapis\.com|fonts\.gstatic\.com)[^>]*>', '', page)
        page = page.replace('<meta charset="utf-8">', '<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">', 1)
        if args.round >= 2:
            old = json.loads(data.joinpath('vers', previous_tag, 'editor.json').read_text())
            old_batch = json.loads(data.joinpath('vers', previous_tag, 'batch.json').read_text())
            payload = json.dumps(old, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
            page = page.replace('<script>', '<script>window.__ROUND2_OLD=' + payload + ';</script><script>', 1)
            page = page.replace("'fv-ver2-vv'", "'fv-ver2-vv-r" + str(args.round) + "'").replace("'vk-pvmode'", "'vk-pvmode-r" + str(args.round) + "'")
            page = page.replace("var vm='van'", "var vm='chu'").replace("getItem('vk-pvmode-r" + str(args.round) + "')||'van'", "getItem('vk-pvmode-r" + str(args.round) + "')||'chu'")
            old_line = "d: opsToD(sel.kind === 'm' ? (FV.marks[sel.id] || []) : sourceOpsPristine())"
            new_line = "d: opsToD(window.__FV_VER === " + repr(current_tag) + " ? (sel.kind === 'm' ? (window.__ROUND2_OLD.marks[sel.id] || []) : (window.__ROUND2_OLD.glyphs[sel.id] || {c:sourceOpsPristine()}).c) : (sel.kind === 'm' ? (FV.marks[sel.id] || []) : sourceOpsPristine()))"
            assert old_line in page
            page = page.replace(old_line, new_line)
            old_ghost = "if(moved&&hi)mk+='<path class=\"gh\" d=\"'+m.d+'\"/>';"
            new_ghost = "if(hi&&(moved||m.old_d))mk+='<path class=\"gh\" d=\"'+(m.old_d||m.d)+'\"/>';"
            assert old_ghost in page
            page = page.replace(old_ghost, new_ghost)
            switch = "var ROUND2_BATCH_BASE=D,ROUND2_BATCH_OLD=" + json.dumps(old_batch, ensure_ascii=False, separators=(',', ':')) + ";window.addEventListener('fv-ver',function(e){D=e.detail.tag===" + repr(previous_tag) + "?ROUND2_BATCH_OLD:ROUND2_BATCH_BASE;BY={};D.chars.forEach(function(c){BY[c.ch]=c;});render();});"
            init = "var BY={};D.chars.forEach(function(c){BY[c.ch]=c;});"
            assert init in page
            page = page.replace(init, init + switch)
        path.write_text(re.sub(r'(?m)^[ \t]+$', '', page))
    print(output)


if __name__ == '__main__':
    main()
