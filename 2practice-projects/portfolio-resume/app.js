const profile = {
  name: "Reflective Systems Engineer",
  summary:
    "A personal portfolio for repositories, research artifacts, and long-horizon agent systems. Replace this line with your real name, direction, and strongest proof.",
  github: "https://github.com/Harzva",
  email: "mailto:hello@example.com",
  metrics: [
    ["8", "loop skills packaged for major agent CLIs"],
    ["1", "MOA computation graph for multi-agent work"],
    ["∞", "roadmap-first iterations for long tasks"],
  ],
};

const repositories = [
  {
    name: "Oh-Reflective-loop-skills",
    tag: "loop",
    summary:
      "A family of reflective loop skills that turn CLI agents into persistent optimize/check systems.",
    stack: "Codex · Gemini · Claude · Qwen · Kimi",
    signal: "Roadmap as weights",
    url: "../../",
  },
  {
    name: "moa-loop",
    tag: "agent",
    summary:
      "A mixture-of-agents loop with DAG scheduling, shared blackboard communication, and epoch management.",
    stack: "Python · DAG · Blackboard",
    signal: "Computation graph",
    url: "../../moa-loop/",
  },
  {
    name: "codex-loop",
    tag: "loop",
    summary:
      "Plan-driven recurring iteration for Codex with external daemon resume and durable state files.",
    stack: "Codex CLI · daemon · logs",
    signal: "Thread continuity",
    url: "../../codex-loop/",
  },
  {
    name: "gemini-loop",
    tag: "loop",
    summary:
      "Reflective loop architecture for Gemini CLI with optimize/check alternation and failure memory.",
    stack: "Gemini CLI · state machine",
    signal: "Self-correction",
    url: "../../gemini-loop/",
  },
  {
    name: "Roadmaps Are Weights",
    tag: "research",
    summary:
      "A paper draft framing long-horizon agent loops as non-parametric training systems.",
    stack: "LaTeX · Mermaid · ICML style",
    signal: "Training view",
    url: "../../paper/main.pdf",
  },
  {
    name: "Portfolio Resume",
    tag: "research",
    summary:
      "The first practice project: a sharp personal site for repositories, systems, and research direction.",
    stack: "HTML · CSS · Canvas",
    signal: "Public surface",
    url: "./index.html",
  },
  {
    name: "Loop Simulator",
    tag: "agent",
    summary:
      "An interactive topic page for explaining loop mechanisms with step-through event playback across four runtimes.",
    stack: "HTML · CSS · JavaScript",
    signal: "Hands-on learning",
    url: "../reflective-loop-simulator/index.html",
  },
];

const methodSteps = [
  [
    "Roadmap backbone",
    "Keep the durable objective outside the chat window, where every future epoch can read it.",
  ],
  [
    "Fast adapter",
    "Use active_task.json for the current bounded slice, scope patch, and verification target.",
  ],
  [
    "Check as loss",
    "Treat review output as an error signal that must produce a concrete next update.",
  ],
  [
    "Failure memory",
    "Compress repeated mistakes into reusable patterns instead of replaying long transcripts.",
  ],
];

const timeline = [
  ["01", "Skill kernel", "Defined optimize/check alternation as the smallest useful loop."],
  ["02", "CLI family", "Packaged the same loop semantics across eight agent runtimes."],
  ["03", "MOA layer", "Lifted the loop into a DAG-backed mixture-of-agents architecture."],
  ["04", "Daemon management", "Added unified start/stop/status/cron supervision across all skills."],
  ["05", "Public work", "Turned the systems into a portfolio, paper, and reusable practice track."],
];

const consoleLines = [
  "$ reflective-loop start portfolio-resume",
  "roadmap.md        loaded as project weights",
  "active_task.json  selected: build public surface",
  "optimize          render repository narrative",
  "check             verify contrast, motion, links",
  "patch             sharpen hero + reduce generic copy",
  "failure_bank.json updated: avoid template energy",
  "cron              health-check daemon auto-restart",
  "next epoch        add real projects and deploy",
];

const root = document.documentElement;
const body = document.body;
const canvas = document.getElementById("field");
const ctx = canvas.getContext("2d");
let width = 0;
let height = 0;
let pointer = { x: 0, y: 0, active: false };
let particles = [];
let modeIndex = 0;

const modes = ["day", "night"];

function setProfile() {
  document.getElementById("profileName").textContent = profile.name;
  document.getElementById("profileSummary").textContent = profile.summary;
  document.getElementById("githubLink").href = profile.github;
  document.getElementById("emailLink").href = profile.email;

  document.getElementById("heroMetrics").innerHTML = profile.metrics
    .map(([value, label]) => `<div class="metric"><strong>${value}</strong><span>${label}</span></div>`)
    .join("");
}

