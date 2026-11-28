import { requestAPI } from "./api.js";

const cohortForm = document.getElementById("cohortForm");
const filters = document.getElementById("cohortFilters");
const period = document.getElementById("cohortPeriod");
const ages = document.getElementById("cohortAge");
const status = document.getElementById("operationStatus");
const result = document.getElementById("cohortResult");
const searchControl = document.getElementById("cohortSearchControl");
const search = document.getElementById("cohortSearch");
const noMatch = document.getElementById("cohortNoMatch");
const tableWrap = document.getElementById("cohortTableWrap");
const tableRows = document.getElementById("cohortRows");
const reviewForm = document.getElementById("cohortReviewForm");
const reviewControls = document.getElementById("reviewControls");
const threshold = document.getElementById("cohortMinimum");
const buildReview = document.getElementById("buildCohortReview");
const reviewStatus = document.getElementById("cohortReviewStatus");
const reviewResult = document.getElementById("cohortReviewResult");
const download = document.getElementById("downloadCohortReview");
const number = new Intl.NumberFormat();
const percent = new Intl.NumberFormat(undefined, { style: "percent", maximumFractionDigits: 1 });
const maxSelection = 12;
let reviewExport;

function setStatus(message, isError = false, target = status) {
  target.textContent = message;
  target.classList.toggle("status-error", isError);
  target.hidden = !message;
}

function selectedClasses() {
  return [...tableRows.querySelectorAll("input:checked")].map((input) => input.value);
}

function syncSelection() {
  const count = selectedClasses().length;
  document.getElementById("cohortSelection").textContent = `${count} of ${maxSelection} selected`;
  buildReview.disabled = count === 0;
  for (const input of tableRows.querySelectorAll("input")) {
    input.disabled = count === maxSelection && !input.checked;
  }
}

function invalidateReview() {
  reviewExport = undefined;
  reviewResult.hidden = true;
  setStatus("", false, reviewStatus);
}

function selectedScope() {
  return {
    cycle_id: period.value ? Number(period.value) : null,
    age_band: ages.value,
  };
}

function filterClasses() {
  const term = search.value.trim().toLowerCase();
  let visible = 0;
  for (const row of tableRows.rows) {
    row.hidden = !row.dataset.drugClass.toLowerCase().includes(term);
    if (!row.hidden) visible += 1;
  }
  tableWrap.hidden = visible === 0;
  noMatch.hidden = tableRows.rows.length === 0 || visible > 0;
}

function showCohort(data, selected = []) {
  const checkedClasses = new Set(selected);
  document.getElementById("cohortTotal").textContent =
    `${number.format(data.cohort_size)} participants · ${number.format(data.rows.length)} drug classes`;
  tableRows.replaceChildren(...data.rows.map((row) => {
    const line = document.createElement("tr");
    line.dataset.drugClass = row.drug_class;
    const input = document.createElement("input");
    input.type = "checkbox";
    input.value = row.drug_class;
    input.checked = checkedClasses.has(row.drug_class);
    input.setAttribute("aria-label", `Review ${row.drug_class}`);
    line.insertCell().append(input);
    for (const value of [
      row.drug_class,
      number.format(row.participants),
      number.format(row.entries),
      percent.format(row.participants / data.cohort_size),
    ]) {
      line.insertCell().textContent = value;
    }
    return line;
  }));
  searchControl.hidden = data.rows.length === 0;
  reviewForm.hidden = data.rows.length === 0;
  result.hidden = false;
  filterClasses();
  syncSelection();
}

cohortForm.addEventListener("change", () => {
  result.hidden = true;
  invalidateReview();
  setStatus("Filters changed. Analyze the cohort to update the results.");
});

cohortForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (filters.disabled) return;
  const scope = selectedScope();
  const query = new URLSearchParams({ age_band: scope.age_band });
  if (scope.cycle_id !== null) query.set("cycle_id", scope.cycle_id);
  result.hidden = true;
  invalidateReview();
  filters.disabled = true;
  setStatus("Analyzing medication records…");
  try {
    const data = await requestAPI(`medication-cohort?${query}`, "Analyze medication cohort");
    search.value = "";
    showCohort(data);
    setStatus(data.rows.length ? "Select drug classes to build a review list." : "No linked medication entries match these filters.");
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    filters.disabled = false;
  }
});

tableRows.addEventListener("change", () => {
  invalidateReview();
  syncSelection();
});
search.addEventListener("input", filterClasses);
threshold.addEventListener("input", invalidateReview);

reviewForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (reviewControls.disabled || result.hidden) return;
  const classes = selectedClasses();
  if (!classes.length) return;
  const minimum = Number(threshold.value);
  const periodLabel = period.selectedOptions[0].textContent;
  const ageLabel = ages.selectedOptions[0].textContent;
  const scope = selectedScope();
  filters.disabled = true;
  reviewControls.disabled = true;
  tableWrap.inert = true;
  search.disabled = true;
  invalidateReview();
  setStatus("Checking selected classes…", false, reviewStatus);
  try {
    const response = await requestAPI("medication-cohort/review", "Build medication review list", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...scope, drug_classes: classes, minimum_participants: minimum }),
    });
    showCohort(response, classes);
    if (response.review.status === "rejected") {
      setStatus(`${response.review.reason} Select qualifying classes or adjust the minimum.`, true, reviewStatus);
      return;
    }
    reviewExport = { rows: response.review.rows, size: response.cohort_size, minimum, periodLabel, ageLabel };
    document.getElementById("cohortReviewSummary").textContent =
      `${response.review.rows.length} drug classes passed the review rule of ${number.format(minimum)} participants per class.`;
    const reviewedClasses = document.getElementById("cohortReviewedClasses");
    reviewedClasses.replaceChildren(...response.review.rows.map((row) => {
      const item = document.createElement("li");
      item.textContent = `${row.drug_class} · ${number.format(row.participants)} participants · ${number.format(row.entries)} entries`;
      return item;
    }));
    reviewResult.hidden = false;
    setStatus("Review list is ready to download.", false, reviewStatus);
  } catch (error) {
    setStatus(error.message, true, reviewStatus);
  } finally {
    filters.disabled = false;
    reviewControls.disabled = false;
    tableWrap.inert = false;
    search.disabled = false;
  }
});

function csvField(value) {
  let text = String(value);
  if (/^\s*[=+@-]/.test(text) || /^[\t\r\n]/.test(text)) text = `'${text}`;
  return `"${text.replaceAll('"', '""')}"`;
}

download.addEventListener("click", () => {
  if (!reviewExport) return;
  const { rows, size, minimum, periodLabel, ageLabel } = reviewExport;
  const lines = [
    ["Survey period", "Age group", "Cohort participants", "Minimum participants", "Drug class", "Participants", "Medication entries"],
    ...rows.map((row) => [periodLabel, ageLabel, size, minimum, row.drug_class, row.participants, row.entries]),
  ];
  const url = URL.createObjectURL(new Blob([lines.map((line) => line.map(csvField).join(",")).join("\r\n")], { type: "text/csv;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = "carecenter-medication-review.csv";
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});

async function initializeCohort() {
  try {
    const { periods } = await requestAPI("medication-cohort/options", "Load cohort survey periods");
    for (const { cycle_id, period_label } of periods) period.add(new Option(period_label, cycle_id));
    setStatus("Choose a survey period and age group to begin.");
  } catch {
    setStatus("Survey periods could not load. You can still analyze all periods.", true);
  } finally {
    filters.disabled = false;
  }
}

initializeCohort();
