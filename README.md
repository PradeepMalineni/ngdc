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
