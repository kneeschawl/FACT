// popup.js

const scanBtn = document.getElementById("scan-btn");
const statusMsg = document.getElementById("status-msg");
const statusDot = document.getElementById("status-dot");
const resultsDiv = document.getElementById("results");
const rawJson = document.getElementById("raw-json");
const rawToggle = document.getElementById("raw-toggle");
const rawBtn = document.getElementById("raw-btn");

const BACKEND = "http://localhost:5000";

// Check backend health on load
async function checkBackend() {
  try {
    const r = await fetch(`${BACKEND}/health`, { signal: AbortSignal.timeout(2000) });
    if (r.ok) {
      statusDot.className = "status-dot connected";
      statusMsg.textContent = "Backend connected ✓";
    } else throw new Error();
  } catch {
    statusDot.className = "status-dot error";
    statusMsg.textContent = "⚠ Backend offline — run backend.py first";
  }
}
checkBackend();

// Toggle raw JSON
rawBtn.addEventListener("click", () => {
  const visible = rawJson.style.display === "block";
  rawJson.style.display = visible ? "none" : "block";
  rawBtn.textContent = visible ? "{ } raw json" : "✕ hide json";
});

// Main scan
scanBtn.addEventListener("click", async () => {
  scanBtn.disabled = true;
  resultsDiv.style.display = "none";
  rawToggle.style.display = "none";
  rawJson.style.display = "none";
  resultsDiv.innerHTML = "";
  statusMsg.innerHTML = `<span class="spinner"></span>Scraping page...`;

  try {
    // 1. Get active tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    // 2. Inject content script message
    const scrapeResult = await chrome.tabs.sendMessage(tab.id, { action: "scrape" });

    if (!scrapeResult?.success) throw new Error("Scrape failed");

    statusMsg.innerHTML = `<span class="spinner"></span>Running NER analysis...`;

    // 3. Send to Python backend
    const response = await fetch(`${BACKEND}/extract`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(scrapeResult.data)
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.error || `Backend error ${response.status}`);
    }

    const nerResult = await response.json();

    // 4. Render results
    renderResults(nerResult);
    rawJson.textContent = JSON.stringify(nerResult, null, 2);
    rawToggle.style.display = "block";
    statusMsg.textContent = `✓ Extracted ${countEntities(nerResult)} entities`;

  } catch (err) {
    statusMsg.textContent = "";
    resultsDiv.innerHTML = `<div class="error-box">❌ ${err.message}</div>`;
    resultsDiv.style.display = "block";
  } finally {
    scanBtn.disabled = false;
  }
});

function countEntities(r) {
  return (r.brands?.length || 0) + (r.prices?.length || 0) +
    (r.discounts?.length || 0) + (r.urgency_texts?.length || 0) +
    (r.other_entities?.length || 0);
}

function renderResults(data) {
  resultsDiv.innerHTML = "";

  const sections = [
    {
      key: "brands", label: "BRANDS & PRODUCTS",
      cls: "brand-header", tagCls: "brand", icon: "🏷"
    },
    {
      key: "prices", label: "PRICES",
      cls: "price-header", tagCls: "price", icon: "💰"
    },
    {
      key: "discounts", label: "DISCOUNTS & OFFERS",
      cls: "discount-header", tagCls: "discount", icon: "🔖"
    },
    {
      key: "urgency_texts", label: "URGENCY / CTA TEXT",
      cls: "urgency-header", tagCls: "urgency", icon: "⚡"
    },
    {
      key: "other_entities", label: "OTHER ENTITIES",
      cls: "other-header", tagCls: "other", icon: "📌"
    }
  ];

  for (const sec of sections) {
    const items = data[sec.key] || [];
    const card = document.createElement("div");
    card.className = "card";

    card.innerHTML = `
      <div class="card-header ${sec.cls}">
        <span class="dot"></span>
        ${sec.icon} ${sec.label}
        <span style="margin-left:auto;opacity:0.5;">${items.length}</span>
      </div>
      <div class="card-body">
        ${items.length === 0
          ? '<span class="empty">None detected</span>'
          : `<div class="tag-list">
              ${items.map(item => `
                <span class="tag ${sec.tagCls}">
                  ${escHtml(item.text || item)}
                  ${item.confidence !== undefined
                    ? `<span class="confidence">${Math.round(item.confidence * 100)}%</span>`
                    : ""}
                </span>
              `).join("")}
            </div>`
        }
      </div>`;

    resultsDiv.appendChild(card);
  }

  resultsDiv.style.display = "flex";
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
