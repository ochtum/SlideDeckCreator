#!/usr/bin/env python3
"""Check/update Copilot skill copies, translating only the skill root paths."""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".codex/skills"
TARGET = ROOT / ".github/skills"


def portable_text(value):
    return (value.replace(".codex/skills", ".github/skills")
            .replace(".codex\\skills", ".github\\skills")
            .replace('".codex", "skills"', '".github", "skills"'))


def main():
    parser = argparse.ArgumentParser(description="Codex版からCopilot版へスキルの変更を反映する。既定は差分確認のみ")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    changed = []
    for source in sorted(SOURCE.rglob("*")):
        if not source.is_file() or "__pycache__" in source.parts or "agents" in source.relative_to(SOURCE).parts:
            continue
        relative = source.relative_to(SOURCE)
        target = TARGET / relative
        try:
            expected = portable_text(source.read_text(encoding="utf-8"))
            actual = target.read_text(encoding="utf-8") if target.exists() else None
        except UnicodeDecodeError:
            expected = source.read_bytes()
            actual = target.read_bytes() if target.exists() else None
        if actual == expected:
            continue
        changed.append(str(relative))
        if args.write:
            target.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(expected, str):
                target.write_text(expected, encoding="utf-8")
            else:
                target.write_bytes(expected)
    if changed:
        print(("Updated" if args.write else "Differences") + f": {len(changed)} files")
        if not args.write:
            print("\n".join(changed))
            return 1
    else:
        print("OK: Codex/Copilot skill copies match (platform paths normalized)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
