import { apiURL } from "./api.js";

const status = document.getElementById("dashboardStatus");

async function loadChartData(name) {
  const response = await fetch(apiURL(`charts/${name}`));
  if (!response.ok) {
    throw new Error(`${name} returned HTTP ${response.status}`);
  }

  const rows = await response.json();
  if (!Array.isArray(rows)) {
    throw new Error(`${name} must contain an array`);
  }
  return rows;
}

function requireRows(rows, name) {
  if (rows.length === 0) {
    throw new Error(`${name} contains no chart data`);
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

function createCoverageChart(rows) {
  new Chart(document.getElementById("coverageChart"), {
    type: "line",
    data: {
      labels: rows.map((row) => row.period_label),
      datasets: [
        { label: "Loaded participants", data: rows.map((row) => row.participants), borderColor: "#253d56" },
        { label: "With BMI", data: rows.map((row) => row.with_bmi), borderColor: "#26766e" },
        { label: "With systolic BP", data: rows.map((row) => row.with_systolic), borderColor: "#b06b26" },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      scales: { y: { beginAtZero: true, title: { display: true, text: "Participants" } } },
    },
  });
}

function createSystolicChart(rows) {
  new Chart(document.getElementById("systolicChart"), {
    type: "bar",
    data: {
      labels: rows.map((row) => row.age_group),
      datasets: [{
        label: "Average systolic BP",
        data: rows.map((row) => row.avg_systolic),
        backgroundColor: "#3b82b4",
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: { y: { beginAtZero: true, title: { display: true, text: "mmHg" } } },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: { afterLabel: ({ dataIndex }) => `Records: ${rows[dataIndex].observations}` },
        },
      },
    },
  });
}

function createMedicationCoverageChart(rows) {
  const bandColors = {
    "No linked entries": "#aebbc4",
    "1 entry": "#26766e",
    "2 entries": "#3b82b4",
    "3+ entries": "#b06b26",
  };
  new Chart(document.getElementById("medicationCoverageChart"), {
    type: "doughnut",
    data: {
      labels: rows.map((row) => row.entry_band),
      datasets: [{
        label: "Participants",
        data: rows.map((row) => row.participants),
        backgroundColor: rows.map((row) => bandColors[row.entry_band]),
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "bottom" } },
    },
  });
}

async function initializeDashboard() {
  const charts = [
    ["bmi_by_age_cycle", "bmiChart", createBmiChart],
    ["meds_by_drug_class", "drugChart", createDrugChart],
    ["dietary_by_cycle", "dietaryChart", createDietaryChart],
    ["coverage_by_cycle", "coverageChart", createCoverageChart],
    ["systolic_by_age", "systolicChart", createSystolicChart],
    ["medication_records_per_participant", "medicationCoverageChart", createMedicationCoverageChart],
  ];
  const outcomes = await Promise.allSettled(charts.map(async ([dataset, canvas, draw]) => {
    try {
      draw(requireRows(await loadChartData(dataset), dataset));
    } catch (error) {
      const message = document.createElement("p");
      message.className = "chart-unavailable";
      message.textContent = "Chart data is currently unavailable.";
      document.getElementById(canvas).replaceWith(message);
      throw error;
    }
  }));
  const ready = outcomes.filter(({ status }) => status === "fulfilled").length;
  status.textContent = ready === charts.length
    ? "Charts loaded from PostgreSQL."
    : `${ready} of ${charts.length} charts loaded. Some datasets are unavailable.`;
  status.classList.toggle("status-error", ready === 0);
}

initializeDashboard();
