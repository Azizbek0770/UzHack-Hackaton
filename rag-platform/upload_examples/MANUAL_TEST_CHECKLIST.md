# Manual Test Checklist

## 1) Start Services

- Backend API is running at `http://127.0.0.1:8000`
- Frontend UI is running at `http://localhost:5173/`

## 2) Upload Packs

Upload one company folder at a time from:

- `upload_examples/AlphaBank`
- `upload_examples/SilkRoadInvest`
- `upload_examples/MixedHoldings`

Each folder includes:

- one PDF
- one XLSX
- one JSON

## 3) Ingestion Debug Checks

After ingestion, verify in debug panel:

- Health status is `ok`
- Text/Table index counts increase
- Ingestion processed > 0
- Ingestion failed = 0
- Last failed file = `none`
- Audit ingestion runs and QA runs increase

Optional API checks:

- `GET /health`
- `GET /metrics`
- `GET /ingestion/report`
- `GET /audit/runs`

## 4) Query Validation by Dataset

### AlphaBank

- Query: `What is revenue in 2024 for AlphaBank?`
  - Expected source includes `alpha_financials.xlsx`
  - Expected mode: `table`
- Query: `Что говорится в отчете AlphaBank о стратегии?`
  - Expected source includes `alpha_management_ru.pdf`
  - Expected mode: `text`

### SilkRoadInvest

- Query: `2024 daromad qancha SilkRoadInvest?`
  - Expected source includes `silk_financials_uz.xlsx`
  - Expected mode: `table`
- Query: `SilkRoadInvest sharhida nima deyilgan?`
  - Expected source includes `silk_commentary_uz.pdf`
  - Expected mode: `text`

### MixedHoldings

- Query: `What is profit in 2024 for MixedHoldings?`
  - Expected source includes `mixed_financials.xlsx`
  - Expected mode: `table`
- Query: `What does the bilingual note say about risk and revenue?`
  - Expected source includes `mixed_bilingual.pdf`
  - Expected mode: `text` or `hybrid`

## 5) Source/Traceability Validation

For each answer, verify:

- Source chips show file and page/sheet
- Source preview modal opens and shows metadata
- Query history records each run
- Debug panel shows rising audit QA run count

## 6) Robustness Validation

- Ask empty question and verify validation error handling
- Trigger repeated same query and verify stable response
- Switch company filter and verify source company matches selected company
- Use `pdf` doc type filter and verify XLSX citations are excluded

## 7) Success Criteria

- No frontend error banners during normal workflow
- No backend 500 for supported files
- Ingestion report has no failed files for valid examples
- Audit runs contain ingestion and QA entries
- At least one accurate answer per company for both narrative and numeric queries
