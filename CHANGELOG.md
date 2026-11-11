# Changelog

## v1.003 — 2026-11-11

First public Vietnamese release, based on Departure Mono 1.500.

- Add 76 missing Vietnamese letters for 134 Vietnamese-specific precomposed characters.
- Add combining hook above and horn marks, bringing the font to 1,264 glyphs.
- Support precomposed (NFC) and decomposed (NFD) Vietnamese input.
- Preserve the original 350-unit character advance and 50-unit pixel grid.
- Use compact three-pixel marks for the breve and hook above; align the hook on `ỉ` with other lowercase vowels.
- Fit stacked uppercase accents within the font's vertical metrics.
- Provide OTF, TTF, WOFF and WOFF2, plus a ZIP with credits, the OFL license and test text.
- Preserve original author and license metadata; remove review-kit branding from release font metadata.

Vietnamese adaptation by **tuantm**. Original typeface by **Helena Zhang**;
original source: [rektdeckard/departure-mono](https://github.com/rektdeckard/departure-mono).

The release passed outline, Unicode shaping, metadata, browser loading and font
compatibility checks. Its version number is independent of the upstream font's version.
