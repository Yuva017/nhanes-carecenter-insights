async function mountSection(id, templatePath) {
  const response = await fetch(new URL(templatePath, import.meta.url));
  if (!response.ok) {
    throw new Error(`Could not load ${templatePath} (HTTP ${response.status})`);
  }
  const template = document.createElement("template");
  template.innerHTML = await response.text();
  document.getElementById(id).replaceChildren(template.content);
}

async function loadCharts() {
  try {
    await mountSection("surveyCharts", "../sections/survey_charts.html");
    await import("./dashboard.js");
  } catch (error) {
    const status = document.getElementById("dashboardStatus");
    status.textContent = "The survey charts could not load. Refresh the page to try again.";
    status.classList.add("status-error");
    console.error(error);
  }
}

async function loadMedicationWorkflow() {
  try {
    await mountSection("medicationWorkflow", "../sections/medication_workflow.html");
    await import("./database_operations.js");
  } catch (error) {
    const message = document.createElement("p");
    message.className = "status status-error operation-status";
    message.textContent = "The medication workflow could not load. Refresh the page to try again.";
    document.getElementById("medicationWorkflow").replaceChildren(message);
    console.error(error);
  }
}

loadCharts();
loadMedicationWorkflow();
