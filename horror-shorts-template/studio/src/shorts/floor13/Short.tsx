// "The Thirteenth Floor" — full horror short, toon look with deep black shadows. ~41.7 s.
import React from "react";
import { AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { ThreeCanvas } from "@remotion/three";
import * as THREE from "three";
import { CharState, charTexture, propTexture } from "../../engine/draw";
import { CamKey, CamRig, Card, Picture, V3, camAt, flicker, handheld } from "../../engine/scene";
import { Glow, OBox, PaintedFloor, PaintedWall, WarmLamp } from "../../engine/toon";
import { Captions, Grain, Tint, Vignette, Word } from "../../engine/overlay";
import words from "../../../public/floor13/words.json";

export const FRAMES = 1250;
const IMPACT = 1201, BLACKOUT = 1215;
const INK = "#120c16";

// ---------- layout ----------
const GUEST_LOBBY_END: V3 = [-0.6, 0, -2.0];
const RECEP: V3 = [0.2, 0, -3.8];
const CAB_X = 40; // elevator cab + 13th floor hallway live far away from the lobby
const GUEST_CAB: V3 = [CAB_X, 0, -0.55];
const RECEP_BEHIND: V3 = [CAB_X + 0.42, 0, -0.18];
const RECEP_FAR: V3 = [CAB_X, 0, -20];
const PANEL: V3 = [CAB_X + 1.08, 1.3, -1.6];
const INDICATOR: V3 = [CAB_X, 2.5, -2.16];
// world height of a card's head centre: h * (1 - 0.29)
const headY = (h: number) => h * 0.71;
const RH = 2.0; // receptionist card height (tall, so her face clears the desk)

// ---------- shots: [start frame, set, camera keys] ----------
type SetId = "lobby" | "cab";
const S = (a: number, set: SetId, keys: CamKey[]) => ({ a, set, keys });
const k = (f: number, pos: V3, look: V3, fov = 45): CamKey => ({ f, pos, look, fov });
const C = CAB_X;
const SHOTS = [
  S(0, "lobby", [k(0, [1.2, 1.75, 8.0], [-0.1, 1.2, -3], 48), k(92, [0.9, 1.6, 6.0], [-0.1, 1.15, -3], 46)]),
  S(92, "lobby", [k(92, [-0.15, 1.55, 1.0], [-0.2, 1.2, -3], 46), k(196, [-0.15, 1.5, 0.55], [-0.2, 1.2, -3], 46)]),
  S(196, "lobby", [k(196, [0.25, 1.26, -2.15], [0.2, headY(RH), -3.8], 32), k(262, [0.22, 1.25, -2.4], [0.2, headY(RH), -3.8], 32)]),
  S(262, "cab", [k(262, [C + 0.3, 1.42, -1.6], [PANEL[0], 1.42, PANEL[2]], 40), k(380, [C + 0.5, 1.45, -1.6], [PANEL[0], 1.45, PANEL[2]], 40)]),
  S(380, "lobby", [k(380, [0.2, 1.25, -2.7], [0.2, headY(RH), -3.8], 24), k(426, [0.2, 1.25, -2.95], [0.2, headY(RH), -3.8], 24)]),
  S(426, "lobby", [k(426, [-0.35, 1.3, 0.4], [-0.6, 1.15, -2.0], 36), k(458, [-0.4, 1.3, 0.1], [-0.6, 1.15, -2.0], 36)]),
  S(458, "cab", [k(458, [C + 0.3, 1.45, -2.0], [C, 1.15, -0.5], 52), k(526, [C + 0.2, 1.42, -1.75], [C, 1.15, -0.5], 50)]),
  S(526, "cab", [k(526, [C + 0.5, 1.37, -1.6], [PANEL[0], 1.37, PANEL[2]], 34), k(568, [C + 0.58, 1.37, -1.6], [PANEL[0], 1.37, PANEL[2]], 34)]),
  S(568, "cab", [k(568, [C, 2.15, -1.3], [C, 2.5, -2.2], 30), k(638, [C, 2.2, -1.5], [C, 2.5, -2.2], 30)]),
  S(638, "cab", [k(638, [C, 2.2, -1.5], [C, 2.5, -2.2], 30), k(716, [C, 2.25, -1.62], [C, 2.5, -2.2], 30)]),
  S(716, "cab", [k(716, [C, 1.5, -0.25], [C, 1.4, -6], 50), k(762, [C, 1.5, -0.6], [C, 1.4, -6], 50)]),
  S(762, "cab", [k(762, [C, 1.55, -1.6], [C, 1.3, -15], 55), k(846, [C, 1.5, -3.4], [C, 1.3, -15], 52)]),
  S(846, "cab", [k(846, [C, 1.5, -2.0], [C, 1.15, -20], 16), k(942, [C, 1.48, -2.0], [C, 1.2, -20], 12)]),
  S(942, "cab", [k(942, [C, 1.45, -2.0], [C, headY(RH), -20], 6), k(982, [C, 1.45, -2.0], [C, headY(RH), -20], 4.5)]),
  S(982, "cab", [k(982, [C + 0.4, 1.45, -1.6], [PANEL[0], 1.45, PANEL[2]], 40), k(1030, [C + 0.48, 1.45, -1.6], [PANEL[0], 1.45, PANEL[2]], 40)]),
  S(1030, "cab", [k(1030, [C, 1.3, -1.7], [C, headY(1.8), -0.55], 34), k(1062, [C, 1.3, -1.6], [C, headY(1.8), -0.55], 34)]),
  S(1062, "cab", [k(1062, [C, 1.3, -1.6], [C, headY(1.8), -0.55], 32), k(1110, [C, 1.3, -1.45], [C, headY(1.8), -0.55], 30)]),
  S(1110, "cab", [k(1110, [C - 0.05, 1.32, -1.75], [C + 0.15, 1.25, -0.4], 38), k(1182, [C - 0.05, 1.32, -1.5], [C + 0.2, 1.25, -0.4], 36)]),
  S(1182, "cab", [k(1182, [C - 0.05, 1.32, -1.5], [C + 0.2, 1.25, -0.4], 36), k(1199, [C - 0.03, 1.32, -1.45], [C + 0.22, 1.25, -0.4], 36),
    k(1204, [C + 0.3, 1.26, -0.95], [RECEP_BEHIND[0], headY(RH), RECEP_BEHIND[2]], 30), k(1250, [C + 0.31, 1.26, -0.98], [RECEP_BEHIND[0], headY(RH), RECEP_BEHIND[2]], 30)]),
];

// ---------- timeline helpers ----------
const blink = (f: number, ks: number[]) => {
  for (const b of ks) { const d = f - b; if (d >= 0 && d < 5) return [0.4, 0.05, 0.05, 0.4, 0.9][d]; }
  return 1;
};
const guestState = (f: number): CharState => {
  const lid = blink(f, [60, 300, 470, 1040, 1150]);
  if (f < 426) return { kind: "guest", expr: "calm", lid };
  if (f < 458) return { kind: "guest", expr: "smile", lid: 1 };
  if (f < 1040) return { kind: "guest", expr: f < 600 ? "calm" : "uneasy", lid };
  if (f < 1066) return { kind: "guest", expr: "scared", lid };
  return { kind: "guest", expr: "terror", lid };
};
const recepState = (f: number, set: SetId): CharState => {
  if (set === "cab") return { kind: "receptionist", expr: "creepy", pose: f < 1000 ? (Math.floor(f / 7) % 2 ? "wave1" : "wave2") : "stand" };
  if (f >= 405 && f < 409) return { kind: "receptionist", expr: "creepy" }; // a 4-frame flash of her true face
  return { kind: "receptionist", expr: f >= 196 ? "serious" : "polite", lid: blink(f, [150, 230]) };
};
const floorAt = (f: number) => (f < 575 ? 1 : f < 590 ? 7 : f < 600 ? 8 : f < 641 ? 9 : f < 654 ? 10 : f < 674 ? 11 : f < 699 ? 12 : 13);
const cabLight = (f: number) => {
  if (f >= 1062) return flicker(f, 1062, 1080, 0.18) * (f >= 1190 ? 0.4 : 1);
  return flicker(f, 699, 716, 1);
};
const doorsOpen = (f: number) => (f < 722 ? 0 : f < 752 ? (f - 722) / 30 : 1);

// ---------- textures ----------
const brassPanel = (lit: number | null, red13: boolean) => propTexture(`panel-${lit}-${red13}`, 400, 800, (c) => {
  c.fillStyle = "#b08a3c"; c.fillRect(0, 0, 400, 800);
  const g = c.createLinearGradient(0, 0, 400, 0); g.addColorStop(0, "rgba(255,240,190,0.35)"); g.addColorStop(0.5, "rgba(0,0,0,0)"); g.addColorStop(1, "rgba(60,30,0,0.3)");
  c.fillStyle = g; c.fillRect(0, 0, 400, 800);
  c.strokeStyle = INK; c.lineWidth = 14; c.strokeRect(7, 7, 386, 786);
  // blank plate where 13 would be
  c.fillStyle = red13 ? "#4a0606" : "#7a5e28"; c.beginPath(); c.arc(200, 110, 50, 0, Math.PI * 2); c.fill(); c.lineWidth = 8; c.stroke();
  if (red13) { c.fillStyle = "#ff2a1a"; c.font = "bold 52px Georgia, serif"; c.textAlign = "center"; c.fillText("13", 200, 128); }
  for (let n = 1; n <= 12; n++) {
    const row = Math.floor((12 - n) / 2), col = (n - 1) % 2;
    const x = 120 + col * 160, y = 230 + row * 95;
    c.fillStyle = lit === n ? "#ffd86a" : "#efe6cf"; c.beginPath(); c.arc(x, y, 36, 0, Math.PI * 2); c.fill();
    c.lineWidth = 7; c.strokeStyle = INK; c.stroke();
    c.fillStyle = INK; c.font = "bold 36px Georgia, serif"; c.textAlign = "center"; c.fillText(String(n), x, y + 12);
  }
});
export const buttonPos = (n: number): [number, number] => { // panel-local metres (panel plane 0.36 x 0.72)
  const row = Math.floor((12 - n) / 2), col = (n - 1) % 2;
  return [((120 + col * 160) / 400 - 0.5) * 0.36, (0.5 - (230 + row * 95) / 800) * 0.72];
};
const indicatorTex = (n: number) => propTexture(`ind-${n}`, 400, 200, (c) => {
  c.fillStyle = "#0a0606"; c.fillRect(0, 0, 400, 200);
  c.fillStyle = n === 13 ? "#ff2a1a" : "#ffb53a"; c.font = "bold 150px monospace"; c.textAlign = "center"; c.fillText(String(n), 200, 160);
  c.strokeStyle = "#b08a3c"; c.lineWidth = 16; c.strokeRect(8, 8, 384, 184);
});
const clockTex = () => propTexture("wallclock", 300, 300, (c) => {
  c.fillStyle = "#f3ead4"; c.beginPath(); c.arc(150, 150, 140, 0, Math.PI * 2); c.fill();
  c.strokeStyle = "#5a3a1a"; c.lineWidth = 16; c.stroke();
  c.fillStyle = INK; c.font = "bold 34px Georgia, serif"; c.textAlign = "center";
  for (let h = 1; h <= 12; h++) { const a = (h / 12) * Math.PI * 2 - Math.PI / 2; c.fillText(String(h), 150 + Math.cos(a) * 105, 162 + Math.sin(a) * 105); }
  c.lineCap = "round"; c.strokeStyle = INK; c.lineWidth = 10; c.beginPath(); c.moveTo(150, 150); c.lineTo(150, 70); c.stroke();
  c.lineWidth = 7; c.beginPath(); c.moveTo(150, 150); c.lineTo(150, 40); c.stroke();
});
const cabWoodTex = () => propTexture("cabwood", 512, 512, (c) => {
  c.fillStyle = "#5a2e1c"; c.fillRect(0, 0, 512, 512);
  for (let x = 0; x < 512; x += 128) { c.fillStyle = x % 256 ? "#64341f" : "#552b19"; c.fillRect(x + 8, 20, 112, 472); c.strokeStyle = INK; c.lineWidth = 6; c.strokeRect(x + 8, 20, 112, 472); }
  c.strokeStyle = "rgba(30,10,4,0.35)"; c.lineWidth = 3;
  for (let i = 0; i < 60; i++) { const x = (i * 97) % 512; c.beginPath(); c.moveTo(x, 20); c.bezierCurveTo(x + 6, 200, x - 6, 330, x + 3, 492); c.stroke(); }
});
const redPaperTex = () => propTexture("redpaper", 512, 1024, (c) => {
  c.fillStyle = "#5a1420"; c.fillRect(0, 0, 512, 1024);
  c.fillStyle = "rgba(255,160,120,0.12)";
  for (let y = 30; y < 760; y += 110) for (let x = 0; x < 512; x += 128) { c.beginPath(); c.ellipse(x + 64, y + 40, 22, 40, 0, 0, Math.PI * 2); c.fill(); }
  c.fillStyle = "#2a0e12"; c.fillRect(0, 780, 512, 244);
  c.strokeStyle = INK; c.lineWidth = 8; c.beginPath(); c.moveTo(0, 780); c.lineTo(512, 780); c.stroke();
});
const runnerTex = () => propTexture("runner", 256, 1024, (c) => {
  c.fillStyle = "#3a0c14"; c.fillRect(0, 0, 256, 1024);
  c.strokeStyle = "#c79a3a"; c.lineWidth = 10; c.strokeRect(14, -10, 228, 1044);
  c.fillStyle = "rgba(199,154,58,0.35)";
  for (let y = 40; y < 1024; y += 120) { c.beginPath(); c.moveTo(128, y); c.lineTo(168, y + 40); c.lineTo(128, y + 80); c.lineTo(88, y + 40); c.closePath(); c.fill(); }
});

// ---------- sets ----------
const Lobby: React.FC<{ keyX: number }> = ({ keyX }) => (
  <group>
    <PaintedFloor w={12} d={16} z={-1} />
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[-0.3, 0.01, -0.5]} receiveShadow>
      <planeGeometry args={[3, 6]} /><meshStandardMaterial map={runnerTex()} roughness={0.95} />
    </mesh>
    <mesh rotation={[Math.PI / 2, 0, 0]} position={[0, 4, -1]}><planeGeometry args={[12, 16]} /><meshStandardMaterial color="#1e1428" /></mesh>
    <PaintedWall p={[0, 2, -8]} w={12} h={4} />
    <PaintedWall p={[-6, 2, -1]} w={16} h={4} rotY={Math.PI / 2} />
    <PaintedWall p={[6, 2, -1]} w={16} h={4} rotY={-Math.PI / 2} />
    {/* reception desk + bell + key */}
    <OBox p={[0, 0.55, -3]} s={[3.2, 1.1, 0.9]} c="#6b3420" />
    <OBox p={[0, 1.13, -3]} s={[3.4, 0.08, 1.05]} c="#3a1a10" />
    <mesh position={[0.9, 1.22, -2.85]} castShadow><sphereGeometry args={[0.09, 16, 10, 0, Math.PI * 2, 0, Math.PI / 2]} /><meshStandardMaterial color="#d9b04a" metalness={0.6} roughness={0.3} /></mesh>
    <group position={[keyX, 1.19, -2.75]}>
      <OBox p={[0, 0, 0]} s={[0.18, 0.02, 0.05]} c="#d9b04a" ink={0.008} />
      <OBox p={[0.13, 0, 0]} s={[0.12, 0.015, 0.16]} c="#c0392b" ink={0.008} />
    </group>
    {/* key board on the back wall */}
    <OBox p={[0, 2.3, -7.9]} s={[2.6, 1.3, 0.08]} c="#4a2414" />
    {Array.from({ length: 12 }, (_, i) => <OBox key={i} p={[-1.0 + (i % 6) * 0.4, 2.6 - Math.floor(i / 6) * 0.55, -7.82]} s={[0.07, 0.2, 0.03]} c={i === 8 ? "#4a2414" : "#d9b04a"} ink={0.01} />)}
    <Picture tex={clockTex()} p={[-3.2, 2.9, -7.94]} w={0.9} h={0.9} />
    {/* elevator doors on the right wall + plants */}
    <OBox p={[5.95, 1.3, -3]} s={[0.1, 2.6, 2.0]} c="#b08a3c" rough={0.35} />
    <OBox p={[5.9, 1.3, -3]} s={[0.04, 2.6, 0.03]} c={INK} ink={0} />
    {[[-4.8, -6.6], [4.6, -6.6]].map(([x, z], i) => (
      <group key={i} position={[x, 0, z]}>
        <OBox p={[0, 0.3, 0]} s={[0.5, 0.6, 0.5]} c="#7a3b26" />
        {[[0, 1.0, 0, 0.45], [0.2, 1.3, 0.05, 0.32], [-0.18, 1.25, -0.05, 0.34]].map(([a, b, cc, r], j) => (
          <mesh key={j} position={[a, b, cc]} castShadow><icosahedronGeometry args={[r, 1]} /><meshStandardMaterial color="#2f7a3a" flatShading roughness={0.9} /></mesh>
        ))}
      </group>
    ))}
    {[[-3, -1], [3, -1], [-3, -5], [3, -5]].map(([x, z], i) => <WarmLamp key={i} pos={[x, 3.3, z]} on={0.9} />)}
    <directionalLight position={[4, 7, 4]} intensity={1.3} color="#ffd9a8" castShadow shadow-mapSize-width={2048} shadow-mapSize-height={2048}
      shadow-camera-left={-8} shadow-camera-right={8} shadow-camera-top={8} shadow-camera-bottom={-8} shadow-bias={-0.0005} />
  </group>
);

