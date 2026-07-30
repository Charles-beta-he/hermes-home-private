// 叠桥冲刺 — Canvas presentation over the deterministic kernel.
// Original clean-room visual system (navy/teal/amber); no source assets.

import { LEVELS, createGame, setSteer, advance, getPublicState } from './kernel.js';

const COLORS = {
  sky: '#0b1f33',
  skyDeep: '#081627',
  road: '#12304c',
  roadEdge: '#1d4a6e',
  chasm: '#050d18',
  plank: '#ffb340',
  plankLight: '#ffd28a',
  pickup: '#ffb340',
  pickupCore: '#fff1d6',
  hazard: '#0a1828',
  hazardStripe: '#ffb340',
  player: '#19b6a6',
  playerLight: '#5fd9cc',
  finish: '#5fd9cc',
};

const LEVEL_LABELS = {
  1: '第 1 关 · 热身',
  2: '第 2 关 · 真本事',
};

const stage = document.getElementById('stage');
const canvas = document.getElementById('scene');
const ctx = canvas.getContext('2d');
const levelBadge = document.getElementById('level-badge');
const stackCount = document.getElementById('stack-count');
const progressFill = document.getElementById('progress-fill');
const statusRegion = document.getElementById('status');
const overlay = document.getElementById('overlay');
const overlayKicker = document.getElementById('overlay-kicker');
const overlayTitle = document.getElementById('overlay-title');
const overlayCopy = document.getElementById('overlay-copy');
const overlayHint = document.getElementById('overlay-hint');
const primaryBtn = document.getElementById('primary-btn');
const restartBtn = document.getElementById('restart-btn');

const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

let sim = null;
let screen = 'start'; // 'start' | 'playing' | 'result'
let paused = false;
let rafId = 0;
let lastTime = 0;
let primaryAction = () => beginLevel(1);

// --- screen/overlay state -------------------------------------------------

function announce(text) {
  statusRegion.textContent = text;
}

// copy is an array of lines; each line is an array of { text, strong? } segments.
function renderOverlayCopy(lines) {
  overlayCopy.textContent = '';
  lines.forEach((segments, index) => {
    if (index > 0) overlayCopy.appendChild(document.createElement('br'));
    for (const segment of segments) {
      if (segment.strong) {
        const strong = document.createElement('strong');
        strong.textContent = segment.text;
        overlayCopy.appendChild(strong);
      } else {
        overlayCopy.appendChild(document.createTextNode(segment.text));
      }
    }
  });
}

function showOverlay({ kicker, title, copy, button, hint, action }) {
  overlayKicker.textContent = kicker;
  overlayTitle.textContent = title;
  renderOverlayCopy(copy);
  overlayHint.textContent = hint || '';
  primaryBtn.textContent = button;
  primaryAction = action;
  overlay.classList.add('is-open');
  primaryBtn.focus({ preventScroll: true });
}

function hideOverlay() {
  overlay.classList.remove('is-open');
}

function beginLevel(levelNumber) {
  sim = createGame(levelNumber);
  screen = 'playing';
  hideOverlay();
  syncHud();
  announce(
    levelNumber === 1
      ? '第一关开始，第一关只是热身。左右拖动或用方向键转向。'
      : '第二关开始，第二关才是真本事。桥板分布在左右两侧。'
  );
  render();
}

function finishLevel() {
  screen = 'result';
  const won = sim.status === 'won';
  if (won && sim.levelNumber === 1) {
    announce('第一关通过。第一关只是热身，第二关才是真本事。');
    showOverlay({
      kicker: '热身完成',
      title: '第一关通过',
      copy: [
        [{ text: '第一关只是热身' }],
        [{ text: '第二关才是真本事', strong: true }],
      ],
      button: '挑战第二关',
      hint: '第二关的桥板在左右两侧，站着不动过不去',
      action: () => beginLevel(2),
    });
  } else if (won) {
    announce('第二关通过，通关成功。');
    showOverlay({
      kicker: '通关',
      title: '真本事！',
      copy: [
        [
          { text: '第二关通过，剩余桥板 ' },
          { text: String(sim.stack), strong: true },
          { text: ' 块' },
        ],
      ],
      button: '再玩一次',
      hint: '从热身关重新开始',
      action: () => beginLevel(1),
    });
  } else {
    const why =
      sim.reason === 'insufficient_stack_for_gap'
        ? '桥板不够，跨不过断路'
        : '撞上路障，桥板不够抵扣';
    announce(`挑战失败：${why}。可以重新开始本关。`);
    showOverlay({
      kicker: '差一点',
      title: '挑战失败',
      copy: [[{ text: why }], [{ text: '多吃几块桥板再冲' }]],
      button: '重新开始',
      hint: sim.levelNumber === 2 ? '第二关才是真本事' : '第一关只是热身',
      action: () => beginLevel(sim.levelNumber),
    });
  }
}

