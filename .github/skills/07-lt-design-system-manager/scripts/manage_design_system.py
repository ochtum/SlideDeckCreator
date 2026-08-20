#!/usr/bin/env python3
"""CRUD, validate, and preview LT design systems without overwriting siblings."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import re
import shutil
from typing import Any

import yaml


REGISTRY_KIND = "lt-design-system-registry"
SYSTEM_KIND = "lt-design-system"
COLOR_KEYS = ("background", "surface", "text", "muted_text", "primary", "secondary", "accent", "border", "success", "warning", "danger")
TYPOGRAPHY_KEYS = ("family", "mono_family", "title_px", "heading_px", "body_px", "detail_px", "source_px", "title_weight", "body_weight")


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def dump_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8")
    temporary.replace(path)


def registry_path(root: Path) -> Path:
    return root / "registry.yaml"


def empty_registry() -> dict[str, Any]:
    return {"schema_version": 1, "kind": REGISTRY_KIND, "systems": []}


def load_registry(root: Path, create: bool = False) -> dict[str, Any]:
    path = registry_path(root)
    if not path.exists():
        if not create:
            raise ValueError(f"registry does not exist: {path}")
        data = empty_registry()
        dump_yaml(path, data)
        return data
    data = load_yaml(path)
    if data.get("kind") != REGISTRY_KIND or not isinstance(data.get("systems"), list):
        raise ValueError(f"invalid registry: {path}")
    return data


def parse_hex(value: str) -> tuple[float, float, float]:
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", value or ""):
        raise ValueError(f"invalid color: {value}")
    rgb = [int(value[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    return tuple(component / 12.92 if component <= .04045 else ((component + .055) / 1.055) ** 2.4 for component in rgb)


def contrast(a: str, b: str) -> float:
    first = parse_hex(a)
    second = parse_hex(b)
    lum_a = .2126 * first[0] + .7152 * first[1] + .0722 * first[2]
    lum_b = .2126 * second[0] + .7152 * second[1] + .0722 * second[2]
    light, dark = max(lum_a, lum_b), min(lum_a, lum_b)
    return (light + .05) / (dark + .05)


def validate_spec(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != 1 or data.get("kind") != SYSTEM_KIND:
        errors.append("schema_version: 1 and kind: lt-design-system are required")
    system_id = str(data.get("id") or "")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", system_id):
        errors.append("id must use lowercase letters, numbers, and hyphens")
    if not str(data.get("name") or "").strip():
        errors.append("name is required")
    if not re.fullmatch(r"\d+\.\d+\.\d+", str(data.get("version") or "")):
        errors.append("version must use major.minor.patch")

    tokens = data.get("tokens") or {}
    canvas = tokens.get("canvas") or {}
    if canvas.get("width") != 1280 or canvas.get("height") != 720:
        errors.append("canvas must be 1280x720")
    if int(canvas.get("safe_margin") or 0) < 40:
        errors.append("canvas.safe_margin must be at least 40")

    colors = tokens.get("colors") or {}
    for key in COLOR_KEYS:
        if key not in colors:
            errors.append(f"tokens.colors.{key} is required")
        else:
            try:
                parse_hex(str(colors[key]))
            except ValueError as exc:
                errors.append(str(exc))
    typography = tokens.get("typography") or {}
    for key in TYPOGRAPHY_KEYS:
        if key not in typography:
            errors.append(f"tokens.typography.{key} is required")
    for key, minimum in (("title_px", 48), ("heading_px", 36), ("body_px", 24), ("detail_px", 20), ("source_px", 16)):
        if int(typography.get(key) or 0) < minimum:
            errors.append(f"tokens.typography.{key} must be at least {minimum}")

    components = data.get("components") or {}
    code = components.get("code") or {}
    conclusion = components.get("conclusion") or {}
    if all(key in colors for key in ("background", "surface", "text", "muted_text", "primary")):
        body_min = float((data.get("accessibility") or {}).get("body_contrast_min") or 4.5)
        checks = [
            ("background/text", colors["background"], colors["text"], body_min),
            ("surface/text", colors["surface"], colors["text"], body_min),
            ("background/muted_text", colors["background"], colors["muted_text"], body_min),
        ]
        conclusion_text = conclusion.get("text")
        if conclusion_text:
            checks.append(("primary/conclusion.text", colors["primary"], conclusion_text, 4.5))
        if code.get("background") and code.get("text"):
            checks.append(("code.background/code.text", code["background"], code["text"], 4.5))
        for label, background, foreground, minimum in checks:
            try:
                ratio = contrast(str(background), str(foreground))
                if ratio < minimum:
                    errors.append(f"contrast {label} is {ratio:.2f}:1; requires {minimum:.1f}:1")
            except ValueError as exc:
                errors.append(str(exc))

    accessibility = data.get("accessibility") or {}
    if accessibility.get("reduced_motion") is not True:
        errors.append("accessibility.reduced_motion must be true")
    if accessibility.get("color_only_meaning") is not False:
        errors.append("accessibility.color_only_meaning must be false")
    motion = data.get("motion") or {}
    if motion.get("energy") not in {"quiet", "standard", "expressive"}:
        errors.append("motion.energy must be quiet, standard, or expressive")
    limit = int(motion.get("strong_moment_limit_percent") or -1)
    if not 0 <= limit <= 25:
        errors.append("motion.strong_moment_limit_percent must be 0..25")
    return errors


def system_entry(spec: dict[str, Any], relative_path: str, created_at: str | None = None) -> dict[str, Any]:
    timestamp = now()
    return {
        "id": spec["id"], "name": spec["name"], "version": spec["version"],
        "status": spec.get("status", "active"), "path": relative_path,
        "description": spec.get("description", ""), "tags": spec.get("personality", []),
        "created_at": created_at or timestamp, "updated_at": timestamp,
    }


def ensure_safe_child(root: Path, child: Path) -> None:
    root_resolved = root.resolve()
    child_resolved = child.resolve()
    if child_resolved == root_resolved or root_resolved not in child_resolved.parents:
        raise ValueError(f"unsafe path outside design-system root: {child}")


def render_preview(spec: dict[str, Any]) -> str:
    colors = spec["tokens"]["colors"]
    typography = spec["tokens"]["typography"]
    shape = spec["tokens"].get("shape") or {}
    code = (spec.get("components") or {}).get("code") or {"background": "#07162C", "text": "#ECF4FF"}
    swatches = "".join(f'<div class="swatch"><i style="background:{escape(value)}"></i><b>{escape(key)}</b><code>{escape(value)}</code></div>' for key, value in colors.items())
    return f"""<!doctype html><html lang=\"ja\"><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width\"><title>{escape(spec['name'])} preview</title>
