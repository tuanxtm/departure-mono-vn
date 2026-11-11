# Vietnamese build and validation

Vietnamese adaptation by **[tuantm](https://github.com/tuanxtm)**, based on the
original font by **[Helena Zhang](https://helenazhang.com)** and the source at
**[rektdeckard/departure-mono](https://github.com/rektdeckard/departure-mono)**.
See the [project README](../README.md) for credits, installation and licensing.

VER 3 is approved and exported as **Departure Mono Regular**, version 1.003.
Download [all four formats with the OFL license and test text](DepartureMono-Vietnamese-1.003.zip),
or get [OTF](release/DepartureMono-Regular.otf), [TTF](release/DepartureMono-Regular.ttf),
[WOFF](release/DepartureMono-Regular.woff) or [WOFF2](release/DepartureMono-Regular.woff2).
All export metadata uses the original font name, author, website and license;
the kit prefix and watermark have been removed. Install either OTF or TTF.

All four files passed the Word gate and Chromium font loading. Export validation
compared every glyph outline and advance with approved VER 3, tested NFC/NFD
for all 134 Vietnamese characters, and checked all font tables and CFF string
entries for leftover branding. Copyright and license metadata match the original.

The earlier [review.html](review.html) remains available for comparison and records
the review versions with their original working names.

VER 3 lowers only the hook on lowercase `ỉ` by 100 units (two pixels), from
y=450 to y=350, matching `ả/ẻ/ỏ/ủ/ỷ`. Its shape, horizontal placement, uppercase
`Ỉ`, every other glyph, character advances and line metrics remain as in VER 2.
The page opens VER 3 and retains VER 2 for comparison.

The font contains 58 of the 134 Vietnamese letters already. The builder composes
the remaining 76 from the original outlines, retaining the original 50-unit pixel
grid, 350-unit character advance, copyright, OFL license and OpenType features.
Round 1 used the upper part of `?` for the hook; the horn uses `ư/Ư`. Combining marks have zero advance. Vietnamese `ccmp`
rules cover decomposed input, including shape/tone order variations.

The round-2 review compared the chosen VER 1B (tones above, using the original
150-unit stack step) with VER 2. VER 2 applies the user's supplied screenshot:
the original 3-square caron becomes the compact breve (150 × 100 units), and
the same shape rotated 90° counterclockwise becomes the hook (100 × 150).
Both uppercase and lowercase use the same mark size. Exactly 34 letters and
the two corresponding combining marks change; every other outline and all
character advances and line metrics remain identical to VER 1B. The
preview supports typing, loading a comparison font, adjusting marks, drawing
glyph feedback, and exporting edits from local browser storage. Send the exported
JSON with feedback: the agent cannot read another browser's local storage.

Build with Python and the installed viet-hoa-font skill:

```sh
uv --cache-dir scratchpad/uv-cache venv scratchpad/.venv
uv --cache-dir scratchpad/uv-cache pip install --python scratchpad/.venv/bin/python -r scripts/requirements-vietnamese.txt
scratchpad/.venv/bin/python -I scripts/vietnamese.py --kit /path/to/viet-hoa-font
scratchpad/.venv/bin/python -I scripts/vietnamese_round2.py --kit /path/to/viet-hoa-font
scratchpad/.venv/bin/python -I scripts/vietnamese_round3.py --kit /path/to/viet-hoa-font
scratchpad/.venv/bin/python -I scripts/vietnamese_review.py --kit /path/to/viet-hoa-font
scratchpad/.venv/bin/python -I scripts/vietnamese_export.py --kit /path/to/viet-hoa-font
```

The build commands require a separately installed `viet-hoa-font` skill, passed
through `--kit`; its tools are not bundled in this repository. Fonts and generated
review data are rebuilt from the original `public/assets/DepartureMono-1.500.otf`.
To refresh only the English release documentation and archive while preserving
the approved font bytes, run the export command with `--package-only`.

Intermediate fonts and data stay in ignored `scratchpad/vietnamese`. The original
release assets and the main specimen website remain unchanged during review.
The release includes OTF, TTF, WOFF and WOFF2 files, the font's
[OFL license](../public/assets/LICENSE), and Vietnamese test text.

The skill's Word gate checks font metadata, glyph coverage and outline widths;
it does not run Microsoft Word, Excel or Canva. Browser validation additionally
checks actual font loading and NFC/NFD shaping. Stacked accents increase the
vertical metrics; measured values are recorded with each review build.

Round 1 validation passed all five checks: original outlines and character widths,
Unicode composition, exact editor recipes, exact detail previews, and offline
Chromium loading/layout at 1280, 800 and 390 pixels in both themes. Every preview
font passed `kiemword.py` with `KIỂM WORD: ĐẠT`.

Round 2 passed all six checks, including an exact comparison against VER 1B
that permits only the 34 requested letters and their two combining marks.
The review opens VER 2, retains VER 1B for comparison, and shows the previous
outlines in the batch editor and drawing board. VER 3 was subsequently approved
for final export.

| Version | Top / descent | Default line increase | Character width changes |
| --- | --- | --- | --- |
| VER 1A | 800 / 150 | 35.7% | 0 |
| VER 1B | 800 / 150 | 35.7% | 0 |
| VER 1C | 700 / 150 | 21.4% | 0 |
| VER 2 | 800 / 150 (ink top 750) | 35.7% | 0 |
| VER 3 | 800 / 150 (ink top 750) | 35.7% | 0 |

Re-run the checks after building:

```sh
scratchpad/.venv/bin/python -m unittest discover -s scripts -p test_vietnamese.py -v
```

The final release can also be validated from a fresh clone without the skill or
review intermediates:

```sh
python3 -m venv scratchpad/.venv
scratchpad/.venv/bin/python -m pip install -r scripts/requirements-vietnamese.txt
scratchpad/.venv/bin/python -m playwright install --with-deps chromium
scratchpad/.venv/bin/python -m unittest discover -s scripts -p test_vietnamese_export.py -v
```

GitHub Actions runs these final-release checks on pushes and pull requests. The
inherited DreamHost deployment jobs are restricted to the upstream repository.
The original specimen website remains an upstream specimen and does not serve
the Vietnamese font files; download those from this project's release page.
