hi u### DP_2_NGDC (DataPower legacy → Target conversion)

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
> Until these are addressed, migration velocity will remain Thank you. Now, as I step in, let’s ground ourselves in what this journey truly means. We’ve come a long way—thank you for every ounce of effort—but what excites me most is that we’re just at the beginning of what’s possible.

Now, speaking of people: You’ve seen the names on the last slide. Those celebrating anniversaries, those recognized for performance—it’s all of you who make this journey meaningful. Congratulations, and here’s to more success together.

Now let’s talk scale. We’re supporting 40 million transactions—already huge—but with only 9% of our APIs on the gateway. That tells us something powerful: We’ve achieved big things—but the potential is far greater as we scale intelligently.

And that scaling momentum? We’ve seen a 30% growth in internal APIs, 65% in egress, and 69% in ingress. At the same time, API producers and consumers both rose by 29%. That’s proof that APIs aren’t just being built—they’re being used, reused, and trusted.

Now, about the roadmap. We’re not just running the bank—we’re transforming it. We’re building governance, starting with audits and inventory, so we can move faster with confidence. We’re simplifying with hybrid adoption, reducing legacy platforms, and lowering complexity. And finally, we’re enhancing developer experience—standardized patterns, faster onboarding, and yes, even AI-powered support.

These OKRs? They’re our transformation work. Self-service migrations, DataPower reduction, resilience across neighborhoods—this is how we’re building a future-ready platform, while still handling day-to-day operations.

And lastly, this is the team making it happen. We have clear leadership, dedicated domains, and global delivery. This structure ensures we’re not just keeping up—we’re leading.

So, to wrap it up: We’re balancing the present while building the future. Thank you for being part of this journey, and let’s keep pushing ahead!


index=esga sourcetype IN ("wf:rise:errors:txt","wf:rise:profiling:txt")
| eval is_success=if(like(_raw,"%StatDesc=Success%"),1,0)
| eval is_unsuccess=if(is_success=0,1,0)

| timechart span=1m count as total_tx sum(is_unsuccess) as unsuccess_tx

| eval TPS=total_tx/60
| eval unsuccess_TPS=unsuccess_tx/60

| eventstats perc95(TPS) as P95_TPS perc99(TPS) as P99_TPS
| eventstats perc95(unsuccess_TPS) as P95_unsuccess_TPS perc99(unsuccess_TPS) as P99_unsuccess_TPS

| eval above_p95=if(TPS>P95_TPS,1,0)
| eval above_p99=if(TPS>P99_TPS,1,0)

| stats
    max(TPS) as Max_TPS
    values(P95_TPS) as P95_TPS
    values(P99_TPS) as P99_TPS
    values(P95_unsuccess_TPS) as P95_unsuccess_TPS
    values(P99_unsuccess_TPS) as P99_unsuccess_TPS
    avg(unsuccess_TPS) as Avg_unsuccess_TPS
    avg(TPS) as Avg_total_TPS
    sum(above_p95) as minutes_above_p95
    sum(above_p99) as minutes_above_p99
    count as total_minutes

| eval pct_above_p95=round((minutes_above_p95/total_minutes)*100,2)
| eval pct_above_p99=round((minutes_above_p99/total_minutes)*100,2)

| eval pct_TPS_unsuccess=round((Avg_unsuccess_TPS/Avg_total_TPS)*100,2)

More Gran
index=esga sourcetype IN ("wf:rise:errors:txt","wf:rise:profiling:txt") earliest=-7d@d latest=now
| eval is_success=if(like(_raw,"%StatDesc=Success%") OR StatDesc="Success",1,0)
| eval is_unsuccess=if(is_success=1,0,1)

| timechart span=1m count as total_tx sum(is_success) as success_tx sum(is_unsuccess) as unsuccess_tx

| eval total_TPS=total_tx/60
| eval success_TPS=success_tx/60
| eval unsuccess_TPS=unsuccess_tx/60

| eventstats perc95(total_TPS) as P95_total_TPS

| eval is_top5=if(total_TPS>=P95_total_TPS,1,0)

| stats
    sum(total_tx) as total_tx_all
    sum(success_tx) as success_tx_all
    sum(unsuccess_tx) as unsuccess_tx_all
    sum(eval(if(is_top5=1,total_tx,0))) as total_tx_top5
    sum(eval(if(is_top5=1,success_tx,0))) as success_tx_top5
    sum(eval(if(is_top5=1,unsuccess_tx,0))) as unsuccess_tx_top5