const Cab: React.FC<{ f: number; light: number; open: number }> = ({ f, light, open }) => {
  const wood = cabWoodTex();
  const n = floorAt(f);
  const lit = f >= 541 && f < 700 ? 9 : null;
  return (
    <group>
      {/* cab box: x C-1.1..C+1.1, z 0..-2.2, h 2.7 */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[C, 0.005, -1.1]} receiveShadow><planeGeometry args={[2.2, 2.2]} /><meshStandardMaterial color="#2a1a14" roughness={0.6} /></mesh>
      <OBox p={[C, 2.72, -1.1]} s={[2.2, 0.06, 2.2]} c="#2a1a14" />
      <mesh position={[C, 2.68, -1.1]} rotation={[Math.PI / 2, 0, 0]}><planeGeometry args={[1.2, 1.2]} /><meshStandardMaterial color="#332a1a" emissive="#ffe0a0" emissiveIntensity={0.2 + 1.8 * light} /></mesh>
      <pointLight position={[C, 2.4, -1.1]} color="#ffd59a" intensity={5 * light} distance={6} decay={1.6} />
      {[[C, 1.36, 0.0, 0], [C - 1.1, 1.36, -1.1, Math.PI / 2], [C + 1.1, 1.36, -1.1, -Math.PI / 2]].map(([x, y, z, r], i) => (
        <mesh key={i} position={[x, y, z]} rotation={[0, r, 0]} receiveShadow><planeGeometry args={[2.2, 2.72]} /><meshStandardMaterial map={wood} roughness={0.7} /></mesh>
      ))}
      <OBox p={[C, 0.95, -0.04]} s={[2.0, 0.05, 0.05]} c="#c9a24a" rough={0.3} ink={0.012} />
      <Picture tex={brassPanel(lit, f >= 982)} p={[PANEL[0] - 0.015, PANEL[1], PANEL[2]]} w={0.36} h={0.72} rot={[0, -Math.PI / 2, 0]} glow={0.1} />
      {f >= 982 && <Glow p={[PANEL[0] - 0.06, PANEL[1] + 0.26, PANEL[2]]} size={0.35} color="#ff2a1a" strength={0.7} />}
      {/* front wall with the door opening + indicator */}
      <OBox p={[C - 0.85, 1.36, -2.2]} s={[0.5, 2.72, 0.08]} c="#3a2016" />
      <OBox p={[C + 0.85, 1.36, -2.2]} s={[0.5, 2.72, 0.08]} c="#3a2016" />
      <OBox p={[C, 2.5, -2.2]} s={[1.2, 0.44, 0.08]} c="#3a2016" />
      <Picture tex={indicatorTex(n)} p={[INDICATOR[0], INDICATOR[1], INDICATOR[2] + 0.02]} w={0.5} h={0.25} rot={[0, 0, 0]} glow={0.9} />
      <Glow p={[INDICATOR[0], INDICATOR[1], INDICATOR[2] + 0.1]} size={0.9} color={n === 13 ? "#ff2a1a" : "#ffb53a"} strength={0.5} />
      {/* sliding doors */}
      <OBox p={[C - 0.3 - open * 0.6, 1.14, -2.25]} s={[0.6, 2.28, 0.04]} c="#b08a3c" rough={0.35} ink={0.012} />
      <OBox p={[C + 0.3 + open * 0.6, 1.14, -2.25]} s={[0.6, 2.28, 0.04]} c="#b08a3c" rough={0.35} ink={0.012} />
    </group>
  );
};

