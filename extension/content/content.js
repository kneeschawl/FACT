function parsePriceString(raw) {
  if (!raw) return "";
  const cleaned = raw.replace(/,/g, "");
  const match = cleaned.match(/\d+(\.\d+)?/);
  return match ? match[0] : "";
}

const URGENCY_PATTERNS = [
  /almost sold out/i,
  /sold out soon/i,
  /only\s*\d+\s*(left|item|piece|unit)/i,
  /hurry/i,
  /limited\s*(stock|stocks|quantity|time|edition)/i,
  /selling fast/i,
  /low(\s+in)?\s*stock/i,
  /last\s*chance/i,
  /ends?\s*in\s*\d/i,
  /flash\s*sale/i,
  // /buy\s*now/i,
  /while\s*(stock|supplies)\s*last/i,
];

function findUrgencyTextByPattern() {
  // Leaf elements only (no children) — badges/labels are short single-purpose
  // nodes, so this avoids matching giant blocks of unrelated body text.
  const candidates = document.querySelectorAll("div, span, p, small, a, b, strong");
  for (const el of candidates) {
    if (el.children.length > 0) continue;
    const text = el.innerText?.trim();
    if (!text || text.length > 120) continue;
    if (URGENCY_PATTERNS.some((re) => re.test(text))) {
      return text;
    }
  }
  return null;
}

function scrapeProductDetails() {
  const fullBodyText = document.body.innerText || "";
  const pageTitle = document.title || "";
  
  let details = {
    productId: "",
    productName: "",
    anchorPrice: "",
    discountPercentage: "",
    discountedPrice: "",
    urgencyText: "",
    // Rich properties requested by spaCy NER microservice
    fullText: fullBodyText,
    title: pageTitle,
    priceHints: [],
    discountHints: [],
    brandHints: [],
    urgencyHints: [],
    imageAlts: [],
    url: window.location.href
  };

  // Extract raw image alt arrays for brand processing
  document.querySelectorAll("img").forEach((img) => {
    if (img.alt && img.alt.trim().length > 2) {
      details.imageAlts.push(img.alt.trim());
    }
  });

  if (window.location.host.includes("daraz.com.np")) {
    const titleNode = document.querySelector(".pdp-mod-product-info-name");
    const discPriceNode = document.querySelector(".pdp-price_type_normal");
    const origPriceNode = document.querySelector(".pdp-price_type_deleted");
    const pctNode = document.querySelector(".pdp-product-price__discount");
    
    details.productName = titleNode ? titleNode.innerText.trim() : pageTitle;
    details.discountedPrice = discPriceNode ? parsePriceString(discPriceNode.innerText) : "";
    details.anchorPrice = origPriceNode ? parsePriceString(origPriceNode.innerText) : "";
    details.discountPercentage = pctNode ? parsePriceString(pctNode.innerText) : "";
    
    if (discPriceNode) details.priceHints.push(discPriceNode.innerText);
    if (origPriceNode) details.priceHints.push(origPriceNode.innerText);
    if (pctNode) details.discountHints.push(pctNode.innerText);
    if (titleNode) details.brandHints.push(titleNode.innerText);

    const urlMatch = window.location.href.match(/-i(\d+)-s\d+\.html/);
    if (urlMatch) details.productId = urlMatch[1];
  }

  // Scan and append urgency blocks for your custom Regex match patterns
  const urgencyNode = document.querySelector(".pdp-mod-stock, .flash-sale-countdown, [class*='urgency']");
  if (urgencyNode) {
    details.urgencyText = urgencyNode.innerText.trim();
    details.urgencyHints.push(urgencyNode.innerText.trim());
  } else {
    const patternMatch = findUrgencyTextByPattern();
    if (patternMatch) {
      details.urgencyText = patternMatch;
      details.urgencyHints.push(patternMatch);
    }
  }

  return details;
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "FACT_SCRAPE") {
    sendResponse(scrapeProductDetails());
  }
  return true;
});