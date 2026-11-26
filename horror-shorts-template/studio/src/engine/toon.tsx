// "Toon" look for the horror world: ink-outlined props, hand-painted canvas textures, warm glowing lamps,
// saturated night colours. Use these instead of the plain pieces in scene.tsx for the colourful cartoon style.
import React from "react";
import * as THREE from "three";
import { propTexture } from "./draw";
import type { V3 } from "./scene";

const INK = "#120c16";

// ---------- painted textures ----------
const rng = (seed: number) => () => { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; };
/** Lots of short translucent strokes on top of a texture: reads as "painted" instead of flat. */
const brush = (c: CanvasRenderingContext2D, w: number, h: number, colors: string[], n: number, seed: number, len = 26, alpha = 0.12) => {
  const r = rng(seed);
  c.lineCap = "round";
  for (let i = 0; i < n; i++) {
    c.globalAlpha = alpha * (0.5 + r());
    c.strokeStyle = colors[Math.floor(r() * colors.length)];
    c.lineWidth = 2 + r() * 6;
    const x = r() * w, y = r() * h, a = (r() - 0.5) * 0.6;
    c.beginPath(); c.moveTo(x, y); c.lineTo(x + Math.cos(a) * len * (0.5 + r()), y + Math.sin(a) * len * (0.5 + r())); c.stroke();
  }
  c.globalAlpha = 1;
};

export const woodFloorTex = () => propTexture("toon-wood", 1024, 1024, (c) => {
  const r = rng(11), plank = 128;
  for (let y = 0; y < 1024; y += plank) {
    let x = -Math.floor(r() * 300);
    while (x < 1024) {
      const len = 300 + r() * 260;
      const tone = ["#8a5232", "#7b4529", "#985d38", "#6f3e25"][Math.floor(r() * 4)];
      c.fillStyle = tone; c.fillRect(x, y, len, plank);
      c.strokeStyle = "rgba(40,18,8,0.35)"; c.lineWidth = 3;
      for (let k = 0; k < 5; k++) { const gy = y + 14 + r() * (plank - 28); c.beginPath(); c.moveTo(x, gy); c.bezierCurveTo(x + len * 0.3, gy + 6, x + len * 0.6, gy - 6, x + len, gy + 2); c.stroke(); }
      c.strokeStyle = INK; c.lineWidth = 5; c.strokeRect(x, y, len, plank);
      x += len;
    }
  }
  brush(c, 1024, 1024, ["#c98a5a", "#4a2414", "#a86a40"], 1400, 5, 40, 0.1);
});

export const wallpaperTex = () => propTexture("toon-wallpaper", 512, 1024, (c) => {
  c.fillStyle = "#2e6b6b"; c.fillRect(0, 0, 512, 1024);
  for (let x = 0; x < 512; x += 128) { c.fillStyle = "#2a6162"; c.fillRect(x, 0, 64, 1024); }
  c.fillStyle = "rgba(160,220,200,0.22)";
  for (let y = 40; y < 760; y += 120) for (let x = 32; x < 512; x += 128) { // diamond motif
    c.beginPath(); c.moveTo(x + 32, y); c.lineTo(x + 52, y + 30); c.lineTo(x + 32, y + 60); c.lineTo(x + 12, y + 30); c.closePath(); c.fill();
  }
  // wainscot: dark wood panels at the bottom
  c.fillStyle = "#4a2a1c"; c.fillRect(0, 780, 512, 244);
  c.strokeStyle = INK; c.lineWidth = 8;
  c.beginPath(); c.moveTo(0, 780); c.lineTo(512, 780); c.stroke();
  for (let x = 16; x < 512; x += 128) { c.strokeStyle = "#2c160e"; c.lineWidth = 5; c.strokeRect(x, 812, 96, 180); }
  c.fillStyle = "#6b3e28"; c.fillRect(0, 768, 512, 16);
  brush(c, 512, 1024, ["#7fc3b4", "#16403f", "#3d8a84"], 900, 9, 30, 0.12);
});

