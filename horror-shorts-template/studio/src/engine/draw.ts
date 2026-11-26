// Character painter: flat cut-out characters drawn with Canvas2D (600x1000, feet at y=980).
// Own horror design: squarish heads, big whites with tiny pupils, tired eye bags, desaturated clothes.
import * as THREE from "three";

export type Expr = "calm" | "uneasy" | "scared" | "terror";
export type Kind = "guard" | "mannequin";
export type CharState = {
  kind: Kind;
  expr?: Expr;
  lid?: number; // 1 open .. 0 closed
  look?: number; // pupils -1 left .. 1 right
  view?: "front" | "back";
  creepy?: number; // mannequin face: 0 blank .. 1 eyes + smile
};

const W = 600, H = 1000;
const INK = "#121014";

const rr = (c: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) => {
  c.beginPath();
  c.moveTo(x + r, y);
  c.arcTo(x + w, y, x + w, y + h, r);
  c.arcTo(x + w, y + h, x, y + h, r);
  c.arcTo(x, y + h, x, y, r);
  c.arcTo(x, y, x + w, y, r);
  c.closePath();
};
const fillStroke = (c: CanvasRenderingContext2D, fill: string, lw = 9) => {
  c.fillStyle = fill; c.fill();
  c.lineWidth = lw; c.strokeStyle = INK; c.lineJoin = "round"; c.stroke();
};
const poly = (c: CanvasRenderingContext2D, pts: number[][]) => {
  c.beginPath(); pts.forEach(([x, y], i) => (i ? c.lineTo(x, y) : c.moveTo(x, y))); c.closePath();
};
// shade the right side of the current path (key light from the left)
const shadeRight = (c: CanvasRenderingContext2D, color: string, x0: number) => {
  c.save(); c.clip(); c.fillStyle = color; c.fillRect(x0, 0, W, H); c.restore();
};

