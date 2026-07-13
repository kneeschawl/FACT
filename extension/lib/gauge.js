// Reusable pure-SVG Ring Gauge Module
class FACTGauge {
  constructor(containerId, options = {}) {
    this.container = document.getElementById(containerId);
    this.score = parseFloat(options.score || 0).toFixed(1);
    this.size = options.size || 120;
    this.strokeWidth = options.strokeWidth || 10;
    this.render();
  }

  getColor(score) {
    if (score <= 3.0) return "#2ecc71"; // Emerald Green (Safe)
    if (score <= 7.0) return "#f1c40f"; // Sunflower Yellow (Warning)
    return "#e74c3c"; // Alizarin Red (Highly Deceptive)
  }

  render() {
    this.container.innerHTML = "";
    const radius = (this.size - this.strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (this.score / 10) * circumference;
    const targetColor = this.getColor(this.score);

    const svg = `
      <svg width="${this.size}" height="${this.size}" viewBox="0 0 ${this.size} ${this.size}">
        <!-- Base Track Ring -->
        <circle cx="${this.size / 2}" cy="${this.size / 2}" r="${radius}" 
                fill="none" stroke="#f1f2f6" stroke-width="${this.strokeWidth}" />
        <!-- Data Path Ring -->
        <circle cx="${this.size / 2}" cy="${this.size / 2}" r="${radius}" 
                fill="none" stroke="${targetColor}" stroke-width="${this.strokeWidth}"
                stroke-dasharray="${circumference}" stroke-dashoffset="${offset}"
                stroke-linecap="round" transform="rotate(-90 ${this.size / 2} ${this.size / 2})" />
        <!-- Metric Value Text -->
        <text x="50%" y="53%" dominant-baseline="middle" text-anchor="middle" 
              font-family="'Segoe UI', Roboto, sans-serif" font-weight="700" 
              font-size="${this.size * 0.24}px" fill="#2d3436">${this.score}</text>
      </svg>
    `;
    this.container.innerHTML = svg;
  }
}