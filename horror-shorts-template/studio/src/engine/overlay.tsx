// DOM overlays drawn above the 3D canvas: film grain, vignette, flashes, blackout, word-by-word captions.
import React from "react";
import { AbsoluteFill, continueRender, delayRender, staticFile } from "remotion";

export const FONT = "HorrorCaption";
if (typeof document !== "undefined") {
  const h = delayRender("caption font");
  new FontFace(FONT, `url(${staticFile("fonts/anton.woff2")})`).load()
    .then((x) => (document.fonts as unknown as { add: (f: FontFace) => void }).add(x)).catch((e) => console.warn(e)).finally(() => continueRender(h));
}

export const Grain: React.FC<{ f: number; amount?: number }> = ({ f, amount = 0.16 }) => (
  <AbsoluteFill style={{ mixBlendMode: "overlay", opacity: amount, pointerEvents: "none" }}>
    <svg width="100%" height="100%">
      <filter id="g"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed={f % 97} /><feColorMatrix type="saturate" values="0" /></filter>
      <rect width="100%" height="100%" filter="url(#g)" />
    </svg>
  </AbsoluteFill>
);

export const Vignette: React.FC<{ strength?: number }> = ({ strength = 0.75 }) => (
  <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 45%, rgba(0,0,0,${strength}) 100%)`, pointerEvents: "none" }} />
);

export const Tint: React.FC<{ color: string; opacity: number }> = ({ color, opacity }) =>
  opacity > 0 ? <AbsoluteFill style={{ background: color, opacity, pointerEvents: "none" }} /> : null;

// ---------- captions ----------
export type Word = { w: string; s: number; e: number; x?: number }; // x: 1 = emphasis colour
export type CaptionStyle = { y: number; size: number; emph: string[]; emphColor: string };

/** One word on screen at a time (horror pacing), from its start until the next word (max 0.9 s). */
export const Captions: React.FC<{ words: Word[]; f: number; fps: number; style: CaptionStyle; hidden?: boolean }> = ({ words, f, fps, style, hidden }) => {
  if (hidden) return null;
  const t = f / fps;
  let i = -1;
  for (let k = 0; k < words.length; k++) if (words[k].s <= t) i = k;
  if (i < 0) return null;
  const w = words[i];
  const until = Math.min(i + 1 < words.length ? words[i + 1].s : w.e + 0.5, w.s + 0.9, w.e + 0.5);
  if (t > until) return null;
  const k = (t - w.s) * fps;
  const pop = k < 4 ? 0.82 + 0.18 * (k / 4) + Math.sin((k / 4) * Math.PI) * 0.06 : 1;
  const clean = w.w.replace(/[.,!?:;]+$/g, "").toUpperCase();
  const red = !!w.x || style.emph.includes(clean);
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div style={{
        position: "absolute", left: 0, right: 0, top: `${style.y * 100}%`, transform: `translateY(-50%) scale(${pop})`,
        textAlign: "center", fontFamily: FONT, fontSize: style.size, letterSpacing: "0.02em",
        color: red ? style.emphColor : "#f4f1ea", WebkitTextStroke: "14px #000", paintOrder: "stroke fill",
        textShadow: red ? `0 0 28px ${style.emphColor}88` : "0 6px 16px rgba(0,0,0,0.6)",
      }}>{clean}</div>
    </AbsoluteFill>
  );
};
