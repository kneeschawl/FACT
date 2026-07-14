// content.js — runs inside the active tab, scrapes visible product text

function scrapePageData() {
  const data = {};

  // --- Page Title ---
  data.title = document.title || "";

  // --- Full visible text (cleaned) ---
  // Remove scripts, styles, nav, footer to reduce noise
  const clone = document.body.cloneNode(true);
  ["script", "style", "nav", "footer", "header", "noscript", "svg"].forEach(tag => {
    clone.querySelectorAll(tag).forEach(el => el.remove());
  });
  data.full_text = (clone.innerText || clone.textContent || "")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 8000); // cap at 8k chars for NER

  // --- Structured hints (help NER focus) ---

  // Price-like elements
  const priceSelectors = [
    "[class*='price']", "[class*='Price']",
    "[id*='price']", "[id*='Price']",
    "[class*='cost']", "[class*='amount']",
    "[data-price]", ".a-price", ".price-box"
  ];
  data.price_hints = [];
  priceSelectors.forEach(sel => {
    document.querySelectorAll(sel).forEach(el => {
      const t = el.innerText?.trim();
      if (t) data.price_hints.push(t);
    });
  });
  data.price_hints = [...new Set(data.price_hints)].slice(0, 10);

  // Discount / badge elements
  const discountSelectors = [
    "[class*='discount']", "[class*='Discount']",
    "[class*='badge']", "[class*='Badge']",
    "[class*='sale']", "[class*='Sale']",
    "[class*='saving']", "[class*='offer']",
    "[class*='deal']", "[class*='promo']"
  ];
  data.discount_hints = [];
  discountSelectors.forEach(sel => {
    document.querySelectorAll(sel).forEach(el => {
      const t = el.innerText?.trim();
      if (t) data.discount_hints.push(t);
    });
  });
  data.discount_hints = [...new Set(data.discount_hints)].slice(0, 10);

  // Brand / product name area
  const brandSelectors = [
    "[class*='brand']", "[class*='Brand']",
    "[class*='manufacturer']", "[class*='vendor']",
    "h1", "[class*='product-title']", "[class*='product_title']",
    "[id*='product-title']", "[itemprop='brand']", "[itemprop='name']"
  ];
  data.brand_hints = [];
  brandSelectors.forEach(sel => {
    document.querySelectorAll(sel).forEach(el => {
      const t = el.innerText?.trim();
      if (t) data.brand_hints.push(t);
    });
  });
  data.brand_hints = [...new Set(data.brand_hints)].slice(0, 10);

// Urgency / FOMO / CTA text
const urgencySelectors = [
  "[class*='urgent']", "[class*='hurry']",
  "[class*='countdown']", "[class*='timer']",
  "[class*='limited']", "[class*='stock']",
  "[class*='cta']", "[class*='banner']",
  "[class*='flash']", "[class*='deal']",
  // --- ADDED FOR EXPERIMENT TARGETS ---
  ".quantity-content-default",            // Exact target class discovered via inspection
  "[class*='quantity-content']",          // Substring matching variations of this container
  "[class*='product-info-stock']",        // Common e-commerce desktop structures
  ".pdp-mod-product-info-stock"           // Standard regional marketplace layout wrapper
];

data.urgency_hints = [];
urgencySelectors.forEach(sel => {
  try {
    document.querySelectorAll(sel).forEach(el => {
      const t = el.innerText?.trim();
      // Ensure we catch valid text and don't push massive page text blobs accidentally
      if (t && t.length > 0 && t.length < 150) { 
        data.urgency_hints.push(t);
      }
    });
  } catch (err) {
    console.error(`Selector processing exception for (${sel}):`, err);
  }
});

// Remove duplicates and limit the payload slice array to 10 indices
data.urgency_hints = [...new Set(data.urgency_hints)].slice(0, 10);

  // Product images alt text (often contains brand/product info)
  data.image_alts = [];
  document.querySelectorAll("img[alt]").forEach(img => {
    const a = img.alt?.trim();
    if (a && a.length > 3) data.image_alts.push(a);
  });
  data.image_alts = [...new Set(data.image_alts)].slice(0, 10);

  // Meta tags
  data.meta = {};
  document.querySelectorAll("meta").forEach(m => {
    const name = m.getAttribute("name") || m.getAttribute("property");
    const content = m.getAttribute("content");
    if (name && content) data.meta[name] = content;
  });

  // Page URL
  data.url = window.location.href;

  return data;
}

// Listen for message from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "scrape") {
    const pageData = scrapePageData();
    sendResponse({ success: true, data: pageData });
  }
  return true; // keep channel open for async
});
