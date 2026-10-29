#!/usr/bin/env python3
"""Regenerate references/bibliography.md from references/sources.json (deterministic)."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK_DATE = '2026年10月29日'


def bibliography_text(sources: dict) -> str:
    lines = ['# 参考文献と確認範囲', '', '[連載目次へ](../README.md)', '',
             f'この一覧は各回末尾の脚注と対応する。リンク先が原著そのものか、書誌・紹介ページかを `note` と `確認範囲` で区別している。確認日：{CHECK_DATE}。全文未確認の資料を、確認済みと表示しない。外部URLの生存は機械検査の対象外である。', '']
    for sid, s in sources.items():
        lines += [f'## {sid}', '', f'**{s["author"]} / {s["year"]}**', '', f'[{s["title"]}]({s["url"]})', '', s['note'], '', f'**今回の確認範囲：** {s["checked"]}', '']
    return '\n'.join(lines)


def main() -> int:
    sources = json.loads((ROOT / 'references/sources.json').read_text(encoding='utf-8'))
    (ROOT / 'references/bibliography.md').write_text(bibliography_text(sources), encoding='utf-8')
    print(f'wrote references/bibliography.md ({len(sources)} entries)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