function renderRepos(filter = "all") {
  const grid = document.getElementById("repoGrid");
  grid.innerHTML = repositories
    .filter((repo) => filter === "all" || repo.tag === filter)
    .map(
      (repo) => `
        <a class="repo reveal" href="${repo.url}">
          <div>
            <div class="repo__top">
              <h3>${repo.name}</h3>
              <span class="repo__tag">${repo.tag}</span>
            </div>
            <p>${repo.summary}</p>
          </div>
          <div class="repo__meta">
            <span>${repo.stack}</span>
            <span>${repo.signal}</span>
          </div>
        </a>
      `
    )
    .join("");
  observeReveals();
}

function renderMethod() {
  document.getElementById("methodSteps").innerHTML = methodSteps
    .map(([title, bodyText]) => `<li class="reveal"><div><strong>${title}</strong><span>${bodyText}</span></div></li>`)
    .join("");

  document.getElementById("timelineRail").innerHTML = timeline
    .map(
      ([time, title, bodyText]) => `
        <article class="moment reveal">
          <time>${time}</time>
          <h3>${title}</h3>
          <p>${bodyText}</p>
        </article>
      `
    )
    .join("");
}

function typeConsole() {
  const target = document.getElementById("consoleText");
  const text = consoleLines.join("\n");
  let index = 0;

  function tick() {
    target.textContent = text.slice(0, index);
    index += 1;
    if (index <= text.length) window.setTimeout(tick, index % 23 === 0 ? 90 : 16);
  }

  tick();
}

function observeReveals() {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) entry.target.classList.add("is-visible");
      });
    },
    { threshold: 0.12 }
  );

  document.querySelectorAll(".reveal:not(.is-visible)").forEach((el) => observer.observe(el));
}

function resizeCanvas() {
  const ratio = window.devicePixelRatio || 1;
  width = window.innerWidth;
  height = window.innerHeight;
  canvas.width = Math.floor(width * ratio);
  canvas.height = Math.floor(height * ratio);
  canvas.style.width = `${width}px`;
  canvas.style.height = `${height}px`;
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);

  const count = Math.min(84, Math.max(38, Math.floor(width / 18)));
  particles = Array.from({ length: count }, (_, i) => ({
    x: Math.random() * width,
    y: Math.random() * height,
    vx: (Math.random() - 0.5) * 0.34,
    vy: (Math.random() - 0.5) * 0.34,
    r: i % 9 === 0 ? 2.2 : 1.25,
  }));
}

function drawField() {
  ctx.clearRect(0, 0, width, height);
  const styles = getComputedStyle(body);
  const ink = styles.getPropertyValue("--ink").trim();
  const accent = styles.getPropertyValue("--accent").trim();
  const accent2 = styles.getPropertyValue("--accent-2").trim();

  particles.forEach((p) => {
    p.x += p.vx;
    p.y += p.vy;
    if (p.x < -20) p.x = width + 20;
    if (p.x > width + 20) p.x = -20;
    if (p.y < -20) p.y = height + 20;
    if (p.y > height + 20) p.y = -20;
  });

  for (let i = 0; i < particles.length; i += 1) {
    for (let j = i + 1; j < particles.length; j += 1) {
      const a = particles[i];
      const b = particles[j];
      const dx = a.x - b.x;
      const dy = a.y - b.y;
      const dist = Math.hypot(dx, dy);
      if (dist < 128) {
        ctx.globalAlpha = (1 - dist / 128) * 0.16;
        ctx.strokeStyle = ink;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.stroke();
      }
    }
  }

  particles.forEach((p, i) => {
    const pull = pointer.active ? Math.max(0, 1 - Math.hypot(pointer.x - p.x, pointer.y - p.y) / 220) : 0;
    ctx.globalAlpha = 0.42 + pull * 0.42;
    ctx.fillStyle = i % 5 === 0 ? accent : i % 7 === 0 ? accent2 : ink;
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r + pull * 2.4, 0, Math.PI * 2);
    ctx.fill();
  });

  ctx.globalAlpha = 1;
  requestAnimationFrame(drawField);
}

function wireInteractions() {
  document.querySelectorAll(".filter").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".filter").forEach((item) => item.classList.remove("is-active"));
      button.classList.add("is-active");
      renderRepos(button.dataset.filter);
    });
  });

  document.getElementById("paletteToggle").addEventListener("click", () => {
    modeIndex = (modeIndex + 1) % modes.length;
    body.classList.toggle("mode-night", modes[modeIndex] === "night");
  });

  window.addEventListener("pointermove", (event) => {
    pointer = { x: event.clientX, y: event.clientY, active: true };
    root.style.setProperty("--cursor-x", `${event.clientX}px`);
    root.style.setProperty("--cursor-y", `${event.clientY}px`);
  });

  window.addEventListener("pointerleave", () => {
    pointer.active = false;
  });

  window.addEventListener("resize", resizeCanvas);
}

setProfile();
renderRepos();
renderMethod();
wireInteractions();
observeReveals();
typeConsole();
resizeCanvas();
drawField();

