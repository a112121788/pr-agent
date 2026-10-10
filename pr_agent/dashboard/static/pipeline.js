const prUrl = new URLSearchParams(location.search).get("url") || "";
const slot = document.querySelector("#run-slot");
const statusLine = document.querySelector("#dock-status");
const reviewButton = document.querySelector("#actions button[value='review']");
let reviewing = false;
let inflight = false;
let stamp = "";

function paint(status) {
  slot.replaceChildren();
  const active = status === "排队" || status === "运行中";
  if (active) {
    const icon = document.createElement("span");
    icon.className = "run-mark";
    icon.setAttribute("aria-label", "执行中");
    slot.append(icon);
  }
  if (status) {
    const text = document.createElement("span");
    text.className = "run-status";
    text.textContent = status;
    slot.append(text);
  }
  syncReview();
}

function syncReview() {
  const busy = reviewing || inflight;
  reviewButton.disabled = busy;
  reviewButton.textContent = busy ? "审查中" : "审查";
}

function link(url, label) {
  const anchor = document.createElement("a");
  if (String(url).startsWith("https://")) {
    anchor.href = url;
    anchor.target = "_blank";
    anchor.rel = "noopener noreferrer";
  }
  anchor.textContent = label;
  return anchor;
}

function renderIdentity(identity) {
  const root = document.querySelector("#identity");
  root.replaceChildren();
  if (!identity || !identity.named) {
    const lead = document.createElement("p");
    lead.className = "lead";
    lead.append(link(identity && identity.gitee_url, "在 Gitee 打开这张拉取请求"));
    root.append(lead);
    return;
  }
  const title = document.createElement("p");
  title.className = "identity";
  const number = document.createElement("span");
  number.textContent = "#" + identity.number;
  title.append(number, document.createTextNode(identity.title || ""));
  const lead = document.createElement("p");
  lead.className = "lead";
  lead.append(document.createTextNode((identity.meta || "") + " · "), link(identity.gitee_url, "在 Gitee 打开"));
  root.append(title, lead);
}

function renderPipeline(data) {
  if (data.stamp && data.stamp === stamp) return;
  stamp = data.stamp || "";
  const y = window.scrollY;
  const box = document.querySelector("#pipeline");
  box.replaceChildren();
  const hint = document.createElement("p");
  hint.className = "hint";
  hint.textContent = data.hint || "";
  const steps = document.createElement("ol");
  steps.className = "steps";
  for (const step of data.steps || []) {
    const item = document.createElement("li");
    if (step.done) item.classList.add("done");
    if (step.current) item.classList.add("current");
    item.textContent = step.name;
    steps.append(item);
  }
  const cards = document.createElement("section");
  cards.className = "cards";
  const messages = data.messages || [];
  if (!messages.length) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = "Gitee 上还没有评论。用下方的审查、建议或状态开始。";
    cards.append(empty);
  }
  for (const item of messages) {
    const card = document.createElement("article");
    card.className = "card";
    const header = document.createElement("header");
    header.className = "card-top";
    const kind = document.createElement("strong");
    kind.textContent = item.kind || "";
    const stage = document.createElement("span");
    stage.className = "stage";
    stage.textContent = item.stage || "";
    header.append(kind, stage);
    card.append(header);
    if (item.meta) {
      const meta = document.createElement("small");
      meta.textContent = item.meta;
      card.append(meta);
    }
    const body = document.createElement("div");
    body.innerHTML = item.html || "";
    card.append(body);
    cards.append(card);
  }
  box.append(hint, steps, cards);
  window.scrollTo(0, y);
}

async function loadPipeline() {
  if (!prUrl || document.hidden) return;
  const response = await fetch("/dashboard/api/pr?url=" + encodeURIComponent(prUrl));
  if (!response.ok) {
    statusLine.textContent = "流水线没有读到，请再试一次";
    return;
  }
  const data = await response.json();
  reviewing = Boolean(data.reviewing);
  renderIdentity(data.identity);
  renderPipeline(data);
  syncReview();
}

async function watchJob(jobId) {
  const timer = setInterval(async () => {
    try {
      const response = await fetch("/dashboard/api/jobs/" + jobId);
      if (!response.ok) return;
      const job = await response.json();
      paint(job.status);
      if (job.status !== "排队" && job.status !== "运行中") {
        clearInterval(timer);
        inflight = false;
        await loadPipeline();
        syncReview();
      }
    } catch (_error) {
      /* keep the icon until the next tick */
    }
  }, 2000);
}

document.querySelector("#actions").addEventListener("submit", async (event) => {
  event.preventDefault();
  const command = event.submitter && event.submitter.value;
  if (!command || !prUrl || inflight) return;
  inflight = command === "review";
  paint("排队");
  statusLine.textContent = "已提交，正在更新流水线";
  const response = await fetch("/dashboard/api/run", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({pr_url: prUrl, command}),
  });
  if (!response.ok) {
    inflight = false;
    paint("失败");
    statusLine.textContent = "提交没有成功，请再试一次";
    return;
  }
  const job = await response.json();
  paint(job.status);
  statusLine.textContent = "任务已进入流水线";
  if (job.status === "排队" || job.status === "运行中") watchJob(job.job_id);
  else inflight = false;
  await loadPipeline();
});

document.querySelector("#verdicts").addEventListener("submit", async (event) => {
  event.preventDefault();
  const verdict = event.submitter && event.submitter.value;
  if (!verdict || !prUrl) return;
  paint("排队");
  const response = await fetch("/dashboard/api/verdict", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({pr_url: prUrl, verdict}),
  });
  paint(response.ok ? "完成" : "失败");
  if (response.ok) await loadPipeline();
});

setInterval(loadPipeline, 2000);
loadPipeline();
