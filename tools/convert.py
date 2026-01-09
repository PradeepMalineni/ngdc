from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from xml.etree import ElementTree as ET

from tachyon_client import TachyonClient, TachyonConfig, TachyonError


@dataclass(frozen=True)
class ExportBundle:
    export_xml_path: Path
    export_xml_text: str
    local_files: Dict[str, str]  # local:///name -> file contents
    mpgw_names: List[str]


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def _find_mpgw_names(export_root: ET.Element) -> List[str]:
    names: List[str] = []
    for el in export_root.iter():
        if el.tag.endswith("MultiProtocolGateway") and "name" in el.attrib:
            names.append(el.attrib["name"])
    # stable + unique
    seen = set()
    out: List[str] = []
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def _parse_export_bundle(export_xml_path: Path) -> ExportBundle:
    export_dir = export_xml_path.parent
    export_xml_text = _read_text(export_xml_path)

    # DataPower exports are often huge; using defusedxml would be nicer but we keep deps minimal.
    root = ET.fromstring(export_xml_text)

    # Extract <files><file name="local:///..." src="local/..." .../>
    local_files: Dict[str, str] = {}
    for file_el in root.iter():
        if not file_el.tag.endswith("file"):
            continue
        name = file_el.attrib.get("name", "")
        src = file_el.attrib.get("src", "")
        location = file_el.attrib.get("location", "")
        if not name.startswith("local:///"):
            continue
        if location and location != "local":
            continue
        if not src:
            continue

        src_path = export_dir / src
        if src_path.exists():
            local_files[name] = _read_text(src_path)
        else:
            local_files[name] = f"/* MISSING FILE: expected at {src_path} */\n"

    mpgw_names = _find_mpgw_names(root)

    return ExportBundle(
        export_xml_path=export_xml_path,
        export_xml_text=export_xml_text,
        local_files=local_files,
        mpgw_names=mpgw_names,
    )


def _read_target_framework(target_root: Path) -> Dict[str, str]:
    """
    Provide a compact context for the model: file list + a few key framework contents.
    """
    fw_dir = target_root / "Framework"
    if not fw_dir.exists():
        return {"_note": f"Framework directory not found at: {fw_dir}"}

    # Keep this lightweight: only include small files; list all.
    out: Dict[str, str] = {}
    for p in sorted(fw_dir.rglob("*")):
        if p.is_dir():
            continue
        rel = str(p.relative_to(target_root))
        try:
            text = _read_text(p)
        except Exception:
            continue
        if len(text) <= 20_000:
            out[rel] = text
        else:
            out[rel] = f"/* omitted (size={len(text)} bytes) */\n"

    # also include top-level framework xml if present
    top = target_root / "MPGW_GWS_Framework.xml"
    if top.exists():
        out[str(top.relative_to(target_root))] = _read_text(top)

    return out


def _build_prompt(app: str, bundle: ExportBundle, framework_ctx: Dict[str, str]) -> List[Dict[str, str]]:
    # Keep raw export.xml out of the prompt by default (it can be huge); include only relevant slices.
    # We'll include: found MPGW names + list of local files + their contents.
    local_file_list = "\n".join(sorted(bundle.local_files.keys()))
    mpgws = ", ".join(bundle.mpgw_names) if bundle.mpgw_names else "(none detected)"

    # Extract a compact snippet around the first MPGW tag for quick context.
    snippet = ""
    m = re.search(r"<MultiProtocolGateway[^>]*name=['\"][^'\"]+['\"][^>]*>", bundle.export_xml_text)
    if m:
        start = max(0, m.start() - 800)
        end = min(len(bundle.export_xml_text), m.start() + 5000)
        snippet = bundle.export_xml_text[start:end]
    else:
        snippet = bundle.export_xml_text[:6000]

    framework_files = "\n".join(sorted(k for k in framework_ctx.keys() if not k.startswith("_")))

    system = (
        "You are a senior IBM DataPower engineer. "
        "Convert a legacy DataPower service export into a new service that conforms to the provided Target framework. "
        "We deploy ONLY to DataPower PHYSICAL appliances (no container-only features). "
        "Prefer GatewayScript and XSLT 1.0 compatibility."
    )

    user = f"""
INPUTS
- App name: {app}
- Legacy export.xml path: {bundle.export_xml_path}
- MPGW(s) detected: {mpgws}

LEGACY EXPORT SNIPPET (for object names / policy wiring)
---BEGIN EXPORT SNIPPET---
{snippet}
---END EXPORT SNIPPET---

LEGACY local:/// FILES (available to you)
---BEGIN LOCAL FILE LIST---
{local_file_list}
---END LOCAL FILE LIST---

LEGACY local:/// FILE CONTENTS
---BEGIN LOCAL FILES---
{json.dumps(bundle.local_files, ensure_ascii=False)}
---END LOCAL FILES---

TARGET FRAMEWORK FILE LIST (existing)
---BEGIN TARGET FRAMEWORK FILE LIST---
{framework_files}
---END TARGET FRAMEWORK FILE LIST---

TARGET FRAMEWORK CONTENTS (existing)
---BEGIN TARGET FRAMEWORK CONTENTS---
{json.dumps(framework_ctx, ensure_ascii=False)}
---END TARGET FRAMEWORK CONTENTS---

TASK
- Produce a target-structure conversion for this legacy service.
- Use the Target framework conventions (GWS shared JS, XSL shared XSLT, common error handling).
- Keep names deterministic and easy to diff (no random suffixes).

OUTPUT FORMAT (STRICT)
Return ONLY valid JSON (no markdown) with this shape:
{{
  "summary": "short text",
  "files": [
    {{
      "path": "Target/<app>/<service>/.../file.ext",
      "content": "full file content as a string"
    }}
  ]
}}

Rules:
- Every path must be relative to the repo root.
- Do not modify existing Target/Framework/* files; create app/service-specific files under Target/{app}/...
- If you need to update Target/MPGW_GWS_Framework.xml, instead output a NEW file under Target/{app}/... and say how it is referenced in summary.
""".strip()

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _parse_llm_json(text: str) -> Dict[str, Any]:
    # Some models might wrap JSON with leading/trailing whitespace.
    text = text.strip()

    # If the model accidentally returns extra text, try to extract the first JSON object.
    if not text.startswith("{"):
        m = re.search(r"\{[\s\S]*\}$", text)
        if m:
            text = m.group(0)

    return json.loads(text)


