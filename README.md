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
