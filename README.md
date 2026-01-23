### DP_2_NGDC (DataPower legacy → Target conversion)

This repo contains:
- **`src/`**: unzipped legacy DataPower exports (per app)
- **`Target/`**: standard Target framework structure (shared assets)
- **`tools/`**: AI-assisted conversion utilities (Tachyon API)

### Tachyon API configuration

Export these environment variables (see `tachyon.env.example`):
- **`TACHYON_BASE_URL`**
- **`TACHYON_API_KEY`**
- **`TACHYON_MODEL`**

Optional:
- **`TACHYON_CHAT_PATH`** (default: `/v1/chat/completions`)
- **`TACHYON_TIMEOUT_SECS`** (default: `60`)

### Install (conversion tool)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run conversion (example: VISA GetStat export)

Dry-run (no files written):

```bash
export TACHYON_BASE_URL="https://tachyon.example.com"
export TACHYON_API_KEY="..."
export TACHYON_MODEL="..."

python tools/convert.py \
  --app visa \
  --export-xml "/Users/pradeepm/ProjX/DP_2_NGDC/src/visa/GetStat_MPG_and_LogCategory/export.xml" \
  --dry-run
```

Write files (will fail if outputs already exist unless `--force`):

```bash
python tools/convert.py \
  --app visa \
  --export-xml "/Users/pradeepm/ProjX/DP_2_NGDC/src/visa/GetStat_MPG_and_LogCategory/export.xml" \
  --force
```

### Notes / assumptions
- The Tachyon endpoint is assumed to be **OpenAI chat-completions compatible**:
  `POST {TACHYON_BASE_URL}{TACHYON_CHAT_PATH}` with `Authorization: Bearer ...`.
- We keep the **Target framework immutable** (`Target/Framework/*`). Conversions are written under `Target/<app>/...`.

# ngdc

You are building a Python-based AI-assisted analyzer for IBM DataPower.

Goal:
Given legacy DataPower source code spanning multiple domains, discover
how a single VIP routes requests across chained domains and finally reaches
the real backend.

The solution must be prompt-driven, not rule-restricted.

Requirements:

1. The script must accept:
   - A VIP name
   - A directory containing DataPower exports (XML, XSLT, ZIPs)
   - A prompt file selected per application/domain

2. The script must:
   - Parse DataPower configurations
   - Identify service routing URLs, backend URLs, and domain-to-domain calls
   - Detect chained routing across domains
   - Recursively resolve child domains until a final backend is found
   - Build a call graph per API

3. Use Generative AI for:
   - Understanding routing intent
   - Resolving conditional logic in XSLT
   - Identifying backend URLs even when variables are used
   - Explaining routing decisions in plain English

4. The script must:
   - Load the selected prompt dynamically from file
   - Inject extracted legacy snippets into the prompt
   - Send the prompt to a GenAI API
   - Receive structured JSON output

5. Output must include:
   - All child domains involved
   - API paths
   - Call chain per API
   - Final backend URL
   - Routing conditions
   - Missing information as questions

6. Architecture:
   - PromptLoader
   - LegacyParser
   - ChainResolver (recursive)
   - AIReasoner
   - GraphBuilder
   - OutputExporter (JSON)

Do not hardcode rules.
Design this as a flexible, extensible, prompt-based system.

Generate clean, production-quality Python code with clear comments.

Map the legacy behavior to the latest DataPower framework.

Rules:
- Use standardized naming
- Externalize configuration
- Centralize error handling
- Use reusable policy patterns
- Ensure observability

Generate:
1. New gateway structure
2. Required policies
3. Updated flow diagram (textual)

Generate the modernized DataPower configuration.

Output:
- Gateway XML
- XSLT placeholders
- Policy references
- Clear TODO markers where answers are pending

Do not include guessed values.
Mark unknowns explicitly.
Generate migration documentation including:

1. Legacy overview
2. New architecture overview
3. Security model
4. Assumptions
5. Open questions
6. Migration risks
7. Validation checklist

START
  |
  v
Is this a NEW service?
  |
  +-- YES (Greenfield)
  |     |
  |     v
  |   Pattern?
  |     |
  |     +-- Internal
  |     |     |
  |     |     +-- REST + OAuth?
  |     |     |       -> APG Hybrid (Self-Service)
  |     |     |
  |     |     +-- SOAP / MQ / mTLS?
  |     |             -> DataPower (NGDC)
  |     |
  |     +-- Ingress
  |     |     |
  |     |     +-- OAuth supported by partner?
  |     |     |       -> APG Hybrid
  |     |     |
  |     |     +-- SOAP or mTLS only?
  |     |             -> DataPower (NGDC)
  |     |
  |     +-- Egress
  |           |
  |           +-- OAuth / REST?
  |           |       -> APG Hybrid
  |           |
  |           +-- MQ / SOAP / mTLS?
  |                   -> DataPower (NGDC)
  |
  +-- NO (Brownfield)
        |
        v
    Current Gateway?
        |
        +-- APG OPDK
        |     |
        |     v
        |   Pattern?
        |     |
        |     +-- Ingress
        |     |     -> Partner migrates via HD60
        |     |
        |     +-- Egress / Internal
        |           -> APIM team migrates
        |
        +-- DataPower
              |
              v
        Is service SIMPLE & PASS-THROUGH?
              |
              +-- YES (≈70%)
              |     |
              |     +-- REST + OAuth?
              |     |       -> Migrate to APG Hybrid
              |     |
              |     +-- SOAP / mTLS / MQ?
              |             -> BLOCKER (Needs pattern/tool)
              |
              +-- NO (≈30%)
                    -> Modernize on DataPower (NGDC)

                    | Field Type | Pattern   | Protocol | Interface | Security | Complexity   | Target Gateway   | Migration Owner | Tool          |
