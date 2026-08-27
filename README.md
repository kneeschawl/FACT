# FACT (Fake Anchoring & Cost Transparency)

FACT is a consumer-protection prototype focused on detecting deceptive e-commerce pricing and urgency dark patterns.  
It combines:

- a **Chrome extension** that scrapes product/page signals from supported retail sites
- a **FastAPI backend** that computes deception scores
- a **DistilBERT-based model** for urgency/dark-pattern text scoring
- a **MySQL/MariaDB data layer** for historical price tracking

---

## Repository Structure

```text
FACT/
├─ extension/               # Chrome extension (popup UI + content scraper)
├─ fact-backend/            # FastAPI backend and scoring pipeline
├─ DPD-Engine/              # DistilBERT training + inference utilities
├─ database/                # SQL schema and seed data
├─ training_set/            # Dataset utilities/scripts
├─ requirements.txt         # Python dependencies used across services
└─ docker-compose.yml       # Reserved for container orchestration
```

---

## Core Workflow

1. User opens a product page (currently designed for daraz.com.np / sastodeal.com).
2. Extension content script scrapes:
   - product ID/name
   - anchor/original and discounted prices
   - discount percentage
   - urgency phrases (e.g., “Only 2 left”)
3. Extension popup sends payload to backend:
   - `POST http://localhost:8000/api/v1/analysis`
4. Backend pipeline:
   - stores current scrape into `scraped_products`
   - fetches recent history for same product
   - computes inflation/manipulation score (FISCAL component)
   - computes urgency score using DistilBERT model inference
   - fuses both into final `deceptive_score` (0–10)
5. Extension renders:
   - total deceptive score gauge
   - urgency and inflation sub-scores
   - price history chart

---

## Main Components

### 1) Chrome Extension (`/extension`)

- **Manifest v3** extension
- Injects `content/content.js` on supported host permissions
- Popup UI (`popup/popup.html`, `popup/popup.js`, `popup/popup.css`)
- Uses local storage for theme preference
- Uses custom visual widgets from `lib/gauge.js` and `lib/chart.js`

### 2) Backend (`/fact-backend`)

- FastAPI app entrypoint: `app/main.py`
- Enabled CORS for extension-to-localhost communication
- Active route:
  - `GET /health`
  - `POST /api/v1/analysis`
- Pipeline logic: `app/pipeline/pipeline_manager.py`

### 3) DPD Engine (`/DPD-Engine`)

- `dark_pattern_classifier.py`
  - training pipeline for DistilBERT regression scoring (1–10)
- `inference.py`
  - model load + runtime scoring helpers (`score`, `score_many`)

### 4) Database (`/database`)

- `schema.sql` creates `fiscal_db.scraped_products`
- `seed_data.sql` inserts sample product records
- `important_commands.txt` contains local MySQL command references

---

## API Contract

### `POST /api/v1/analysis`

**Request body (core fields):**

- `product_id` (string)
- `product_name` (string)
- `anchor_price` (number)
- `discount_percentage` (number)
- `discounted_price` (number)
- `urgency_text` (string)

**Optional enrichment fields also accepted by schema:**

- `full_text`, `title`, `price_hints`, `discount_hints`, `brand_hints`, `urgency_hints`, `image_alts`, `url`

**Response fields:**

- `status`
- `deceptive_score`
- `urgency_score`
- `inflation_score`
- `price_history`
- `complaint_template`

---

## Local Setup

### 1) Prerequisites

- Python 3.10+
- MySQL/MariaDB instance (project files reference database `fiscal_db`)
- Google Chrome (for extension loading/testing)

### 2) Install dependencies

From repository root:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3) Initialize database

Run SQL scripts from `/database`:

- `schema.sql`
- `seed_data.sql` (optional sample data)

### 4) Run backend

From `/home/runner/work/FACT/FACT/fact-backend`:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Health check:

```bash
curl http://localhost:8000/health
```

### 5) Load extension

1. Open `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked**
4. Select `/home/runner/work/FACT/FACT/extension`
5. Navigate to supported product page and open FACT popup

---

## Development Notes

- The analysis pipeline currently contains environment-specific defaults:
  - hardcoded DPD engine path in `pipeline_manager.py` (`E:\FYP_FACT\DPD-Engine`)
  - local DB defaults (`localhost:3307`, user `root`, empty password)
- Several backend route/service files exist but are currently empty stubs.
- Extension includes complaint submission UI that posts to:
  - `POST /api/v1/complaints/submit`
  - this endpoint is not implemented in the active backend routes.

---

## Testing

Test files are present under `/fact-backend/tests`, but currently empty.  
Add concrete tests before relying on CI or automated regression coverage.

---

## License

This project is licensed under the terms in [`LICENSE`](./LICENSE).