const guard = (c: CanvasRenderingContext2D, s: CharState) => {
  const expr = s.expr ?? "calm", lid = s.lid ?? 1, look = s.look ?? 0;
  // legs + shoes
  for (const x of [232, 318]) {
    rr(c, x, 700, 58, 260, 22); fillStroke(c, "#2a2f3a");
    c.beginPath(); c.ellipse(x + 29 + (x < 300 ? -10 : 10), 962, 48, 22, 0, 0, Math.PI * 2); fillStroke(c, "#0f0f12");
  }
  // arms (behind jacket edges)
  rr(c, 146, 470, 64, 250, 30); fillStroke(c, "#25324f");
  rr(c, 390, 470, 64, 250, 30); fillStroke(c, "#25324f");
  c.beginPath(); c.arc(178, 735, 32, 0, Math.PI * 2); fillStroke(c, "#e9d3c3");
  // flashlight in the right hand
  rr(c, 396, 700, 54, 120, 14); fillStroke(c, "#3b3e46");
  rr(c, 388, 806, 70, 34, 10); fillStroke(c, "#ffe7a0");
  c.beginPath(); c.arc(422, 735, 32, 0, Math.PI * 2); fillStroke(c, "#e9d3c3");
  // jacket
  poly(c, [[170, 470], [430, 470], [452, 730], [148, 730]]); fillStroke(c, "#2b3a5c");
  poly(c, [[170, 470], [430, 470], [452, 730], [148, 730]]); shadeRight(c, "rgba(0,0,0,0.22)", 330);
  poly(c, [[262, 470], [338, 470], [300, 560]]); fillStroke(c, "#d9dde6", 7);
  c.beginPath(); c.moveTo(300, 560); c.lineTo(300, 728); c.lineWidth = 6; c.strokeStyle = INK; c.stroke();
  rr(c, 200, 540, 56, 34, 6); fillStroke(c, "#e2b33b", 6); // badge
  rr(c, 338, 520, 70, 16, 4); fillStroke(c, "#1a2238", 5); // pocket
  // neck + head
  rr(c, 266, 400, 68, 90, 20); fillStroke(c, "#dcc1ae");
  rr(c, 184, 150, 232, 280, 92); fillStroke(c, "#efd9c9");
  rr(c, 184, 150, 232, 280, 92); shadeRight(c, "rgba(120,70,60,0.16)", 340);
  // ears
  c.beginPath(); c.ellipse(184, 300, 18, 30, 0, 0, Math.PI * 2); fillStroke(c, "#e6cdbc", 7);
  c.beginPath(); c.ellipse(416, 300, 18, 30, 0, 0, Math.PI * 2); fillStroke(c, "#d9bda9", 7);
  // messy hair
  poly(c, [[176, 250], [170, 170], [210, 118], [260, 96], [300, 112], [340, 92], [392, 118], [430, 170], [424, 250], [400, 196], [372, 222], [356, 180], [318, 206], [292, 172], [258, 210], [236, 176], [210, 232]]);
  fillStroke(c, "#1d1a22");
  // eyes
  const pr = { calm: 13, uneasy: 11, scared: 7, terror: 5 }[expr];
  const ew = expr === "terror" ? 40 : expr === "scared" ? 37 : 33;
  const eh = (expr === "terror" ? 46 : expr === "scared" ? 43 : 36) * Math.max(0.06, lid);
  for (const ex of [255, 345]) {
    c.strokeStyle = "rgba(90,60,80,0.55)"; c.lineWidth = 6; c.beginPath(); c.arc(ex, 300, 40, 0.25 * Math.PI, 0.75 * Math.PI); c.stroke(); // eye bags
    c.beginPath(); c.ellipse(ex, 290, ew, eh, 0, 0, Math.PI * 2); fillStroke(c, "#fbfbf7", 7);
    if (lid > 0.25) {
      c.save(); c.beginPath(); c.ellipse(ex, 290, ew, eh, 0, 0, Math.PI * 2); c.clip();
      c.fillStyle = INK; c.beginPath(); c.arc(ex + look * 12, 292, pr, 0, Math.PI * 2); c.fill();
      c.restore();
    }
  }
  // brows
  c.strokeStyle = INK; c.lineWidth = 10; c.lineCap = "round";
  const by = expr === "calm" ? 238 : expr === "uneasy" ? 236 : 222;
  const tilt = expr === "calm" ? 0 : expr === "uneasy" ? 12 : 18;
  c.beginPath(); c.moveTo(222, by + tilt * 0.4); c.lineTo(284, by - tilt); c.stroke();
  c.beginPath(); c.moveTo(316, by - tilt); c.lineTo(378, by + tilt * 0.4); c.stroke();
  // nose
  c.lineWidth = 6; c.beginPath(); c.moveTo(300, 318); c.lineTo(292, 348); c.lineTo(304, 350); c.stroke();
  // mouth
  c.lineWidth = 7;
  if (expr === "calm") { c.beginPath(); c.moveTo(276, 384); c.quadraticCurveTo(300, 390, 324, 382); c.stroke(); }
  else if (expr === "uneasy") { c.beginPath(); c.moveTo(272, 386); c.quadraticCurveTo(284, 378, 296, 386); c.quadraticCurveTo(310, 394, 326, 384); c.stroke(); }
  else if (expr === "scared") { c.beginPath(); c.ellipse(300, 388, 16, 20, 0, 0, Math.PI * 2); fillStroke(c, "#3a1218", 6); }
  else {
    c.beginPath(); c.moveTo(262, 372); c.quadraticCurveTo(300, 360, 338, 372); c.quadraticCurveTo(330, 420, 300, 424); c.quadraticCurveTo(270, 420, 262, 372); c.closePath(); fillStroke(c, "#2a0c10", 6);
    c.fillStyle = "#f4f0e6"; c.fillRect(272, 372, 56, 10);
  }
  if (expr === "terror" || expr === "scared") { // sweat
    c.beginPath(); c.moveTo(402, 200); c.quadraticCurveTo(420, 236, 412, 250); c.quadraticCurveTo(396, 260, 390, 240); c.quadraticCurveTo(390, 226, 402, 200); fillStroke(c, "#bfe6ff", 5);
  }
};

