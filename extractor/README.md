# 🛒 E-Commerce NER Extractor — Chrome Extension

Scrapes any e-commerce page and uses spaCy Named Entity Recognition to extract:
- **Brand / Product names**
- **Prices**
- **Discounts & Offers**
- **Urgency / FOMO text** ("Hurry up!", "Only 3 left", etc.)
- **Other named entities**

---

## Project Structure

```
ecom-ner-extension/
├── extension/          ← Load this folder into Chrome
│   ├── manifest.json
│   ├── content.js      ← Page scraper (runs in browser)
│   ├── popup.html      ← Extension UI
│   └── popup.js        ← UI logic
└── backend/
    ├── backend.py      ← Python NER server (Flask + spaCy)
    └── requirements.txt
```

---

## ⚙️ Setup (One Time)

### Step 1 — Install Python dependencies

```bash
cd backend/
pip install -r requirements.txt
```

### Step 2 — Download spaCy language model

For faster/lighter (recommended to start):
```bash
python -m spacy download en_core_web_sm
```

For better accuracy (larger, ~45MB):
```bash
python -m spacy download en_core_web_md
```

---

## 🚀 How to Run (Every Time)

### Step 1 — Start the Python backend

```bash
cd backend/
python backend.py
```

You should see:
```
=======================================================
  🛒  E-Commerce NER Backend
  Running at http://localhost:5000
  Keep this terminal open while using the extension
=======================================================
```

**Keep this terminal open.**

---

### Step 2 — Load the extension in Chrome

1. Open Chrome and go to: `chrome://extensions/`
2. Enable **Developer mode** (toggle in top-right)
3. Click **"Load unpacked"**
4. Select the `extension/` folder from this project
5. The extension icon will appear in your toolbar

---

### Step 3 — Use it!

1. Navigate to any e-commerce page (Amazon, eBay, Daraz, etc.)
2. Click the extension icon in the Chrome toolbar
3. Click **"⚡ SCAN THIS PAGE"**
4. Results appear in the popup — brands, prices, discounts, urgency text
5. Use **{ } raw json** to see the full structured output

---

## 🔌 How it works (No Deployment Needed)

```
Browser (Chrome Extension)          Your Machine
┌──────────────────────┐            ┌─────────────────────┐
│  content.js          │            │  backend.py          │
│  • Scrapes page DOM  │  ───────►  │  • Flask server      │
│  • Sends text data   │  POST      │  • spaCy NER         │
│                      │  /extract  │  • Regex patterns    │
│  popup.js + html     │  ◄───────  │  • Returns entities  │
│  • Shows results     │  JSON      │                      │
└──────────────────────┘            └─────────────────────┘
          localhost:5000 (no internet needed)
```

The backend runs **entirely on your machine** — no cloud, no deployment.

---

## 🧪 Test the backend manually

```bash
curl -X POST http://localhost:5000/extract \
  -H "Content-Type: application/json" \
  -d '{
    "full_text": "Buy the Nike Air Max for $129.99, was $180. Save 28% off! Hurry up, only 3 left in stock!",
    "title": "Nike Air Max 270",
    "price_hints": ["$129.99", "$180.00"],
    "discount_hints": ["28% OFF"],
    "brand_hints": ["Nike"],
    "urgency_hints": ["Only 3 left!"],
    "image_alts": [],
    "url": "https://example.com/product"
  }'
```

---

## 🛠 Troubleshooting

| Problem | Fix |
|---|---|
| "Backend offline" in popup | Run `python backend.py` first |
| "Could not establish connection" | Reload the extension after loading the page |
| Poor brand extraction | Use `en_core_web_md` model for better NER |
| Page not scraping | Some SPAs may need a page reload before scanning |

---

## 📦 Tested on

- Amazon, eBay, Daraz, Flipkart, AliExpress
- Any standard HTML e-commerce page