const posterTex = (key: string, title: string, sub: string, bg: string, fg: string) => propTexture(key, 400, 560, (c) => {
  c.fillStyle = bg; c.fillRect(0, 0, 400, 560);
  c.fillStyle = fg; c.textAlign = "center";
  c.font = "bold 120px Georgia, serif"; c.fillText(title, 200, 250);
  c.font = "bold 54px Georgia, serif"; c.fillText(sub, 200, 340);
  c.strokeStyle = INK; c.lineWidth = 16; c.strokeRect(8, 8, 384, 544);
  brush(c, 400, 560, ["#ffffff", "#000000"], 300, 3, 20, 0.08);
});

// ---------- outlined meshes ----------
/** Box with an inked outline (inverted hull) and an optional painted map. */
export const OBox: React.FC<{ p: V3; s: V3; c: string; rot?: V3; map?: THREE.Texture; ink?: number; rough?: number; emissive?: string; ei?: number; shadow?: boolean }> =
  ({ p, s, c, rot, map, ink = 0.022, rough = 0.85, emissive, ei = 1, shadow = true }) => (
    <group position={p} rotation={rot ?? [0, 0, 0]}>
      <mesh castShadow={shadow} receiveShadow>
        <boxGeometry args={s} />
        <meshStandardMaterial color={c} map={map ?? null} roughness={rough} emissive={emissive ?? "#000"} emissiveIntensity={ei} />
      </mesh>
      {ink > 0 && (
        <mesh scale={[(s[0] + ink * 2) / s[0], (s[1] + ink * 2) / s[1], (s[2] + ink * 2) / s[2]]}>
          <boxGeometry args={s} />
          <meshBasicMaterial color={INK} side={THREE.BackSide} />
        </mesh>
      )}
    </group>
  );

/** Soft additive glow (a cheap bloom) around lamps, windows, signs. */
const glowTex = () => propTexture("glow", 128, 128, (c) => {
  const g = c.createRadialGradient(64, 64, 0, 64, 64, 64);
  g.addColorStop(0, "rgba(255,255,255,1)"); g.addColorStop(0.25, "rgba(255,255,255,0.45)"); g.addColorStop(1, "rgba(255,255,255,0)");
  c.fillStyle = g; c.fillRect(0, 0, 128, 128);
});
export const Glow: React.FC<{ p: V3; size: number; color: string; strength?: number }> = ({ p, size, color, strength = 1 }) =>
  strength <= 0.01 ? null : (
    <sprite position={p} scale={[size, size, 1]}>
      <spriteMaterial map={glowTex()} color={color} transparent opacity={Math.min(1, strength)} blending={THREE.AdditiveBlending} depthWrite={false} />
    </sprite>
  );

// ---------- set pieces ----------
export const PaintedFloor: React.FC<{ w: number; d: number; z?: number }> = ({ w, d, z = 0 }) => {
  const t = woodFloorTex();
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(w / 5, d / 5); t.anisotropy = 8;
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, z]} receiveShadow>
      <planeGeometry args={[w, d]} />
      <meshStandardMaterial map={t} roughness={0.55} />
    </mesh>
  );
};
export const PaintedWall: React.FC<{ p: V3; w: number; h: number; rotY?: number }> = ({ p, w, h, rotY = 0 }) => {
  const t = wallpaperTex().clone();
  t.wrapS = THREE.RepeatWrapping; t.repeat.set(w / 2.2, 1); t.needsUpdate = true;
  return (
    <group position={p} rotation={[0, rotY, 0]}>
      <mesh receiveShadow>
        <planeGeometry args={[w, h]} />
        <meshStandardMaterial map={t} roughness={0.95} />
      </mesh>
      <OBox p={[0, h / 2 - 0.08, 0.04]} s={[w, 0.16, 0.08]} c="#3a2030" />
    </group>
  );
};

/** Warm ceiling lamp: glowing shade + light + halo; `on` 0..1. */
export const WarmLamp: React.FC<{ pos: V3; on: number }> = ({ pos, on }) => (
  <group position={pos}>
    <OBox p={[0, 0.25, 0]} s={[0.04, 0.5, 0.04]} c="#1a1418" ink={0.012} shadow={false} />
    <mesh position={[0, 0, 0]}>
      <coneGeometry args={[0.42, 0.32, 20, 1, true]} />
      <meshStandardMaterial color="#2c4a3a" side={THREE.DoubleSide} roughness={0.6} />
    </mesh>
    <mesh position={[0, -0.12, 0]}>
      <sphereGeometry args={[0.12, 16, 12]} />
      <meshStandardMaterial color="#332a1a" emissive="#ffd27a" emissiveIntensity={0.2 + 3 * on} />
    </mesh>
    <pointLight position={[0, -0.4, 0]} color="#ffb257" intensity={9 * on} distance={10} decay={1.6} />
    <Glow p={[0, -0.14, 0]} size={1.4} color="#ffbe6a" strength={on * 0.9} />
  </group>
);

