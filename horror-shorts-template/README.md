# Horror Shorts template

Vertical English horror shorts: flat 2D cut-out characters in a colourful night-time three.js toon world (ink outlines,
painted textures, warm glowing lamps, fog, flashlight, flicker, film grain), one-word captions, fully synthesised horror sound design.

- `studio/` — Remotion 4 + three.js project. Engine in `src/engine/`, shorts in `src/shorts/<name>/`.
  Demos: `Floor13` ("The Thirteenth Floor", 42 s, main Dark Toon look), `MannequinsToon` (main colourful toon look) and `Mannequins` (dark look), "Eleven Mannequins", 21 s. `npm install`, then `npx remotion studio src/index.ts`.
- `tools/` — `voice_words.py` (word timings with faster-whisper), `horror_sfx.py` (sound bed + mix, −14 LUFS),
  `qa.py` (checks), `draft_voice.py` (draft TTS for pacing only).
- `CLAUDE.md` — workflow for Claude Code (commands «Установи», «Придумай темы», «Сделай ролик», «Поправь»).
- `STYLE.md` — the style guide. `НАЧНИ ЗДЕСЬ.md` — quick start for the owner (Russian).

The demo voice in `studio/public/mannequins/` is a synthetic draft voice (Kokoro TTS), used only to show the pacing.

The caption font (Anton, studio/public/fonts) is under the SIL Open Font License.
