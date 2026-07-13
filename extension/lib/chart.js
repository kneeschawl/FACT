// Reusable pure-SVG Temporal Analysis Chart Module
class FACTChart {
  constructor(containerId, dataPoints) {
    this.container = document.getElementById(containerId);
    this.data = dataPoints || [];
    this.width = 320;
    this.height = 140;
    this.padding = 25;
    this.render();
  }

  render() {
    this.container.innerHTML = "";
    if (this.data.length === 0) return;

    const maxVal = Math.max(...this.data) * 1.15;
    const minVal = Math.min(...this.data) * 0.85;
    const range = maxVal - minVal || 1;

    // Map numerical inputs into exact coordinates within bounding boxes
    const points = this.data.map((val, index) => {
      const x = this.padding + (index / (this.data.length - 1)) * (this.width - this.padding * 2);
      const y = this.height - this.padding - ((val - minVal) / range) * (this.height - this.padding * 2);
      return { x, y, value: val };
    });

    let pathD = `M ${points[0].x} ${points[0].y} `;
    for (let i = 1; i < points.length; i++) {
      pathD += `L ${points[i].x} ${points[i].y} `;
    }

    // Horizontal Guideline Y coordinates
    const gridY1 = this.height - this.padding;
    const gridY2 = this.height / 2;
    const gridY3 = this.padding;

    let circles = "";
    points.forEach(p => {
      circles += `<circle cx="${p.x}" cy="${p.y}" r="4" fill="#2f3542" stroke="#ffffff" stroke-width="1.5"/>`;
    });

    const svg = `
      <svg width="100%" height="100%" viewBox="0 0 ${this.width} ${this.height}">
        <!-- Dynamic Horizontal Grid Lines -->
        <line x1="${this.padding}" y1="${gridY1}" x2="${this.width - this.padding}" y2="${gridY1}" stroke="#e4e7eb" stroke-width="1" />
        <line x1="${this.padding}" y1="${gridY2}" x2="${this.width - this.padding}" y2="${gridY2}" stroke="#e4e7eb" stroke-width="1" stroke-dasharray="4" />
        <line x1="${this.padding}" y1="${gridY3}" x2="${this.width - this.padding}" y2="${gridY3}" stroke="#e4e7eb" stroke-width="1" />
        
        <!-- Y Axis Markers -->
        <text x="${this.padding - 5}" y="${gridY1}" font-size="8" text-anchor="end" fill="#747d8c">${Math.round(minVal)}</text>
        <text x="${this.padding - 5}" y="${gridY2 + 3}" font-size="8" text-anchor="end" fill="#747d8c">${Math.round((minVal + maxVal) / 2)}</text>
        <text x="${this.padding - 5}" y="${gridY3 + 6}" font-size="8" text-anchor="end" fill="#747d8c">${Math.round(maxVal)}</text>

        <!-- Main Trend Line Path -->
        <path d="${pathD}" fill="none" stroke="#2f3542" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
        
        <!-- Interactive Node Circles -->
        ${circles}
      </svg>
    `;
    this.container.innerHTML = svg;
  }
}