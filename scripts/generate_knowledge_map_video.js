#!/usr/bin/env node

const WIDTH = 576;
const HEIGHT = 848;
const FPS = 30;
const DURATION = 10.5;
const FRAMES = Math.round(FPS * DURATION);

const buf = Buffer.alloc(WIDTH * HEIGHT * 3);

function clamp(v, lo = 0, hi = 255) {
  return v < lo ? lo : v > hi ? hi : v;
}

function setPixel(x, y, r, g, b, a = 1) {
  x = x | 0;
  y = y | 0;
  if (x < 0 || y < 0 || x >= WIDTH || y >= HEIGHT) return;
  const i = (y * WIDTH + x) * 3;
  buf[i] = clamp(buf[i] * (1 - a) + r * a);
  buf[i + 1] = clamp(buf[i + 1] * (1 - a) + g * a);
  buf[i + 2] = clamp(buf[i + 2] * (1 - a) + b * a);
}

function fillBackground(t) {
  for (let y = 0; y < HEIGHT; y++) {
    const vy = y / HEIGHT;
    for (let x = 0; x < WIDTH; x++) {
      const vx = x / WIDTH;
      const cx = vx - 0.56;
      const cy = vy - 0.46;
      const d = Math.sqrt(cx * cx + cy * cy);
      const pulse = 0.5 + 0.5 * Math.sin(t * Math.PI * 2);
      const r = 6 + 18 * (1 - vy) + 18 * Math.max(0, 1 - d * 2.1);
      const g = 12 + 24 * (1 - d) + 10 * pulse * Math.max(0, 1 - Math.abs(vx - 0.62) * 2);
      const b = 22 + 42 * (1 - d) + 28 * Math.max(0, 1 - vy);
      const i = (y * WIDTH + x) * 3;
      buf[i] = clamp(r);
      buf[i + 1] = clamp(g);
      buf[i + 2] = clamp(b);
    }
  }
}

function line(x0, y0, x1, y1, r, g, b, a = 1, width = 1) {
  const dx = x1 - x0;
  const dy = y1 - y0;
  const steps = Math.max(Math.abs(dx), Math.abs(dy)) | 0;
  for (let i = 0; i <= steps; i++) {
    const p = steps ? i / steps : 0;
    const x = x0 + dx * p;
    const y = y0 + dy * p;
    for (let ox = -width; ox <= width; ox++) {
      for (let oy = -width; oy <= width; oy++) setPixel(x + ox, y + oy, r, g, b, a / (1 + Math.abs(ox) + Math.abs(oy)));
    }
  }
}

function circle(cx, cy, radius, r, g, b, a = 1) {
  const minX = Math.floor(cx - radius);
  const maxX = Math.ceil(cx + radius);
  const minY = Math.floor(cy - radius);
  const maxY = Math.ceil(cy + radius);
  for (let y = minY; y <= maxY; y++) {
    for (let x = minX; x <= maxX; x++) {
      const d = Math.hypot(x - cx, y - cy) / radius;
      if (d <= 1) setPixel(x, y, r, g, b, a * (1 - d * d));
    }
  }
}

function rect(x, y, w, h, r, g, b, a = 1) {
  for (let yy = y | 0; yy < y + h; yy++) {
    for (let xx = x | 0; xx < x + w; xx++) setPixel(xx, yy, r, g, b, a);
  }
}

function roundedCard(x, y, w, h, t, idx) {
  rect(x, y, w, h, 18, 34, 45, 0.52);
  line(x, y, x + w, y, 117, 226, 210, 0.28, 1);
  line(x, y + h, x + w, y + h, 255, 255, 255, 0.08, 1);
  const rows = 4 + (idx % 3);
  for (let i = 0; i < rows; i++) {
    const yy = y + 16 + i * 15;
    const ww = w * (0.42 + 0.36 * ((Math.sin(t * 4 + idx + i) + 1) / 2));
    rect(x + 14, yy, ww, 3, 176, 213, 219, 0.34);
  }
  circle(x + w - 18, y + 18, 4, 77, 229, 200, 0.72);
}

function drawGrid(t) {
  const horizon = 544;
  for (let i = -8; i <= 8; i++) {
    const x = WIDTH * 0.5 + i * 42 + Math.sin(t * 3 + i) * 4;
    line(WIDTH * 0.5, horizon, x, HEIGHT + 40, 80, 180, 190, 0.12, 1);
  }
  for (let j = 0; j < 11; j++) {
    const p = j / 10;
    const y = horizon + p * p * 320;
    line(40, y, WIDTH - 40, y, 80, 180, 190, 0.10 * (1 - p * 0.3), 1);
  }
}

