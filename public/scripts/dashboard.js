const status = document.getElementById("dashboardStatus");

async function loadJSON(name) {
  const response = await fetch(`data/${name}.json`);
  if (!response.ok) {
    throw new Error(`${name}.json returned HTTP ${response.status}`);
  }

  const rows = await response.json();
  if (!Array.isArray(rows)) {
    throw new Error(`${name}.json must contain an array`);
  }
  return rows;
}

function requireRows(rows, name) {
  if (rows.length === 0) {
    throw new Error(`${name}.json contains no chart data`);
  }
  return rows;
}

function createBmiChart(rows) {
  const ageOrder = ["under 20", "20-39", "40-59", "60+"];
  const ageGroups = [...new Set(rows.map((row) => row.age_group))].sort(
    (a, b) => ageOrder.indexOf(a) - ageOrder.indexOf(b),
  );
  const periods = [...new Set(rows.map((row) => row.period_label))];
  const filter = document.getElementById("bmiPeriodFilter");

  for (const period of periods) {
    const option = document.createElement("option");
    option.value = period;
    option.textContent = period;
    filter.append(option);
  }

  const chart = new Chart(document.getElementById("bmiChart"), {
    type: "bar",
    data: { labels: ageGroups, datasets: [] },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      scales: {
        y: { beginAtZero: true, title: { display: true, text: "BMI" } },
      },
    },
  });

  function update() {
    const selectedPeriod = filter.value;
    const visiblePeriods = selectedPeriod ? [selectedPeriod] : periods;
    chart.data.datasets = visiblePeriods.map((period, index) => ({
      label: period,
      data: ageGroups.map(
        (ageGroup) =>
          rows.find(
            (row) => row.period_label === period && row.age_group === ageGroup,
          )?.avg_bmi ?? null,
      ),
      backgroundColor: [
        "rgba(31, 119, 111, 0.78)",
        "rgba(59, 130, 180, 0.78)",
        "rgba(217, 139, 54, 0.78)",
        "rgba(129, 97, 166, 0.78)",
      ][index % 4],
    }));
    chart.update();
  }

  filter.addEventListener("change", update);
  update();
}

function createDrugChart(rows) {
  const search = document.getElementById("drugSearch");
  const limit = document.getElementById("drugLimit");
  const chart = new Chart(document.getElementById("drugChart"), {
    type: "bar",
    data: { labels: [], datasets: [{ label: "Medication entries", data: [] }] },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { beginAtZero: true, title: { display: true, text: "Entries" } },
      },
    },
  });

  function update() {
    const query = search.value.trim().toLocaleLowerCase();
    const maxRows = limit.value === "all" ? rows.length : Number(limit.value);
    const visibleRows = rows
      .filter((row) =>
        String(row.drug_class ?? "Unclassified")
          .toLocaleLowerCase()
          .includes(query),
      )
      .slice(0, maxRows);
    chart.data.labels = visibleRows.map(
      (row) => row.drug_class ?? "Unclassified",
    );
    chart.data.datasets[0].data = visibleRows.map((row) => row.entry_count);
    chart.update();
  }

  search.addEventListener("input", update);
  limit.addEventListener("change", update);
  update();
}

function createDietaryChart(rows) {
  new Chart(document.getElementById("dietaryChart"), {
    type: "bar",
    data: {
      labels: rows.map((row) => row.period_label),
      datasets: [
        {
          label: "Participants",
          data: rows.map((row) => row.participants),
          backgroundColor: "rgba(59, 130, 180, 0.72)",
          yAxisID: "participants",
        },
        {
          type: "line",
          label: "Average dietary amount",
          data: rows.map((row) => row.avg_dietary_amount),
          borderColor: "rgb(217, 139, 54)",
          backgroundColor: "rgb(217, 139, 54)",
          tension: 0.25,
          yAxisID: "amount",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      scales: {
        participants: {
          beginAtZero: true,
          position: "left",
          title: { display: true, text: "Participants" },
        },
        amount: {
          beginAtZero: true,
          position: "right",
          grid: { drawOnChartArea: false },
          title: { display: true, text: "Average amount" },
        },
      },
    },
  });
}

async function initializeDashboard() {
  const [bmi, drugs, dietary] = await Promise.all([
    loadJSON("bmi_by_age_cycle"),
    loadJSON("meds_by_drug_class"),
    loadJSON("dietary_by_cycle"),
  ]);

  createBmiChart(requireRows(bmi, "bmi_by_age_cycle"));
  createDrugChart(requireRows(drugs, "meds_by_drug_class"));
  createDietaryChart(requireRows(dietary, "dietary_by_cycle"));
  status.textContent = "Charts loaded from the database exports.";
}

initializeDashboard().catch((error) => {
  status.textContent =
    `Could not load chart data: ${error.message}. ` +
    "Run `python -m src.analytics.export` after loading the database.";
  status.classList.add("status-error");
  console.error("Dashboard initialization failed:", error);
});
