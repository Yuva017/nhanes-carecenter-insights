import { requestAPI } from "./api.js";

const buttons = [...document.querySelectorAll("[data-operation]")];
const status = document.getElementById("operationStatus");
const result = document.getElementById("operationResult");

function paintOperation(operation) {
  for (const side of ["before", "after"]) {
    document.getElementById(`${side}Status`).textContent = operation[side].status;
    document.getElementById(`${side}Count`).textContent = operation[side].medication_count;
  }
  document.getElementById("triggerResult").textContent = operation.trigger;
  document.getElementById("operationSteps").replaceChildren(...operation.steps.map((step) => {
    const item = document.createElement("li");
    item.textContent = step;
    return item;
  }));
  result.hidden = false;
}

async function runOperation(name, label) {
  buttons.forEach((button) => { button.disabled = true; });
  status.textContent = "Running database operation…";
  status.classList.remove("status-error");
  result.hidden = true;
  try {
    const operation = await requestAPI(`operations/medications/${name}`, label, { method: "POST" });
    paintOperation(operation);
    status.textContent = "Operation complete. The temporary session data has been discarded.";
  } catch (error) {
    status.textContent = error.message;
    status.classList.add("status-error");
  } finally {
    buttons.forEach((button) => { button.disabled = false; });
  }
}

buttons.forEach((button) => {
  button.addEventListener("click", () => runOperation(button.dataset.operation, button.textContent.trim()));
});