| ---------- | --------- | -------- | --------- | -------- | ------------ | ---------------- | --------------- | ------------- |
| Greenfield | Internal  | HTTP     | REST      | OAuth    | Any          | APG Hybrid       | App Team        | Self-Service  |
| Greenfield | Ingress   | HTTP     | REST      | OAuth    | Any          | APG Hybrid       | Partner         | Self-Service  |
| Greenfield | Ingress   | HTTP     | SOAP      | mTLS     | Any          | DataPower (NGDC) | App Team        | Manual        |
| Brownfield | APG OPDK  | Ingress  | REST      | OAuth    | Pass-through | APG Hybrid       | Partner         | HD60          |
| Brownfield | APG OPDK  | Egress   | REST      | OAuth    | Any          | APG Hybrid       | APIM            | HD60          |
| Brownfield | DataPower | Any      | REST      | OAuth    | Pass-through | APG Hybrid       | APIM / App      | TBD Tool      |
| Brownfield | DataPower | Any      | SOAP      | mTLS     | Complex      | DataPower (NGDC) | App Team        | Modernization |


# API Gateway Migration – End-to-End Flow Coverage

**Scope:** Greenfield & Brownfield services migrating from Legacy Data Centers to New Data Center (NGDC)  
**Target Gateways:** APG Hybrid (Primary), DataPower (Niche / Exception)

---

## 1. Core Principles

### 1.1 Strategic Direction
- APG Hybrid is the **default target gateway**
- DataPower is retained only for:
  - Complex transformations
  - Protocols / security patterns not supported by APG Hybrid
- Target footprint reduction:
  - ~70% DataPower services → APG Hybrid
  - ~30% remain on DataPower (modernized in NGDC)

### 1.2 Definitions
- **Greenfield**: Newly onboarded services
- **Brownfield**: Existing services
- **Patterns**
  - Ingress (External → Bank)
  - Egress (Bank → External)
  - Internal (Bank → Bank)
- **Protocols**
  - HTTP (Sync)
  - MQ (Async)
- **Interfaces**
  - REST
  - SOAP
- **Security**
  - OAuth
  - mTLS
  - BasicAuth (primarily Egress)

---

## 2. Greenfield Flows (Target State)

> **Design intent:**  
> All Greenfield services should be **self-service**, wherever technically feasible.

---

### 2.1 Greenfield – Ingress

| Combination | Target Gateway | Self-Service | Status | Open Gaps / Questions |
|------------|---------------|--------------|--------|-----------------------|
| REST + OAuth | APG Hybrid | Yes | ✅ Supported (Golden Path) | Is partner self-service fully enabled on the portal? |
| REST + mTLS | ❓ | ❓ | ⚠️ Unknown | Does APG Hybrid support mTLS for Ingress? |
| SOAP + OAuth | ❓ | ❓ | ⚠️ Unknown | Is SOAP supported in APG Hybrid? |
| SOAP + mTLS | ❓ | ❓ | ❌ Gap | What is the go-forward approach? DataPower fallback? |

---

### 2.2 Greenfield – Egress

| Combination | Target Gateway | Self-Service | Status | Open Gaps / Questions |
|------------|---------------|--------------|--------|-----------------------|
| REST + OAuth | APG Hybrid | Yes | ⚠️ Assumed | Is outbound OAuth token handling validated? |
| REST + mTLS | ❓ | ❓ | ⚠️ Unknown | Is mTLS supported for outbound traffic? |
| SOAP | ❓ | ❓ | ⚠️ Unknown | Is SOAP supported for Egress? |
| BasicAuth (Backend) | ❓ | ❓ | ⚠️ Unknown | Is BasicAuth supported/tested in Hybrid? |
| Partner IDP (Outbound OAuth) | ❓ | ❓ | ⚠️ Unknown | Has integration with partner IDPs been tested? |

---

### 2.3 Greenfield – Internal

