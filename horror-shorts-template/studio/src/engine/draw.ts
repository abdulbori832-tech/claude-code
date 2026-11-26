// Character painter: flat cut-out characters drawn with Canvas2D (600x1000, feet at y=980).
// Own horror design: squarish heads, big whites with tiny pupils, tired eye bags, desaturated clothes.
import * as THREE from "three";

export type Expr = "calm" | "uneasy" | "scared" | "terror" | "smile" | "polite" | "serious" | "creepy";
export type Kind = "guard" | "guest" | "mannequin" | "receptionist" | "hand";
export type CharState = {
  kind: Kind;
  expr?: Expr;
  lid?: number; // 1 open .. 0 closed
  look?: number; // pupils -1 left .. 1 right
  view?: "front" | "back";
  creepy?: number; // mannequin face: 0 blank .. 1 eyes + smile
  pose?: "stand" | "wave1" | "wave2";
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
  const guest = s.kind === "guest";
  const JACKET = guest ? "#2f7a55" : "#2b3a5c", SLEEVE = guest ? "#286a49" : "#25324f", PANTS = guest ? "#3b4d72" : "#2a2f3a";
  // legs + shoes
  for (const x of [232, 318]) {
    rr(c, x, 700, 58, 260, 22); fillStroke(c, PANTS);
    c.beginPath(); c.ellipse(x + 29 + (x < 300 ? -10 : 10), 962, 48, 22, 0, 0, Math.PI * 2); fillStroke(c, guest ? "#f2efe6" : "#0f0f12");
  }
  // arms (behind jacket edges)
  rr(c, 146, 470, 64, 250, 30); fillStroke(c, SLEEVE);
  rr(c, 390, 470, 64, 250, 30); fillStroke(c, SLEEVE);
  c.beginPath(); c.arc(178, 735, 32, 0, Math.PI * 2); fillStroke(c, "#e9d3c3");
  if (!guest) { // flashlight in the right hand
    rr(c, 396, 700, 54, 120, 14); fillStroke(c, "#3b3e46");
    rr(c, 388, 806, 70, 34, 10); fillStroke(c, "#ffe7a0");
  }
  c.beginPath(); c.arc(422, 735, 32, 0, Math.PI * 2); fillStroke(c, "#e9d3c3");
  if (guest) { c.beginPath(); c.ellipse(300, 470, 120, 40, 0, Math.PI, 0); fillStroke(c, SLEEVE); } // hood
  poly(c, [[170, 470], [430, 470], [452, 730], [148, 730]]); fillStroke(c, JACKET);
  poly(c, [[170, 470], [430, 470], [452, 730], [148, 730]]); shadeRight(c, "rgba(0,0,0,0.22)", 330);
  if (guest) {
    rr(c, 220, 610, 160, 70, 18); fillStroke(c, SLEEVE, 6); // front pocket
    c.strokeStyle = "#e8e2d0"; c.lineWidth = 6; c.beginPath(); c.moveTo(270, 480); c.lineTo(266, 560); c.moveTo(330, 480); c.lineTo(334, 560); c.stroke(); // strings
    poly(c, [[160, 480], [196, 480], [176, 700], [146, 700]]); fillStroke(c, "#7a3b26", 6); // backpack strap
  } else {
    poly(c, [[262, 470], [338, 470], [300, 560]]); fillStroke(c, "#d9dde6", 7);
    c.beginPath(); c.moveTo(300, 560); c.lineTo(300, 728); c.lineWidth = 6; c.strokeStyle = INK; c.stroke();
    rr(c, 200, 540, 56, 34, 6); fillStroke(c, "#e2b33b", 6); // badge
    rr(c, 338, 520, 70, 16, 4); fillStroke(c, "#1a2238", 5); // pocket
  }
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
  const pr = ({ calm: 13, uneasy: 11, scared: 7, terror: 5 } as Record<string, number>)[expr] ?? 13;
  const happy = expr === "smile";
  const ew = expr === "terror" ? 40 : expr === "scared" ? 37 : 33;
  const eh = (expr === "terror" ? 46 : expr === "scared" ? 43 : 36) * Math.max(0.06, lid);
  for (const ex of [255, 345]) {
    c.strokeStyle = "rgba(90,60,80,0.55)"; c.lineWidth = 6; c.beginPath(); c.arc(ex, 300, 40, 0.25 * Math.PI, 0.75 * Math.PI); c.stroke(); // eye bags
    if (happy) { c.strokeStyle = INK; c.lineWidth = 9; c.beginPath(); c.arc(ex, 304, 28, 1.15 * Math.PI, 1.85 * Math.PI); c.stroke(); continue; }
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
  if (happy) {
    c.beginPath(); c.moveTo(258, 368); c.quadraticCurveTo(300, 376, 342, 368); c.quadraticCurveTo(330, 418, 300, 420); c.quadraticCurveTo(270, 418, 258, 368); c.closePath(); fillStroke(c, "#5a1622", 6);
    c.fillStyle = "#ff8aa0"; c.beginPath(); c.ellipse(300, 406, 18, 9, 0, 0, Math.PI * 2); c.fill();
  } else if (expr === "calm") { c.beginPath(); c.moveTo(276, 384); c.quadraticCurveTo(300, 390, 324, 382); c.stroke(); }
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

const receptionist = (c: CanvasRenderingContext2D, s: CharState) => {
  const expr = s.expr ?? "polite", lid = s.lid ?? 1, pose = s.pose ?? "stand";
  const VEST = "#7a1f2b", SKIN = "#eadfd2";
  for (const x of [252, 318]) { rr(c, x, 720, 34, 240, 14); fillStroke(c, "#1c1a1f"); c.beginPath(); c.ellipse(x + 17, 962, 34, 16, 0, 0, Math.PI * 2); fillStroke(c, "#0b0a0c"); }
  poly(c, [[200, 640], [400, 640], [420, 760], [180, 760]]); fillStroke(c, "#1f1a26"); // skirt
  // left arm down
  rr(c, 160, 470, 56, 230, 26); fillStroke(c, VEST);
  c.beginPath(); c.arc(188, 712, 28, 0, Math.PI * 2); fillStroke(c, SKIN);
  // right arm: down or waving
  if (pose === "stand") { rr(c, 384, 470, 56, 230, 26); fillStroke(c, VEST); c.beginPath(); c.arc(412, 712, 28, 0, Math.PI * 2); fillStroke(c, SKIN); }
  else {
    const a = pose === "wave1" ? -0.35 : 0.05;
    c.save(); c.translate(410, 490); c.rotate(Math.PI + a);
    rr(c, -28, 0, 56, 210, 26); fillStroke(c, VEST);
    c.beginPath(); c.arc(0, 226, 32, 0, Math.PI * 2); fillStroke(c, SKIN);
    for (let k = -2; k <= 2; k++) { rr(c, k * 13 - 6, 236, 12, 40, 6); fillStroke(c, SKIN, 5); }
    c.restore();
  }
  poly(c, [[184, 470], [416, 470], [410, 660], [190, 660]]); fillStroke(c, VEST); // vest
  poly(c, [[184, 470], [416, 470], [410, 660], [190, 660]]); shadeRight(c, "rgba(0,0,0,0.25)", 330);
  poly(c, [[262, 470], [338, 470], [300, 580]]); fillStroke(c, "#f1ede4", 7);
  poly(c, [[288, 478], [312, 478], [306, 560], [300, 574], [294, 560]]); fillStroke(c, "#1a1a1a", 5); // tie
  rr(c, 330, 520, 60, 22, 4); fillStroke(c, "#d8b04a", 5); // name tag
  rr(c, 272, 400, 56, 84, 18); fillStroke(c, "#d9cbbd");
  // head
  c.beginPath(); c.ellipse(300, 290, 104, 140, 0, 0, Math.PI * 2); fillStroke(c, SKIN);
  c.beginPath(); c.ellipse(300, 290, 104, 140, 0, 0, Math.PI * 2); shadeRight(c, "rgba(80,90,70,0.18)", 340);
  // slick hair with centre part + bun
  c.beginPath(); c.arc(300, 92, 52, 0, Math.PI * 2); fillStroke(c, "#0f0d12");
  c.beginPath(); c.moveTo(194, 300); c.bezierCurveTo(180, 150, 260, 130, 300, 150); c.bezierCurveTo(340, 130, 420, 150, 406, 300);
  c.bezierCurveTo(392, 230, 360, 196, 300, 182); c.bezierCurveTo(240, 196, 208, 230, 194, 300); c.closePath(); fillStroke(c, "#0f0d12");
  c.strokeStyle = "#3a3448"; c.lineWidth = 4; c.beginPath(); c.moveTo(300, 152); c.lineTo(300, 182); c.stroke();
  // eyes
  for (const [ex, d] of [[258, -1], [342, 1]] as const) {
    if (expr === "creepy") {
      const g = c.createRadialGradient(ex, 280, 4, ex, 280, 38); g.addColorStop(0, "#000"); g.addColorStop(0.7, "#120608"); g.addColorStop(1, "rgba(18,6,8,0)");
      c.fillStyle = g; c.beginPath(); c.ellipse(ex, 280, 38, 34, 0, 0, Math.PI * 2); c.fill();
      c.fillStyle = "#fff6e0"; c.beginPath(); c.arc(ex, 282, 5, 0, Math.PI * 2); c.fill();
      continue;
    }
    const eh = (expr === "serious" ? 14 : 22) * Math.max(0.06, lid);
    c.beginPath(); c.ellipse(ex, 282, 30, eh, 0, 0, Math.PI * 2); fillStroke(c, "#fbf8f2", 6);
    if (lid > 0.25) { c.save(); c.beginPath(); c.ellipse(ex, 282, 30, eh, 0, 0, Math.PI * 2); c.clip(); c.fillStyle = "#2a1a14"; c.beginPath(); c.arc(ex, 284, 13, 0, Math.PI * 2); c.fill(); c.fillStyle = "#fff"; c.beginPath(); c.arc(ex - 4, 279, 4, 0, Math.PI * 2); c.fill(); c.restore(); }
    c.strokeStyle = INK; c.lineWidth = 8; c.beginPath(); c.moveTo(ex - 32, 282 - eh * 0.6); c.quadraticCurveTo(ex, 282 - eh - 6, ex + 34, 276 - eh * 0.6); c.lineTo(ex + 44 * d * (d > 0 ? 1 : 1), 268 - eh * 0.6); c.stroke(); // liner + flick
    c.lineWidth = 7; c.beginPath(); c.moveTo(ex - 30, 236 + (expr === "serious" ? 8 * -d : 0)); c.quadraticCurveTo(ex, 226, ex + 30, 236 + (expr === "serious" ? 8 * d : 0)); c.stroke(); // brow
  }
  c.strokeStyle = INK; c.lineWidth = 5; c.beginPath(); c.moveTo(302, 306); c.lineTo(296, 334); c.lineTo(306, 336); c.stroke();
  // red lips
  if (expr === "creepy") {
    c.beginPath(); c.moveTo(218, 360); c.quadraticCurveTo(300, 380, 382, 360); c.quadraticCurveTo(352, 420, 300, 424); c.quadraticCurveTo(248, 420, 218, 360); c.closePath(); fillStroke(c, "#b3121f", 6);
    c.fillStyle = "#f6f1e4"; c.beginPath(); c.moveTo(226, 366); c.quadraticCurveTo(300, 384, 374, 366); c.lineTo(364, 384); c.quadraticCurveTo(300, 398, 236, 384); c.closePath(); c.fill();
    c.strokeStyle = "#8a7a70"; c.lineWidth = 3; for (let x = 240; x <= 360; x += 15) { c.beginPath(); c.moveTo(x, 370); c.lineTo(x, 390); c.stroke(); }
  } else if (expr === "serious") {
    c.beginPath(); c.moveTo(270, 372); c.quadraticCurveTo(300, 366, 330, 372); c.quadraticCurveTo(300, 384, 270, 372); fillStroke(c, "#b3121f", 5);
  } else {
    c.beginPath(); c.moveTo(266, 366); c.quadraticCurveTo(300, 384, 334, 366); c.quadraticCurveTo(300, 396, 266, 366); fillStroke(c, "#b3121f", 5);
  }
};

const hand = (c: CanvasRenderingContext2D) => { // pointing hand, finger up (for button presses)
  rr(c, 150, 560, 160, 420, 50); fillStroke(c, "#286a49"); // sleeve
  rr(c, 140, 520, 180, 70, 24); fillStroke(c, "#2f7a55");
  rr(c, 150, 330, 170, 220, 60); fillStroke(c, "#e9d3c3"); // fist
  rr(c, 196, 90, 62, 280, 30); fillStroke(c, "#e9d3c3"); // index finger
  c.strokeStyle = INK; c.lineWidth = 5;
  for (const y of [400, 450, 500]) { c.beginPath(); c.moveTo(160, y); c.lineTo(230, y - 6); c.stroke(); }
  c.beginPath(); c.ellipse(227, 120, 18, 22, 0, 0, Math.PI * 2); c.strokeStyle = "rgba(80,40,30,0.5)"; c.stroke();
};

const cache = new Map<string, THREE.CanvasTexture>();
export const charTexture = (s: CharState): THREE.CanvasTexture => {
  const key = JSON.stringify(s);
  const hit = cache.get(key);
  if (hit) return hit;
  const cv = document.createElement("canvas");
  cv.width = W; cv.height = H;
  const c = cv.getContext("2d")!;
  if (s.kind === "guard" || s.kind === "guest") guard(c, s);
  else if (s.kind === "receptionist") receptionist(c, s);
  else if (s.kind === "hand") hand(c);
  else mannequin(c, s);
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
