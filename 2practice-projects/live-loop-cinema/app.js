const scenes = [
  {
    kicker: "Scene 01 · long task",
    title: "Agents do not fail at thinking. They fail at staying in training.",
    body: "A long coding task needs reusable intent, local adaptation, and error feedback across many bounded runs.",
    nodes: ["intent", "slice", "check", "resume"],
    mode: "problem"
  },
  {
    kicker: "Scene 02 · roadmap",
    title: "The roadmap is the slow state.",
    body: "It behaves like reusable weights: not neural parameters, but persistent project knowledge that makes the next run less blank.",
    nodes: ["roadmap", "constraints", "style", "memory"],
    mode: "weights"
  },
  {
    kicker: "Scene 03 · active adapter",
    title: "The active task is the fast adapter.",
    body: "Each loop binds the agent to one narrow objective, one workspace, and one local criterion for progress.",
    nodes: ["task", "scope", "budget", "patch"],
    mode: "adapter"
  },
  {
    kicker: "Scene 04 · reflective check",
    title: "Checks turn execution into learning signal.",
    body: "Tests, reviews, screenshots, and contradiction scans become the loss surface for the next local update.",
    nodes: ["test", "review", "diff", "loss"],
    mode: "loss"
  },
  {
    kicker: "Scene 05 · failure bank",
    title: "Failure memory makes repetition expensive.",
    body: "The loop records mistakes as reusable counterexamples, so the next epoch can avoid re-paying the same cost.",
    nodes: ["failure", "cause", "rule", "guard"],
    mode: "memory"
  },
  {
    kicker: "Scene 06 · MOA graph",
    title: "MOA lifts loops from a line into a graph.",
    body: "Independent loop skills become workers in a shared blackboard: parallel search horizontally, persistent optimization vertically.",
    nodes: ["DAG", "agents", "blackboard", "merge"],
    mode: "moa"
  }
];

const root = document.querySelector("#sceneRoot");
const nav = document.querySelector("#sceneNav");
const count = document.querySelector("#sceneCount");
const rail = document.querySelector("#railProgress");
const mode = document.querySelector("#sceneMode");
const deck = document.querySelector("#deck");
const prevBtn = document.querySelector("#prevBtn");
const nextBtn = document.querySelector("#nextBtn");
const playBtn = document.querySelector("#playBtn");
const themeBtn = document.querySelector("#themeBtn");
const canvas = document.querySelector("#field");
const ctx = canvas.getContext("2d");

let index = 0;
let timer = null;
let pointer = { x: 0.5, y: 0.45 };
let dots = [];

function renderNav() {
  nav.innerHTML = scenes
    .map((_, i) => `<button type="button" data-jump="${i}" aria-label="Go to scene ${i + 1}">${i + 1}</button>`)
    .join("");
}

function renderScene() {
  const scene = scenes[index];
  root.innerHTML = `
    <section class="scene">
      <div class="scene-copy">
        <span class="kicker">${scene.kicker}</span>
        <h1>${scene.title}</h1>
        <p>${scene.body}</p>
      </div>
      <div class="visual" aria-label="${scene.mode} visual">
        <div class="loop-orbit">
          <span class="pulse-line"></span>
          ${scene.nodes.map((node) => `<span class="node">${node}</span>`).join("")}
        </div>
      </div>
    </section>`;
  [...nav.querySelectorAll("button")].forEach((button, i) => {
    button.setAttribute("aria-current", i === index ? "true" : "false");
  });
  count.textContent = `${String(index + 1).padStart(2, "0")} / ${String(scenes.length).padStart(2, "0")}`;
  rail.style.height = `${((index + 1) / scenes.length) * 100}%`;
  mode.textContent = scene.mode;
}

function go(next) {
  index = (next + scenes.length) % scenes.length;
  renderScene();
}

function togglePlay() {
  if (timer) {
    clearInterval(timer);
    timer = null;
    playBtn.textContent = "Play";
    return;
  }
  timer = setInterval(() => go(index + 1), 4200);
  playBtn.textContent = "Pause";
}

function resizeCanvas() {
  const ratio = window.devicePixelRatio || 1;
  canvas.width = Math.floor(window.innerWidth * ratio);
  canvas.height = Math.floor(window.innerHeight * ratio);
  canvas.style.width = `${window.innerWidth}px`;
  canvas.style.height = `${window.innerHeight}px`;
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  dots = Array.from({ length: Math.min(82, Math.floor(window.innerWidth / 16)) }, (_, i) => ({
    x: Math.random() * window.innerWidth,
    y: Math.random() * window.innerHeight,
    r: 1 + Math.random() * 2.6,
    a: (i / 12) * Math.PI,
    s: 0.25 + Math.random() * 0.9
  }));
}

function animate() {
  ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
  ctx.lineWidth = 1;
  dots.forEach((dot, i) => {
    dot.a += 0.006 * dot.s;
    dot.x += Math.cos(dot.a) * dot.s + (pointer.x * window.innerWidth - dot.x) * 0.0008;
    dot.y += Math.sin(dot.a) * dot.s + (pointer.y * window.innerHeight - dot.y) * 0.0008;
    if (dot.x < -40) dot.x = window.innerWidth + 40;
    if (dot.x > window.innerWidth + 40) dot.x = -40;
    if (dot.y < -40) dot.y = window.innerHeight + 40;
    if (dot.y > window.innerHeight + 40) dot.y = -40;

    ctx.beginPath();
    ctx.fillStyle = i % 3 === 0 ? "rgba(233,79,55,.5)" : "rgba(0,166,118,.38)";
    ctx.arc(dot.x, dot.y, dot.r, 0, Math.PI * 2);
    ctx.fill();

    for (let j = i + 1; j < dots.length; j += 1) {
      const other = dots[j];
      const dx = dot.x - other.x;
      const dy = dot.y - other.y;
      const dist = Math.hypot(dx, dy);
      if (dist < 118) {
        ctx.strokeStyle = `rgba(22,20,17,${0.08 * (1 - dist / 118)})`;
        ctx.beginPath();
        ctx.moveTo(dot.x, dot.y);
        ctx.lineTo(other.x, other.y);
        ctx.stroke();
      }
    }
  });
  requestAnimationFrame(animate);
}

renderNav();
renderScene();
resizeCanvas();
animate();

nav.addEventListener("click", (event) => {
  const button = event.target.closest("[data-jump]");
  if (button) go(Number(button.dataset.jump));
});

prevBtn.addEventListener("click", () => go(index - 1));
nextBtn.addEventListener("click", () => go(index + 1));
playBtn.addEventListener("click", togglePlay);
themeBtn.addEventListener("click", () => {
  document.documentElement.dataset.theme = document.documentElement.dataset.theme === "studio" ? "" : "studio";
});

window.addEventListener("resize", resizeCanvas);
window.addEventListener("pointermove", (event) => {
  pointer = { x: event.clientX / window.innerWidth, y: event.clientY / window.innerHeight };
  deck.style.setProperty("--mx", `${event.clientX}px`);
  deck.style.setProperty("--my", `${event.clientY}px`);
});

window.addEventListener("keydown", (event) => {
  if (event.key === "ArrowRight") go(index + 1);
  if (event.key === "ArrowLeft") go(index - 1);
  if (event.key === " ") {
    event.preventDefault();
    togglePlay();
  }
  const numeric = Number(event.key);
  if (numeric >= 1 && numeric <= scenes.length) go(numeric - 1);
});
