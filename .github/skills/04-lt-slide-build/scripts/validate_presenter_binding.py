from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path


PROFILE_RE = re.compile(
    r'<section\b(?=[^>]*\bdata-role\s*=\s*(["\'])profile\1)[^>]*>(.*?)</section>',
    re.IGNORECASE | re.DOTALL,
)


class ProfileMarkupAudit(HTMLParser):
    TRACKED_CLASSES = {"profile-copy", "profile-name-note", "qr-card", "avatar-card"}
    VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[set[str]] = []
        self.text_by_class: dict[str, list[str]] = defaultdict(list)
        self.zone_names: list[str] = []
        self.classes: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        classes = set(values.get("class", "").split())
        self.classes.update(classes)
        if values.get("data-zone"):
            self.zone_names.append(values["data-zone"])
        if tag.lower() not in self.VOID_TAGS:
            self.stack.append(classes)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        classes = set(values.get("class", "").split())
        self.classes.update(classes)
        if values.get("data-zone"):
            self.zone_names.append(values["data-zone"])

    def handle_endtag(self, tag: str) -> None:
        if self.stack:
            self.stack.pop()

    def handle_data(self, data: str) -> None:
        if not data.strip():
            return
        for classes in self.stack:
            for class_name in classes & self.TRACKED_CLASSES:
                self.text_by_class[class_name].append(data)


def normalized_text(value: str) -> str:
    return re.sub(r'\s+', ' ', value).strip()


def visible_text(markup: str) -> str:
    markup = re.sub(r'<(script|style)\b[^>]*>.*?</\1\s*>', '', markup, flags=re.I | re.S)
    return html.unescape(re.sub(r'<[^>]+>', ' ', markup)).replace('\xa0', ' ')


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_string(data: dict, key: str, errors: list[str]) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f'presenter.json の {key} は空でない文字列である必要があります')
        return ''
    return value