function drawVectorMap(t) {
  const nodes = [];
  for (let i = 0; i < 54; i++) {
    const a = i * 2.399 + t * 1.2;
    const rad = 34 + (i % 9) * 13 + 16 * Math.sin(t * 2 + i);
    const x = WIDTH * 0.58 + Math.cos(a) * rad * (0.78 + (i % 4) * 0.04);
    const y = HEIGHT * 0.48 + Math.sin(a * 1.1) * rad * 1.14;
    nodes.push([x, y, i]);
  }
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const [x0, y0] = nodes[i];
      const [x1, y1] = nodes[j];
      const d = Math.hypot(x1 - x0, y1 - y0);
      if (d < 92) line(x0, y0, x1, y1, 86, 218, 205, 0.13 * (1 - d / 92), 1);
    }
  }
  for (const [x, y, i] of nodes) {
    const hot = (Math.sin(t * 7 + i) + 1) / 2;
    circle(x, y, 3.2 + hot * 2.2, 95 + hot * 80, 232, 210, 0.78);
  }
}

function drawPackets(t) {
  for (let i = 0; i < 34; i++) {
    const phase = (t * 1.65 + i / 17) % 1;
    const sx = -40 + (i % 5) * 30;
    const sy = 100 + (i % 9) * 70;
    const ex = WIDTH * 0.58 + Math.sin(i * 1.9) * 118;
    const ey = HEIGHT * 0.47 + Math.cos(i * 1.35) * 154;
    const ease = phase < 0.5 ? phase * phase * 2 : 1 - Math.pow(-2 * phase + 2, 2) / 2;
    const x = sx + (ex - sx) * ease;
    const y = sy + (ey - sy) * ease;
    const tx = sx + (ex - sx) * Math.max(0, ease - 0.12);
    const ty = sy + (ey - sy) * Math.max(0, ease - 0.12);
    line(tx, ty, x, y, 98, 244, 226, 0.34, 2);
    line(sx, sy, x, y, 64, 205, 208, 0.08, 1);
    circle(x, y, 7 + 7 * (1 - Math.abs(phase - 0.5) * 2), 156, 255, 236, 0.82);
  }
}

function drawScanBeam(t) {
  const x = -80 + ((t * 1.15) % 1) * (WIDTH + 160);
  for (let i = -18; i <= 18; i++) {
    line(x + i, 0, x + i - 96, HEIGHT, 93, 232, 218, 0.018 * (19 - Math.abs(i)), 1);
  }
}

function drawEmbeddingAxes(t) {
  const cx = WIDTH * 0.58;
  const cy = HEIGHT * 0.48;
  for (let i = 0; i < 4; i++) {
    const a = t * Math.PI * 2 + i * Math.PI / 4;
    const x0 = cx + Math.cos(a) * 34;
    const y0 = cy + Math.sin(a) * 22;
    const x1 = cx + Math.cos(a) * 170;
    const y1 = cy + Math.sin(a) * 116;
    line(x0, y0, x1, y1, 205, 255, 245, 0.18, 1);
    circle(x1, y1, 5, 205, 255, 245, 0.55);
  }
}

function drawKnowledgeCore(t) {
  const cx = WIDTH * 0.58;
  const cy = HEIGHT * 0.48;
  const pulse = 0.5 + 0.5 * Math.sin(t * Math.PI * 4);
  for (let r = 120; r > 20; r -= 16) {
    circle(cx, cy, r + pulse * 3, 44, 122 + r * 0.3, 140 + r * 0.35, 0.018);
  }
  line(cx - 92, cy + 118, cx + 92, cy + 118, 210, 246, 238, 0.22, 1);
  line(cx - 72, cy + 140, cx + 72, cy + 140, 210, 246, 238, 0.14, 1);
}

function drawFrame(frame) {
  const t = frame / FRAMES;
  fillBackground(t);
  drawGrid(t);
  drawScanBeam(t);
  drawKnowledgeCore(t);
  drawVectorMap(t);
  drawEmbeddingAxes(t);
  drawPackets(t);

  for (let i = 0; i < 5; i++) {
    const y = 108 + i * 92 + Math.sin(t * 5 + i) * 4;
    const x = 34 + Math.sin(t * 2 + i) * 6;
    roundedCard(x, y, 148, 58, t, i);
  }

  for (let i = 0; i < 8; i++) {
    const p = (t + i / 8) % 1;
    const x = 78 + p * 390;
    const y = 702 + Math.sin(p * Math.PI * 2 + i) * 18;
    rect(x, y, 26, 5, 128, 238, 221, 0.20 * (1 - Math.abs(p - 0.5)));
  }

  // Subtle focus vignette.
  for (let y = 0; y < HEIGHT; y++) {
    for (let x = 0; x < WIDTH; x++) {
      const d = Math.hypot((x - WIDTH * 0.54) / WIDTH, (y - HEIGHT * 0.46) / HEIGHT);
      const shade = clamp(1 - Math.max(0, d - 0.18) * 1.35, 0.28, 1);
      const i = (y * WIDTH + x) * 3;
      buf[i] = clamp(buf[i] * shade);
      buf[i + 1] = clamp(buf[i + 1] * shade);
      buf[i + 2] = clamp(buf[i + 2] * shade);
    }
  }
}

for (let f = 0; f < FRAMES; f++) {
  drawFrame(f);
  process.stdout.write(buf);
}
