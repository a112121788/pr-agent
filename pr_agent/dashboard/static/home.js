const stages = ["受理", "取证", "判定", "汇入"];
const polls = new Map();

function stopPolls() {
  for (const timer of polls.values()) clearInterval(timer);
  polls.clear();
}

function renderCounts(counts) {
  const list = document.querySelector("#counts");
  list.replaceChildren();
  for (const stage of stages) {
    const item = document.createElement("li");
    const name = document.createElement("span");
    name.textContent = stage;
    const value = document.createElement("strong");
    value.textContent = String(counts[stage] || 0);
    item.append(name, value);
    list.append(item);
  }
}

function paint(row, status, command) {
  const slot = row.querySelector(".run-slot");
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
  const review = row.querySelector("[data-command='review']");
  if (!review) return;
  if (command === "review" && active) {
    review.disabled = true;
    review.textContent = "审查中";
    return;
  }
  if (command === "review" && !active) {
    review.disabled = false;
    review.textContent = "审查";
  }
}

function arm(row, jobId, command) {
  if (!jobId || polls.has(String(jobId))) return;
  const timer = setInterval(async () => {
    try {
      const response = await fetch("/dashboard/api/jobs/" + jobId);
      if (!response.ok) return;
      const job = await response.json();
      paint(row, job.status, command);
      if (job.status !== "排队" && job.status !== "运行中") {
        clearInterval(timer);
        polls.delete(String(jobId));
      }
    } catch (_error) {
      /* keep the icon; the next tick retries */
    }
  }, 2000);
  polls.set(String(jobId), timer);
}

async function runCommand(row, command) {
  if (command === "review") paint(row, "排队", command);
  const response = await fetch("/dashboard/api/run", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({pr_url: row.dataset.url, command}),
  });
  if (!response.ok) {
    paint(row, "失败", command);
    return;
  }
  const job = await response.json();
  paint(row, job.status, command);
  if (job.status === "排队" || job.status === "运行中") arm(row, job.job_id, command);
}

function renderPull(pull) {
  const row = document.createElement("li");
  row.className = "pr";
  row.dataset.url = pull.url;
  const link = document.createElement("a");
  if (String(pull.url).startsWith("https://")) {
    link.href = "/dashboard/pr?url=" + encodeURIComponent(pull.url);
  }
  link.textContent = "#" + pull.number + " " + pull.title;
  const slot = document.createElement("span");
  slot.className = "run-slot";
  slot.setAttribute("aria-live", "polite");
  const title = document.createElement("span");
  title.className = "pr-title";
  title.append(link, slot);
  const actions = document.createElement("span");
  actions.className = "pr-actions";
  for (const [command, label, secondary] of [
    ["review", "审查", false],
    ["improve", "建议", true],
    ["status", "状态", true],
  ]) {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.command = command;
    button.textContent = label;
    if (secondary) button.className = "secondary";
    button.addEventListener("click", () => runCommand(row, command));
    actions.append(button);
  }
  row.append(title, actions);
  if (pull.reviewing) {
    paint(row, pull.status || "运行中", "review");
    arm(row, pull.job_id, "review");
  }
  return row;
}

function renderRepo(repo) {
  const section = document.createElement("section");
  section.className = "repo";
  const heading = document.createElement("h2");
  heading.textContent = repo.owner + "/" + repo.repo;
  const form = document.createElement("form");
  form.method = "post";
  form.action = "/dashboard/repos/remove";
  const button = document.createElement("button");
  button.className = "secondary";
  button.type = "submit";
  button.textContent = "移除";
  form.append(button);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const response = await fetch("/dashboard/api/repos/remove", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({owner: repo.owner, repo: repo.repo}),
    });
    if (response.ok) render(await response.json());
  });
  section.append(heading, form);
  if (repo.error) {
    const error = document.createElement("p");
    error.className = "error";
    error.textContent = repo.error;
    section.append(error);
  }
  const list = document.createElement("ul");
  const pulls = repo.pulls || [];
  if (!pulls.length) {
    const empty = document.createElement("li");
    empty.textContent = "没有打开的拉取请求";
    list.append(empty);
  } else {
    for (const pull of pulls) list.append(renderPull(pull));
  }
  section.append(list);
  return section;
}

function render(data) {
  stopPolls();
  const build = document.querySelector(".build");
  if (data.build) build.textContent = "构建 " + data.build;
  renderCounts(data.counts || {});
  const root = document.querySelector("#repos");
  root.replaceChildren();
  const repos = data.repos || [];
  if (!repos.length) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = "还没有登记仓库";
    root.append(empty);
    return;
  }
  for (const repo of repos) root.append(renderRepo(repo));
}

async function loadHome() {
  const response = await fetch("/dashboard/api/home");
  if (response.ok) render(await response.json());
}

document.querySelector("#register").addEventListener("submit", async (event) => {
  event.preventDefault();
  const repo = new FormData(event.currentTarget).get("repo");
  const response = await fetch("/dashboard/api/repos", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({repo}),
  });
  if (!response.ok) return;
  event.currentTarget.reset();
  render(await response.json());
});

document.querySelector("#drive").addEventListener("submit", async (event) => {
  event.preventDefault();
  const response = await fetch("/dashboard/api/drive", {method: "POST"});
  if (response.ok) render(await response.json());
});

loadHome();