<style>:root{{--bg:{colors['background']};--surface:{colors['surface']};--text:{colors['text']};--muted:{colors['muted_text']};--primary:{colors['primary']};--secondary:{colors['secondary']};--accent:{colors['accent']};--border:{colors['border']};--radius:{int(shape.get('radius_card') or 20)}px}}*{{box-sizing:border-box}}body{{margin:0;padding:32px;background:#e8eef6;color:var(--text);font-family:{typography['family']}}}main{{max-width:1280px;margin:auto}}.slide{{aspect-ratio:16/9;background:var(--bg);padding:64px;border-radius:20px;box-shadow:0 18px 50px #152a4430;overflow:hidden}}h1{{font-size:{typography['title_px']}px;margin:0 0 18px}}h2{{font-size:{typography['heading_px']}px;margin:0 0 18px}}p,td,th{{font-size:{typography['body_px']}px}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}.card{{background:var(--surface);border:2px solid var(--border);border-radius:var(--radius);padding:24px}}.flow{{display:flex;align-items:center;gap:12px}}.node{{padding:18px;border-radius:var(--radius);background:var(--surface);border:2px solid var(--primary)}}.arrow{{font-size:36px;color:var(--secondary)}}table{{width:100%;border-collapse:collapse}}th{{background:var(--primary);color:#fff}}td,th{{padding:12px;border:1px solid var(--border);text-align:left}}pre{{padding:20px;border-radius:var(--radius);background:{code['background']};color:{code['text']};font:24px/1.5 {typography['mono_family']}}}.conclusion{{margin-top:24px;padding:22px;border-radius:var(--radius);background:var(--primary);color:#fff;font-size:34px;font-weight:900}}.swatches{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin-top:20px}}.swatch{{display:grid;grid-template-columns:48px 1fr;gap:4px 10px;align-items:center;background:#fff;padding:9px;border-radius:10px}}.swatch i{{grid-row:1/3;width:48px;height:48px;border-radius:8px;border:1px solid #7774}}.swatch code{{color:#445}}</style>
<main><section class=\"slide\"><h1>{escape(spec['name'])}</h1><p>{escape(spec.get('description',''))}</p><div class=\"grid\"><div class=\"card\"><h2>仕組みを読む</h2><div class=\"flow\"><span class=\"node\">入力</span><span class=\"arrow\">→</span><span class=\"node\">検証</span><span class=\"arrow\">→</span><span class=\"node\">完了</span></div><div class=\"conclusion\">判断できる具体物を残す</div></div><div class=\"card\"><table><tr><th>対象</th><th>確認</th></tr><tr><td>設定</td><td>値と使用箇所</td></tr><tr><td>変更</td><td>テスト結果</td></tr></table><pre><code>verify --target sample\nOK: 3 checks passed</code></pre></div></div></section><div class=\"swatches\">{swatches}</div></main></html>"""


def create_preview(system_dir: Path, spec: dict[str, Any]) -> Path:
    path = system_dir / "preview.html"
    path.write_text(render_preview(spec), encoding="utf-8")
    return path


def find_references(project_root: Path, design_root: Path, system_id: str) -> list[str]:
    references: list[str] = []
    allowed = {".yaml", ".yml", ".json", ".html", ".md"}
    for path in project_root.rglob("*"):
        if not path.is_file() or path.suffix.casefold() not in allowed:
            continue
        try:
            path.resolve().relative_to(design_root.resolve())
            continue
        except ValueError:
            pass
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        patterns = [f"id: {system_id}", f'id: "{system_id}"', f"data-design-system-id=\"{system_id}\"", f"design_system: {system_id}"]
        if any(pattern in content for pattern in patterns):
            references.append(path.resolve().as_posix())
    return references


def add(root: Path, spec_path: Path) -> None:
    spec = load_yaml(spec_path)
    errors = validate_spec(spec)
    if errors:
        raise ValueError("\n".join(errors))
    registry = load_registry(root, create=True)
    if any(item.get("id") == spec["id"] for item in registry["systems"]):
        raise ValueError(f"design system already exists; add never overwrites: {spec['id']}")
    system_dir = root / spec["id"]
    ensure_safe_child(root, system_dir)
    if system_dir.exists():
        raise ValueError(f"directory already exists: {system_dir}")
    dump_yaml(system_dir / "design-system.yaml", spec)
    create_preview(system_dir, spec)
    registry["systems"].append(system_entry(spec, f"{spec['id']}/design-system.yaml"))
    dump_yaml(registry_path(root), registry)
    print(f"ADDED: {spec['id']} {spec['version']}")


def update(root: Path, system_id: str, spec_path: Path) -> None:
    spec = load_yaml(spec_path)
    if spec.get("id") != system_id:
        raise ValueError("update cannot change id; use add for a new id")
    errors = validate_spec(spec)
    if errors:
        raise ValueError("\n".join(errors))
    registry = load_registry(root)
    entry = next((item for item in registry["systems"] if item.get("id") == system_id), None)
    if not entry:
        raise ValueError(f"unknown design system: {system_id}")
    system_dir = root / system_id
    ensure_safe_child(root, system_dir)
    current = system_dir / "design-system.yaml"
    if not current.exists():
        raise ValueError(f"missing current spec: {current}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    history = system_dir / "history" / f"{stamp}-{entry.get('version', 'unknown')}.yaml"
    history.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(current, history)
    dump_yaml(current, spec)
    create_preview(system_dir, spec)
    replacement = system_entry(spec, entry["path"], entry.get("created_at"))
    registry["systems"] = [replacement if item.get("id") == system_id else item for item in registry["systems"]]
    dump_yaml(registry_path(root), registry)
    print(f"UPDATED: {system_id} {entry.get('version')} -> {spec['version']}")


def remove(root: Path, project_root: Path, system_id: str, force: bool, purge: bool) -> None:
    registry = load_registry(root)
    entry = next((item for item in registry["systems"] if item.get("id") == system_id), None)
    if not entry:
        raise ValueError(f"unknown design system: {system_id}")
    references = find_references(project_root, root, system_id)
    if references and not force:
        raise ValueError("design system is in use:\n" + "\n".join(references))
    system_dir = root / system_id
    ensure_safe_child(root, system_dir)
    if system_dir.exists():
        if purge:
            shutil.rmtree(system_dir)
        else:
            archive = root / "_archive" / f"{system_id}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
            ensure_safe_child(root, archive)
            archive.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(system_dir), str(archive))
    registry["systems"] = [item for item in registry["systems"] if item.get("id") != system_id]
    dump_yaml(registry_path(root), registry)
    print(f"{'PURGED' if purge else 'ARCHIVED'}: {system_id}")


def validate_registry(root: Path) -> list[str]:
    registry = load_registry(root)
    errors: list[str] = []
    ids = [str(item.get("id") or "") for item in registry["systems"]]
    duplicates = sorted({value for value in ids if ids.count(value) > 1})
    if duplicates:
        errors.append("duplicate ids: " + ", ".join(duplicates))
    for item in registry["systems"]:
        spec_path = root / str(item.get("path") or "")
        try:
            spec_path.resolve().relative_to(root.resolve())
        except ValueError:
            errors.append(f"{item.get('id')}: path escapes root")
            continue
        if not spec_path.exists():
            errors.append(f"{item.get('id')}: missing spec {spec_path}")
            continue
        spec = load_yaml(spec_path)
        errors.extend(f"{item.get('id')}: {error}" for error in validate_spec(spec))
        if spec.get("id") != item.get("id") or spec.get("version") != item.get("version"):
            errors.append(f"{item.get('id')}: registry id/version does not match spec")
    return errors


class BindingParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.system_id = ""
        self.version = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if values.get("data-design-system-id"):
            self.system_id = values["data-design-system-id"]
            self.version = values.get("data-design-system-version", "")


def validate_binding(root: Path, story_path: Path, blueprint_path: Path, html_path: Path) -> list[str]:
    story = load_yaml(story_path)
    selected = story.get("design_system")
    if not selected:
        return []
    errors: list[str] = []
    system_id = str(selected.get("id") or "")
    version = str(selected.get("version") or "")
    registry = load_registry(root)
    entry = next((item for item in registry["systems"] if item.get("id") == system_id), None)
    if not entry:
        errors.append(f"selected design system is not registered: {system_id}")
    elif entry.get("version") != version:
        errors.append(f"registry version is {entry.get('version')}; Story requires {version}")
    blueprint = load_yaml(blueprint_path)
    blueprint_selected = blueprint.get("design_system") or {}
    if blueprint_selected.get("id") != system_id or blueprint_selected.get("version") != version:
        errors.append("Blueprint design_system id/version does not match Story")
    parser = BindingParser()
    parser.feed(html_path.read_text(encoding="utf-8"))
    if parser.system_id != system_id or parser.version != version:
        errors.append(f"HTML design-system binding is {parser.system_id or '(missing)'} {parser.version or '(missing)'}; expected {system_id} {version}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="LT design-system registry manager")
    sub = parser.add_subparsers(dest="command", required=True)
    init_parser = sub.add_parser("init")
    init_parser.add_argument("--root", type=Path, default=Path("config/design-systems"))
    list_parser = sub.add_parser("list")
    list_parser.add_argument("--root", type=Path, default=Path("config/design-systems"))
    add_parser = sub.add_parser("add")
    add_parser.add_argument("--root", type=Path, default=Path("config/design-systems"))
    add_parser.add_argument("--spec", type=Path, required=True)
    update_parser = sub.add_parser("update")
    update_parser.add_argument("--root", type=Path, default=Path("config/design-systems"))
    update_parser.add_argument("--id", required=True)
    update_parser.add_argument("--spec", type=Path, required=True)
    remove_parser = sub.add_parser("remove", aliases=["delete"])
    remove_parser.add_argument("--root", type=Path, default=Path("config/design-systems"))
    remove_parser.add_argument("--project-root", type=Path, default=Path.cwd())
    remove_parser.add_argument("--id", required=True)
    remove_parser.add_argument("--force", action="store_true")
    remove_parser.add_argument("--purge", action="store_true")
    preview_parser = sub.add_parser("preview")
    preview_parser.add_argument("--root", type=Path, default=Path("config/design-systems"))
    preview_parser.add_argument("--id", required=True)
    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument("--root", type=Path, default=Path("config/design-systems"))
    spec_parser = sub.add_parser("validate-spec")
    spec_parser.add_argument("--spec", type=Path, required=True)
    binding_parser = sub.add_parser("validate-binding")
    binding_parser.add_argument("--root", type=Path, default=Path("config/design-systems"))
    binding_parser.add_argument("--story", type=Path, required=True)
    binding_parser.add_argument("--blueprint", type=Path, required=True)
    binding_parser.add_argument("--html", type=Path, required=True)
    args = parser.parse_args()

    try:
        if args.command == "init":
            load_registry(args.root.resolve(), create=True)
            print(f"OK: {registry_path(args.root.resolve())}")
        elif args.command == "list":
            registry = load_registry(args.root.resolve())
            for item in registry["systems"]:
                print(f"{item['id']}\t{item['version']}\t{item['status']}\t{item['name']}")
        elif args.command == "add":
            add(args.root.resolve(), args.spec.resolve())
        elif args.command == "update":
            update(args.root.resolve(), args.id, args.spec.resolve())
        elif args.command in {"remove", "delete"}:
            remove(args.root.resolve(), args.project_root.resolve(), args.id, args.force, args.purge)
        elif args.command == "preview":
            registry = load_registry(args.root.resolve())
            entry = next((item for item in registry["systems"] if item.get("id") == args.id), None)
            if not entry:
                raise ValueError(f"unknown design system: {args.id}")
            spec_path = args.root.resolve() / entry["path"]
            print(create_preview(spec_path.parent, load_yaml(spec_path)))
        elif args.command == "validate":
            errors = validate_registry(args.root.resolve())
            if errors:
                raise ValueError("\n".join(errors))
            print("OK: registry and all design systems are valid")
        elif args.command == "validate-spec":
            errors = validate_spec(load_yaml(args.spec.resolve()))
            if errors:
                raise ValueError("\n".join(errors))
            print("OK: design-system spec is valid")
        elif args.command == "validate-binding":
            errors = validate_binding(args.root.resolve(), args.story.resolve(), args.blueprint.resolve(), args.html.resolve())
            if errors:
                raise ValueError("\n".join(errors))
            print("OK: Story, Blueprint, HTML design-system binding is valid")
        return 0
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
