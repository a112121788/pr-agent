"""Build the cockpit homepage payload. The browser renders it."""

from pr_agent.dashboard.actions import open_pulls
from pr_agent.dashboard.store import FactoryStore

_STAGES = ("受理", "取证", "判定", "汇入")


def home_view(store: FactoryStore, pulls_for=None) -> dict:
    """Return registered repositories and whether each pull request is under review."""
    if pulls_for is None:
        pulls_for = open_pulls
    running = store.active_reviews()
    repos = []
    for owner, repo in store.repos():
        error = ""
        try:
            pulls = pulls_for(owner, repo)
        except Exception as exc:
            pulls = []
            error = str(exc)
        rows = []
        for item in pulls:
            url = item.get("url") or ""
            job = running.get(url)
            rows.append({
                "number": item.get("number"),
                "title": item.get("title") or "",
                "url": url,
                "reviewing": job is not None,
                "job_id": job[0] if job else None,
                "status": job[1] if job else "",
            })
        repos.append({"owner": owner, "repo": repo, "error": error, "pulls": rows})
    counts = {stage: 0 for stage in _STAGES}
    for record in store.latest():
        if record.stage in counts:
            counts[record.stage] += 1
    return {"counts": counts, "repos": repos}