const Hallway: React.FC<{ f: number }> = ({ f }) => {
  const paper = redPaperTex().clone();
  paper.wrapS = THREE.RepeatWrapping; paper.repeat.set(9, 1); paper.needsUpdate = true;
  const sconce = flicker(f, 0, 1e9, 1) * 0.6 + 0.4;
  return (
    <group>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[C, 0, -12]} receiveShadow><planeGeometry args={[2.6, 20]} /><meshStandardMaterial color="#1e0a0e" /></mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[C, 0.01, -12]}><planeGeometry args={[1.4, 20]} /><meshStandardMaterial map={runnerTex()} roughness={0.95} /></mesh>
      <mesh rotation={[Math.PI / 2, 0, 0]} position={[C, 3, -12]}><planeGeometry args={[2.6, 20]} /><meshStandardMaterial color="#12080c" /></mesh>
      {[-1, 1].map((s) => (
        <mesh key={s} position={[C + s * 1.3, 1.5, -12]} rotation={[0, -s * Math.PI / 2, 0]} receiveShadow>
          <planeGeometry args={[20, 3]} /><meshStandardMaterial map={paper} roughness={0.95} />
        </mesh>
      ))}
      <mesh position={[C, 1.5, -21.9]}><planeGeometry args={[2.6, 3]} /><meshStandardMaterial color="#1a0a10" /></mesh>
      {/* open doors: dark openings, frames, leaves swung inward */}
      {Array.from({ length: 7 }, (_, i) => -4 - i * 2.5).flatMap((z) => [-1, 1].map((s) => (
        <group key={`${z}${s}`} position={[C + s * 1.29, 0, z]} rotation={[0, -s * Math.PI / 2, 0]}>
          <mesh position={[0, 1.05, 0.005]}><planeGeometry args={[0.9, 2.1]} /><meshBasicMaterial color="#030203" /></mesh>
          <OBox p={[-0.5, 1.1, 0.03]} s={[0.1, 2.2, 0.06]} c="#2a120c" ink={0.012} />
          <OBox p={[0.5, 1.1, 0.03]} s={[0.1, 2.2, 0.06]} c="#2a120c" ink={0.012} />
          <OBox p={[0, 2.2, 0.03]} s={[1.1, 0.12, 0.06]} c="#2a120c" ink={0.012} />
          <OBox p={[-0.45 + 0.42 * Math.cos(1.2), 1.05, -0.42 * Math.sin(1.2)]} s={[0.86, 2.06, 0.05]} rot={[0, 1.2, 0]} c="#3a1a10" ink={0.012} />
        </group>
      )))}
      {[-5, -10, -15, -20].map((z, i) => (
        <group key={z}>
          <OBox p={[C - 1.25, 2.1, z]} s={[0.08, 0.25, 0.16]} c="#c9a24a" ink={0.01} />
          <Glow p={[C - 1.15, 2.2, z]} size={0.7} color="#ff5a2a" strength={sconce * (i === 3 ? 1.2 : 0.8)} />
          <pointLight position={[C - 0.9, 2.2, z]} color="#ff4a20" intensity={6 * sconce} distance={7} decay={1.6} />
        </group>
      ))}
      <pointLight position={[C, 1.9, -18.4]} color="#9fe8c0" intensity={4} distance={5} decay={1.5} />
    </group>
  );
};

