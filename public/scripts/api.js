import { recordSQLActivity } from "./sql_activity.js";

// Render serves the dashboard and API together. GitHub Pages calls that same API.
const pagesHost = "yuva017.github.io";
const apiBase = window.location.hostname === pagesHost
  ? new URL("https://nhanes-carecenter-insights.onrender.com/")
  : new URL("../", import.meta.url);

export function apiURL(path) {
  return new URL(`api/${path}`, apiBase);
}

export async function requestAPI(path, label, options) {
  const url = apiURL(path);
  url.searchParams.set("include_sql", "true");
  let queries = [];
  let failed = true;
  try {
    const response = await fetch(url, options);
    const payload = await response.json();
    queries = Array.isArray(payload?.queries) ? payload.queries : [];
    if (!response.ok) {
      throw new Error(typeof payload?.detail === "string" ? payload.detail : `HTTP ${response.status}`);
    }
    failed = false;
    return payload;
  } finally {
    recordSQLActivity(label, queries, failed);
  }
}
