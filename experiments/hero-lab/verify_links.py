#!/usr/bin/env python3
"""Check built study links, fragments, CSS assets and GitHub Pages prefixes."""
import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


class Links(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.urls = []
        self.ids = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in ('href', 'src', 'data-service-url', 'data-service-image') and value:
                self.urls.append(value)
            if name == 'id':
                self.ids.append(value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site-root', type=Path, default=Path('dist'))
    parser.add_argument('--base', default='')
    args = parser.parse_args()
    root, base = args.site_root.resolve(), args.base.rstrip('/')
    lab = root / 'hero-lab'
    errors, checked = [], 0
    pages = sorted(lab.glob('*.html'))
    for source in pages + sorted(lab.glob('*.css')):
        text = source.read_text()
        parsed = Links(text) if source.suffix == '.html' else None
        if parsed and len(parsed.ids) != len(set(parsed.ids)):
            errors.append(f'{source.name}: duplicate ids')
        urls = parsed.urls if parsed else re.findall(r'url\([\"\']?([^\)\"\']+)', text)
        for url in urls:
            parts = urlsplit(url)
            if parts.scheme or parts.netloc:
                continue
            route = unquote(parts.path)
            if route.startswith('/'):
                if base and not route.startswith(base + '/'):
                    errors.append(f'{source.name}: missing prefix: {url}')
                    continue
                target = root / route[len(base):].lstrip('/')
            else:
                target = source.parent / route if route else source
            if target.is_dir():
                target = target / 'index.html'
            if not target.is_file():
                errors.append(f'{source.name}: missing file: {url}')
            elif parts.fragment and target.suffix == '.html':
                if unquote(parts.fragment) not in Links(target.read_text()).ids:
                    errors.append(f'{source.name}: missing anchor: {url}')
            checked += 1
    if len(pages) != 25:
        errors.append(f'Expected 25 HTML files, found {len(pages)}')
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'PASS: {len(pages)} pages, {checked} internal references, base={base or "/"}')


if __name__ == '__main__':
    main()