function syncHud() {
  if (!sim) return;
  levelBadge.textContent = LEVEL_LABELS[sim.levelNumber];
  stackCount.textContent = String(sim.stack);
  const pub = getPublicState(sim);
  progressFill.style.width = `${(pub.progress * 100).toFixed(1)}%`;
}

function stepSimulation(seconds, step) {
  if (!sim || sim.status !== 'running') return;
  advance(sim, seconds, step);
  syncHud();
  if (sim.status !== 'running' && screen === 'playing') {
    finishLevel();
  }
}

// --- input ----------------------------------------------------------------

let dragPointerId = null;
let dragOriginX = 0;
const keysDown = new Set();

function applyKeySteer() {
  if (!sim) return;
  const left = keysDown.has('ArrowLeft') ? -1 : 0;
  const right = keysDown.has('ArrowRight') ? 1 : 0;
  setSteer(sim, left + right);
}

stage.addEventListener('pointerdown', (event) => {
  if (screen !== 'playing') return;
  dragPointerId = event.pointerId;
  dragOriginX = event.clientX;
  stage.setPointerCapture(event.pointerId);
});

stage.addEventListener('pointermove', (event) => {
  if (event.pointerId !== dragPointerId || !sim) return;
  const range = stage.clientWidth * 0.22;
  setSteer(sim, (event.clientX - dragOriginX) / range);
});

function endDrag(event) {
  if (event.pointerId !== dragPointerId) return;
  dragPointerId = null;
  if (sim) setSteer(sim, 0);
  applyKeySteer();
}
stage.addEventListener('pointerup', endDrag);
stage.addEventListener('pointercancel', endDrag);

window.addEventListener('keydown', (event) => {
  if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
  if (screen !== 'playing') return;
  event.preventDefault();
  keysDown.add(event.key);
  applyKeySteer();
});

window.addEventListener('keyup', (event) => {
  if (!keysDown.delete(event.key)) return;
  applyKeySteer();
});

primaryBtn.addEventListener('click', () => primaryAction());
restartBtn.addEventListener('click', () => {
  if (sim) beginLevel(sim.levelNumber);
  else beginLevel(1);
});

// --- rendering ------------------------------------------------------------

function resizeCanvas() {
  const ratio = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.round(stage.clientWidth * ratio);
  canvas.height = Math.round(stage.clientHeight * ratio);
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  render();
}
window.addEventListener('resize', resizeCanvas);

