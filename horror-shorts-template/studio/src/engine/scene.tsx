// 3D building blocks: billboard character cards, camera rig, flashlight, flickering ceiling lamps, simple set pieces.
import React from "react";
import { useThree } from "@react-three/fiber";
import * as THREE from "three";
import { CharState, charTexture, propTexture } from "./draw";

export type V3 = [number, number, number];

// ---------- camera ----------
export type CamKey = { f: number; pos: V3; look: V3; fov?: number };
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const smooth = (t: number) => t * t * (3 - 2 * t);
/** Interpolate camera keys (smoothstep between neighbours); hold outside the range. */
export const camAt = (f: number, keys: CamKey[]): { pos: V3; look: V3; fov: number } => {
  if (f <= keys[0].f) return { pos: keys[0].pos, look: keys[0].look, fov: keys[0].fov ?? 45 };
  for (let i = 0; i < keys.length - 1; i++) {
    const a = keys[i], b = keys[i + 1];
    if (f <= b.f) {
      const t = smooth((f - a.f) / Math.max(1, b.f - a.f));
      return {
        pos: [0, 1, 2].map((k) => lerp(a.pos[k], b.pos[k], t)) as V3,
        look: [0, 1, 2].map((k) => lerp(a.look[k], b.look[k], t)) as V3,
        fov: lerp(a.fov ?? 45, b.fov ?? 45, t),
      };
    }
  }
  const z = keys[keys.length - 1];
  return { pos: z.pos, look: z.look, fov: z.fov ?? 45 };
};
/** Handheld drift + optional shake (amplitude in metres). */
export const handheld = (f: number, amp = 0.012, shake = 0): V3 => [
  Math.sin(f * 0.071) * amp + Math.sin(f * 2.9) * shake,
  Math.sin(f * 0.053 + 1.3) * amp * 0.7 + Math.cos(f * 2.3) * shake * 0.7,
  0,
];

export const CamRig: React.FC<{ pos: V3; look: V3; fov: number; roll?: number }> = ({ pos, look, fov, roll = 0 }) => {
  const cam = useThree().camera as THREE.PerspectiveCamera;
  cam.position.set(...pos);
  cam.fov = fov; cam.near = 0.05; cam.far = 120;
  cam.updateProjectionMatrix();
  cam.up.set(Math.sin(roll), Math.cos(roll), 0);
  cam.lookAt(...look);
  return null;
};

// ---------- character card ----------
/** A flat character standing at `pos` (feet), always turned to the camera (yaw only). */
/** `glow` keeps faces readable in the dark (a little self-light from the drawing itself). */
export const Card: React.FC<{ s: CharState; pos: V3; h: number; cam: V3; tilt?: number; bob?: number; glow?: number }> = ({ s, pos, h, cam, tilt = 0, bob = 0, glow = 0.12 }) => {
  const tex = charTexture(s);
  const w = h * 0.6;
  const yaw = Math.atan2(cam[0] - pos[0], cam[2] - pos[2]);
  return (
    <group position={[pos[0], pos[1] + bob, pos[2]]} rotation={[0, yaw, 0]}>
      <group position={[0, h * 0.62, 0]} rotation={[0, 0, tilt]}>
        <mesh position={[0, h * 0.5 - h * 0.62, 0]} castShadow>
          <planeGeometry args={[w, h]} />
          <meshStandardMaterial map={tex} emissiveMap={tex} emissive="#ffffff" emissiveIntensity={glow} alphaTest={0.5} side={THREE.DoubleSide} roughness={0.85} />
        </mesh>
      </group>
      {/* contact shadow */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.005, 0]}>
        <circleGeometry args={[w * 0.32, 24]} />
        <meshBasicMaterial color="#000" transparent opacity={0.45} depthWrite={false} />
      </mesh>
    </group>
  );
};

// ---------- lights ----------
/** Warm flashlight cone with soft edge; casts shadows. */
export const Flashlight: React.FC<{ pos: V3; target: V3; power?: number }> = ({ pos, target, power = 1 }) => {
  const [tgt] = React.useState(() => new THREE.Object3D());
  tgt.position.set(...target);
  tgt.updateMatrixWorld();
  return (
    <>
      <primitive object={tgt} />
      <spotLight position={pos} target={tgt} color="#ffe2b0" intensity={60 * power} distance={30} angle={0.36} penumbra={0.55} decay={1.6}
        castShadow shadow-mapSize-width={1024} shadow-mapSize-height={1024} shadow-bias={-0.0004} />
    </>
  );
};

/** Ceiling tube lamp: emissive box + point light, both scaled by `on` (0..1). */
export const TubeLamp: React.FC<{ pos: V3; on: number }> = ({ pos, on }) => (
  <group position={pos}>
    <mesh>
      <boxGeometry args={[1.6, 0.06, 0.3]} />
      <meshStandardMaterial color="#20242c" emissive="#dfe9ff" emissiveIntensity={0.15 + 2.2 * on} />
    </mesh>
    <pointLight position={[0, -0.3, 0]} color="#cfe0ff" intensity={6 * on} distance={9} decay={1.7} />
  </group>
);