export const Short: React.FC = () => {
  const f = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  let si = 0;
  for (let i = 0; i < SHOTS.length; i++) if (f >= SHOTS[i].a) si = i;
  const shot = SHOTS[si];
  const cam = camAt(f, shot.keys);
  const shake = f >= IMPACT && f < IMPACT + 16 ? 0.035 * (1 - (f - IMPACT) / 16) : f >= 699 && f < 716 ? 0.012 : 0;
  const hh = handheld(f, cam.fov < 10 ? 0.0015 : 0.01, shake);
  const pos: V3 = [cam.pos[0] + hh[0], cam.pos[1] + hh[1], cam.pos[2]];

  const walk = Math.min(1, f / 92);
  const guestLobby: V3 = si === 0 ? [0.4 - 1.0 * walk, 0, 4.5 - 6.5 * walk] : GUEST_LOBBY_END;
  const keyX = f < 110 ? 0.25 : f < 140 ? 0.25 - 0.75 * ((f - 110) / 30) : -0.5;
  const light = cabLight(f);
  const open = doorsOpen(f);

  // hand pressing button 9 (shots 8 and 15)
  const press = (t0: number) => { const d = f - t0; return d < -12 ? 0 : d < 0 ? (d + 12) / 12 : d < 6 ? 1 : d < 16 ? 1 - (d - 6) / 10 : 0; };
  const pressAmt = si === 7 ? press(541) : si === 14 ? Math.max(press(1000), press(1018)) : 0;
  const [bx, by] = buttonPos(9);

  const showRecepBehind = si >= 15 && f >= 1110;
  const recepGlow = f < 1110 ? 0 : f < 1199 ? 0.05 + 0.2 * ((f - 1110) / 89) : 0.45;
  const impactTint = f >= IMPACT && f < IMPACT + 6 ? 0.6 * (1 - (f - IMPACT) / 6) : 0;

  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <ThreeCanvas width={width} height={height} shadows gl={{ antialias: true, preserveDrawingBuffer: true }}
        style={{ filter: "saturate(1.2) contrast(1.16) brightness(0.96)" }}>
        <color attach="background" args={["#0b0812"]} />
        <fog attach="fog" args={[shot.set === "lobby" ? "#1a1230" : "#160812", 8, 34]} />
        <CamRig pos={pos} look={cam.look} fov={cam.fov} roll={si === 9 ? Math.sin(f * 0.2) * 0.02 : 0} />
        <hemisphereLight args={["#6a58c8", "#140a18", shot.set === "lobby" ? 0.9 : 0.75]} />
        {shot.set === "lobby" && (
          <>
            <Lobby keyX={keyX} />
            <Card s={guestState(f)} pos={guestLobby} h={1.8} cam={pos} glow={0.3} bob={si === 0 ? Math.abs(Math.sin(f * 0.25)) * 0.03 : 0} />
            <Card s={recepState(f, "lobby")} pos={RECEP} h={RH} cam={pos} glow={0.25} />
          </>
        )}
        {shot.set === "cab" && (
          <>
            <Cab f={f} light={light} open={open} />
            {open > 0 && <Hallway f={f} />}
            {open > 0 && f < 1000 && <Card s={recepState(f, "cab")} pos={RECEP_FAR} h={RH} cam={pos} glow={0.35} />}
            {[6, 15, 16, 17, 18].includes(si) && <Card s={guestState(f)} pos={GUEST_CAB} h={1.8} cam={pos} glow={0.3} />}
            {showRecepBehind && <Card s={{ kind: "receptionist", expr: "creepy" }} pos={RECEP_BEHIND} h={RH} cam={pos} glow={recepGlow} />}
            {pressAmt > 0 && (
              <Picture tex={handPicture()} p={[PANEL[0] - 0.03 - 0.25 * (1 - pressAmt), PANEL[1] + by - 0.1 - 0.05 * (1 - pressAmt), PANEL[2] + bx + 0.025]}
                w={0.18} h={0.27} rot={[0, -Math.PI / 2, 0]} />
            )}
            <directionalLight position={[C + 3, 6, 3]} intensity={0.5 * light + 0.1} color="#ffd9a8" castShadow shadow-mapSize-width={1024} shadow-mapSize-height={1024}
              shadow-camera-left={-4} shadow-camera-right={4} shadow-camera-top={4} shadow-camera-bottom={-4} shadow-bias={-0.0005} />
          </>
        )}
      </ThreeCanvas>
      <Vignette strength={0.78} />
      <Tint color="#b00000" opacity={impactTint} />
      <Tint color="#ff1a1a" opacity={f >= 699 && f < 716 ? 0.12 * flicker(f, 699, 716, 1) : 0} />
      <Grain f={f} amount={0.13} />
      <Tint color="#000" opacity={f >= BLACKOUT ? 1 : 0} />
      <Captions words={words as Word[]} f={f} fps={fps} hidden={f >= BLACKOUT}
        style={{ y: 0.77, size: 140, emph: ["TWELVE", "THIRTEEN", "WARNING", "BACK", "NINE"], emphColor: "#ff2b2b" }} />
      <Audio src={staticFile("floor13/mix.wav")} />
    </AbsoluteFill>
  );
};

// the pointing hand is drawn by the character painter (kind "hand")
const handPicture = () => charTexture({ kind: "hand" });
