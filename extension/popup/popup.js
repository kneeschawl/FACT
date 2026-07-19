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
  
  // Pipeline application states across loops
  let cachedResultData = null;
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

  // 2. Legend Visibility Interactions
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

    const currentUrgencyText = document.getElementById("urgencyText").value || "";

    // Comprehensive network payload structured mapping to FastAPI documentation bounds
    const payload = {
      product_id: document.getElementById("productId").value,
      product_name: document.getElementById("productName").value,
      anchor_price: parseFloat(document.getElementById("anchorPrice").value) || 0,
      discount_percentage: parseFloat(document.getElementById("discountPercentage").value) || 0,
      discounted_price: parseFloat(document.getElementById("discountedPrice").value) || 0,
      urgency_text: currentUrgencyText,
      urgency_hints: currentUrgencyText ? [currentUrgencyText] : [],
      full_text: document.getElementById("productName").value || ""
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

      // Cache structural records securely for internal dynamic generation flows
      cachedResultData = result;
      generatedTemplate = result.complaint_template || "";

      // Clean old states out if user processes sequential targets on same instantiation
      document.getElementById("complaintFormPanel").style.display = "none";
      document.getElementById("userDeceptionDescription").value = "";

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
  });

  // ==========================================
  // 4. Automated Legal Complaints Generation Pipeline (Embedded Panel Layout)
  // ==========================================
  complaintYesBtn.addEventListener("click", () => {
    if (!generatedTemplate || !cachedResultData) {
      alert("No active audit assessment detected to construct a complaint format.");
      return;
    }
    
    const targetProdId = document.getElementById("productId").value || "N/A";
    const targetProdName = document.getElementById("productName").value || "Unknown Product";
    const currentAnchorPrice = document.getElementById("anchorPrice").value || "0.0";
    const currentDiscountedPrice = document.getElementById("discountedPrice").value || "0.0";
    
    // Auto-assemble structural context summary metrics for read-only tracking element
    const metaSummary = 
      `Product Reference ID: ${targetProdId}\n` +
      `Product Name: ${targetProdName}\n` +
      `Deception Rating: ${cachedResultData.deceptive_score}/10 | Urgency Score: ${cachedResultData.urgency_score}/10\n` +
      `Listed Anchor Baseline: Rs. ${currentAnchorPrice} | Scraped Price: Rs. ${currentDiscountedPrice}`;
      
    // Expose layout layer components within user viewport matrix
    document.getElementById("complaintPrefilledMeta").value = metaSummary;
    document.getElementById("complaintFormPanel").style.display = "block";
    
    // Smooth navigation viewport tracking repositioning
    document.getElementById("complaintFormPanel").scrollIntoView({ behavior: 'smooth' });
  });

  complaintNoBtn.addEventListener("click", () => {
    window.close();
  });

  // Final Action Handler: Packages data payloads along with interactive description blocks
  document.getElementById("finalSubmitComplaintBtn").addEventListener("click", async () => {
    const manualEntryDescription = document.getElementById("userDeceptionDescription").value.trim();
    
    if (!manualEntryDescription) {
      alert("Please provide a brief manual description of the deceptive event before finalizing the regulatory submission.");
      return;
    }
    
    // Append contextual user text to system calculated report matrix blocks
    const completeFinalDossierText = 
      `${generatedTemplate}\n\n` +
      `==================================================\n` +
      `ADDITIONAL CONSUMER EYEWITNESS STATEMENT:\n` +
      `${manualEntryDescription}\n` +
      `==================================================`;
      
    try {
      const actionBtn = document.getElementById("finalSubmitComplaintBtn");
      actionBtn.disabled = true;
      actionBtn.innerText = "Transmitting to Department Logs...";

      // Pipe to your dedicated FastAPI backend submission endpoint
      const reportResponse = await fetch("http://localhost:8000/api/v1/complaints/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          product_id: document.getElementById("productId").value,
          compiled_complaint_text: completeFinalDossierText,
          user_comments: manualEntryDescription
        })
      });

      if (reportResponse.ok) {
        alert("Success! Your comprehensive consumer complaint dossier has been officially recorded and submitted to the department registry.");
        window.close();
      } else {
        throw new Error("Target registry endpoint rejected data serialization.");
      }
    } catch (err) {
      console.error("Transmission failure: ", err);
      alert("Submission Error: Backend system could not transmit report. Check local hosting status.");
    } finally {
      document.getElementById("finalSubmitComplaintBtn").disabled = false;
      document.getElementById("finalSubmitComplaintBtn").innerText = "Submit Form to Department";
    }
  });
});