/** Deterministic flicker: returns 0..1 light level for frame f inside [a,b). */
export const flicker = (f: number, a: number, b: number, base = 1) => {
  if (f < a || f >= b) return base;
  const h = Math.sin(f * 12.9898 + a * 78.233) * 43758.5453;
  const r = h - Math.floor(h);
  return r > 0.55 ? base : r > 0.3 ? base * 0.25 : 0;
};

// ---------- set pieces ----------
export const Box: React.FC<{ p: V3; s: V3; c: string; rough?: number; emissive?: string; ei?: number; rot?: V3; shadow?: boolean }> = ({ p, s, c, rough = 0.9, emissive, ei = 1, rot, shadow = true }) => (
  <mesh position={p} rotation={rot ?? [0, 0, 0]} castShadow={shadow} receiveShadow>
    <boxGeometry args={s} />
    <meshStandardMaterial color={c} roughness={rough} emissive={emissive ?? "#000"} emissiveIntensity={ei} />
  </mesh>
);

const tileTex = () => propTexture("tiles", 512, 512, (c) => {
  for (let y = 0; y < 4; y++) for (let x = 0; x < 4; x++) {
    c.fillStyle = (x + y) % 2 ? "#2a3036" : "#3b4248";
    c.fillRect(x * 128, y * 128, 128, 128);
  }
  c.strokeStyle = "#15191c"; c.lineWidth = 4;
  for (let i = 0; i <= 4; i++) { c.beginPath(); c.moveTo(i * 128, 0); c.lineTo(i * 128, 512); c.stroke(); c.beginPath(); c.moveTo(0, i * 128); c.lineTo(512, i * 128); c.stroke(); }
});
const wallTex = () => propTexture("wall", 512, 512, (c) => {
  c.fillStyle = "#3a3340"; c.fillRect(0, 0, 512, 512);
  for (let x = 0; x < 512; x += 64) { c.fillStyle = "#332c39"; c.fillRect(x, 0, 32, 512); }
  c.fillStyle = "#231e27"; c.fillRect(0, 440, 512, 72);
});

export const Floor: React.FC<{ w: number; d: number; z?: number }> = ({ w, d, z = 0 }) => {
  const t = tileTex();
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(w / 2.4, d / 2.4);
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, z]} receiveShadow>
      <planeGeometry args={[w, d]} />
      <meshStandardMaterial map={t} roughness={0.32} metalness={0.1} />
    </mesh>
  );
};
export const Wall: React.FC<{ p: V3; w: number; h: number; rotY?: number }> = ({ p, w, h, rotY = 0 }) => {
  const t = wallTex().clone();
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(w / 3, 1); t.needsUpdate = true;
  return (
    <mesh position={p} rotation={[0, rotY, 0]} receiveShadow>
      <planeGeometry args={[w, h]} />
      <meshStandardMaterial map={t} roughness={0.95} />
    </mesh>
  );
};
/** Moonlit window: glowing pane + mullions. */
export const MoonWindow: React.FC<{ p: V3; rotY?: number; w?: number; h?: number }> = ({ p, rotY = 0, w = 2, h = 2.2 }) => (
  <group position={p} rotation={[0, rotY, 0]}>
    <mesh><planeGeometry args={[w, h]} /><meshBasicMaterial color="#4b6a9e" /></mesh>
    <Box p={[0, 0, 0.02]} s={[0.08, h, 0.05]} c="#0d0f14" shadow={false} />
    <Box p={[0, 0, 0.02]} s={[w, 0.08, 0.05]} c="#0d0f14" shadow={false} />
  </group>
);
/** Clothes rack with hanging garments (box silhouettes). */
export const Rack: React.FC<{ p: V3; rotY?: number; colors: string[] }> = ({ p, rotY = 0, colors }) => (
  <group position={p} rotation={[0, rotY, 0]}>
    <Box p={[0, 1.5, 0]} s={[2.4, 0.04, 0.04]} c="#8d8f96" rough={0.4} />
    <Box p={[-1.2, 0.75, 0]} s={[0.05, 1.5, 0.05]} c="#8d8f96" rough={0.4} />
    <Box p={[1.2, 0.75, 0]} s={[0.05, 1.5, 0.05]} c="#8d8f96" rough={0.4} />
    {colors.map((c, i) => <Box key={i} p={[-1 + i * (2 / Math.max(1, colors.length - 1)), 1.05, 0]} s={[0.12, 0.85, 0.5]} c={c} />)}
  </group>
);
/** A flat picture (note, sign, clock face) on a plane; `glow` makes it emissive. */
export const Picture: React.FC<{ tex: THREE.Texture; p: V3; w: number; h: number; rot?: V3; glow?: number }> = ({ tex, p, w, h, rot, glow = 0 }) => (
  <mesh position={p} rotation={rot ?? [0, 0, 0]} receiveShadow>
    <planeGeometry args={[w, h]} />
    <meshStandardMaterial map={tex} emissiveMap={glow ? tex : null} emissive={glow ? "#ffffff" : "#000000"} emissiveIntensity={glow} roughness={0.9} transparent />
  </mesh>
);
