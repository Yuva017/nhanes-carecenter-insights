import { requestAPI } from "./api.js";

const form = document.getElementById("validationForm");
const exercise = document.getElementById("validationExercise");
const run = document.getElementById("validationRun");
const status = document.getElementById("validationStatus");
const results = document.getElementById("validationResults");
const source = document.getElementById("validationSource");
const outputs = document.getElementById("validationOutputs");

function setStatus(message, isError = false) {
  status.textContent = message;
  status.hidden = !message;
  status.classList.toggle("status-error", isError);
}

function element(tag, value) {
  const node = document.createElement(tag);
  if (value !== undefined) node.textContent = value;
  return node;
}

function formatValue(value) {
  if (value === null) return "NULL";
  return Array.isArray(value) ? JSON.stringify(value) : String(value);
}

function resultDetails(output) {
  const details = element("details");
  details.className = "validation-output";
  const description = output.columns.length
    ? output.columns.map((column) => column.replaceAll("_", " ")).join(", ")
    : "PostgreSQL messages";
  details.append(element("summary", `Statement ${output.statement} · ${description}`));
  for (const notice of output.notices) details.append(element("pre", notice));
  if (!output.columns.length) return details;
  if (!output.rows.length) {
    details.append(element("p", "No rows returned."));
    return details;
  }

  const scroll = element("div");
  scroll.className = "validation-table-scroll";
  scroll.tabIndex = 0;
  scroll.setAttribute("role", "region");
  scroll.setAttribute("aria-label", `Rows from statement ${output.statement}`);
  const table = element("table");
  table.className = "validation-table";
  const header = table.createTHead().insertRow();
  for (const column of output.columns) {
    const heading = element("th", column.replaceAll("_", " "));
    heading.scope = "col";
    header.append(heading);
  }

  const body = table.createTBody();
  for (const row of output.rows) {
    const line = body.insertRow();
    for (const value of row) line.insertCell().textContent = formatValue(value);
  }
  scroll.append(table);
  details.append(scroll);
  if (output.truncated) details.append(element("p", `Showing the first ${output.rows.length} rows.`));
  return details;
}

exercise.addEventListener("change", () => {
  results.hidden = true;
  setStatus("");
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (run.disabled) return;
  const label = exercise.selectedOptions[0].textContent;
  run.disabled = true;
  exercise.disabled = true;
  results.hidden = true;
  setStatus("Running validation in PostgreSQL…");
  try {
    const data = await requestAPI(`validation/${exercise.value}`, `Validation · ${label}`, { method: "POST" });
    source.textContent = `database/validation/${data.file}`;
    outputs.replaceChildren(...data.outputs.map(resultDetails));
    const firstResult = outputs.querySelector("details");
    if (firstResult) firstResult.open = true;
    results.hidden = false;
    setStatus(`${data.statements_executed} statements executed. Expand the results below or view the SQL in the activity pane.`);
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    exercise.disabled = false;
    run.disabled = false;
  }
});

run.disabled = false;