| eval top5_pct_of_total=round((total_tx_top5/total_tx_all)*100,2)
| eval top5_success_pct_of_total=round((success_tx_top5/success_tx_all)*100,2)
| eval top5_unsuccess_pct_of_total=round((unsuccess_tx_top5/unsuccess_tx_all)*100,2)

| eval within_top5_success_share=round((success_tx_top5/total_tx_top5)*100,2)
| eval within_top5_unsuccess_share=round((unsuccess_tx_top5/total_tx_top5)*100,2)

| table
    top5_pct_of_total
    top5_success_pct_of_total
    top5_unsuccess_pct_of_total
    within_top5_success_share
    within_top5_unsuccess_share
    total_tx_top5
    success_tx_top5
    unsuccess_tx_top5
    total_tx_all
    success_tx_all
    unsuccess_tx_all

index=esga sourcetype IN ("wf:rise:errors:txt","wf:rise:profiling:txt") earliest=-7d@d latest=now
| rex field=_raw "\]\[(?<domain>[^\]]+)\]\[0x"
| eval minute=_time - (_time % 60)

| eventstats count as total_events

| eventstats count as tmp by minute
| eval tx_per_min=tmp
| eval TPS=tx_per_min/60

| eventstats perc95(TPS) as P95_TPS
| where TPS>=P95_TPS

| stats count as tx_in_top5 by domain
| sort - tx_in_top5
| head 20

index=esga sourcetype IN ("wf:rise:errors:txt","wf:rise:profiling:txt") earliest=-7d@d latest=now
| rex field=_raw "\]\[(?<domain>[^\]]+)\]\[0x"
| eval minute=_time - (_time % 60)

| eventstats count as tmp by minute
| eval TPS=(tmp/60)

| eventstats perc95(TPS) as P95_TPS
| where TPS>=P95_TPS

| stats count as tx by domain
| eventstats sum(tx) as total_tail_tx
| eval pct_of_tail=round((tx/total_tail_tx)*100,2)
| sort - pct_of_tail
| head 20
| table domain tx pct_of_tail

index=esga sourcetype IN ("wf:rise:errors:txt","wf:rise:profiling:txt") earliest=-7d@d latest=now
| rex field=_raw "\]\[(?<domain>[^\]]+)\]\[0x"
| eval is_success=if(like(_raw,"%StatDesc=Success%") OR StatDesc="Success",1,0)
| eval is_unsuccess=if(is_success=1,0,1)
| eval minute=_time - (_time % 60)

| eventstats count as tmp by minute
| eval TPS=(tmp/60)

| eventstats perc95(TPS) as P95_TPS
| where TPS>=P95_TPS

| stats
    count as total_tx
    sum(is_success) as success_tx
    sum(is_unsuccess) as unsuccess_tx
  by domain

| eval unsuccess_rate_pct=round((unsuccess_tx/total_tx)*100,2)
| sort - total_tx
| head 20
| table domain total_tx success_tx unsuccess_tx unsuccess_rate_pct

index=esga sourcetype IN ("wf:rise:errors:txt","wf:rise:profiling:txt") earliest=-7d@d latest=now
| rex field=_raw "MsgNm=(?<MsgNm>[^|]+)"
| eval minute=_time - (_time % 60)

| eventstats count as tmp by minute
| eval TPS=(tmp/60)

| eventstats perc95(TPS) as P95_TPS
| where TPS>=P95_TPS

| stats count as tx_in_top5 by MsgNm
| sort - tx_in_top5
| head 20


You are an NGDC migration status assistant focused on API Gateway modernization from DataPower/OPDK to Apigee Hybrid/NGDC.

Your primary goal is to provide clear, concise, and leadership-ready summaries of migration progress, blockers, risks, and next actions.

Always structure your responses in the following format:

1. Executive Summary
2. Current Progress
3. Blockers / Dependencies
4. Risks
5. Recommended Actions
6. Leadership Ask

Guidelines:
- Be crisp, factual, and to the point.
- Avoid long paragraphs; use bullet points wherever possible.
- Clearly distinguish between confirmed facts and assumptions.
- Do not invent data. If information is missing, explicitly call it out.
- Focus on high-impact areas such as:
  - API migration progress (DataPower → Apigee Hybrid)
  - OAS generation status
  - Proxy generation readiness
  - Environment readiness (Dev, UAT, Prod)
  - Firewall and infrastructure dependencies
  - CI/CD pipeline readiness (ETLX or equivalent)
  - Portal onboarding and integration gaps
  - Testing and deployment readiness