def _safe_write_files(repo_root: Path, files: List[Dict[str, str]], *, dry_run: bool, force: bool) -> None:
    for f in files:
        rel = f.get("path", "")
        content = f.get("content", "")
        if not rel or not isinstance(rel, str):
            raise ValueError(f"Invalid file path entry: {f!r}")
        if not isinstance(content, str):
            raise ValueError(f"Invalid file content entry for {rel}")

        out_path = (repo_root / rel).resolve()
        if repo_root.resolve() not in out_path.parents and out_path != repo_root.resolve():
            raise ValueError(f"Refusing to write outside repo: {rel}")

        if out_path.exists() and not force:
            raise FileExistsError(f"Refusing to overwrite existing file without --force: {rel}")

        if dry_run:
            print(f"[dry-run] would write: {rel} ({len(content)} bytes)")
            continue

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
        print(f"[write] {rel}")


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Convert legacy DataPower export to Target structure using Tachyon API.")
    ap.add_argument("--app", required=True, help="App folder name under src/ (e.g., visa)")
    ap.add_argument("--export-xml", required=True, help="Path to legacy export.xml")
    ap.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]), help="Repo root path")
    ap.add_argument("--target-root", default="Target", help="Target folder path (relative to repo root)")
    ap.add_argument("--dry-run", action="store_true", help="Do not write files; just print what would happen")
    ap.add_argument("--force", action="store_true", help="Allow overwriting existing files")
    ap.add_argument("--temperature", type=float, default=0.2, help="LLM temperature")
    ap.add_argument("--max-tokens", type=int, default=4000, help="LLM max_tokens")
    args = ap.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    export_xml_path = Path(args.export_xml).resolve()
    target_root = (repo_root / args.target_root).resolve()

    if not export_xml_path.exists():
        print(f"export.xml not found: {export_xml_path}", file=sys.stderr)
        return 2

    bundle = _parse_export_bundle(export_xml_path)
    framework_ctx = _read_target_framework(target_root)
    messages = _build_prompt(args.app, bundle, framework_ctx)

    try:
        cfg = TachyonConfig.from_env()
        client = TachyonClient(cfg)
        raw = client.chat(messages, temperature=args.temperature, max_tokens=args.max_tokens)
    except TachyonError as e:
        print(f"Tachyon error: {e}", file=sys.stderr)
        return 3

    try:
        payload = _parse_llm_json(raw)
    except Exception as e:
        # Keep the raw output for debugging.
        dbg_dir = repo_root / "tools" / "out"
        dbg_dir.mkdir(parents=True, exist_ok=True)
        dbg_file = dbg_dir / "tachyon_raw_output.txt"
        dbg_file.write_text(raw, encoding="utf-8")
        print(f"Failed to parse model JSON. Raw output saved to: {dbg_file}", file=sys.stderr)
        print(f"Parse error: {e}", file=sys.stderr)
        return 4

    files = payload.get("files", [])
    if not isinstance(files, list):
        print("Model JSON missing 'files' list", file=sys.stderr)
        return 5

    _safe_write_files(repo_root, files, dry_run=args.dry_run, force=args.force)
    print("\nSummary:\n" + str(payload.get("summary", "")).strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