| Combination | Target Gateway | Self-Service | Status | Open Gaps / Questions |
|------------|---------------|--------------|--------|-----------------------|
| REST + OAuth | APG Hybrid | Yes | ⚠️ Likely | Are default OAuth scopes enforced? |
| REST + mTLS | ❓ | ❓ | ⚠️ Unknown | Is internal mTLS supported? |
| SOAP | ❓ | ❓ | ⚠️ Unknown | Is SOAP supported internally? |
| MQ | ❓ | ❓ | ❌ Gap | No defined target architecture for Greenfield MQ |

---

## 3. Brownfield – APG OPDK → APG Hybrid

### Ownership Model
- **Internal services** → Partner / App team
- **Ingress & Egress** → Central APIM team
- **Primary accelerator** → HD-60

---

### 3.1 Brownfield – Ingress (APG OPDK)

| Combination | Target | Tool | Owner | Status | Open Questions |
|------------|--------|------|-------|--------|----------------|
| REST + OAuth | APG Hybrid | HD-60 | Partner | ⚠️ Partial | Are OAuth configs fully migrated? |
| SOAP | ❓ | ❓ | ❓ | ❌ Gap | SOAP support post-migration? |
| mTLS | ❓ | ❓ | ❓ | ❌ Gap | Does Hybrid support mTLS Ingress? |
| Bulk Migration | APG Hybrid | HD-60 | APIM | ❓ | Does HD-60 support bulk proxy migration? |

---

### 3.2 Brownfield – Egress (APG OPDK)

| Combination | Target | Tool | Owner | Status | Open Questions |
|------------|--------|------|-------|--------|----------------|
| REST + OAuth | APG Hybrid | HD-60 | APIM | ⚠️ Partial | Is outbound OAuth flow compatible? |
| SOAP | ❓ | ❓ | ❓ | ❌ Gap | SOAP Egress support? |
| mTLS | ❓ | ❓ | ❓ | ❌ Gap | mTLS outbound support? |
| Bulk Migration | APG Hybrid | HD-60 | APIM | ❓ | Bulk migration capability? |

---

### 3.3 Brownfield – Internal (APG OPDK)

| Combination | Target | Tool | Owner | Status | Open Questions |
|------------|--------|------|-------|--------|----------------|
| REST + OAuth | APG Hybrid | HD-60 | Partner | ⚠️ Partial | Does scope enforcement impact consumers? |
| SOAP | ❓ | ❓ | ❓ | ❌ Gap | Internal SOAP support? |
| mTLS | ❓ | ❓ | ❓ | ❌ Gap | Internal mTLS support? |

---

## 4. Brownfield – DataPower → APG Hybrid / DataPower NGDC

> **Highest complexity and highest risk area**

---

### 4.1 Service Classification Requirement

| Classification | Action |
|---------------|--------|
| Simple / Pass-through | Migrate to APG Hybrid |
| Complex Transformation | Remain on DataPower (NGDC) |

**Open Question**
- Is service classification automated or manual?

---

### 4.2 DataPower – Internal

| Aspect | Current Reality | Open Gaps |
|------|----------------|-----------|
| Proxy creation | Manual / Visual | No automated conversion |
| OAS availability | Rare | OAS required for Hybrid |
| Migration model | Dev assisted, higher env partner-driven | No accelerator |
| Tooling | None | Need template-based proxy generator |

---

### 4.3 DataPower – Ingress & Egress

| Aspect | Current Reality | Open Gaps |
|------|----------------|-----------|
| Ownership | APIM team | Who executes migration at scale? |
| SOAP prevalence | High | SOAP → REST strategy missing |
| OAS generation | Hard from WSDL / flows | No fast solution |
| Accelerators | None | Partial / stub OAS needed |

---

## 5. Producer vs Consumer Journey

### 5.1 Producer Journey (Current Focus)
- Proxy creation
- Migration tooling
- Deployment and ownership

### 5.2 Consumer Journey (Open Gap)

**Open Questions**
- How do consumers discover migrated APIs?
- Do endpoints or contracts change?
- Are OAuth scopes newly enforced?
- How is backward compatibility ensured?
- How are consumers notified?

---

## 6. Accelerator Inventory

### Existing
- **HD-60**
  - APG OPDK → APG Hybrid
  - ❓ Bulk support
  - ❓ Coverage across all patterns

### Missing / Needed
- DataPower → APG Hybrid proxy generator
- Partial / stub OAS generator
- SOAP → REST façade accelerator
- mTLS / certificate migration utility
- Consumer compatibility tooling

---

## 7. Summary of Open Gaps

### Platform Gaps
- SOAP support in APG Hybrid
- mTLS support (Ingress / Egress / Internal)
- MQ target architecture

### Tooling Gaps
- DataPower migration accelerator
- Bulk migration support
- OAS generation at scale

### Process Gaps
- Ownership clarity
- Consumer journey definition
- Exception handling model

---

## 8. Key Statement

> “This migration is not constrained by intent or strategy.  
> It is constrained by **tooling readiness, ownership clarity, and protocol coverage**.  
> Until these are addressed, migration velocity will remain limited.”

---