function roundedRect(x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

function render() {
  const width = stage.clientWidth;
  const height = stage.clientHeight;
  if (!width || !height) return;

  ctx.clearRect(0, 0, width, height);
  const gradient = ctx.createLinearGradient(0, 0, 0, height);
  gradient.addColorStop(0, COLORS.sky);
  gradient.addColorStop(1, COLORS.skyDeep);
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, width, height);

  if (!sim) return;

  const level = LEVELS[sim.levelNumber];
  const playerY = height * 0.74;
  const unitsVisible = 24;
  const ppu = height / unitsVisible;
  const laneHalf = width * 0.31;
  const roadHalf = laneHalf + width * 0.09;
  const centerX = width / 2;
  const yFor = (z) => playerY - (z - sim.z) * ppu;
  const xFor = (x) => centerX + x * laneHalf;

  // Road strip with side glow.
  ctx.fillStyle = COLORS.road;
  ctx.fillRect(centerX - roadHalf, 0, roadHalf * 2, height);
  ctx.fillStyle = COLORS.roadEdge;
  ctx.fillRect(centerX - roadHalf, 0, 4, height);
  ctx.fillRect(centerX + roadHalf - 4, 0, 4, height);

  // Gaps: dark chasm; paid gaps get amber planks laid across.
  for (const gap of level.gaps) {
    const top = yFor(gap.z + gap.span);
    const bottom = yFor(gap.z);
    if (bottom < -60 || top > height + 60) continue;
    ctx.fillStyle = COLORS.chasm;
    ctx.fillRect(centerX - roadHalf, top, roadHalf * 2, bottom - top);
    if (sim.gapsPaid[gap.id]) {
      const planks = gap.cost;
      for (let i = 0; i < planks; i += 1) {
        const y = bottom - ((i + 0.5) / planks) * (bottom - top);
        ctx.fillStyle = i % 2 ? COLORS.plank : COLORS.plankLight;
        roundedRect(centerX - laneHalf * 0.5, y - 5, laneHalf, 10, 5);
        ctx.fill();
      }
    } else {
      ctx.fillStyle = COLORS.plankLight;
      ctx.font = `700 ${Math.max(14, width * 0.045)}px system-ui, sans-serif`;
      ctx.textAlign = 'center';
      ctx.fillText(`需要 ${gap.cost} 块`, centerX, (top + bottom) / 2 + 5);
    }
  }

  // Finish line.
  const finishY = yFor(level.finish);
  if (finishY > -40 && finishY < height + 40) {
    ctx.fillStyle = COLORS.finish;
    for (let i = 0; i < 10; i += 1) {
      if (i % 2 === 0) {
        ctx.fillRect(centerX - roadHalf + (i / 10) * roadHalf * 2, finishY - 6, roadHalf * 0.2, 12);
      }
    }
  }

  // Pickups.
  const tile = Math.max(14, width * 0.05);
  for (const pickup of level.pickups) {
    if (sim.collected[pickup.id]) continue;
    const y = yFor(pickup.z);
    if (y < -30 || y > height + 30) continue;
    const x = xFor(pickup.x);
    ctx.fillStyle = COLORS.pickup;
    roundedRect(x - tile / 2, y - tile / 2, tile, tile, 4);
    ctx.fill();
    ctx.fillStyle = COLORS.pickupCore;
    roundedRect(x - tile / 4, y - tile / 4, tile / 2, tile / 2, 3);
    ctx.fill();
  }

  // Obstacles: dark blocks with amber hazard stripes.
  for (const obstacle of level.obstacles) {
    if (sim.obstaclesCharged[obstacle.id]) continue;
    const y = yFor(obstacle.z);
    if (y < -30 || y > height + 30) continue;
    const x = xFor(obstacle.x);
    const w = tile * 2.1;
    const h = tile * 0.9;
    ctx.fillStyle = COLORS.hazard;
    roundedRect(x - w / 2, y - h / 2, w, h, 4);
    ctx.fill();
    ctx.save();
    ctx.clip();
    ctx.strokeStyle = COLORS.hazardStripe;
    ctx.lineWidth = 4;
    for (let sx = -w; sx < w; sx += 12) {
      ctx.beginPath();
      ctx.moveTo(x + sx, y + h);
      ctx.lineTo(x + sx + h, y - h);
      ctx.stroke();
    }
    ctx.restore();
  }

  // Player + carried stack.
  const px = xFor(sim.x);
  const bodyW = tile * 1.1;
  const bodyH = tile * 1.5;
  const stackToDraw = Math.min(sim.stack, 12);
  for (let i = 0; i < stackToDraw; i += 1) {
    const y = playerY + bodyH * 0.55 + 6 + i * 7;
    ctx.fillStyle = i % 2 ? COLORS.plank : COLORS.plankLight;
    roundedRect(px - tile * 0.65, y, tile * 1.3, 5.5, 2.5);
    ctx.fill();
  }
  ctx.fillStyle = COLORS.player;
  roundedRect(px - bodyW / 2, playerY - bodyH / 2, bodyW, bodyH, bodyW / 2);
  ctx.fill();
  ctx.fillStyle = COLORS.playerLight;
  ctx.beginPath();
  ctx.arc(px, playerY - bodyH * 0.18, bodyW * 0.26, 0, Math.PI * 2);
  ctx.fill();
}

// --- main loop ------------------------------------------------------------

function tick(now) {
  rafId = requestAnimationFrame(tick);
  const dt = Math.min((now - lastTime) / 1000, 0.05);
  lastTime = now;
  if (!paused && screen === 'playing') {
    stepSimulation(dt);
  }
  render();
}

function startLoop() {
  cancelAnimationFrame(rafId);
  lastTime = performance.now();
  rafId = requestAnimationFrame(tick);
}

reducedMotion.addEventListener?.('change', render);

resizeCanvas();
startLoop();

// --- narrow deterministic browser test API --------------------------------
// Fixed verbs only; no eval, no arbitrary command execution.

window.__STACK_PATH_RUNNER__ = Object.freeze({
  startLevel(levelNumber) {
    beginLevel(levelNumber);
    return this.getState();
  },
  setSteer(value) {
    if (sim) setSteer(sim, value);
    return this.getState();
  },
  advance(seconds, step) {
    stepSimulation(seconds, step);
    render();
    return this.getState();
  },
  getState() {
    return {
      screen,
      paused,
      reducedMotion: reducedMotion.matches,
      ...(sim ? getPublicState(sim) : { levelNumber: null, status: 'idle' }),
    };
  },
  restart() {
    beginLevel(sim ? sim.levelNumber : 1);
    return this.getState();
  },
  stop() {
    paused = true;
    cancelAnimationFrame(rafId);
    rafId = 0;
    return this.getState();
  },
  resume() {
    paused = false;
    startLoop();
    return this.getState();
  },
});
