# Clearline HMO Health Screening Platform — Design Spec
**Date:** 2026-06-10  
**Status:** Approved — ready for implementation  
**Author:** Kenechukwu Chukwuka

---

## Overview

Convert the existing Streamlit health screening app into a FastAPI REST backend + React staff portal. Klaire (powered by Claude API `claude-opus-4-8`) replaces all hardcoded medical logic. The PDF is the enrollee's interface — staff handle everything through the web portal.

---

## 1. Architecture

**Stack:**
- Backend: FastAPI (Python)
- Frontend: React + Vite (TypeScript) — staff-only portal
- AI: Claude API `claude-opus-4-8` via Anthropic Python SDK — Klaire persona
- PDF generation: ReportLab
- Storage: Backblaze B2 (PDFs), MotherDuck / DuckDB (customer data)
- Email: Zoho Mail (OAuth) + SMTP fallback
- Async jobs: Celery + Redis
- Secrets: Pydantic Settings — all credentials in `.env`, validated at startup

**User flows:**

*Internal staff (web portal):*
1. Upload CSV/Excel with enrollee health data
2. Klaire analyses each enrollee (streaming preview on screen)
3. PDFs generated (individual + company aggregate)
4. Staff send via email (Backblaze B2 + Zoho recommended) or download

*Enrollees (PDF only):*
1. Receive PDF by email
2. Read Klaire's analysis
3. See telemedicine prompt → consult doctors via mobile app

**Backend file structure:**
```
health-api/
├── api/
│   ├── routers/
│   │   ├── reports.py        # PDF generation endpoints
│   │   ├── klaire.py         # AI analysis + streaming
│   │   ├── email.py          # send individual + bulk
│   │   ├── storage.py        # Backblaze B2
│   │   └── jobs.py           # Celery job status
│   ├── services/
│   │   ├── klaire_service.py # Claude API calls
│   │   ├── report_service.py # ReportLab PDF generation
│   │   ├── email_service.py  # Zoho OAuth + SMTP
│   │   ├── storage_service.py# B2 upload/signed URLs
│   │   └── analysis_service.py # data prep + validation
│   ├── models/
│   │   ├── health_data.py    # Pydantic input schemas
│   │   └── responses.py      # Pydantic output schemas
│   └── core/
│       ├── config.py         # Pydantic Settings (.env)
│       ├── database.py       # MotherDuck connection
│       └── security.py       # API key auth (X-API-Key)
├── workers/
│   └── tasks.py              # Celery task definitions
├── .env                      # ALL secrets (never commit)
└── main.py
```

**Frontend file structure:**
```
health-frontend/
├── src/
│   ├── pages/
│   │   ├── Upload.tsx
│   │   ├── CompanyReport.tsx
│   │   ├── IndividualReports.tsx
│   │   └── Admin.tsx
│   ├── components/
│   │   ├── klaire/           # preview panel, streaming display
│   │   ├── metrics/          # vitals cards, score bar
│   │   └── shared/           # layout, nav, badges
│   └── hooks/
│       ├── useKlaireStream.ts # SSE hook
│       └── useJobStatus.ts    # Celery job polling
```

---

## 2. API Endpoints

All endpoints authenticated via `X-API-Key` header.

### Reports
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/reports/upload` | Upload CSV/Excel, returns parsed preview |
| POST | `/api/reports/generate/{batch_id}` | Queue batch PDF generation (Celery) |
| GET | `/api/reports/batch/{batch_id}` | Get all reports in a batch |
| GET | `/api/reports/{enrollee_id}/pdf` | Download individual PDF |
| GET | `/api/reports/company/{batch_id}/pdf` | Download company aggregate PDF |

### Klaire (AI)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/klaire/analyse/{enrollee_id}` | Trigger Klaire analysis, returns job ID |
| GET | `/api/klaire/stream/{enrollee_id}` | SSE stream of Klaire's analysis (patient tone) |
| GET | `/api/enrollees/{enrollee_id}/doctor-brief` | Clinician-tone summary (mobile app) |

### Email
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/email/send/{enrollee_id}` | Send individual PDF by email |
| POST | `/api/email/bulk/{batch_id}` | Queue bulk email send (Celery) |
| GET | `/api/email/methods` | List available send methods |

### Storage
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/storage/upload/{enrollee_id}` | Upload PDF to Backblaze B2 |
| GET | `/api/storage/url/{enrollee_id}` | Get 7-day signed download URL |

### Jobs
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/jobs/{job_id}` | Job status (pending/running/done/failed) |
| GET | `/api/jobs/{job_id}/progress` | Progress count for bulk jobs |

---

## 3. Klaire — AI Design

### Identity
Klaire is Clearline HMO's named AI health companion. Customers know her name. She is warm, direct, and explains results the way a knowledgeable doctor-friend would — honest and human, never cold or clinical.

### System Prompt (4 layers)

**Layer 1 — Identity** *(static, prompt-cached)*  
Klaire's persona: warm, named, genuine.

**Layer 2 — Tone Rules** *(static, prompt-cached)*  
Short paragraphs, explain jargon, celebrate small wins, always end with 3 actionable steps, never catastrophise, always append medical disclaimer.

**Layer 3 — Medical Guardrails** *(static, prompt-cached)*  
Not a diagnosis tool. Critical thresholds trigger escalated language ("Please see a doctor within 24 hours"). Disclaimer always appended — enforced at API layer, not bypassable by the frontend.

**Layer 4 — Patient Data** *(per-request, NOT cached)*  
Name, age, gender, company, all metric readings. Injected after the cache breakpoint.

### Health Score
Klaire receives all metric readings plus age/gender context and reasons holistically — no hardcoded thresholds. She returns:
- Overall score 0–100
- Per-metric sub-scores
- Dominant risk flag
- Urgency level: `routine` / `watch` / `urgent` / `critical`
- 3 personalised next steps

### Dual Mode
Klaire produces two outputs from the same health data:

| Mode | Audience | Tone | Used in |
|------|----------|------|---------|
| Patient | Enrollee | Warm, gamified, emoji-light | PDF report |
| Clinician | Doctor | Clinical, concise, structured | Doctor Brief API |

### Streaming (SSE)
```
FastAPI GET /api/klaire/stream/{id}
  → anthropic.messages.stream(claude-opus-4-8)
  → StreamingResponse(media_type="text/event-stream")
  → React useKlaireStream hook (EventSource)
  → Staff sees Klaire "typing" in preview panel
