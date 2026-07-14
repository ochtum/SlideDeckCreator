from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path


PROFILE_RE = re.compile(
    r'<section\b(?=[^>]*\bdata-role\s*=\s*(["\'])profile\1)[^>]*>(.*?)</section>',
    re.IGNORECASE | re.DOTALL,
)


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
    bio = require_string(presenter, 'bio', errors)
    links = presenter.get('links')
    if not isinstance(links, list) or not links:
        errors.append('presenter.json の links は1件以上必要です')
        links = []

    for _, profile_html in profiles:
        text = visible_text(profile_html)
        for label, expected in [('display_name', display_name), ('bio', bio)]:
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