const mannequin = (c: CanvasRenderingContext2D, s: CharState) => {
  const body = "#cdbfac", seam = "rgba(60,48,36,0.55)";
  const back = s.view === "back";
  const creepy = s.creepy ?? 0;
  // legs
  for (const x of [244, 312]) { poly(c, [[x, 640], [x + 46, 640], [x + 38, 960], [x + 8, 960]]); fillStroke(c, body); }
  c.beginPath(); c.rect(220, 960, 160, 18); fillStroke(c, "#3a3632"); // base plate
  // arms
  for (const [x, d] of [[172, -1], [428, 1]] as const) {
    poly(c, [[x - 18, 420], [x + 22, 420], [x + 18 + d * 6, 690], [x - 14 + d * 6, 690]]); fillStroke(c, body);
    c.strokeStyle = seam; c.lineWidth = 4; c.beginPath(); c.moveTo(x - 12, 560); c.lineTo(x + 18, 560); c.stroke();
    c.beginPath(); c.ellipse(x + 2 + d * 6, 712, 22, 28, 0, 0, Math.PI * 2); fillStroke(c, body);
  }
  // torso (hourglass)
  c.beginPath();
  c.moveTo(190, 410); c.bezierCurveTo(250, 395, 350, 395, 410, 410);
  c.bezierCurveTo(400, 500, 352, 540, 356, 590); c.bezierCurveTo(372, 630, 380, 650, 374, 670);
  c.lineTo(226, 670); c.bezierCurveTo(220, 650, 228, 630, 244, 590); c.bezierCurveTo(248, 540, 200, 500, 190, 410); c.closePath();
  fillStroke(c, body);
  c.beginPath();
  c.moveTo(190, 410); c.bezierCurveTo(250, 395, 350, 395, 410, 410); c.bezierCurveTo(400, 500, 352, 540, 356, 590); c.bezierCurveTo(372, 630, 380, 650, 374, 670); c.lineTo(226, 670); c.bezierCurveTo(220, 650, 228, 630, 244, 590); c.bezierCurveTo(248, 540, 200, 500, 190, 410); c.closePath();
  shadeRight(c, "rgba(70,50,30,0.22)", 330);
  c.strokeStyle = seam; c.lineWidth = 4; c.beginPath(); c.moveTo(232, 600); c.quadraticCurveTo(300, 620, 368, 600); c.stroke();
  if (back) { c.beginPath(); c.moveTo(300, 420); c.lineTo(300, 600); c.stroke(); }
  // neck + egg head
  rr(c, 276, 330, 48, 84, 16); fillStroke(c, body);
  c.beginPath(); c.ellipse(300, 236, 92, 120, 0, 0, Math.PI * 2); fillStroke(c, "#d6c9b6");
  c.beginPath(); c.ellipse(300, 236, 92, 120, 0, 0, Math.PI * 2); shadeRight(c, "rgba(70,50,30,0.2)", 330);
  if (!back && creepy > 0) {
    c.globalAlpha = Math.min(1, creepy);
    for (const ex of [266, 334]) {
      const g = c.createRadialGradient(ex, 226, 4, ex, 226, 34);
      g.addColorStop(0, "#0b0808"); g.addColorStop(1, "rgba(11,8,8,0)");
      c.fillStyle = g; c.beginPath(); c.ellipse(ex, 226, 34, 26, 0, 0, Math.PI * 2); c.fill();
      c.fillStyle = "#fffbe8"; c.beginPath(); c.arc(ex, 226, 5, 0, Math.PI * 2); c.fill();
    }
    c.strokeStyle = "#1a1210"; c.lineWidth = 5; c.beginPath(); c.moveTo(254, 296); c.quadraticCurveTo(300, 322 + 10 * creepy, 346, 296); c.stroke();
    c.globalAlpha = 1;
  }
};

const cache = new Map<string, THREE.CanvasTexture>();
export const charTexture = (s: CharState): THREE.CanvasTexture => {
  const key = JSON.stringify(s);
  const hit = cache.get(key);
  if (hit) return hit;
  const cv = document.createElement("canvas");
  cv.width = W; cv.height = H;
  const c = cv.getContext("2d")!;
  if (s.kind === "guard") guard(c, s); else mannequin(c, s);
  const t = new THREE.CanvasTexture(cv);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 4;
  cache.set(key, t);
  return t;
};

// flat props drawn as textures (notes, clocks, signs)
export const propTexture = (key: string, w: number, h: number, paint: (c: CanvasRenderingContext2D) => void) => {
  const hit = cache.get("prop:" + key);
  if (hit) return hit;
  const cv = document.createElement("canvas");
  cv.width = w; cv.height = h;
  paint(cv.getContext("2d")!);
  const t = new THREE.CanvasTexture(cv);
  t.colorSpace = THREE.SRGBColorSpace;
  cache.set("prop:" + key, t);
  return t;
};
