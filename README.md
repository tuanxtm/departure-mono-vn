# Departure Mono VN

[![Latest release](https://img.shields.io/github/v/release/tuanxtm/departure-mono-vn)](https://github.com/tuanxtm/departure-mono-vn/releases/latest)
[![Font license: SIL OFL 1.1](https://img.shields.io/badge/font-SIL%20OFL%201.1-blue)](OFL.txt)
[![Vietnamese coverage](https://img.shields.io/badge/Vietnamese-134%20characters-green)](#vietnamese-support)

A Vietnamese adaptation of **Departure Mono**, the monospaced pixel font designed
by [Helena Zhang](https://helenazhang.com).

**Vietnamese adaptation by [tuantm](https://github.com/tuanxtm).**

This project builds on [rektdeckard/departure-mono](https://github.com/rektdeckard/departure-mono),
preserving its pixel shapes and fixed character width while adding the missing
Vietnamese letters. The original font and its visual identity belong to their
original creators. Visit the [original specimen website](https://departuremono.com)
to learn about Departure Mono.

## Download

[**Download the latest Vietnamese font release**](https://github.com/tuanxtm/departure-mono-vn/releases/latest)

The current release is **v1.003**, based on upstream **Departure Mono 1.500**.
The Vietnamese release number is independent of the upstream version number.

| Format | Use | Direct download |
| --- | --- | --- |
| OTF | Desktop applications | [DepartureMono-Regular.otf](https://github.com/tuanxtm/departure-mono-vn/releases/download/v1.003/DepartureMono-Regular.otf) |
| TTF | Desktop applications | [DepartureMono-Regular.ttf](https://github.com/tuanxtm/departure-mono-vn/releases/download/v1.003/DepartureMono-Regular.ttf) |
| WOFF | Web embedding | [DepartureMono-Regular.woff](https://github.com/tuanxtm/departure-mono-vn/releases/download/v1.003/DepartureMono-Regular.woff) |
| WOFF2 | Web embedding with smaller downloads | [DepartureMono-Regular.woff2](https://github.com/tuanxtm/departure-mono-vn/releases/download/v1.003/DepartureMono-Regular.woff2) |
| ZIP | All formats, license, credits and test text | [DepartureMono-Vietnamese-1.003.zip](https://github.com/tuanxtm/departure-mono-vn/releases/download/v1.003/DepartureMono-Vietnamese-1.003.zip) |

The same files are available in [vietnamese/release](vietnamese/release).
See the [changelog](CHANGELOG.md) for release details.

## Vietnamese support

The adaptation adds **76 missing Vietnamese letters**, bringing coverage to
**134 Vietnamese-specific precomposed characters**: 67 lowercase and 67 uppercase.
This includes modified vowels, their tone combinations, and `đ/Đ`; the ordinary
unaccented Latin letters are already present in the original font.

| Measure | Upstream 1.500 | Vietnamese v1.003 |
| --- | --- | --- |
| Vietnamese characters | 58 | **134** |
| Total glyphs | 1,186 | **1,264** |
| Mapped Unicode code points | 1,079 | **1,157** |
| Character advance | 350 font units | **350 font units** |

The 78 added glyphs consist of the **76 letters** and **two combining marks**:
hook above (`U+0309`) and horn (`U+031B`). Both precomposed input (NFC) and
decomposed input (NFD) are supported. Combining marks have zero advance.

The Vietnamese accents use parts of the original font. The compact mark on
`ă/Ă` uses its three-pixel caron shape; the hook above uses the same shape rotated
vertically. Horns come from the original `ư/Ư`. The hook on lowercase `ỉ` aligns
with `ả/ẻ/ỏ/ủ/ỷ`.

```text
Ă Ắ Ằ Ẳ Ẵ Ặ · Â Ấ Ầ Ẩ Ẫ Ậ · Ê Ế Ề Ể Ễ Ệ
Ô Ố Ồ Ổ Ỗ Ộ · Ơ Ớ Ờ Ở Ỡ Ợ · Ư Ứ Ừ Ử Ữ Ự
ă ắ ằ ẳ ẵ ặ · â ấ ầ ẩ ẫ ậ · ê ế ề ể ễ ệ
ô ố ồ ổ ỗ ộ · ơ ớ ờ ở ỡ ợ · ư ứ ừ ử ữ ự
ả ẻ ỉ ỏ ủ ỷ · Đ đ
Người chỉ nghỉ ở cửa. Tiếng Việt có dấu.
```

## Installation

1. Download and extract the ZIP, or download either the OTF or TTF file.
2. Close applications that use the font. Uninstall an older Departure Mono build
   first: this adaptation retains the family name **Departure Mono** and the
   PostScript name **DepartureMono-Regular**.
3. Install **one** desktop format: open the OTF or TTF and choose **Install**.
4. Reopen your applications and select **Departure Mono**.

On Linux, you can copy the OTF or TTF into your user font directory and refresh
the font cache. Use the WOFF/WOFF2 files for websites.

Upstream Homebrew and Nix packages install the original font. Use this
repository's releases to install the Vietnamese adaptation.

## Web usage

Copy the WOFF2 and WOFF files into your site's font directory:

```css
@font-face {
  font-family: "Departure Mono";
  src: url("/fonts/DepartureMono-Regular.woff2") format("woff2"),
       url("/fonts/DepartureMono-Regular.woff") format("woff");
  font-style: normal;
  font-weight: 400;
  font-display: swap;
}

code, pre {
  font-family: "Departure Mono", monospace;
  font-size: 22px;
}
```

For pixel alignment, use font sizes in multiples of **11px**: 11, 22, 33, 44 or
55px. Adjust tracking to suit your layout. Default line metrics are about 35.7%
taller than upstream so stacked uppercase accents fit without clipping.

## Validation and development

All four formats passed the font compatibility gate and loaded in Chromium.
Validation checks Vietnamese NFC/NFD shaping, fixed advances, matching outlines
across formats, clipping metrics, preserved copyright/license metadata, and the
absence of the review kit's prefix and watermark in release metadata. These
checks do not constitute a manual test in every desktop application.

See [the build and validation guide](vietnamese/README.md) for reproducible build
commands and the distinction between the final fonts and the inherited specimen
website. The original website files and upstream release assets remain available
in this repository; the Vietnamese font downloads are under `vietnamese/release`.

For a rendering issue, [open an issue](https://github.com/tuanxtm/departure-mono-vn/issues/new)
with the affected text, font version, application, operating system and a screenshot.

## Credits

| Contribution | Credit |
| --- | --- |
| Original Departure Mono typeface | [Helena Zhang](https://helenazhang.com) |
| Original specimen website | [Helena Zhang](https://helenazhang.com) and [Tobias Fried](https://tobiasfried.com) |
| Original source repository | [rektdeckard/departure-mono](https://github.com/rektdeckard/departure-mono) |
| Vietnamese adaptation and maintenance | [tuantm](https://github.com/tuanxtm) |

This is a derivative adaptation, not an official upstream release.

## Licenses

| Material | License |
| --- | --- |
| Original font, Vietnamese font modifications and distributed font files | [SIL Open Font License 1.1](OFL.txt) |
| Original specimen website and repository code | [MIT](LICENSE) |

Original copyright and license notices are preserved. The OFL text is also
included with the downloadable fonts. See [LICENSES.md](LICENSES.md) for the
license layout; the root MIT license does not replace the font's OFL license.