def validate(html_path: Path, presenter_path: Path, presenter: dict) -> list[str]:
    errors: list[str] = []
    page = html_path.read_text(encoding='utf-8')
    profiles = PROFILE_RE.findall(page)
    if not profiles:
        return [f'{html_path}: data-role="profile" の section がありません']

    display_name = require_string(presenter, 'display_name', errors)
    name_note_value = presenter.get('name_note')
    if name_note_value is None:
        name_note = ''
    elif not isinstance(name_note_value, str) or not name_note_value.strip():
        errors.append('presenter.json の name_note は指定する場合、空でない文字列である必要があります')
        name_note = ''
    else:
        name_note = name_note_value
    bio = require_string(presenter, 'bio', errors)
    links = presenter.get('links')
    if not isinstance(links, list) or not links:
        errors.append('presenter.json の links は1件以上必要です')
        links = []

    for _, profile_html in profiles:
        text = visible_text(profile_html)
        audit = ProfileMarkupAudit()
        audit.feed(profile_html)
        allowed_zones = {"title", "visual", "text", "qr", "footer"}
        unexpected_zones = sorted(set(audit.zone_names) - allowed_zones)
        if unexpected_zones:
            errors.append(
                f'{html_path}: profile に presenter.json 以外の表示領域があります: {", ".join(unexpected_zones)}'
            )
        forbidden_classes = {"conclusion-bar", "message-ribbon", "talk-points", "anchor-row", "profile-extra"}
        found_forbidden = sorted(audit.classes & forbidden_classes)
        if found_forbidden:
            errors.append(
                f'{html_path}: profile に追加メッセージ用の要素があります: {", ".join(found_forbidden)}'
            )
        for label, expected in [('display_name', display_name), ('name_note', name_note), ('bio', bio)]:
            if expected and expected not in text:
                errors.append(f'{html_path}: profile に presenter.json の {label} が表示されていません: {expected}')
        for index, link in enumerate(links, start=1):
            if not isinstance(link, dict):
                errors.append(f'presenter.json の links[{index}] はオブジェクトである必要があります')
                continue
            platform = link.get('platform')
            account = link.get('account')
            if not isinstance(platform, str) or not isinstance(account, str) or not platform or not account:
                errors.append(f'presenter.json の links[{index}] には platform と account が必要です')
            elif platform not in text or account not in text:
                errors.append(f'{html_path}: profile に links[{index}] ({platform}: {account}) が表示されていません')

        expected_copy = normalized_text(
            ' '.join(
                [display_name, bio]
                + [
                    f'{link.get("platform", "")} {link.get("account", "")}'
                    for link in links
                    if isinstance(link, dict)
                ]
            )
        )
        actual_copy = normalized_text(' '.join(audit.text_by_class.get('profile-copy') or []))
        if actual_copy != expected_copy:
            errors.append(
                f'{html_path}: profile-copy の可視テキストは presenter.json の display_name / bio / links だけにしてください'
            )
        actual_name_note = normalized_text(' '.join(audit.text_by_class.get('profile-name-note') or []))
        if name_note and actual_name_note != normalized_text(name_note):
            errors.append(f'{html_path}: profile-name-note は presenter.json の name_note と一致させてください')
        elif not name_note and actual_name_note:
            errors.append(f'{html_path}: name_note 未指定時は profile-name-note を表示できません')
        if normalized_text(' '.join(audit.text_by_class.get('avatar-card') or [])):
            errors.append(f'{html_path}: avatar-card に presenter.json 以外の可視テキストを置けません')

        for kind, filename in [('avatar', 'presenter-avatar'), ('qr', 'presenter-qr')]:
            asset = presenter.get(kind)
            if not isinstance(asset, dict) or not asset.get('use'):
                continue
            source = asset.get('path')
            if not isinstance(source, str) or not source:
                errors.append(f'presenter.json の {kind}.path が必要です')
                continue
            source_path = Path(source)
            if not source_path.is_absolute():
                source_path = presenter_path.parent / source_path
            output_path = html_path.parent / 'assets' / f'{filename}{source_path.suffix}'
            if not source_path.is_file():
                errors.append(f'presenter.json の {kind}.path が存在しません: {source_path}')
            elif not output_path.is_file():
                errors.append(f'{html_path}: {kind} の出力assetがありません: {output_path}')
            elif digest(source_path) != digest(output_path):
                errors.append(f'{html_path}: {kind} の出力assetが presenter.json の path と一致しません')

        qr = presenter.get('qr')
        if isinstance(qr, dict) and qr.get('use'):
            label = qr.get('label')
            if not isinstance(label, str) or not label:
                errors.append('presenter.json の qr.label が必要です')
            elif label not in text:
                errors.append(f'{html_path}: profile に presenter.json の qr.label が表示されていません: {label}')
            actual_qr = normalized_text(' '.join(audit.text_by_class.get('qr-card') or []))
            if isinstance(label, str) and actual_qr != normalized_text(label):
                errors.append(f'{html_path}: qr-card の可視テキストは presenter.json の qr.label だけにしてください')
        elif audit.text_by_class.get('qr-card'):
            errors.append(f'{html_path}: qr.use=false のとき profile にQR表示を置けません')
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description='プロフィールスライドと presenter.json の反映を検証する')
    parser.add_argument('--presenter', required=True, type=Path)
    parser.add_argument('html', nargs='+', type=Path)
    args = parser.parse_args()

    try:
        presenter = json.loads(args.presenter.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        print(f'ERROR: presenter.json を読めません: {exc}')
        return 1
    if not isinstance(presenter, dict):
        print('ERROR: presenter.json のルートはオブジェクトである必要があります')
        return 1

    errors: list[str] = []
    for html_path in args.html:
        if not html_path.is_file():
            errors.append(f'HTMLがありません: {html_path}')
        else:
            errors.extend(validate(html_path, args.presenter, presenter))
    if errors:
        print('\n'.join(f'ERROR: {error}' for error in errors))
        return 1
    print(f'OK: presenter.json の内容が {len(args.html)} 件のプロフィールスライドへ反映されています')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
