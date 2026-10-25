const SECTIONS = {
  "India": "National developments selected for relevance and significance.",
  "Kerala": "State news, public affairs and developments from Kerala.",
  "World Affairs": "International developments with wider political and economic significance.",
  "Law": "Courts, legislation, legal institutions and significant judgments.",
  "Politics": "Political developments, labelled by the parties mentioned in each headline."
};
const $ = (selector) => document.querySelector(selector);
let activeSection = "India";
let newsData = null;

function safeDate(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleString("en-IN", { day:"numeric", month:"short", hour:"2-digit", minute:"2-digit" });
}
function escapeHTML(value) {
  return String(value ?? "").replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
}
function politicalLabel(story) {
  const label = story.label || story.party || "";
  return label ? {text: label, type: "party"} : null;
}
function render() {
  $("#section-title").textContent = activeSection;
  $("#section-description").textContent = SECTIONS[activeSection];
  const stories = (newsData?.sections?.[activeSection] || []).slice(0, 12);
  $("#story-count").textContent = stories.length + (stories.length === 1 ? " story" : " stories") + " · maximum 12";
  $("#updated-at").textContent = newsData?.updated_at ? "Updated " + safeDate(newsData.updated_at) : "";
  const container = $("#stories");
  container.innerHTML = "";
  if (!stories.length) {
    container.innerHTML = '<div class="empty">No stories are available for this section yet. The automatic news refresh may still be running, or the source may have returned no matching articles.</div>';
    return;
  }
  for (const story of stories) {
    const card = document.createElement("article");
    card.className = "story-card";
    const label = activeSection === "Politics" ? politicalLabel(story) : null;
    const summary = story.description || "";
    card.innerHTML = `
      <div class="story-top"><span class="source">${escapeHTML(story.source || story.domain || "News source")}</span>${label ? '<span class="tag '+escapeHTML(label.type)+'">'+escapeHTML(label.text)+'</span>' : ""}</div>
      <h2>${escapeHTML(story.title || "Untitled story")}</h2>
      ${summary ? '<p class="story-summary">'+escapeHTML(summary)+'</p>' : ""}
      <div class="story-bottom"><span class="story-date">${escapeHTML(safeDate(story.published || story.seendate))}</span><a class="read-link" href="${escapeHTML(story.url || "#")}" target="_blank" rel="noopener noreferrer">Read report ↗</a></div>`;
    container.appendChild(card);
  }
}
async function loadNews(showStatus = true) {
  const status = $("#status");
  if (showStatus) status.textContent = "Loading the latest briefing…";
  try {
    const response = await fetch("data/news.json?cache=" + Date.now(), {cache:"no-store"});
    if (!response.ok) throw new Error("HTTP " + response.status);
    newsData = await response.json();
    status.textContent = "";
    render();
  } catch (error) {
    status.textContent = "The news file could not be loaded. Once the first automated update has completed, refresh this page.";
    $("#stories").innerHTML = "";
    $("#story-count").textContent = "Briefing unavailable";
  }
}
$("#navigation").addEventListener("click", event => {
  const button = event.target.closest("[data-section]");
  if (!button) return;
  activeSection = button.dataset.section;
  document.querySelectorAll(".nav-link").forEach(item => item.classList.toggle("active", item === button));
  render();
});
$("#refresh-button").addEventListener("click", () => loadNews(true));
loadNews();