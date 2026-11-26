// "Eleven Mannequins" — demo horror short (second person, twist ending). 21 s.
import React from "react";
import { AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { propTexture, Expr } from "../../engine/draw";
import { Box, CamKey, CamRig, Card, Floor, Flashlight, MoonWindow, Picture, Rack, TubeLamp, V3, Wall, camAt, flicker, handheld } from "../../engine/scene";
import { Captions, Grain, Tint, Vignette, Word } from "../../engine/overlay";
import words from "../../../public/mannequins/words.json";

export const FRAMES = 630;

// ---------- story beats (frames @30 fps, aligned to words.json) ----------
const SHOTS: { a: number; keys: CamKey[] }[] = [
  { a: 0, keys: [{ f: 0, pos: [-0.7, 1.65, 8.0], look: [-0.5, 1.15, -3], fov: 48 }, { f: 96, pos: [-0.5, 1.6, 6.6], look: [-0.45, 1.1, -3], fov: 46 }] },
  { a: 96, keys: [{ f: 96, pos: [2.78, 1.56, 1.05], look: [2.6, 1.4, 0], fov: 40 }, { f: 145, pos: [2.66, 1.45, 0.66], look: [2.6, 1.4, 0], fov: 40 }] },
  { a: 145, keys: [{ f: 145, pos: [-4.5, 1.6, -5.2], look: [-4, 1.2, -10.6], fov: 46 }, { f: 222, pos: [3.5, 1.55, -5.6], look: [4, 1.2, -10.6], fov: 46 }] },
  { a: 222, keys: [{ f: 222, pos: [-4, 3.0, -9.0], look: [-4, 3.3, -12], fov: 34 }, { f: 268, pos: [-4, 3.1, -10.0], look: [-4, 3.3, -12], fov: 34 }] },
  { a: 268, keys: [{ f: 268, pos: [0.6, 0.7, 5.5], look: [0, 2.6, -4], fov: 62 }, { f: 300, pos: [0.5, 0.75, 5.2], look: [0, 2.6, -4], fov: 60 }] },
  { a: 300, keys: [{ f: 300, pos: [0.35, 1.3, 4.3], look: [0, 1.15, 1.5], fov: 38 }, { f: 345, pos: [0.3, 1.3, 3.9], look: [0, 1.15, 1.5], fov: 38 }] },
  { a: 345, keys: [345, 351, 371, 377, 398, 404, 421, 427, 445].map((f, i) => ({ f, pos: [0, 1.6, 0.8] as V3, look: [[0, 3, 3, 4, 4, 5, 5, 6.2, 6.25][i], 1.3, -10.4] as V3, fov: 30 })) },
  { a: 445, keys: [{ f: 445, pos: [0, 1.32, 3.5], look: [0, 1.22, 1.5], fov: 34 }, { f: 525, pos: [0, 1.32, 2.85], look: [0, 1.24, 1.5], fov: 34 }] },
  { a: 525, keys: [{ f: 525, pos: [4.4, 1.6, -5.8], look: [6.2, 1.45, -10.2], fov: 40 }, { f: 574, pos: [5.0, 1.62, -7.2], look: [6.2, 1.45, -10.2], fov: 40 },
    { f: 578, pos: [5.6, 1.7, -8.3], look: [6.2, 1.62, -10.2], fov: 34 }, { f: 630, pos: [5.63, 1.7, -8.4], look: [6.2, 1.62, -10.2], fov: 34 }] },
];
const IMPACT = 576, BLACKOUT = 590;
const GUARD_POS: V3 = [0, 0, 1.5];
const TWELFTH: V3 = [6.2, 0, -10.2];

const guardExpr = (f: number): { expr: Expr; lid: number } => {
  const blink = (k: number) => { const d = f - k; return d >= 0 && d < 5 ? [0.4, 0.05, 0.05, 0.4, 0.9][d] : 1; };
  const lid = Math.min(blink(50), blink(320), blink(486));
  if (f < 268) return { expr: "calm", lid };
  if (f < 488) return { expr: "uneasy", lid };
  return { expr: "scared", lid };
};
const lampLevel = (f: number) => {
  if (f >= 565) return 0;
  let v = 0.45;
  v = flicker(f, 270, 300, v); v = flicker(f, 420, 432, v); v = flicker(f, 498, 510, v); v = flicker(f, 540, 548, v);
  return v;
};

// ---------- set ----------
const noteTex = () => propTexture("note", 640, 480, (c) => {
  c.fillStyle = "#e9dfc4"; c.fillRect(0, 0, 640, 480);
  c.fillStyle = "rgba(255,240,170,0.6)"; c.fillRect(250, -10, 140, 50);
  c.fillStyle = "#1b1a24"; c.textAlign = "center";
  c.font = "bold 58px Georgia, serif"; c.fillText("ONE RULE:", 320, 140);
  c.font = "italic bold 46px Georgia, serif";
  c.fillText("Every mannequin", 320, 230); c.fillText("must face", 320, 295); c.fillText("THE WALL.", 320, 360);
  c.fillStyle = "#8a1010"; c.font = "bold 40px Georgia, serif"; c.fillText("Always.", 320, 430);
});
const clockTex = () => propTexture("clock", 512, 220, (c) => {
  c.fillStyle = "#050505"; c.fillRect(0, 0, 512, 220);
  c.fillStyle = "#ff2a1a"; c.textAlign = "center"; c.font = "bold 150px monospace"; c.fillText("3:00", 230, 165);
  c.font = "bold 50px monospace"; c.fillText("AM", 445, 165);
});
const exitTex = () => propTexture("exit", 256, 110, (c) => {
  c.fillStyle = "#06240f"; c.fillRect(0, 0, 256, 110);
  c.fillStyle = "#3dff7a"; c.textAlign = "center"; c.font = "bold 76px sans-serif"; c.fillText("EXIT", 128, 82);
});

const Store: React.FC<{ lamps: number }> = ({ lamps }) => (
  <group>
    <Floor w={14} d={24} z={-1} />
    <mesh rotation={[Math.PI / 2, 0, 0]} position={[0, 4.5, -1]}><planeGeometry args={[14, 24]} /><meshStandardMaterial color="#121318" /></mesh>
    <Wall p={[0, 2.25, -12]} w={14} h={4.5} />
    <Wall p={[-7, 2.25, -1]} w={24} h={4.5} rotY={Math.PI / 2} />
    <Wall p={[7, 2.25, -1]} w={24} h={4.5} rotY={-Math.PI / 2} />
    {[-8, -3, 2].map((z) => <MoonWindow key={z} p={[-6.98, 2.3, z]} rotY={Math.PI / 2} />)}
    {[-9, -4, 1].flatMap((z) => [-3, 3].map((x) => <TubeLamp key={`${x}${z}`} pos={[x, 4.42, z]} on={lamps} />))}
    <Rack p={[-4.8, 0, -4]} rotY={Math.PI / 2} colors={["#5a2430", "#2f3d2a", "#3c3a52", "#6b5a3a", "#2a2a2e", "#5a2430"]} />
    <Rack p={[-4.8, 0, 0.5]} rotY={Math.PI / 2} colors={["#2f3d2a", "#4b2f45", "#2a2a2e", "#36506b", "#5a4a30"]} />
    <Rack p={[4.6, 0, -4.5]} rotY={-Math.PI / 2} colors={["#3c3a52", "#5a2430", "#2a2a2e", "#4b5a3a", "#3c3a52"]} />
    <Box p={[-3.6, 0.5, 2.6]} s={[2.0, 1, 0.8]} c="#2a1f1a" />
    <Box p={[2.6, 2.25, -0.3]} s={[0.6, 4.5, 0.5]} c="#2b2731" />
    <Picture tex={noteTex()} p={[2.6, 1.5, -0.04]} w={0.5} h={0.375} />
    <Box p={[-4, 3.3, -11.97]} s={[1.3, 0.6, 0.04]} c="#050505" shadow={false} />
    <Picture tex={clockTex()} p={[-4, 3.3, -11.94]} w={1.2} h={0.52} glow={0.55} />
    <pointLight position={[-4, 3.2, -11.3]} color="#ff2a1a" intensity={1.5} distance={3} />
    <Picture tex={exitTex()} p={[4, 3.7, -11.96]} w={0.7} h={0.3} glow={1.6} />
    <pointLight position={[4, 3.5, -11.4]} color="#3dff7a" intensity={1.2} distance={4} />
  </group>
);

export const Short: React.FC = () => {
  const f = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  let si = 0;
  for (let i = 0; i < SHOTS.length; i++) if (f >= SHOTS[i].a) si = i;
  const cam = camAt(f, SHOTS[si].keys);
  const shake = f >= IMPACT && f < IMPACT + 16 ? 0.05 * (1 - (f - IMPACT) / 16) : 0;
  const hh = handheld(f, si === 6 ? 0.006 : 0.012, shake);
  const pos: V3 = [cam.pos[0] + hh[0], cam.pos[1] + hh[1], cam.pos[2]];
  const lamps = lampLevel(f);

  // guard: walks in during shot 1, then stands at GUARD_POS
  const walk = Math.min(1, f / 96);
  const gpos: V3 = si === 0 ? [-1.2 + 0.9 * walk, 0, 3.4 - 1.8 * walk] : GUARD_POS;
  const ge = guardExpr(f);
  const showGuard = [0, 4, 5, 7].includes(si);

  // flashlight: from the guard in shot 1, from "your" hand (camera) elsewhere
  const tremble = (k: number) => Math.sin(f * 1.7 + k) * 0.03 + Math.sin(f * 0.37 + k) * 0.05;
  const handOff: V3 = [0.25, -0.35, 0.1];
  let spotPos: V3 = [pos[0] + handOff[0], pos[1] + handOff[1], pos[2] + handOff[2]];
  let spotTgt: V3 = [cam.look[0] + tremble(1), cam.look[1] + tremble(2), cam.look[2]];
  if (si === 0) { spotPos = [gpos[0] + 0.3, 1.05, gpos[2] + 0.1]; spotTgt = [gpos[0] + 1.2, 0.3, -6]; }
  if (si === 4 || si === 5 || si === 7) { spotPos = [GUARD_POS[0] + 0.35, 1.05, GUARD_POS[2] - 0.2]; spotTgt = [0.5, 0.5, -8]; }
  if (si === 3) { spotTgt = [-4, 1.6, -11]; }
  if (si === 1) { spotPos = [1.4, 1.9, 3.4]; spotTgt = [2.6 + tremble(3) * 0.3, 1.45, 0]; }
  const spotPower = (f >= 421 && f < 430) || (f >= 560 && f < 575) ? flicker(f, 0, 1e9, 1) * 0.8 + 0.2 : 1;

  // the twelfth mannequin turns between shots
  const twelfthFront = f >= 525;
  const creepy = f < 525 ? 0 : f < 575 ? 0.15 + 0.3 * ((f - 525) / 50) : 1;
  const tilt = f < 576 ? 0 : -0.3;

  const impactTint = f >= IMPACT && f < IMPACT + 6 ? 0.55 * (1 - (f - IMPACT) / 6) : 0;
  const black = f >= BLACKOUT ? 1 : 0;

  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <ThreeCanvas width={width} height={height} shadows gl={{ antialias: true, preserveDrawingBuffer: true }}>
        <color attach="background" args={["#040509"]} />
        <fog attach="fog" args={["#05060b", 7, 26]} />
        <CamRig pos={pos} look={cam.look} fov={cam.fov} roll={si === 8 && f >= IMPACT ? 0.05 : 0} />
        <hemisphereLight args={["#2b3a66", "#0a0a0e", 0.5]} />
        <directionalLight position={[-10, 6, -2]} color="#6b8cff" intensity={0.55} />
        <Flashlight pos={spotPos} target={spotTgt} power={spotPower} />
        <Store lamps={lamps} />
        {Array.from({ length: 11 }, (_, i) => (
          <Card key={i} s={{ kind: "mannequin", view: "back" }} pos={[-5 + i * 1.0, 0, -10.6]} h={1.85} cam={pos} />
        ))}
        <Card s={{ kind: "mannequin", view: twelfthFront ? "front" : "back", creepy: Math.round(creepy * 10) / 10 }} pos={TWELFTH} h={1.88} cam={pos} tilt={tilt} />
        {showGuard && <Card s={{ kind: "guard", expr: ge.expr, lid: ge.lid, look: si === 5 ? 0.6 : 0 }} pos={gpos} h={1.8} cam={pos} glow={0.32}
          bob={si === 0 ? Math.abs(Math.sin(f * 0.25)) * 0.035 : 0} />}
      </ThreeCanvas>
      <Vignette strength={0.8} />
      <Tint color="#b00000" opacity={impactTint} />
      <Grain f={f} amount={0.18} />
      <Tint color="#000" opacity={black} />
      <Captions words={words as Word[]} f={f} fps={fps} hidden={f >= BLACKOUT}
        style={{ y: 0.77, size: 140, emph: ["RULE", "WALL", "TWELVE", "ELEVEN", "3 A.M"], emphColor: "#ff2b2b" }} />
      <Audio src={staticFile("mannequins/mix.wav")} />
    </AbsoluteFill>
  );
};