Tone:
- Professional and executive-friendly
- Suitable for CIO-level updates
- Direct, confident, and actionable

Special Behavior:
- If asked for a summary, always prioritize risks and blockers.
- If asked for updates, highlight what has changed recently.
- If data is incomplete, include a “Missing Information” section.

Your responses should help leadership make decisions quickly.

# ESGA Vulnerability Pattern Discovery

We have approximately 80 DataPower integration repositories whose names start with `app-esga*`.

We receive hundreds of vulnerability findings every week from GPT/LLM-based code scans. A major problem is recurring false positives because the LLM often analyzes code statically without understanding the complete ESGA/DataPower execution context.

Our goal is to reduce this repetitive work by identifying:

1. Recurring **false-positive patterns** that can safely be taught to future LLM vulnerability scanners.
2. Recurring **true-positive root causes** that can be fixed centrally so we do not repeatedly fix the same vulnerability across many repositories.

## Important Architecture

There is an `ESGA DataPower Common` repository containing common DataPower files used during the build of the integration repositories.

An integration-specific repo may contain the same file as Common.

When that happens, we expect the integration-specific file to take precedence during the build.

**First verify this behavior from the actual build logic.**

Security analysis must be performed against the **effective built code**, not simply the files visible in each repository.

## Known False-Positive Example

One example we already see involves files such as `captureReqDatafiles` and `setroute`.

`captureReqDatafiles` may capture incoming headers and store them in DataPower context variables.

Later, `setroute` may restore those same values into the request being sent to the backend.

An LLM may recommend replacing use of the original header with the value stored in the DP context variable.

But if:

`DP context value = original header`

and nothing security-relevant happens between the two, then changing:

`backend header = original value`

to:

`backend header = DP context value`

may be security-equivalent and therefore a redundant remediation.

Trace the **complete source → transformations → validation → context variable → sink** before classifying such findings.

Do not assume this example is always an FP. Verify the complete flow.

## What I Want You to Discover

Scan all `app-esga*` repositories plus ESGA DataPower Common and identify recurring patterns where LLM scanners misunderstand ESGA context.

For each recurring FP pattern determine:

* What the LLM typically flags
* Why it gets the context wrong
* Complete source-to-sink evidence
* Conditions required to classify it as FP
* Conditions where the same pattern would actually be vulnerable
* Number of integrations affected
* Confidence level

Also identify recurring **true-positive root causes**.

For each TP determine:

* Root vulnerability cause
* Common vs integration-specific implementation
* Number of integrations affected
* Whether one fix in ESGA DataPower Common could eliminate the issue across many integrations
* Which integrations override the common file and therefore require separate remediation
* Recommended permanent remediation

Do not treat 80 repositories as 80 independent problems.

Cluster equivalent implementations into security patterns.

For example:

`Pattern → inherited from Common in 55 repos → overridden in 10 → not applicable in 15`

## Expected Output

Produce:

### 1. Build Model

Explain how Common + integration-specific files become the final deployable artifact and confirm override precedence.

### 2. FP Catalogue

Recurring false-positive patterns with evidence, conditions, exceptions and affected repo counts.

### 3. TP Catalogue

Recurring true-positive root causes, affected repo counts and permanent remediation opportunities.

### 4. Common Fix Opportunities

Identify TP patterns where fixing ESGA DataPower Common once could eliminate the vulnerability across many integrations, including integrations that override the affected file.

### 5. LLM Scanner Knowledge

Create concise reusable knowledge that can later be supplied to GPT/LLM vulnerability scans so known FP patterns are understood before vulnerabilities are raised.

### 6. Repo/Pattern Matrix

Map repositories to FP/TP patterns and indicate Common inheritance vs integration override.

Use HIGH / MEDIUM / LOW confidence.

Only HIGH-confidence FP patterns should be considered candidates for future scanner suppression.

If something does not match a known pattern, classify it as a **new pattern requiring analysis** rather than forcing it into an FP category.

## Important

This session is for **analysis only**.

Do not modify code or create PRs.

The goal is:

**Understand recurring FP patterns + identify recurring TP root causes + find opportunities to fix vulnerability classes centrally rather than repeatedly fixing individual findings.**





