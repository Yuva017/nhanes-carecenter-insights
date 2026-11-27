// Render serves the dashboard and API together. GitHub Pages calls that same API.
const pagesHost = "yuva017.github.io";
const apiBase = window.location.hostname === pagesHost
  ? new URL("https://nhanes-carecenter-insights.onrender.com/")
  : new URL("../", import.meta.url);

export function apiURL(path) {
  return new URL(`api/${path}`, apiBase);
}
