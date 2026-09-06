#!/usr/bin/env python3
"""Render the two MUSE beginner guides using their small Markdown subset.

No third-party dependencies. Run from any directory after editing QUICKSTART*.md.
This is a renderer for these documents, not a general-purpose Markdown parser.
"""
import html
from pathlib import Path
import re

DOCS = Path(__file__).resolve().parents[1] / 'docs'
SECTIONS = ['intro', 'benefits', 'start', 'commands', 'day', 'lanes', 'switch', 'questions']
CONFIG = [
    ('QUICKSTART_CN.md', 'guide.html', 'zh-CN', '入门指南', '返回官网', 'English',
     'guide-en.html', '先认识 MUSE，再开始你的第一个项目。',
     ['三个指令', '每天怎么用', '换一个 AI', '常见问题'], '适用于 MUSE 3.6',
     '阅读 GitHub 版', '跳到正文'),
    ('QUICKSTART.md', 'guide-en.html', 'en', 'First steps', 'MUSE home', '简体中文',
     'guide.html', 'Meet MUSE, then start your first project.',
     ['Three commands', 'Daily use', 'Switch AI', 'Questions'], 'For MUSE 3.6',
     'Read on GitHub', 'Skip to content'),
]


def inline(text):
    text = html.escape(text)

    def link(match):
        label, url = match.groups()
        base = url.split('#')[0]
        if base == 'QUICKSTART_CN.md':
            url = url.replace(base, 'guide.html')
        elif base == 'QUICKSTART.md':
            url = url.replace(base, 'guide-en.html')
        elif base.startswith('CONTINUITY'):
            url = 'https://github.com/myths-labs/muse/blob/main/docs/' + url
        return '<a href="{}">{}</a>'.format(url, label)

    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link, text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    return re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)


def render_blocks(lines, faq=False):
    out = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')])
                i += 1
            headers = rows[0]
            out.append('<table><thead><tr>' + ''.join('<th scope="col">' + inline(c) + '</th>' for c in headers) + '</tr></thead><tbody>')
            for row in rows[2:]:
                out.append('<tr>' + ''.join('<td data-label="{}">{}</td>'.format(html.escape(headers[n], quote=True), inline(cell)) for n, cell in enumerate(row)) + '</tr>')
            out.append('</tbody></table>')
        elif line.startswith('- ') or re.match(r'^\d+\. ', line):
            ordered = not line.startswith('- ')
            pattern = r'^\d+\. ' if ordered else r'^- '
            items = []
            while i < len(lines) and re.match(pattern, lines[i]):
                items.append(re.sub(pattern, '', lines[i]))
                i += 1
            if faq and not ordered:
                for item in items:
                    match = re.fullmatch(r'\*\*(.+?)\*\*\s*(.*)', item)
                    if not match:
                        raise ValueError('FAQ needs a bold question followed by an answer')
                    out.append('<details><summary>{}</summary><p>{}</p></details>'.format(inline(match[1]), inline(match[2])))
            else:
                tag = 'ol' if ordered else 'ul'
                out.append('<{}>'.format(tag) + ''.join('<li>' + inline(item) + '</li>' for item in items) + '</{}>'.format(tag))
        elif line.startswith('> '):
            out.append('<blockquote><p>' + inline(line[2:]) + '</p></blockquote>')
            i += 1
        else:
            paragraph = [line]
            i += 1
            while i < len(lines) and lines[i].strip():
                paragraph.append(lines[i].strip())
                i += 1
            out.append('<p>' + inline(' '.join(paragraph)) + '</p>')
    return '\n'.join(out)


def main():
    for source, target, lang, label, home, other, other_url, description, toc, version, github_label, skip in CONFIG:
        text = (DOCS / source).read_text(encoding='utf-8')
        title = text.splitlines()[0][2:]
        parts = re.split(r'^## ', text, flags=re.MULTILINE)[1:]
        if len(parts) != len(SECTIONS):
            raise ValueError('Update SECTIONS when changing the guide structure')
        sections = []
        for identifier, part in zip(SECTIONS, parts):
            heading, body = part.split('\n', 1)
            sections.append('<section id="{}" aria-labelledby="{}-title"><h2 id="{}-title">{}</h2>\n{}\n</section>'.format(
                identifier, identifier, identifier, inline(heading), render_blocks(body.splitlines(), identifier == 'questions')))
        toc_html = ''.join('<a href="#{}">{}</a>'.format(key, name) for key, name in zip(['commands', 'day', 'switch', 'questions'], toc))
        github_url = 'https://github.com/myths-labs/muse/blob/main/docs/' + source
        page = '''<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} · MUSE</title>
  <meta name="description" content="{description}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="https://muse.mythslabs.ai/{target}">
  <link rel="canonical" href="https://muse.mythslabs.ai/{target}">
  <link rel="alternate" hreflang="zh-CN" href="https://muse.mythslabs.ai/guide.html">
  <link rel="alternate" hreflang="en" href="https://muse.mythslabs.ai/guide-en.html">
  <link rel="icon" href="https://raw.githubusercontent.com/myths-labs/muse/main/assets/logo.png" type="image/png">
  <link rel="stylesheet" href="guide.css">
</head>
<body>
  <!-- Generated by scripts/render-guides.py from docs/{source}. Edit the Markdown source. -->
  <a class="skip-link" href="#content">{skip}</a>
  <header class="guide-header"><a class="brand" href="./index.html" aria-label="{home}">MUSE<span> / {label}</span></a><nav aria-label="Language"><a href="{other_url}" lang="{other_lang}">{other}</a><a href="{github_url}">GitHub ↗</a></nav></header>
  <main id="content">
    <div class="guide-title"><p class="eyebrow">MUSE / {version}</p><h1>{title}</h1><p class="deck">{description}</p><nav class="guide-toc" aria-label="{label}">{toc_html}</nav></div>
    {sections}
  </main>
  <footer><a href="./index.html">← {home}</a><a href="{github_url}">{github_label} ↗</a></footer>
</body>
</html>
'''.format(lang=lang, title=html.escape(title), description=description, target=target,
           source=source, skip=skip, home=home, label=label, other_url=other_url,
           other_lang='en' if lang == 'zh-CN' else 'zh-CN', other=other,
           github_url=github_url, version=version, toc_html=toc_html,
           sections='\n    '.join(sections), github_label=github_label)
        (DOCS / target).write_text(page, encoding='utf-8')
        print('Rendered ' + target)


if __name__ == '__main__':
    main()
