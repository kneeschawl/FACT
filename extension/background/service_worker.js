// Listens for structural cycles or cross-origin authorization if needed.
chrome.runtime.onInstalled.addListener(() => {
  console.log("FACT Extension initialized successfully.");
});