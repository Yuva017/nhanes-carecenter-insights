const panel = document.getElementById("sqlActivity");
const toggle = document.getElementById("sqlActivityToggle");
const minimize = document.getElementById("sqlActivityMinimize");
const clear = document.getElementById("sqlActivityClear");
const history = document.getElementById("sqlActivityHistory");
const empty = document.getElementById("sqlActivityEmpty");
const count = document.getElementById("sqlActivityCount");
const narrowScreen = window.matchMedia("(max-width: 900px)");
const limit = 30;
const dateFormat = new Intl.DateTimeFormat(undefined, { timeStyle: "medium" });

function setExpanded(expanded, restoreFocus = false) {
  panel.hidden = !expanded;
  panel.closest(".dashboard-shell").classList.toggle("sql-pane-open", expanded);
  toggle.setAttribute("aria-expanded", String(expanded));
  toggle.textContent = expanded ? "Hide SQL activity" : "Show SQL activity";
  if (restoreFocus) toggle.focus();
}

function updateCount() {
  const size = history.children.length;
  count.textContent = `${size} recent ${size === 1 ? "request" : "requests"}`;
  empty.hidden = size > 0;
  clear.disabled = size === 0;
}

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

export function recordSQLActivity(label, queries, requestFailed) {
  const statements = queries.filter((query) => typeof query?.sql === "string");
  const group = element("details");
  const heading = element("summary", label);
  const failures = statements.filter((query) => query.status === "failed").length;
  const outcome = requestFailed ? "Request failed" : failures ? "SQL error handled" : "Completed";
  heading.append(element("small", `${outcome} · ${dateFormat.format(new Date())}`));
  group.append(heading);

  if (statements.length === 0) {
    group.append(element("p", "No SQL was captured for this request."));
  }
  for (const { sql, status } of statements) {
    const failed = status === "failed";
    const detail = element("details", undefined, "sql-statement");
    const command = sql.replace(/^(?:--[^\n]*\n\s*)+/, "").split(/\s+/, 1)[0];
    detail.append(element("summary", `${failed ? "Failed" : "Executed"} · ${command}`));
    const block = element("pre");
    block.append(element("code", sql));
    detail.append(block);
    if (statements.length === 1 || failed) detail.open = true;
    group.append(detail);
  }

  group.open = history.children.length === 0 || statements.length > 1 || requestFailed;
  const item = element("li");
  item.append(group);
  history.prepend(item);
  if (history.children.length > limit) history.lastElementChild.remove();
  updateCount();
}

toggle.addEventListener("click", () => {
  setExpanded(panel.hidden);
  if (!panel.hidden && narrowScreen.matches) minimize.focus();
});
minimize.addEventListener("click", () => setExpanded(false, true));
clear.addEventListener("click", () => {
  history.replaceChildren();
  updateCount();
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !panel.hidden && panel.contains(document.activeElement)) {
    setExpanded(false, true);
  }
});
toggle.hidden = false;
setExpanded(!narrowScreen.matches);
updateCount();