```

### Prompt Caching
Layers 1–3 (~800 tokens, never change) marked `cache_control: ephemeral`. ~90% token savings on static layers per call.

### Auto-Escalation
When Klaire returns `urgency = critical`:
- PDF callout: "A Clearline doctor will be in touch"
- Server-side email notification sent to the telemedicine team inbox (configured in `.env` as `TELE_ALERT_EMAIL`)
- Staff dashboard flags the report with a red critical badge

---

## 4. Telemedicine Integration

Enrollees access doctors via the existing mobile app. Integration is lightweight — no changes to the mobile app required beyond one optional API call.

### PDF telemedicine section
Every PDF includes a section after Klaire's analysis:

- **Routine:** Soft mention — "Your Clearline doctors are available on the mobile app."
- **Watch/Urgent:** Direct callout — "Your [reading] is worth a conversation. Reach out through the Clearline mobile app."
- **Critical:** "A Clearline doctor will be in touch." Auto-referral already sent.

### Doctor Brief API
`GET /api/enrollees/{id}/doctor-brief` — returns structured JSON for the mobile app to display before a telemedicine session starts. Clinician tone, structured for 30-second scanning.

```json
{
  "enrollee_id": "CL_ARIK_003",
  "name": "Chukwuemeka Obi",
  "age": 44,
  "gender": "M",
  "screening_date": "2026-05-20",
  "urgency": "watch",
  "health_score": 72,
  "vitals": {
    "bp_systolic": 142,
    "bp_diastolic": 88,
    "bmi": 26.4,
    "glucose": 94
  },
  "klaire_flags": "Elevated BP consistent across both readings. Stage 1 hypertension range. Recommend discussing lifestyle and whether BP monitoring is ongoing.",
  "recommended_focus": ["Blood pressure", "Lifestyle factors"]
}
```

---

## 5. Staff Portal (Frontend)

The React SPA is internal — enrollees never access it.

### Pages

**Upload**
- Drag-and-drop CSV/Excel
- Client-side preview of first 5 rows with parsed vitals
- Validation: missing required fields highlighted before confirmation
- On confirm → batch generation job queued via Celery
- Critical-reading warning banner before staff confirms

**Individual Reports**
- Enrollee list (left): name, ID, urgency badge, sortable/filterable
- Klaire preview panel (right): streaming analysis, vitals grid, Send + Download buttons
- Bulk actions: "Send All" → Celery job with real-time progress bar
- Failed sends: retry button

**Company Report**
- Aggregate stats: average score, urgency distribution, top 3 risk areas
- Download company-wide PDF
- Shareable with HR

**Admin**
- Email method config (Backblaze+Zoho / Backblaze+SMTP / Zoho only / SMTP+attachment)
- Backblaze B2 credentials check
- Job history and audit log

### Key components
- `KlairePreviewPanel` — SSE streaming via `useKlaireStream` hook
- `UrgencyBadge` — colour-coded: green (routine) / amber (watch) / orange (urgent) / red (critical)
- `BulkJobProgress` — polls `useJobStatus` hook, shows live count and retry failed
- `VitalsGrid` — per-metric cards with colour coding

---

## 6. Security

- All credentials in `.env` via Pydantic Settings — validated at startup, app refuses to start if any are missing
- `backblaze_credentials.env` must never be committed (already in `.gitignore`)
- API authenticated via `X-API-Key` header on all endpoints
- PDF temp files written to `UUID`-keyed directories — concurrent users never collide
- Temp files auto-deleted after successful B2 upload
- Medical disclaimer enforced in Klaire's system prompt — cannot be removed by any frontend call
- Zoho OAuth access token cached per-process with expiry check (replaces the current module-level dict race condition)

---

## 7. Key Bugs Fixed from Current Codebase

| Bug | Fix |
|-----|-----|
| Hardcoded Zoho + MotherDuck credentials in source | Move to `.env` via Pydantic Settings |
| PDF output path hardcoded — concurrent users overwrite each other | UUID-keyed temp dirs per request |
| Zoho token cache is a module-level dict — race condition | Per-process cache with lock + expiry |
| God-file (`streamlit_health_app.py`, 1,547 lines) | Split into routers + services + models |
| Duplicate medical logic across 3 files | Single `klaire_service.py` via Claude API |
| Bulk email blocks the UI thread | Celery async task queue |

---

## 8. Out of Scope

- Building or modifying the mobile app
- Authentication / login for the staff portal (assumed internal network or handled by existing webapp)
- Patient-facing web portal
- Scheduling / cron-based report generation
