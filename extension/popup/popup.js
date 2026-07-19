document.addEventListener("DOMContentLoaded", () => {
  const landingView = document.getElementById("landingView");
  const outputView = document.getElementById("outputView");
  const auditForm = document.getElementById("auditForm");
  const submitBtn = document.getElementById("submitBtn");
  
  const legendTrigger = document.getElementById("legendTrigger");
  const legendCard = document.getElementById("legendCard");
  
  const complaintYesBtn = document.getElementById("complaintYesBtn");
  const complaintNoBtn = document.getElementById("complaintNoBtn");

  const settingsBtn = document.getElementById("settingsBtn");
  const settingsPanel = document.getElementById("settingsPanel");
  const darkModeToggle = document.getElementById("darkModeToggle");
  
  let generatedTemplate = "";

  // 0. Theme: load saved preference (falls back to light) and apply immediately
  chrome.storage.local.get(["factTheme"], ({ factTheme }) => {
    const isDark = factTheme === "dark";
    document.body.dataset.theme = isDark ? "dark" : "light";
    darkModeToggle.checked = isDark;
  });

  settingsBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    settingsPanel.classList.toggle("visible");
  });

  // Clicking anywhere else closes the settings panel (same pattern as the legend)
  document.addEventListener("click", () => {
    settingsPanel.classList.remove("visible");
  });

  // Prevent clicks inside the panel (e.g. on the toggle) from closing it immediately
  settingsPanel.addEventListener("click", (e) => e.stopPropagation());

  darkModeToggle.addEventListener("change", () => {
    const isDark = darkModeToggle.checked;
    document.body.dataset.theme = isDark ? "dark" : "light";
    chrome.storage.local.set({ factTheme: isDark ? "dark" : "light" });
  });

  // 1. Core Runtime Processing: Request Content Scraping Framework
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (!tabs[0]) return;
    
    chrome.tabs.sendMessage(tabs[0].id, { action: "FACT_SCRAPE" }, (response) => {
      if (chrome.runtime.lastError || !response) {
        console.warn("FACT Scraper inaccessible or page target not standard e-commerce.");
        return;
      }
      
      // Auto-populate fields dynamically mapped from target DOM state
      if (response.productId) document.getElementById("productId").value = response.productId;
      if (response.productName) document.getElementById("productName").value = response.productName;
      if (response.anchorPrice) document.getElementById("anchorPrice").value = response.anchorPrice;
      if (response.discountPercentage) document.getElementById("discountPercentage").value = response.discountPercentage;
      if (response.discountedPrice) document.getElementById("discountedPrice").value = response.discountedPrice;
      if (response.urgencyText) document.getElementById("urgencyText").value = response.urgencyText;
    });
  });

  // 2. Legend Visbility Interactions
  legendTrigger.addEventListener("click", (e) => {
    e.stopPropagation();
    legendCard.classList.toggle("visible");
  });

  document.addEventListener("click", () => {
    legendCard.classList.remove("visible");
  });

  // 3. Engine Linkage: Compute Metrics and Render Visualizations
  auditForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    submitBtn.disabled = true;
    submitBtn.innerText = "Auditing Pipeline...";

    // Package payload payload structures
    const payload = {
      product_id: document.getElementById("productId").value,
      product_name: document.getElementById("productName").value,
      anchor_price: parseFloat(document.getElementById("anchorPrice").value) || 0,
      discount_percentage: parseFloat(document.getElementById("discountPercentage").value) || 0,
      discounted_price: parseFloat(document.getElementById("discountedPrice").value) || 0,
      urgency_text: document.getElementById("urgencyText").value
    };

    try {
      // Connect to FastAPI microservices configuration
      const response = await fetch("http://localhost:8000/api/v1/analysis", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!response.ok) throw new Error("Backend connection returned internal warning.");
      const result = await response.json();

      // Store pre-populated formal legal template configuration locally
      generatedTemplate = result.complaint_template || "";

      // Swap panel visibility matrices
      landingView.classList.remove("active");
      outputView.classList.add("active");

      // Initialize primary and core score ring gauges via shared layout functions
      new FACTGauge("mainGaugeContainer", { score: result.deceptive_score, size: 120, strokeWidth: 10 });
      new FACTGauge("urgencyGaugeContainer", { score: result.urgency_score, size: 70, strokeWidth: 7 });
      new FACTGauge("inflationGaugeContainer", { score: result.inflation_score, size: 70, strokeWidth: 7 });

      // Build temporal trend charts using custom vector generation paths
      new FACTChart("historyChartContainer", result.price_history);

    } catch (error) {
      console.error("Pipeline failure: ", error);
      alert("FACT Core Failure: Unable to compute pricing matrices. Check local backend hosting.");
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerText = "Generate Report";
    }

    // // --- FRONTEND MOCK DATA TEST INSERT ---
    // const result = {
    //   "status": "success",
    //   "deceptive_score": 9.0,
    //   "urgency_score": 8.7,
    //   "inflation_score": 7.2,
    //   "price_history": [180, 310, 240, 80, 210, 215, 185],
    //   "complaint_template": "To,\nThe Department of Commerce, Supplies and Consumer Protection (DoCSCP)\nBabarmahal, Kathmandu, Nepal.\n\nSubject: Formal Complaint Against Deceptive Pricing under the Consumer Protection Act 2075.\n\nDear Sir/Madam,\nI am writing to log an official complaint regarding deceptive anchor pricing on the product listed under ID: 987654321. The vendor has artificially inflated the baseline value to fabricate false markdown claims..."
    // };

    // // The remaining UI layout code stays exactly as it is:
    // generatedTemplate = result.complaint_template || "";
    // landingView.classList.remove("active");
    // outputView.classList.add("active");

    // new FACTGauge("mainGaugeContainer", { score: result.deceptive_score, size: 120, strokeWidth: 10 });
    // new FACTGauge("urgencyGaugeContainer", { score: result.urgency_score, size: 70, strokeWidth: 7 });
    // new FACTGauge("inflationGaugeContainer", { score: result.inflation_score, size: 70, strokeWidth: 7 });
    // new FACTChart("historyChartContainer", result.price_history);
    // // --- END MOCK DATA INSERT ---
  });

  // 4. Automated Legal Complaints Generation Pipeline
  complaintYesBtn.addEventListener("click", () => {
    if (!generatedTemplate) {
      alert("No complaint verification payload detected.");
      return;
    }
    
    // Package plain text metrics as downloadable client filesystem buffers
    const blob = new Blob([generatedTemplate], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `DoCSCP_Complaint_${document.getElementById("productId").value || "FACT"}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  });

  complaintNoBtn.addEventListener("click", () => {
    window.close();
  });
});