export const ToonWindow: React.FC<{ p: V3; rotY?: number; w?: number; h?: number }> = ({ p, rotY = 0, w = 2, h = 2.4 }) => (
  <group position={p} rotation={[0, rotY, 0]}>
    <mesh><planeGeometry args={[w, h]} /><meshBasicMaterial color="#5f86d8" /></mesh>
    <mesh position={[w * 0.18, h * 0.22, 0.005]}><circleGeometry args={[0.28, 32]} /><meshBasicMaterial color="#fff3c4" /></mesh>
    <Glow p={[w * 0.18, h * 0.22, 0.05]} size={1.6} color="#cfe0ff" strength={0.8} />
    <OBox p={[0, 0, 0.03]} s={[0.1, h, 0.06]} c="#2a1d2e" />
    <OBox p={[0, 0, 0.03]} s={[w, 0.1, 0.06]} c="#2a1d2e" />
    <OBox p={[0, h / 2, 0.03]} s={[w + 0.2, 0.14, 0.1]} c="#2a1d2e" />
    <OBox p={[0, -h / 2, 0.06]} s={[w + 0.3, 0.12, 0.25]} c="#2a1d2e" />
  </group>
);

export const ToonRack: React.FC<{ p: V3; rotY?: number; colors: string[] }> = ({ p, rotY = 0, colors }) => (
  <group position={p} rotation={[0, rotY, 0]}>
    <OBox p={[0, 1.5, 0]} s={[2.4, 0.05, 0.05]} c="#b9a27a" rough={0.4} ink={0.015} />
    <OBox p={[-1.2, 0.75, 0]} s={[0.06, 1.5, 0.06]} c="#b9a27a" rough={0.4} ink={0.015} />
    <OBox p={[1.2, 0.75, 0]} s={[0.06, 1.5, 0.06]} c="#b9a27a" rough={0.4} ink={0.015} />
    {colors.map((c, i) => (
      <OBox key={i} p={[-1 + i * (2 / Math.max(1, colors.length - 1)), 1.04, 0]} s={[0.13, 0.86, 0.52]} c={c} rot={[0, 0, (i % 2 ? 1 : -1) * 0.03]} />
    ))}
  </group>
);

export const Shelf: React.FC<{ p: V3; rotY?: number; seed?: number }> = ({ p, rotY = 0, seed = 1 }) => {
  const r = rng(seed * 97 + 3);
  const cols = ["#d9534f", "#f0ad4e", "#5bc0de", "#9b59b6", "#5cb85c", "#e8e0c8"];
  return (
    <group position={p} rotation={[0, rotY, 0]}>
      <OBox p={[0, 1.1, -0.2]} s={[2.2, 2.2, 0.08]} c="#4a2a1c" />
      {[0.25, 0.95, 1.65].map((y) => <OBox key={y} p={[0, y, 0]} s={[2.2, 0.06, 0.45]} c="#6b3e28" />)}
      {[0.25, 0.95, 1.65].flatMap((y) => Array.from({ length: 5 }, (_, i) => {
        const h = 0.25 + r() * 0.3, w = 0.22 + r() * 0.12;
        return <OBox key={`${y}-${i}`} p={[-0.85 + i * 0.42, y + 0.03 + h / 2, 0]} s={[w, h, 0.3]} c={cols[Math.floor(r() * cols.length)]} ink={0.015} />;
      }))}
    </group>
  );
};

export const Poster: React.FC<{ p: V3; rotY?: number; title: string; sub: string; bg: string; fg: string; w?: number }> = ({ p, rotY = 0, title, sub, bg, fg, w = 0.8 }) => (
  <mesh position={p} rotation={[0, rotY, 0]}>
    <planeGeometry args={[w, w * 1.4]} />
    <meshStandardMaterial map={posterTex(`poster-${title}-${sub}`, title, sub, bg, fg)} roughness={0.9} />
  </mesh>
);
