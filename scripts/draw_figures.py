#!/usr/bin/env python3
"""Generate every SVG illustration (cover + per-chapter figures) deterministically. Stdlib only.

図の方針: 1枚につき主張は1つ、パネルは2枚まで、ラベルは10個前後。矢印や色だけに意味を依存させず、ラベルでも区別する。
SVGには viewBox / role="img" / title / desc を持たせ、script・外部参照・フォントファイルは入れない。
"""
from __future__ import annotations
from html import escape
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'illustrations'
BG, INK, MUTED, LINE, SOFT = '#f7f5ef', '#232a33', '#5d6873', '#d8d4c8', '#ece9e0'
BLUE, AMBER, TEAL, PLUM = '#2b5f9e', '#c7792b', '#2f8f83', '#8a4f9e'
FONT = 'system-ui, -apple-system, "Hiragino Kaku Gothic ProN", "Noto Sans CJK JP", Meiryo, sans-serif'
CODE = 'MULTI-SCALE TIME'


class Figure:
    def __init__(self, number: int, title: str, subtitle: str, height: int = 620, part: str = '', accent: str = BLUE):
        self.h = height
        self.n = number
        self.part = part
        self.accent = accent
        self.defs: list[str] = []
        self._markers: dict[str, str] = {}
        self.body: list[str] = []
        self.title = title
        self.subtitle = subtitle
        self.gradients = 0
        shown = str(ord(part) - 96) if part.isalpha() and len(part) == 1 else part
        label = CODE if number == 0 else f'{CODE}     {number:02d}' + (f'     図{number}-{shown}' if part else '')
        self.text(50, 52, label, 18, accent, weight=700)
        self.text(50, 103, title, 34, weight=700)
        self.text(50, 141, subtitle, 21, MUTED)
        self.line(50, 166, 1150, 166, color=LINE, width=1)

    # --- primitives -------------------------------------------------------
    MIN_TEXT = 14

    def text(self, x, y, s, size=24, color=INK, anchor='start', weight=400, opacity=1.0):
        size = max(size, self.MIN_TEXT)
        op = f' opacity="{opacity}"' if opacity < 1 else ''
        self.body.append(f'<text x="{x:.1f}" y="{y:.1f}" fill="{color}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}"{op}>{escape(str(s))}</text>')

    def lines(self, x, y, items, size=19, color=INK, anchor='start', gap=None, weight=400):
        gap = gap or size * 1.45
        for i, s in enumerate(items):
            self.text(x, y + i * gap, s, size, color, anchor, weight)

    def _marker(self, color):
        """One arrowhead marker per stroke colour, so heads always match their lines."""
        if color not in self._markers:
            mid = f'arrow-{color.lstrip("#")}'
            self._markers[color] = mid
            self.defs.append(f'<marker id="{mid}" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto-start-reverse"><path d="M1,1 L9,5 L1,9" fill="none" stroke="{color}" stroke-width="1.4"/></marker>')
        return self._markers[color]

    def line(self, x1, y1, x2, y2, color=MUTED, width=2, arrow=False, dash=False, dots=False, opacity=1.0):
        extra = (f' marker-end="url(#{self._marker(color)})"' if arrow else '') + (' stroke-dasharray="8 7"' if dash else '') + (' stroke-dasharray="2 9" stroke-linecap="round"' if dots else '') + (f' opacity="{opacity}"' if opacity < 1 else '')
        self.body.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{width}"{extra}/>')

    def path(self, d, color=MUTED, width=2, arrow=False, dash=False, fill='none', opacity=1.0):
        extra = (f' marker-end="url(#{self._marker(color)})"' if arrow else '') + (' stroke-dasharray="8 7"' if dash else '') + (f' opacity="{opacity}"' if opacity < 1 else '')
        self.body.append(f'<path d="{d}" fill="{fill}" stroke="{color}" stroke-width="{width}"{extra}/>')

    def rect(self, x, y, w, h, fill='#ffffff', stroke=LINE, width=2, rx=12, dash=False, opacity=1.0):
        extra = (' stroke-dasharray="8 7"' if dash else '') + (f' opacity="{opacity}"' if opacity < 1 else '')
        self.body.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"{extra}/>')

    def box(self, x, y, w, h, title, subtitle='', color=BLUE, size=22, dash=False, fill='#ffffff'):
        self.rect(x, y, w, h, fill=fill, stroke=color, width=2, rx=14, dash=dash)
        self.text(x + w / 2, y + (h / 2 + 8 if not subtitle else h / 2 - 4), title, size, color, anchor='middle', weight=700)
        if subtitle:
            self.text(x + w / 2, y + h / 2 + 26, subtitle, 17, MUTED, anchor='middle')

    def circ(self, x, y, r=10, color=BLUE, fill=True, dash=False, width=2, opacity=1.0):
        op = f' opacity="{opacity}"' if opacity < 1 else ''
        if fill:
            self.body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{color}"{op}/>')
        else:
            extra = ' stroke-dasharray="7 6"' if dash else ''
            self.body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="none" stroke="{color}" stroke-width="{width}"{extra}{op}/>')

    def panel(self, x, y, w, h, label=''):
        self.rect(x, y, w, h, fill='none', stroke='#c9c4b6', width=2, rx=16, dash=True)
        if label:
            self.text(x + w / 2, y + 34, label, 23, INK, anchor='middle', weight=700)

    def blob(self, cx, cy, r, color, opacity=0.55):
        self.gradients += 1
        gid = f'g{self.n:02d}{self.part}-{self.gradients}'
        self.defs.append(f'<radialGradient id="{gid}"><stop offset="0" stop-color="{color}" stop-opacity="{opacity}"/><stop offset="0.55" stop-color="{color}" stop-opacity="{opacity*0.45:.2f}"/><stop offset="1" stop-color="{color}" stop-opacity="0"/></radialGradient>')
        self.body.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="url(#{gid})"/>')

    def wave(self, x0, x1, y, amp, periods, color=BLUE, width=2, steps=240, phase=0.0, opacity=1.0):
        pts = []
        for i in range(steps + 1):
            t = i / steps
            pts.append(f'{x0 + (x1 - x0) * t:.1f},{y - amp * math.sin(2 * math.pi * periods * t + phase):.1f}')
        op = f' opacity="{opacity}"' if opacity < 1 else ''
        self.body.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"{op}/>')

    def square_wave(self, x0, x1, y, amp, periods, color=BLUE, width=2):
        pts = [f'{x0:.1f},{y + amp:.1f}']
        seg = (x1 - x0) / periods
        for k in range(periods):
            a, b = x0 + k * seg, x0 + (k + 0.5) * seg
            pts += [f'{a:.1f},{y - amp:.1f}', f'{b:.1f},{y - amp:.1f}', f'{b:.1f},{y + amp:.1f}', f'{a + seg:.1f},{y + amp:.1f}']
        self.body.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="{width}"/>')

    def brace(self, x0, x1, y, down=True, color=MUTED):
        """A horizontal brace spanning x0..x1 with its point at y (pointing down if down)."""
        m = (x0 + x1) / 2
        s = 10 if down else -10
        d = f'M {x0:.1f} {y - s:.1f} Q {x0:.1f} {y:.1f} {x0 + 12:.1f} {y:.1f} L {m - 12:.1f} {y:.1f} Q {m:.1f} {y:.1f} {m:.1f} {y + s:.1f} Q {m:.1f} {y:.1f} {m + 12:.1f} {y:.1f} L {x1 - 12:.1f} {y:.1f} Q {x1:.1f} {y:.1f} {x1:.1f} {y - s:.1f}'
        self.path(d, color=color, width=1.6)

    def footer(self, s):
        if s:
            self.text(50, self.h - 28, s, 19, MUTED)

    def save(self, name: str):
        OUT.mkdir(parents=True, exist_ok=True)
        head = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{self.h}" viewBox="0 0 1200 {self.h}" role="img" aria-labelledby="title desc">',
                f'<title id="title">{escape(self.title)}</title>', f'<desc id="desc">{escape(self.subtitle)}</desc>',
                '<defs>' + ''.join(self.defs) + '</defs>', f'<rect width="1200" height="{self.h}" rx="20" fill="{BG}"/>',
                f'<g font-family=\'{FONT}\'>']
        (OUT / name).write_text('\n'.join(head + self.body + ['</g>', '</svg>']) + '\n', encoding='utf-8')
        return name


def log_axis(f, x0, x1, y, lo, hi, ticks, label='', color=MUTED):
    """A log10 axis from lo..hi (in the same unit) mapped to x0..x1. ticks: list of (value, label)."""
    def X(v):
        return x0 + (math.log10(v) - math.log10(lo)) / (math.log10(hi) - math.log10(lo)) * (x1 - x0)
    f.line(x0, y, x1 + 30, y, color=color, width=2, arrow=True)
    for v, t in ticks:
        x = X(v)
        f.line(x, y - 6, x, y + 6, color=color, width=1.5)
        f.text(x, y + 28, t, 16, MUTED, anchor='middle')
    if label:
        f.text(x1 + 36, y + 6, label, 16, MUTED)
    return X


def band(f, X, lo, hi, y, h, color, label='', sub='', text_color=None, min_w=10):
    x0, x1 = X(lo), X(hi)
    if x1 - x0 < min_w:
        x0, x1 = (x0 + x1) / 2 - min_w / 2, (x0 + x1) / 2 + min_w / 2
    f.rect(x0, y, x1 - x0, h, fill=color, stroke='none', width=0, rx=h / 2, opacity=0.78)
    if label:
        f.text(x0 - 14, y + h / 2 + 6, label, 17, text_color or INK, anchor='end')
    if sub:
        f.text(x1 + 12, y + h / 2 + 6, sub, 15, MUTED)


def person(f, x, y, color=INK, scale=1.0, lean=0.0):
    """A running silhouette: head, leaning torso, limbs with round caps. (x, y) is the hip."""
    s = scale
    f.circ(x + 10 * s * lean, y - 60 * s, 12 * s, color)
    f.body.append(f'<ellipse cx="{x + 5 * s * lean:.1f}" cy="{y - 26 * s:.1f}" rx="{11 * s:.1f}" ry="{24 * s:.1f}" transform="rotate({-18 * lean:.0f} {x + 5 * s * lean:.1f} {y - 26 * s:.1f})" fill="{color}"/>')
    for (x1, y1, x2, y2, w) in [(x, y - 4 * s, x - 22 * s, y + 34 * s, 8), (x, y - 4 * s, x + 24 * s, y + 28 * s, 8), (x + 4 * s, y - 38 * s, x - 22 * s, y - 20 * s, 6.5), (x + 4 * s, y - 38 * s, x + 26 * s, y - 46 * s, 6.5)]:
        f.body.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{w * s:.1f}" stroke-linecap="round"/>')


def loop_nodes(f, cx, cy, r, labels, color=BLUE, box_w=190, box_h=58, size=18, start=-math.pi / 2):
    """Nodes placed on a circle, connected clockwise with arrows. Returns the node centers."""
    n = len(labels)
    centers = []
    for i in range(n):
        a = start + 2 * math.pi * i / n
        centers.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    for i in range(n):
        a0 = start + 2 * math.pi * i / n
        a1 = start + 2 * math.pi * (i + 1) / n
        pad = 0.42 * (box_w / 2) / r + 0.08
        p0 = (cx + r * math.cos(a0 + pad), cy + r * math.sin(a0 + pad))
        p1 = (cx + r * math.cos(a1 - pad), cy + r * math.sin(a1 - pad))
        f.path(f'M {p0[0]:.1f} {p0[1]:.1f} A {r} {r} 0 0 1 {p1[0]:.1f} {p1[1]:.1f}', color=color, width=2.2, arrow=True)
    for (x, y), lab in zip(centers, labels):
        title, sub = (lab if isinstance(lab, tuple) else (lab, ''))
        f.box(x - box_w / 2, y - box_h / 2, box_w, box_h, title, sub, color, size)
    return centers


def main() -> None:
    series = json.loads((ROOT / 'series.json').read_text(encoding='utf-8'))
    expected = {'00-cover.svg'} | {Path(p).name for c in series['chapters'] for p in c['figures']}
    made: set[str] = set()

    # ------------------------------------------------------------------ 00 cover
    f = Figure(0, '時間はどのように生まれるのか', 'マルチ時間スケールから考える時間・意識・心、全8回', 660)
    rows = [('脳波', 'ミリ秒', 48, BLUE), ('心拍・呼吸', '秒', 14, TEAL), ('概日リズム', '約24時間', 5, AMBER), ('免疫記憶・学習', '日〜年', 2, PLUM), ('成長・加齢', '数十年', 0.5, MUTED)]
    for i, (name, unit, periods, color) in enumerate(rows):
        y = 232 + i * 62
        f.text(80, y + 6, name, 19, INK, weight=700)
        f.text(80, y + 28, unit, 14, MUTED)
        f.wave(240, 760, y, 16, periods, color, 2.2, phase=0.6 * i)
    f.rect(600, 196, 60, 340, fill=AMBER, stroke='none', width=0, rx=8, opacity=0.14)
    f.text(630, 190, 'いま', 20, AMBER, anchor='middle', weight=700)
    f.lines(840, 262, ['一つの身体の中で、', '異なる速さの過程が', '同時に進んでいる。', '', 'それらが重なり合うところに、', '私たちが「いま」と呼ぶ', '経験がある。'], 22, INK, gap=34)
    f.text(600, 592, '私たちの中には、複数の時間が流れている。', 30, BLUE, anchor='middle', weight=700)
    f.footer('時間の流れは知覚されるのではなく、生物の情報処理によって経験として構成される。')
    made.add(f.save('00-cover.svg'))

    # ------------------------------------------------------------------ 01-a
    f = Figure(1, '時計が測る30分と、経験される30分', '目盛りは同じでも、経験される長さは場面によって伸び縮みする', 560, 'a')
    f.text(80, 258, '時計の30分', 19, INK, weight=700)
    f.line(300, 252, 1060, 252, color=INK, width=2.5)
    for k in range(7):
        x = 300 + k * (760 / 6)
        f.line(x, 242, x, 262, color=INK, width=2)
        f.text(x, 286, f'{k*5}分', 15, MUTED, anchor='middle')
    f.text(80, 372, '退屈な会議', 19, INK, weight=700)
    f.text(80, 394, '長く感じる', 14, MUTED)
    f.rect(300, 350, 840, 36, fill=AMBER, stroke='none', width=0, rx=18, opacity=0.8)
    f.text(80, 462, '友人と過ごす', 19, INK, weight=700)
    f.text(80, 484, '一瞬で終わる', 14, MUTED)
    f.rect(300, 440, 300, 36, fill=TEAL, stroke='none', width=0, rx=18, opacity=0.8)
    f.line(300, 300, 300, 500, color=LINE, width=1, dash=True)
    f.line(1060, 300, 1060, 500, color=LINE, width=1, dash=True)
    f.text(1060, 520, '時計の上では同じ終点', 15, MUTED, anchor='middle')
    f.brace(300, 1140, 398, down=True)
    f.text(720, 424, '経験された長さ', 14, AMBER, anchor='middle')
    f.brace(300, 600, 488, down=True)
    f.text(450, 514, '経験された長さ', 14, TEAL, anchor='middle')
    f.footer('時計が間違っているのでも、感覚が不正確なのでもない。測っているものが異なる。')
    made.add(f.save('01-a-clock-and-experience.svg'))

    # ------------------------------------------------------------------ 01-d
    f = Figure(1, '主観的時間の三つの働き', '時間知覚、時間展望、時間概念。関係しているが同一ではない', 520, 'd')
    for i, lab in enumerate(['時間知覚', '時間展望', '時間概念']):
        f.panel(70 + i * 360, 200, 330, 290, lab)
    # perception: bird path
    f.path('M 110 420 C 180 300 270 300 360 330', color=BLUE, width=2.5, arrow=True)
    for t in [0.0, 0.2, 0.4, 0.6, 0.8]:
        x = 110 + 250 * t
        y = 420 - 150 * t + 110 * t * t
        f.circ(x, y, 5, BLUE, opacity=0.35 + 0.6 * t)
    f.text(235, 470, '進行中の変化を一続きに経験する', 15, MUTED, anchor='middle')
    # perspective: axis past-future with arcs
    f.line(470, 400, 740, 400, color=MUTED, width=2, arrow=True)
    f.text(470, 428, '過去', 15, MUTED)
    f.text(740, 428, '未来', 15, MUTED, anchor='end')
    f.circ(605, 400, 8, TEAL)
    f.text(605, 452, '現在', 15, TEAL, anchor='middle', weight=700)
    f.path('M 600 390 C 560 300 500 300 490 388', color=TEAL, width=2, arrow=True, dash=True)
    f.path('M 612 390 C 650 300 710 300 720 388', color=TEAL, width=2, arrow=True, dash=True)
    f.text(500, 300, '一年前の旅行', 14, INK, anchor='middle')
    f.text(712, 300, '来年の予定', 14, INK, anchor='middle')
    f.text(595, 470, '目の前にない過去と未来を扱う', 15, MUTED, anchor='middle')
    # concept: ordered boxes
    for k, lab in enumerate(['昨日', '今日', '明日']):
        x = 820 + k * 110
        f.box(x, 300, 90, 54, lab, '', AMBER, 18)
        if k < 2:
            f.line(x + 92, 327, x + 108, 327, color=AMBER, width=2, arrow=True)
    f.brace(820, 1130, 380, down=True)
    f.text(975, 412, '順序・期間・関係', 15, INK, anchor='middle')
    f.text(955, 470, '出来事を整合的な時間構造に組む', 15, MUTED, anchor='middle')
    f.footer('')
    made.add(f.save('01-d-three-aspects.svg'))

    # ------------------------------------------------------------------ 02-a
    f = Figure(2, '速すぎる変化と、遅すぎる変化', '変化として経験できるのは、両端のあいだの限られた範囲である', 560, 'a')
    X = log_axis(f, 150, 1050, 400, 1e-3, 1e5, [(1e-3, '1ms'), (1e-2, '10ms'), (1e-1, '0.1秒'), (1, '1秒'), (10, '10秒'), (100, '1分40秒'), (1e3, '17分'), (1e4, '約3時間'), (1e5, '約1日')], '')
    f.text(590, 462, '変化一回あたりの時間', 15, MUTED, anchor='middle')
    f.rect(X(0.03), 300, X(60) - X(0.03), 80, fill=TEAL, stroke='none', width=0, rx=12, opacity=0.18)
    f.text((X(0.03) + X(60)) / 2, 290, '変化として経験できる範囲', 18, TEAL, anchor='middle', weight=700)
    f.text((X(0.03) + X(60)) / 2, 346, '数十ミリ秒 〜 数十秒（感覚と課題で異なる）', 15, TEAL, anchor='middle')
    # fluorescent lamp (10ms period) on the left
    f.rect(160, 212, 140, 26, fill='#ffffff', stroke=AMBER, width=2, rx=13)
    f.square_wave(170, 290, 225, 7, 6, AMBER, 1.6)
    f.text(230, 262, '蛍光灯の点滅（周期10ms）', 14, INK, anchor='middle')
    f.line(X(0.01), 280, X(0.01), 392, color=AMBER, width=1.5, dash=True)
    f.text(X(0.01), 462, '速すぎる → 連続した光に見える', 15, AMBER, anchor='middle', weight=700)
    # star on the right
    f.path('M 920 236 C 960 206 1010 206 1050 236', color=PLUM, width=1.5, dash=True)
    for k, t in enumerate([0.1, 0.5, 0.9]):
        x = 920 + 130 * t
        y = 236 - 90 * t * (1 - t) * 4 * 0.33
        f.text(x, y + 5, '✦', 16 if k == 1 else 12, PLUM, anchor='middle')
    f.text(985, 262, '星の見かけの移動（1時間に約15°）', 14, INK, anchor='middle')
    f.line(X(3600), 280, X(3600), 392, color=PLUM, width=1.5, dash=True)
    f.text(X(3600), 462, '遅すぎる → 静止して見える', 15, PLUM, anchor='middle', weight=700)
    f.footer('どちらも物理的には変化しているのに、変化の流れとして経験できない。')
    made.add(f.save('02-a-too-fast-too-slow.svg'))

    # ------------------------------------------------------------------ 02-b
    f = Figure(2, '感覚と課題によって、時間スケールは異なる', '横軸は対数。帯の左端から右端までが、各感覚の代表的な範囲', 660, 'c')
    X = log_axis(f, 330, 1080, 548, 0.01, 1e4, [(0.01, '10μs'), (0.1, '100μs'), (1, '1ms'), (10, '10ms'), (100, '100ms'), (1000, '1秒'), (1e4, '10秒')], '')
    items = [('聴覚：二つの音の識別', 2, 5, BLUE), ('聴覚：音の方向の検出', 0.01, 0.7, BLUE), ('視覚：点滅の認識', 13, 100, TEAL), ('映像：60FPSのフレーム間隔', 16, 17.5, TEAL), ('触覚：振動の検出', 1, 10, AMBER), ('痛みへの反応', 450, 550, AMBER), ('味覚・嗅覚', 100, 3000, PLUM)]
    for i, (lab, lo, hi, color) in enumerate(items):
        band(f, X, lo, hi, 206 + i * 44, 24, color, lab, '', min_w=14)
    f.line(330, 196, 330, 540, color=LINE, width=1)
    f.footer('同一の測定方法による比較値ではなく、感覚・課題ごとの代表例である。')
    made.add(f.save('02-c-resolution-by-sense.svg'))

    # ------------------------------------------------------------------ 02-e
    f = Figure(2, '瞬間と持続', '瞬間は弁別できる最小の幅、持続は複数の出来事を一つの流れとして経験すること', 530, 'f')
    f.panel(70, 200, 500, 300, '瞬間')
    f.line(230, 288, 500, 288, color=LINE, width=1.5, arrow=True)
    f.line(230, 358, 500, 358, color=LINE, width=1.5, arrow=True)
    f.text(110, 268, '間隔が長い', 15, MUTED)
    f.circ(300, 262, 12, AMBER)
    f.circ(440, 262, 12, AMBER)
    f.text(520, 268, '二つの出来事', 15, INK)
    f.text(110, 338, '間隔が短い', 15, MUTED)
    f.circ(360, 332, 12, AMBER)
    f.circ(390, 332, 12, AMBER)
    f.text(520, 338, '一つに見える', 15, INK)
    f.brace(346, 404, 356, down=True)
    f.text(375, 392, '弁別できる最小の幅', 14, MUTED, anchor='middle')
    f.text(320, 432, '弁別できる最小の幅 ＝ その個体の「瞬間」', 15, INK, anchor='middle', weight=700)
    f.text(320, 470, '物理的には二つ。知覚の上では一つ。', 15, MUTED, anchor='middle')
    f.panel(630, 200, 500, 300, '持続')
    f.blob(880, 350, 190, TEAL, 0.35)
    notes = [(700, 380), (780, 340), (860, 360), (940, 320), (1020, 345)]
    for i, (x, y) in enumerate(notes):
        f.circ(x, y, 11, TEAL)
        f.line(x, y, x, y - 36, color=TEAL, width=2.5)
        if i < len(notes) - 1:
            nx, ny = notes[i + 1]
            f.path(f'M {x+10} {y-8} Q {(x+nx)/2} {min(y,ny)-50} {nx-10} {ny-8}', color=TEAL, width=1.6, arrow=True, dash=True)
    f.text(880, 440, '前の音が次の音へ残り、意味を変え合う', 15, INK, anchor='middle', weight=700)
    f.text(880, 470, '音の集合ではなく、一つのメロディーとして経験される', 15, MUTED, anchor='middle')
    f.footer('')
    made.add(f.save('02-f-moment-and-duration.svg'))

    # ------------------------------------------------------------------ 03-a
    f = Figure(3, '知覚は、予測と修正の往復で成立する', '感覚入力と生成モデルの予測が照合され、その差が内部モデルを更新する', 580, 'b')
    f.box(80, 420, 240, 90, '外界', '赤いバラから届く光', MUTED, 22)
    f.box(430, 420, 300, 90, '照合', '予測と入力の差 ＝ 予測誤差', AMBER, 22)
    f.box(430, 212, 300, 90, '生成モデル（内部モデル）', '過去の経験から形成', BLUE, 20)
    f.box(860, 316, 270, 90, '知覚', '「赤いバラ」として見える', TEAL, 22)
    f.line(325, 465, 425, 465, color=MUTED, width=2.2, arrow=True)
    f.text(375, 452, '感覚入力', 15, MUTED, anchor='middle')
    f.line(520, 306, 520, 416, color=BLUE, width=2.4, arrow=True)
    f.text(505, 366, '予測', 16, BLUE, anchor='end', weight=700)
    f.line(640, 416, 640, 306, color=AMBER, width=2.4, arrow=True)
    f.text(655, 366, '予測誤差 → 更新', 16, AMBER, weight=700)
    f.path('M 735 257 C 800 257 820 300 855 345', color=TEAL, width=2.2, arrow=True)
    f.text(760, 232, '推定された対象', 14, MUTED)
    f.text(600, 548, '入力を待って処理するだけではない。すでに持つモデルで入力を解釈している。', 17, INK, anchor='middle')
    f.footer('')
    made.add(f.save('03-b-generative-model-loop.svg'))

    # ------------------------------------------------------------------ 03-b
    f = Figure(3, '目を動かしても、世界は動かない', '網膜像は流れているのに、自分の運動を差し引いて安定した世界を推定している', 600, 'c')
    f.panel(70, 200, 480, 350, '網膜に映るもの')
    f.rect(120, 258, 380, 170, fill='#ffffff', stroke=LINE, width=2, rx=10)
    f.rect(200, 336, 70, 84, fill=SOFT, stroke=MUTED, width=1.5, rx=4)
    f.path('M 190 336 L 235 298 L 280 336 Z', color=MUTED, width=1.5, fill=SOFT)
    f.circ(380, 318, 26, TEAL, opacity=0.7)
    f.line(380, 344, 380, 420, color=MUTED, width=4)
    f.line(480, 452, 330, 452, color=AMBER, width=3.5, arrow=True)
    f.text(405, 478, '網膜像は左へ流れる', 15, AMBER, anchor='middle', weight=700)
    f.path('M 130 522 C 185 482 255 482 310 522', color=INK, width=3)
    f.path('M 130 522 C 185 548 255 548 310 522', color=INK, width=3)
    f.circ(222, 515, 11, INK)
    f.line(340, 515, 450, 515, color=INK, width=3, arrow=True)
    f.text(395, 545, '視線を右へ', 15, INK, anchor='middle', weight=700)
    f.panel(640, 200, 490, 350, '脳が行っていること')
    steps = [('① 目を動かす運動指令', BLUE), ('② 網膜像の変化を予測', BLUE), ('③ 実際の入力と照合', AMBER), ('④ 自分の運動による変化と外界の変化を区別', TEAL)]
    for i, (lab, color) in enumerate(steps):
        y = 252 + i * 62
        f.rect(670, y, 430, 40, fill='#ffffff', stroke=color, width=2, rx=10)
        f.text(885, y + 27, lab, 16, color, anchor='middle', weight=700)
        if i < 3:
            f.line(885, y + 42, 885, y + 60, color=MUTED, width=2.2, arrow=True)
    f.text(885, 520, '→ 世界は安定したものとして経験される', 17, INK, anchor='middle', weight=700)
    f.footer('安定しているのは網膜像ではなく、推定された世界である。')
    made.add(f.save('03-c-eye-movement.svg'))

    # ------------------------------------------------------------------ 03-f
    f = Figure(3, '時間スケールギャップを越えて、色が成立する', '光の振動から色の経験まで、時間スケールが上がるごとに情報の表現形式が変わる', 640, 'g')
    steps = [('光の振動', '数百兆Hz', BLUE), ('視細胞の応答', '数十ミリ秒', BLUE), ('神経回路の統合', '数十〜数百ミリ秒', TEAL), ('内部モデルの推定', '数百ミリ秒〜秒', AMBER), ('「赤いバラ」の経験', '色を持った対象', PLUM)]
    for i, (lab, sub, color) in enumerate(steps):
        x = 90 + i * 212
        y = 500 - i * 62
        f.box(x, y, 180, 76, lab, sub, color, 18)
        if i < len(steps) - 1:
            f.line(x + 184, y + 30, x + 210, y - 16, color=MUTED, width=2.2, arrow=True)
    f.wave(100, 280, 592, 7, 14, BLUE, 1.5)
    f.text(190, 618, '細かな変動', 14, MUTED, anchor='middle')
    f.blob(1040, 300, 60, PLUM, 0.5)
    f.text(1040, 232, '統合された質', 14, MUTED, anchor='middle')
    f.line(90, 600, 1130, 600, color=LINE, width=1)
    f.text(1130, 624, '時間スケール →', 15, MUTED, anchor='end')
    f.text(600, 212, '失われる情報がある一方で、上位の尺度で安定した特徴が成立する', 17, INK, anchor='middle')
    f.footer('')
    made.add(f.save('03-g-scale-gap-to-color.svg'))

    # ------------------------------------------------------------------ 04-a
    f = Figure(4, '直結する反応と、余白のある反応', '刺激と反応の間に、記憶・予測・複数の候補が介在するかどうか', 600, 'a')
    f.text(80, 236, '反射', 18, INK, weight=700)
    f.box(80, 252, 220, 70, '刺激', '熱い鍋に触れる', MUTED, 20)
    f.line(305, 287, 820, 287, color=AMBER, width=3, arrow=True)
    f.text(562, 276, '定型的な反応', 15, AMBER, anchor='middle', weight=700)
    f.box(830, 252, 290, 70, '反応', '手を引く', AMBER, 20)
    f.text(80, 390, '余白', 18, INK, weight=700)
    f.box(80, 406, 220, 70, '刺激', 'ひどい言葉を向けられる', MUTED, 20)
    f.line(305, 441, 345, 441, color=MUTED, width=2.2, arrow=True)
    f.rect(350, 372, 440, 150, fill='none', stroke=BLUE, width=2, rx=16, dash=True)
    f.text(570, 398, '時間的余白', 17, BLUE, anchor='middle', weight=700)
    for k, lab in enumerate(['記憶の参照', '未来の予測', '行動候補 A／B／C']):
        f.rect(372 + k * 136, 416, 124, 40, fill='#ffffff', stroke=BLUE, width=1.5, rx=8)
        f.text(434 + k * 136, 442, lab, 14, BLUE, anchor='middle')
    f.text(570, 500, '複数の可能性を評価し、一つを選ぶ', 15, MUTED, anchor='middle')
    f.line(795, 441, 825, 441, color=BLUE, width=2.2, arrow=True)
    f.box(830, 406, 290, 70, '反応', '言い返す／黙る／考える', BLUE, 20)
    f.footer('問題は時計で測った応答時間ではなく、入力と出力の間にどれだけの処理が介在するかである。')
    made.add(f.save('04-a-reflex-vs-deliberation.svg'))

    # ------------------------------------------------------------------ 04-d
    f = Figure(4, '一つの出来事に、三つの時間スケールが応答する', '反射、経験による修正、将来を見越した計画は、同じ身体の中で並行して成立する', 580, 'e')
    f.circ(150, 386, 16, AMBER)
    f.text(150, 428, '熱い鍋に', 15, INK, anchor='middle', weight=700)
    f.text(150, 448, '触れる', 15, INK, anchor='middle', weight=700)
    f.line(200, 250, 200, 500, color=LINE, width=1, dash=True)
    rows = [('反射：手を引く', '一瞬', 120, AMBER), ('修正：次から鍋つかみを使う', '次の機会', 420, TEAL), ('計画：配置と手順を見直す', '数日〜数週間', 820, BLUE)]
    for i, (lab, span, w, color) in enumerate(rows):
        y = 236 + i * 90 + 60
        f.rect(200, y - 14, w, 28, fill=color, stroke='none', width=0, rx=14, opacity=0.8)
        f.text(206 + w, y + 6, span, 15, color, weight=700)
        f.text(206, y - 24, lab, 16, INK)
    f.line(200, 500, 1080, 500, color=MUTED, width=2, arrow=True)
    for x, t in [(200, '0'), (320, '秒'), (620, '分〜時間'), (1020, '日〜週')]:
        f.line(x, 494, x, 506, color=MUTED, width=1.5)
        f.text(x, 528, t, 15, MUTED, anchor='middle')
    f.text(80, 236, '同じ身体の中で並行して応答する', 16, INK, weight=700)
    f.footer('進化が拡張したのは反応の遅さではなく、異なる時間スケールで情報を扱い行動を選ぶ能力である。')
    made.add(f.save('04-e-three-timescales.svg'))

    # ------------------------------------------------------------------ 04-e
    f = Figure(4, '意思決定が扱う時間幅が、実現できる行動を変える', '総予算は同じ。毎日使い切るか、三か月分をまとめて扱うかの違いだけである', 640, 'f')
    def panel_budget(y0, title, tall_day=None):
        f.text(80, y0 + 10, title, 18, INK, weight=700)
        base = y0 + 150
        f.line(300, base, 1100, base, color=MUTED, width=1.5)
        f.line(300, y0 + 20, 300, base, color=MUTED, width=1.5)
        goal = base - 120
        f.line(300, goal, 1100, goal, color=AMBER, width=1.5, dash=True)
        f.text(1104, goal + 5, '5万円', 15, AMBER, weight=700)
        for d in range(90):
            x = 304 + d * 8.8
            if tall_day is None:
                f.rect(x, base - 4, 6, 4, fill=BLUE, stroke='none', width=0, rx=1)
            elif d == tall_day:
                f.rect(x - 4, goal, 14, base - goal, fill=TEAL, stroke='none', width=0, rx=3)
            else:
                f.rect(x, base - 0.8, 6, 0.8, fill=LINE, stroke='none', width=0, rx=0)
        f.text(300, base + 24, '1日目', 14, MUTED, anchor='middle')
        f.text(1096, base + 24, '90日目', 14, MUTED, anchor='middle')
    panel_budget(200, '毎日1,000円を使い切る')
    f.text(700, 300, '毎日の支出は 1,000円（縮尺どおりなら棒の高さは2.4px。見やすさのため少し高くしてある）。どの日も 5万円には届かない。', 14, MUTED, anchor='middle')
    panel_budget(410, '三か月分をまとめて扱う', tall_day=50)
    f.text(560, 510, '支出のタイミングを選べる → 5万円の商品が買える', 15, TEAL, anchor='middle', weight=700)
    f.text(600, 624, '総予算は同じ。変わったのは、意思決定が扱う時間の幅だけである。', 17, INK, anchor='middle')
    f.footer('')
    made.add(f.save('04-f-budget-horizon.svg'))

    # ------------------------------------------------------------------ 05-a
    f = Figure(5, '倉庫としての記憶と、現在を構成する記憶', '保存して取り出す比喩から、過去の蓄積を素材に現在を組み上げる見方へ', 580, 'a')
    f.panel(70, 200, 500, 350, '倉庫としての記憶')
    for r in range(3):
        y = 262 + r * 66
        f.line(110, y + 40, 420, y + 40, color=MUTED, width=2)
        for c in range(3):
            f.rect(120 + c * 100, y, 80, 36, fill='#ffffff', stroke=MUTED, width=1.5, rx=6)
            f.text(160 + c * 100, y + 24, '出来事', 13, MUTED, anchor='middle')
    f.path('M 440 300 C 500 300 500 380 450 400', color=MUTED, width=2, arrow=True, dash=True)
    f.text(505, 300, '検索', 14, MUTED, anchor='middle')
    f.text(505, 424, '同じ内容を取り出す', 14, MUTED, anchor='middle')
    f.text(320, 520, '過去へアクセスするための仕組み', 15, MUTED, anchor='middle')
    f.panel(630, 200, 500, 350, '現在を構成する記憶')
    srcs = [('座った経験', 700, 280), ('「椅子」という言葉', 700, 360), ('見てきた椅子たち', 700, 440)]
    for lab, x, y in srcs:
        f.blob(x + 60, y, 54, BLUE, 0.4)
        f.text(x + 60, y + 5, lab, 14, INK, anchor='middle')
        f.path(f'M {x+120} {y} C {x+200} {y} {x+220} {360} {x+250} {360}', color=BLUE, width=1.8, arrow=True)
    f.box(960, 322, 150, 78, '目の前の物体', '→「椅子」', TEAL, 18)
    f.text(880, 500, '過去の蓄積を素材として、現在の認識が組み上がる', 15, INK, anchor='middle', weight=700)
    f.text(880, 524, '現在を構成するための仕組み', 15, MUTED, anchor='middle')
    f.footer('')
    made.add(f.save('05-a-warehouse-vs-construction.svg'))

    # ------------------------------------------------------------------ 05-c
    f = Figure(5, '記憶は時系列だけで整理されていない', '「海」を中心に、異なる時代・場所の記憶が類似性・近接性・感情で結ばれる', 720, 'c')
    cx, cy = 600, 380
    f.blob(cx, cy, 70, BLUE, 0.5)
    f.text(cx, cy + 8, '海', 28, BLUE, anchor='middle', weight=700)
    nodes = [('海水浴（子どもの頃）', 330, 280, 'solid'), ('旅行先の夕日', 870, 270, 'solid'), ('波の音', 300, 450, 'dash'), ('潮の香り', 900, 440, 'dash'), ('海の映画', 470, 540, 'dots'), ('そこで出会った人', 760, 545, 'dots')]
    for lab, x, y, kind in nodes:
        f.line(cx, cy, x, y, color=MUTED, width=2.4, dash=(kind == 'dash'), dots=(kind == 'dots'))
        f.rect(x - 90, y - 20, 180, 40, fill='#ffffff', stroke=LINE, width=1.5, rx=20)
        f.text(x, y + 6, lab, 14, INK, anchor='middle')
    f.line(330, 300, 300, 430, color=MUTED, width=1.2, dots=True)
    f.line(870, 290, 900, 420, color=MUTED, width=1.2, dash=True)
    f.text(1000, 214, '実線：類似性', 14, INK)
    f.line(1130, 209, 1160, 209, color=MUTED, width=1.8)
    f.text(1000, 238, '破線：近接性', 14, INK)
    f.line(1130, 233, 1160, 233, color=MUTED, width=1.8, dash=True)
    f.text(1000, 262, '点線：感情', 14, INK)
    f.line(1130, 257, 1160, 257, color=MUTED, width=1.8, dots=True)
    f.line(150, 620, 1050, 620, color=MUTED, width=2, arrow=True)
    f.text(150, 648, '子どもの頃', 14, MUTED)
    f.text(1050, 648, '現在', 14, MUTED, anchor='end')
    for x in [200, 380, 520, 700, 840, 960]:
        f.circ(x, 620, 5, AMBER)
    f.text(600, 600, '出来事が起きた順序（時系列）', 14, MUTED, anchor='middle')
    f.footer('同じ記憶でも、どの線をたどるかで別の記憶へつながる。')
    made.add(f.save('05-c-sea-network.svg'))

    # ------------------------------------------------------------------ 05-e
    f = Figure(5, '記憶の自己回帰', '想起→照合→新しい認識→蓄積の輪を回るごとに、記憶は重層化する', 582, 'e')
    loop_nodes(f, 400, 390, 130, [('想起', '過去の記憶を取り出す'), ('照合', '現在の情報と比べる'), ('新しい認識', '意味が変わる'), ('蓄積', '再び記憶になる')], BLUE, 190, 64, 18)
    f.path('M 500 460 C 640 500 700 470 790 460', color=AMBER, width=2.2, arrow=True, dash=True)
    f.text(650, 522, '一周ごとに', 14, AMBER, anchor='middle')
    for i in range(6):
        y = 500 - i * 42
        w = 240 - i * 10
        f.rect(1000 - w / 2, y, w, 34, fill=BLUE if i % 2 == 0 else TEAL, stroke='none', width=0, rx=8, opacity=0.25 + i * 0.1)
    f.text(1000, 548, '記憶の層が一枚増える', 15, INK, anchor='middle', weight=700)
    f.text(1000, 232, '量が増えるだけでなく、内部の関係を変えながら成長する', 14, MUTED, anchor='middle')
    f.footer('')
    made.add(f.save('05-e-recursive-memory.svg'))

    # ------------------------------------------------------------------ 06-c
    f = Figure(6, '「ミ」が鳴っている現在', '原初印象、保持、予感は並んでいるのではなく、一つの現在の中で結びついている', 560, 'd')
    f.line(150, 360, 1080, 360, color=MUTED, width=2, arrow=True)
    f.text(1086, 388, '時間', 14, MUTED)
    notes = [('ド', 330, '保持', '鳴り終わっても現在に残る', 0.45, False), ('ミ', 600, '原初印象', 'いま直接経験している', 1.0, False), ('ソ', 870, '予感', 'まだ鳴っていないが先取りされる', 1.0, True)]
    for name, x, role, desc, op, dashed in notes:
        if dashed:
            f.circ(x, 330, 22, TEAL, fill=False, dash=True, width=2.5)
        else:
            f.circ(x, 330, 22, TEAL, opacity=op)
        f.text(x, 338, name, 20, '#ffffff' if not dashed and op == 1 else INK, anchor='middle', weight=700)
        f.text(x, 268, role, 20, TEAL if role == '原初印象' else INK, anchor='middle', weight=700)
        f.text(x, 294, desc, 14, MUTED, anchor='middle')
        f.text(x, 400, '鳴り終わった' if name == 'ド' else ('鳴っている' if name == 'ミ' else '次に鳴る'), 14, MUTED, anchor='middle')
    f.path('M 356 322 C 440 250 520 250 578 318', color=MUTED, width=1.5, dash=True, arrow=True)
    f.path('M 622 318 C 680 250 760 250 846 320', color=MUTED, width=1.5, dash=True, arrow=True)
    f.rect(250, 230, 700, 200, fill=TEAL, stroke='none', width=0, rx=100, opacity=0.08)
    f.brace(250, 950, 450, down=True)
    f.text(600, 486, '一つの現在', 20, TEAL, anchor='middle', weight=700)
    f.footer('だから三つの音は、独立した刺激ではなくメロディーとして経験される。')
    made.add(f.save('06-d-melody-retention.svg'))

    # ------------------------------------------------------------------ 06-f
    f = Figure(6, '時刻としての現在と、心理的現在', '一点としての現在と、保持と予感を含んで未来へ開いた厚みのある現在', 568, 'h')
    f.text(80, 258, '時刻としての現在', 18, INK, weight=700)
    f.line(330, 270, 1080, 270, color=MUTED, width=2, arrow=True)
    f.circ(700, 270, 8, AMBER)
    f.text(700, 304, '12時00分00.000秒', 14, AMBER, anchor='middle')
    f.text(700, 240, '長さのない一点', 15, MUTED, anchor='middle')
    f.text(80, 440, '心理的現在', 18, INK, weight=700)
    f.line(330, 450, 1080, 450, color=MUTED, width=2, arrow=True)
    f.rect(520, 412, 180, 76, fill=TEAL, stroke='none', width=0, rx=10, opacity=0.35)
    f.rect(700, 412, 70, 76, fill=TEAL, stroke='none', width=0, rx=10, opacity=0.75)
    f.rect(770, 412, 150, 76, fill=TEAL, stroke='none', width=0, rx=10, opacity=0.35)
    f.path('M 920 412 L 990 412 L 1010 450 L 990 488 L 920 488', color=TEAL, width=2, dash=True)
    f.text(610, 396, '保持', 16, INK, anchor='middle', weight=700)
    f.text(735, 396, '原初印象', 16, TEAL, anchor='middle', weight=700)
    f.text(845, 396, '予感', 16, INK, anchor='middle', weight=700)
    f.text(1000, 396, '未完了', 15, MUTED, anchor='middle')
    f.text(1000, 520, '生じつつあるが、', 13, MUTED, anchor='middle')
    f.text(1000, 538, 'まだ出来上がっていない', 13, MUTED, anchor='middle')
    f.brace(520, 920, 500, down=True)
    f.text(720, 536, '幅のある現在（代表値 約0.5〜3秒。課題や注意で変わる）', 15, INK, anchor='middle')
    f.footer('')
    made.add(f.save('06-h-thick-present.svg'))

    # ------------------------------------------------------------------ 07-b
    f = Figure(7, '身体の中の、いくつもの時間スケール', '神経系から成長・発達まで、一つの身体の中で異なる速さの過程が同時に進む', 660, 'b')
    year = 365.25 * 86400
    X = log_axis(f, 330, 1080, 556, 1e-3, 10 * year, [(1e-3, '1ms'), (1, '1秒'), (60, '1分'), (3600, '1時間'), (86400, '1日'), (year, '1年'), (10 * year, '10年')], '')
    items = [('神経系', 1e-3, 1, BLUE, '情報伝達・感覚・運動'), ('内分泌系', 1, 3 * 86400, AMBER, 'ホルモンによる調節'), ('免疫系', 60, year, PLUM, '防御・炎症・免疫記憶'), ('代謝系', 1e-3, 86400, TEAL, 'エネルギーの生成と利用'), ('成長・発達', 86400, 10 * year, MUTED, '身体構造と機能の変化')]
    for i, (lab, lo, hi, color, sub) in enumerate(items):
        y = 216 + i * 60
        band(f, X, lo, hi, y, 30, color, lab)
        f.text(X(lo) + 12, y + 20, sub, 13, '#ffffff' if color != MUTED else INK)
    f.line(330, 200, 330, 546, color=LINE, width=1)
    f.footer('帯は重なり合い、同じ身体の中で同時に進行している。範囲は単純化した代表例。')
    made.add(f.save('07-b-body-timescales.svg'))

    # ------------------------------------------------------------------ 07-c
    f = Figure(7, '身体は、脳に何を伝えているのか', '坂道を走る場面。外受容・自己受容・内受容の三つの流れが脳へ集まり、行動の調整として返される', 640, 'c')
    f.path('M 120 560 L 720 400', color=MUTED, width=3)
    f.path('M 120 560 L 720 560 L 720 400 Z', color='none', width=0, fill=SOFT)
    person(f, 470, 430, INK, 1.4, 0.4)
    f.box(470, 206, 260, 70, '脳', '内部モデルで統合・推定', BLUE, 22)
    f.text(220, 300, '外受容感覚', 17, TEAL, anchor='middle', weight=700)
    f.text(220, 322, '傾斜・障害物', 14, MUTED, anchor='middle')
    f.path('M 250 332 C 300 360 360 300 465 250', color=TEAL, width=2.2, arrow=True)
    f.circ(170, 440, 10, TEAL)
    f.text(170, 470, '視覚', 13, MUTED, anchor='middle')
    f.path('M 185 436 C 220 400 230 360 220 334', color=TEAL, width=1.5, dash=True)
    f.text(300, 470, '自己受容感覚', 17, AMBER, anchor='middle', weight=700)
    f.text(300, 492, '脚の動き・姿勢', 14, MUTED, anchor='middle')
    f.path('M 350 458 C 400 400 430 330 475 284', color=AMBER, width=2.2, arrow=True)
    f.text(880, 300, '内受容感覚', 17, PLUM, anchor='middle', weight=700)
    f.text(880, 322, '心拍・呼吸・疲労', 14, MUTED, anchor='middle')
    f.path('M 850 332 C 800 360 760 300 735 250', color=PLUM, width=2.2, arrow=True)
    f.text(880, 370, '♥', 24, PLUM, anchor='middle')
    f.path('M 735 230 C 900 230 980 380 900 520', color=BLUE, width=2.4, arrow=True)
    f.text(1010, 440, '走る速さの調整', 16, BLUE, anchor='middle', weight=700)
    f.text(1010, 462, '行動として身体へ返す', 13, MUTED, anchor='middle')
    f.footer('身体の状態は付随情報ではなく、注意・判断・行動を変える入力である。')
    made.add(f.save('07-c-three-senses.svg'))

    # ------------------------------------------------------------------ 07-h
    f = Figure(7, '世界へ働きかける循環と、その中にいる観察者', '能動的推論の輪と、観察者自身を輪の中に置く二次サイバネティクス', 626, 'i')
    f.panel(70, 196, 520, 400, '能動的推論')
    loop_nodes(f, 330, 410, 118, [('感覚入力', ''), ('行動', '世界へ働きかける'), ('環境の変化', '次の入力になる'), ('内部モデルの更新', '')], BLUE, 170, 56, 16)
    f.text(330, 578, '知覚と行動は循環している', 15, INK, anchor='middle', weight=700)
    f.panel(640, 196, 490, 400, '二次サイバネティクス')
    f.rect(680, 260, 410, 300, fill='none', stroke=PLUM, width=2, rx=22)
    f.text(885, 288, '観察者 ＝ システムの一部', 16, PLUM, anchor='middle', weight=700)
    loop_nodes(f, 850, 430, 84, ['感覚入力', '行動', '環境', '内部モデル'], BLUE, 120, 42, 13)
    f.box(960, 460, 120, 56, '身体の状態', '心拍・注意', AMBER, 14)
    f.path('M 996 456 C 986 448 966 444 944 440', color=AMBER, width=1.8, arrow=True, dash=True)
    f.text(885, 580, '経験する主体自身が、経験の成立過程に組み込まれている', 14, INK, anchor='middle', weight=700)
    f.footer('')
    made.add(f.save('07-i-active-inference-loop.svg'))

    # ------------------------------------------------------------------ 08-b
    f = Figure(8, '一つの身体の中の複数の時計', '脳波から成長・加齢まで、尺度の異なる周期が互いに影響し合っている', 640, 'b')
    f.rect(70, 196, 1060, 380, fill='none', stroke=LINE, width=2, rx=60)
    f.text(600, 226, 'ひとつの身体', 18, MUTED, anchor='middle')
    clocks = [('脳波', 'ミリ秒', 40, BLUE), ('心拍・呼吸', '秒', 12, TEAL), ('概日リズム', '約24時間', 4, AMBER), ('免疫記憶・学習', '日〜年', 1.5, PLUM), ('成長・加齢', '数十年', 0.5, MUTED)]
    for i, (lab, unit, periods, color) in enumerate(clocks):
        x = 180 + i * 210
        f.circ(x, 330, 44, color, fill=False, width=2.5)
        nt = [24, 12, 8, 6, 4][i]
        for k in range(nt):
            a = 2 * math.pi * k / nt
            f.line(x + 38 * math.cos(a), 330 + 38 * math.sin(a), x + 44 * math.cos(a), 330 + 44 * math.sin(a), color=color, width=1.5)
        ah = math.radians([-60, 10, 80, 150, 220][i])
        f.line(x, 330, x + 30 * math.cos(ah), 330 + 30 * math.sin(ah), color=color, width=2.5)
        f.line(x, 330, x + 18 * math.cos(ah + 2.2), 330 + 18 * math.sin(ah + 2.2), color=color, width=2)
        f.text(x, 404, lab, 17, INK, anchor='middle', weight=700)
        f.text(x, 426, unit, 14, MUTED, anchor='middle')
        f.wave(x - 70, x + 70, 470, 10, periods, color, 1.8)
    f.path('M 1010 262 C 800 236 400 236 190 262', color=AMBER, width=2, arrow=True)
    f.text(600, 252, '長い尺度の状態が、短い尺度の反応を変える', 14, AMBER, anchor='middle', weight=700)
    f.path('M 190 540 C 400 566 800 566 1010 540', color=BLUE, width=2, arrow=True)
    f.text(600, 548, '短い尺度の反復が、長い尺度の変化を生む', 14, BLUE, anchor='middle', weight=700)
    f.footer('時計とは時刻を測る装置ではなく、固有の尺度で状態を変える過程のことである。')
    made.add(f.save('08-b-many-clocks.svg'))

    # ------------------------------------------------------------------ 08-c
    f = Figure(8, '時間的な凝縮の階層', '下位の多数の変化が、上位で少数のまとまりへ凝縮され、表現形式が変わる', 624, 'd')
    layers = [('階層0', '物質的な変化', 60, 4, BLUE), ('階層1', '感覚・神経処理（約2ミリ秒）', 16, 10, BLUE), ('階層2', '知覚統合（約0.5〜3秒）', 4, 24, TEAL), ('階層3', '長期記憶', 1, 44, AMBER)]
    for i, (name, desc, count, size, color) in enumerate(layers):
        y = 580 - i * 100
        f.text(80, y - 10, name, 18, INK, weight=700)
        f.text(80, y + 14, desc, 14, MUTED)
        x0, x1 = 360, 1000
        if count == 1:
            f.rect(x0, y - 22, x1 - x0, size, fill=color, stroke='none', width=0, rx=10, opacity=0.75)
        else:
            step = (x1 - x0) / count
            for k in range(count):
                f.rect(x0 + k * step + 2, y - size / 2, max(step - 4, 3), size, fill=color, stroke='none', width=0, rx=3, opacity=0.7)
        if i < 3:
            f.line(680, y - 34, 680, y - 64, color=MUTED, width=2, arrow=True)
            f.text(700, y - 46, '凝縮', 14, MUTED)
    f.lines(1030, 300, ['失われる情報と、', '新たに成立する', '特徴の両方がある'], 14, INK, gap=20)
    f.text(600, 212, '四つの層は実在する処理層ではなく、考えるためのモデルである', 15, MUTED, anchor='middle')
    f.footer('')
    made.add(f.save('08-d-condensation-hierarchy.svg'))

    # ------------------------------------------------------------------ 08-f
    f = Figure(8, '現在の経験を構成する、由来の異なる情報', '感覚入力、直前の保持、遠い過去の記憶、未来への予測が「いま」で重なる', 620, 'g')
    cx, cy = 600, 370
    f.blob(cx - 120, cy - 40, 120, TEAL, 0.35)
    f.blob(cx + 120, cy - 40, 120, BLUE, 0.35)
    f.blob(cx - 120, cy + 60, 120, PLUM, 0.3)
    f.blob(cx + 120, cy + 60, 120, AMBER, 0.35)
    f.circ(cx, cy + 10, 30, '#ffffff')
    f.circ(cx, cy + 10, 30, INK, fill=False, width=2.5)
    f.text(cx, cy + 18, 'いま', 20, INK, anchor='middle', weight=700)
    f.text(cx - 180, cy - 60, '現在の感覚入力', 17, TEAL, anchor='middle', weight=700)
    f.text(cx - 180, cy - 38, '音を聴く', 14, MUTED, anchor='middle')
    f.text(cx + 180, cy - 60, '直前の保持', 17, BLUE, anchor='middle', weight=700)
    f.text(cx + 180, cy - 38, '前の音', 14, MUTED, anchor='middle')
    f.text(cx - 180, cy + 90, '遠い過去の記憶', 17, PLUM, anchor='middle', weight=700)
    f.text(cx - 180, cy + 112, 'メロディーの構造', 14, MUTED, anchor='middle')
    f.text(cx + 180, cy + 90, '未来への予測', 17, AMBER, anchor='middle', weight=700)
    f.text(cx + 180, cy + 112, '次の音', 14, MUTED, anchor='middle')
    f.line(150, 560, 1050, 560, color=MUTED, width=2, arrow=True)
    for x, t, color in [(220, '遠い過去', PLUM), (560, '直前', BLUE), (640, 'いま', TEAL), (760, '次', AMBER)]:
        f.circ(x, 560, 7, color)
        f.text(x, 590, t, 14, color, anchor='middle', weight=700)
    f.text(1056, 566, '時間', 13, MUTED)
    f.footer('')
    made.add(f.save('08-g-present-composed.svg'))

    # ------------------------------------------------------------------ 08-i
    f = Figure(8, '全8回の論理の到達点', '時間知覚の制約から、マルチ時間スケールによる時間経験の成立へ', 680, 'l')
    rows = [('時間知覚の制約', '個体ごとに識別可能な時間スケールが異なる', '第1・2回', BLUE), ('情報の粗視化と再構成', '物理的変化が知覚可能な情報へ変換される', '第2・3回', BLUE), ('意識の時間的内部', '遅延が記憶の参照と行動選択を可能にする', '第4回', TEAL), ('記憶と予測による現在の構成', '過去の保持・現在の知覚・未来の予感が統合される', '第5・6回', TEAL), ('身体と環境の相互作用', '異なる時間スケールの生体システムが相互に影響する', '第7回', AMBER), ('マルチ時間スケールによる時間経験の成立', '複数の時間的過程が統合され、一つの「現在」が経験される', '第8回', PLUM)]
    for i, (title, desc, ch, color) in enumerate(rows):
        y = 572 - i * 66
        f.rect(140, y, 760, 52, fill='#ffffff', stroke=color, width=2, rx=12)
        f.text(170, y + 32, title, 18, color, weight=700)
        f.text(880, y + 32, desc, 14, MUTED, anchor='end')
        f.text(930, y + 32, ch, 15, INK)
    f.line(110, 624, 110, 220, color=MUTED, width=2.5, arrow=True)
    f.body.append(f'<text transform="rotate(-90 92 430)" x="92" y="430" fill="{MUTED}" font-size="15" text-anchor="middle" font-weight="700">積み上げ</text>')
    f.footer('時間の流れは単に知覚されるのではなく、生物の情報処理によって経験として構成される。')
    made.add(f.save('08-l-series-summary.svg'))

    # ================================================================== 追加の30点（2026-10-29 増補）

    # ------------------------------------------------------------------ 01-b second-definition
    f = Figure(1, '1秒は、繰り返す変化を数えて決められている', '地球の自転からセシウム原子へ。基準は変わっても、周期を数えて他の出来事を比べる装置である点は同じ', 580, 'b')
    f.panel(70, 200, 500, 300, '地球の自転')
    f.circ(220, 350, 70, BLUE, fill=False, width=3)
    f.path('M 220 280 A 70 70 0 1 1 150 350', color=BLUE, width=2.2, arrow=True)
    f.line(220, 290, 220, 410, color=LINE, width=1.5, dash=True)
    f.text(220, 358, '1日', 22, BLUE, anchor='middle', weight=700)
    f.lines(330, 320, ['1日 ÷ 24 ÷ 60 ÷ 60', '= 1日の 86,400 分の 1', '＝ かつての 1秒'], 18, INK, gap=30)
    f.text(320, 470, '自転は完全には一定ではない', 14, MUTED, anchor='middle')
    f.panel(630, 200, 500, 300, 'セシウム133原子')
    f.circ(780, 350, 10, AMBER)
    for r in (28, 46, 64):
        f.circ(780, 350, r, AMBER, fill=False, width=1.5)
    f.wave(860, 1100, 350, 14, 12, AMBER, 2)
    f.text(980, 392, '遷移に対応する放射', 14, MUTED, anchor='middle')
    f.lines(880, 300, ['9,192,631,770 回の振動', '＝ 現在の 1秒（SI）'], 18, INK, gap=30)
    f.text(880, 470, '原子の性質は安定した基準になる', 14, MUTED, anchor='middle')
    f.text(600, 540, '時間そのものを取り出すのではなく、周期的な変化を数えて、他の出来事を比べる。それが時計である。', 17, INK, anchor='middle')
    made.add(f.save('01-b-second-definition.svg'))

    # ------------------------------------------------------------------ 01-c common-time
    f = Figure(1, '共通の時間があるから、出来事を比べ、順序づけ、同期できる', '一本の時間軸の上に、列車・取引・記録・期限を並べて見る', 570, 'c')
    f.line(120, 400, 1080, 400, color=INK, width=2.5, arrow=True)
    for k in range(7):
        x = 150 + k * 140
        f.line(x, 392, x, 408, color=INK, width=1.5)
        f.text(x, 432, f'10:{k*5:02d}', 14, MUTED, anchor='middle')
    f.text(1086, 405, '共通の時刻', 14, MUTED)
    f.rect(150, 300, 420, 32, fill=BLUE, stroke='none', width=0, rx=16, opacity=0.8)
    f.text(360, 322, '列車：10:00 発 → 10:30 着', 15, '#ffffff', anchor='middle', weight=700)
    f.line(150, 332, 150, 392, color=BLUE, width=1, dash=True)
    f.line(570, 332, 570, 392, color=BLUE, width=1, dash=True)
    f.circ(486, 250, 9, AMBER)
    f.text(486, 232, '売買成立 10:12:05', 14, AMBER, anchor='middle', weight=700)
    f.line(486, 259, 486, 392, color=AMBER, width=1, dash=True)
    f.circ(780, 250, 9, TEAL)
    f.text(780, 232, 'ログの記録 10:22:30', 14, TEAL, anchor='middle', weight=700)
    f.line(780, 259, 780, 392, color=TEAL, width=1, dash=True)
    f.rect(900, 300, 170, 32, fill=PLUM, stroke='none', width=0, rx=16, opacity=0.8)
    f.text(985, 322, '契約の期限 10:30', 14, '#ffffff', anchor='middle', weight=700)
    f.line(1010, 332, 1010, 392, color=PLUM, width=1, dash=True)
    f.text(600, 488, '比較 ・ 順序づけ ・ 同期', 20, INK, anchor='middle', weight=700)
    f.footer('時計で測れることと、時間がどのような存在かは別の問題である。')
    made.add(f.save('01-c-common-time.svg'))

    # ------------------------------------------------------------------ 02-c coarse-graining
    f = Figure(2, '時間的粗視化', '細かな差異は失われ、代わりに大きな時間単位の性質が現れる', 580, 'd')
    f.text(80, 262, '光の強さ', 17, INK, weight=700)
    f.text(80, 284, '周期 10ms', 14, MUTED)
    f.square_wave(260, 860, 270, 26, 20, AMBER, 2)
    f.line(260, 310, 860, 310, color=LINE, width=1)
    f.line(560, 320, 560, 380, color=MUTED, width=2.5, arrow=True)
    f.text(590, 356, '時間的粗視化', 16, INK, weight=700)
    f.text(80, 442, '経験される', 17, INK, weight=700)
    f.text(80, 464, '明るさ', 17, INK, weight=700)
    f.line(260, 450, 860, 450, color=TEAL, width=4)
    f.rect(260, 424, 600, 52, fill=TEAL, stroke='none', width=0, rx=8, opacity=0.12)
    f.lines(900, 262, ['失われる差異', '個々の点滅、周期'], 15, AMBER, gap=22, weight=700)
    f.text(900, 306, '', 15)
    f.lines(900, 442, ['現れる性質', '平均的な明るさ'], 15, TEAL, gap=22, weight=700)
    f.footer('知覚の失敗ではなく、限られた処理能力で世界を捉えるための仕組みである。')
    made.add(f.save('02-d-coarse-graining.svg'))

    # ------------------------------------------------------------------ 02-d star-trails
    f = Figure(2, '観測する時間の幅を変えると、静止が運動になる', '左右は同じ星空。違うのは観測する時間の幅だけ', 600, 'e')
    f.panel(70, 200, 500, 340, '数秒の観察')
    f.rect(110, 250, 420, 200, fill='#1d2433', stroke='none', width=0, rx=12)
    for (x, y, r) in [(180, 300, 3), (250, 360, 2.5), (330, 290, 3.5), (420, 330, 2.5), (470, 400, 3), (300, 420, 2)]:
        f.circ(x, y, r, '#ffffff')
    f.text(320, 490, '変化量が小さく、静止して見える', 15, INK, anchor='middle', weight=700)
    f.panel(630, 200, 500, 340, '長時間の撮影')
    f.rect(670, 250, 420, 200, fill='#1d2433', stroke='none', width=0, rx=12)
    for r in (60, 95, 130, 165, 200):
        a0, a1 = math.radians(105), math.radians(175)
        x0, y0 = 1060 + r * math.cos(a0), 240 + r * math.sin(a0)
        x1, y1 = 1060 + r * math.cos(a1), 240 + r * math.sin(a1)
        f.path(f'M {x0:.0f} {y0:.0f} A {r} {r} 0 0 1 {x1:.0f} {y1:.0f}', color='#ffffff', width=1.6, opacity=0.9)
    f.text(1030, 268, '天の極', 12, '#cfd6e6', anchor='middle')
    f.text(880, 490, '弧を描く運動として捉えられる', 15, INK, anchor='middle', weight=700)
    f.rect(300, 506, 40, 10, fill=AMBER, stroke='none', width=0, rx=5)
    f.text(320, 532, '観測時間：数秒', 13, MUTED, anchor='middle')
    f.rect(690, 506, 380, 10, fill=AMBER, stroke='none', width=0, rx=5)
    f.text(880, 532, '観測時間：数時間', 13, MUTED, anchor='middle')
    f.footer('物理現象は同じ。変えたのは、変化を観測し統合する時間の幅である。')
    made.add(f.save('02-e-star-trails.svg'))

    # ------------------------------------------------------------------ 02-f scale-relativity
    f = Figure(2, 'スケール相対性', '同じ点滅が、観測する個体の時間分解能によって点滅にも連続光にもなる', 620, 'g')
    f.text(80, 236, '物理的な点滅', 16, INK, weight=700)
    f.square_wave(330, 1000, 232, 14, 24, AMBER, 1.8)
    f.line(330, 268, 1000, 268, color=LINE, width=1)
    rows = [('時間分解能の高い個体', '点滅として識別', 'sq', BLUE), ('人間', '連続した光', 'flat', TEAL), ('時間分解能の低い個体', 'より一様な光', 'flat2', PLUM)]
    for i, (lab, seen, kind, color) in enumerate(rows):
        y = 330 + i * 86
        f.text(80, y + 6, lab, 16, INK, weight=700)
        if kind == 'sq':
            f.square_wave(330, 1000, y, 14, 24, color, 1.8)
        elif kind == 'flat':
            f.wave(330, 1000, y, 3, 24, color, 1.8)
        else:
            f.line(330, y, 1000, y, color=color, width=2.5)
        f.text(1020, y + 6, seen, 15, color, weight=700)
    f.footer('一瞬か変化かは、世界の側だけでは決まらず、個体の知覚構造との関係で決まる。')
    made.add(f.save('02-g-scale-relativity.svg'))

    # ------------------------------------------------------------------ 03-c prediction-error-rose
    f = Figure(3, '予測誤差が、推定を修正する', '遠くの赤いものを「バラ」と予測し、近づいて入力が変わると「造花」へ改める', 580, 'd')
    for i, lab in enumerate(['遠くで', '近づく', '推定の修正']):
        f.panel(70 + i * 360, 200, 330, 300, lab)
    f.blob(235, 330, 26, '#c23b3b', 0.9)
    f.box(130, 400, 210, 56, '予測：バラ', '', BLUE, 18)
    f.text(235, 480, '入力は小さく曖昧', 14, MUTED, anchor='middle')
    f.blob(595, 320, 60, '#c23b3b', 0.9)
    for k in range(5):
        f.line(560 + k * 18, 300, 568 + k * 18, 345, color='#ffffff', width=1.2)
    f.text(595, 384, '入力：布の質感', 15, AMBER, anchor='middle', weight=700)
    f.box(490, 400, 210, 56, '予測：バラ', '', BLUE, 18)
    f.text(595, 480, '予測と入力に差 ＝ 予測誤差', 14, AMBER, anchor='middle', weight=700)
    f.blob(955, 320, 60, '#c23b3b', 0.9)
    f.box(850, 400, 210, 56, '推定：造花', '', TEAL, 18)
    f.text(955, 480, '誤差で内部モデルを更新', 14, TEAL, anchor='middle')
    f.line(405, 428, 440, 428, color=MUTED, width=2, arrow=True)
    f.line(765, 428, 800, 428, color=MUTED, width=2, arrow=True)
    f.footer('誤差は認識の失敗ではなく、モデルを更新するための情報である。')
    made.add(f.save('03-d-prediction-error-rose.svg'))

    # ------------------------------------------------------------------ 03-d cup-tradeoff
    f = Figure(3, '行動に要る情報と、要らない情報', 'コップを持ち上げるのに、表面の傷や反射をすべて解析する必要はない', 578, 'e')
    f.path('M 520 260 L 540 440 Q 600 460 660 440 L 680 260 Z', color=INK, width=2.5, fill='#ffffff')
    f.path('M 680 300 Q 740 320 680 390', color=INK, width=2.5)
    f.lines(140, 290, ['要る情報', '位置', '大きさ', '持ちやすさ'], 17, TEAL, gap=30, weight=700)
    for y in (316, 346, 376):
        f.line(260, y - 6, 510, 300 + (y - 316) * 1.5, color=TEAL, width=1.5, arrow=True)
    f.lines(840, 290, ['要らない情報', '微細な傷', '光の反射のすべて'], 17, MUTED, gap=30, weight=700)
    f.line(830, 340, 600, 330, color=MUTED, width=1.5, dash=True, arrow=True)
    f.line(830, 370, 640, 400, color=MUTED, width=1.5, dash=True, arrow=True)
    f.line(200, 520, 1000, 520, color=MUTED, width=2, arrow=True)
    f.text(200, 548, '速く行動する', 15, INK)
    f.text(1000, 548, '精度を上げる（時間とエネルギーが要る）', 15, INK, anchor='end')
    f.circ(430, 520, 9, TEAL)
    f.text(430, 500, '行動に必要な精度', 14, TEAL, anchor='middle', weight=700)
    f.footer('')
    made.add(f.save('03-e-cup-tradeoff.svg'))

    # ------------------------------------------------------------------ 03-e qualia-process
    f = Figure(3, 'クオリアを、静的な属性ではなく動的な過程として捉える', '左は層として積む見方、右は予測と修正の循環に質が伴うという本連載の仮説', 620, 'f')
    f.panel(70, 200, 480, 380, '静的な見方')
    for i, (lab, color) in enumerate([('「赤さ」（感覚の質）', PLUM), ('神経活動', TEAL), ('光の物理量（波長・強度）', BLUE)]):
        y = 270 + i * 86
        f.rect(130, y, 360, 60, fill='#ffffff', stroke=color, width=2, rx=10)
        f.text(310, y + 37, lab, 16, color, anchor='middle', weight=700)
    f.text(310, 540, '測定値を記述しても「どのような感じか」は説明されない', 13, MUTED, anchor='middle')
    f.panel(630, 200, 500, 380, '本連載の仮説')
    loop_nodes(f, 820, 410, 96, ['感覚入力', '照合（予測誤差）', '内部モデルの更新', '予測'], BLUE, 150, 42, 13)
    f.blob(1050, 330, 70, '#c23b3b', 0.45)
    f.text(1050, 336, '「赤さ」', 18, '#8a2a2a', anchor='middle', weight=700)
    f.path('M 930 390 C 980 380 1000 360 1010 345', color='#8a2a2a', width=1.8, arrow=True, dash=True)
    f.text(1050, 372, '過程に伴う質', 13, MUTED, anchor='middle')
    f.text(880, 556, '再構成し続ける過程に、質が伴うという仮説', 14, INK, anchor='middle', weight=700)
    f.footer('予測誤差そのものをクオリアと同一視はしない。遅延のあるシステムすべてに経験があるとも言えない。')
    made.add(f.save('03-f-qualia-process.svg'))

    # ------------------------------------------------------------------ 04-b paramecium
    f = Figure(4, 'ゾウリムシの回避反応', '接触から後退までを、概念的な理解を仮定せずに電気生理学的な連鎖で説明できる', 560, 'b')
    f.body.append(f'<ellipse cx="260" cy="270" rx="90" ry="34" fill="#ffffff" stroke="{TEAL}" stroke-width="2.5"/>')
    for k in range(14):
        a = k * 2 * math.pi / 14
        f.line(260 + 90 * math.cos(a), 270 + 34 * math.sin(a), 260 + 104 * math.cos(a), 270 + 44 * math.sin(a), color=TEAL, width=1.2)
    f.rect(380, 230, 24, 80, fill=SOFT, stroke=MUTED, width=1.5, rx=4)
    f.text(392, 330, '障害物', 13, MUTED, anchor='middle')
    f.line(340, 270, 372, 270, color=AMBER, width=2, arrow=True)
    f.text(260, 232, 'ゾウリムシ', 14, MUTED, anchor='middle')
    steps = [('接触刺激', '障害物に触れる', MUTED), ('イオンチャネル', '膜のチャネルが働く', BLUE), ('膜電位の変化', 'Ca²⁺ などの移動', BLUE), ('繊毛の切り替え', '打つ向きが反転', TEAL), ('後退', '進行方向を変える', TEAL)]
    for i, (lab, sub, color) in enumerate(steps):
        x = 80 + i * 216
        f.box(x, 390, 180, 70, lab, sub, color, 17)
        if i < 4:
            f.line(x + 184, 425, x + 212, 425, color=MUTED, width=2.2, arrow=True)
    f.footer('脳も神経系もない。それでも刺激を検出し、行動を変える。主観的経験があるかは、この反応だけからは判断できない。')
    made.add(f.save('04-b-paramecium.svg'))

    # ------------------------------------------------------------------ 04-c same-stimulus
    f = Figure(4, '同じ刺激、異なる行動', '内部状態と過去の経験が、刺激と反応の間に入る', 610, 'c')
    f.box(480, 350, 240, 80, '目の前の食べ物', '同じ感覚刺激', MUTED, 20)
    states = [('空腹である', TEAL), ('以前に食べて体調を崩した', AMBER), ('周囲に捕食者がいる', PLUM)]
    acts = [('近づく', TEAL), ('避ける', AMBER), ('逃げる', PLUM)]
    for i, ((s, c1), (a, c2)) in enumerate(zip(states, acts)):
        y = 270 + i * 100
        f.rect(90, y, 300, 56, fill='#ffffff', stroke=c1, width=2, rx=10)
        f.text(240, y + 34, s, 16, c1, anchor='middle', weight=700)
        f.path(f'M 395 {y+28} C 440 {y+28} 440 390 475 390', color=c1, width=1.8, arrow=True)
        f.rect(820, y, 280, 56, fill='#ffffff', stroke=c2, width=2, rx=10)
        f.text(960, y + 34, a, 18, c2, anchor='middle', weight=700)
        f.path(f'M 725 390 C 760 390 760 {y+28} 815 {y+28}', color=c2, width=1.8, arrow=True)
    f.text(240, 240, '内部状態・過去の経験', 15, INK, anchor='middle', weight=700)
    f.text(960, 240, '行動', 15, INK, anchor='middle', weight=700)
    f.footer('刺激と反応は一対一ではない。複数の可能性を評価する仕組みに、時間的な内部が要る。')
    made.add(f.save('04-c-same-stimulus.svg'))

    # ------------------------------------------------------------------ 04-f delay-not-sufficient
    f = Figure(4, '遅延は意識の十分条件ではない', '保持・照合・選択に伴う遅延は、意識のないシステムにもある', 530, 'h')
    f.rect(90, 210, 1020, 250, fill='none', stroke=MUTED, width=2, rx=20, dash=True)
    f.text(600, 244, '処理に遅延がある（情報を保持し、照合し、候補から選ぶ）', 17, INK, anchor='middle', weight=700)
    items = [('コンピュータの処理', '主観的経験は結論できない', MUTED), ('意識に上らない神経処理', '人間の中にも多数ある', MUTED), ('意識的な認知', '遅延を伴うが、それだけではない', BLUE)]
    for i, (lab, sub, color) in enumerate(items):
        x = 130 + i * 330
        f.box(x, 290, 300, 110, lab, sub, color, 17)
    f.text(600, 500, '遅延だけでは三つを区別できない。遅延は意識そのものではなく、意識が成立する時間的な条件を考えるための概念である。', 15, INK, anchor='middle')
    f.footer('')
    made.add(f.save('04-h-delay-not-sufficient.svg'))

    # ------------------------------------------------------------------ 04-g catching-ball
    f = Figure(4, '異なる時間スケールの情報が、一つの行動へ統合される', '三本の線の目盛りがそろわないまま、右の一つの行動へ合流する', 580, 'i')
    rows = [('視覚系', 'ボールの位置と運動', 0.0, TEAL), ('運動系', '身体を動かす指令', 0.37, AMBER), ('自己受容感覚', '姿勢と関節の状態', 0.71, PLUM)]
    for i, (lab, sub, phase, color) in enumerate(rows):
        y = 270 + i * 90
        f.text(80, y + 4, lab, 16, INK, weight=700)
        f.text(80, y + 26, sub, 13, MUTED)
        f.line(300, y, 780, y, color=color, width=2)
        for k in range(12):
            x = 300 + 480 * (k + phase) / 12
            f.line(x, y - 9, x, y + 9, color=color, width=2)
        f.path(f'M 785 {y} C 840 {y} 840 360 880 360', color=color, width=2, arrow=True)
    f.text(540, 236, '更新の時点がそろわない（目盛りの間隔は模式）', 14, MUTED, anchor='middle')
    f.box(885, 320, 230, 80, 'ボールを捕る', '一つのまとまった行動', BLUE, 20)
    f.text(1000, 440, '調整には保持と統合の時間が要る', 14, MUTED, anchor='middle')
    f.footer('処理は完全には同期していない。ずれや待ち時間を含んで、統合された結果が形成される。')
    made.add(f.save('04-i-catching-ball.svg'))

    # ------------------------------------------------------------------ 05-b wood-grain-face
    f = Figure(5, '記憶イメージの投射', '木目模様に顔が見えるのは、過去に見た顔の特徴を曖昧な入力に重ねているから', 580, 'b')
    def grain(x0, y0, w, h, color):
        for k in range(7):
            y = y0 + 20 + k * (h - 40) / 6
            f.path(f'M {x0+10} {y} C {x0+w*0.3} {y-14+6*(k%3)} {x0+w*0.6} {y+12-6*(k%2)} {x0+w-10} {y}', color=color, width=1.6)
    for i, lab in enumerate(['木目模様（入力）', '顔の特徴（記憶）', '顔が見える']):
        f.panel(70 + i * 360, 200, 330, 300, lab)
    f.rect(110, 250, 250, 200, fill='#f3e8d6', stroke=LINE, width=1.5, rx=10)
    grain(110, 250, 250, 200, '#b08a5a')
    f.circ(540, 320, 9, INK); f.circ(620, 320, 9, INK)
    f.line(580, 345, 580, 375, color=INK, width=2.5)
    f.path('M 545 405 Q 580 430 615 405', color=INK, width=2.5)
    f.text(580, 470, '目・鼻・口の配置', 14, MUTED, anchor='middle')
    f.rect(830, 250, 250, 200, fill='#f3e8d6', stroke=LINE, width=1.5, rx=10)
    grain(830, 250, 250, 200, '#b08a5a')
    f.circ(915, 320, 9, INK, opacity=0.75); f.circ(995, 320, 9, INK, opacity=0.75)
    f.line(955, 345, 955, 375, color=INK, width=2.5, dots=False)
    f.path('M 920 405 Q 955 430 990 405', color=INK, width=2.5)
    f.text(420, 352, '＋', 30, MUTED, anchor='middle', weight=700)
    f.text(780, 352, '＝', 30, MUTED, anchor='middle', weight=700)
    f.footer('入力だけでは対象は一意に決まらない。過去の経験が、対象を積極的に描き出している。')
    made.add(f.save('05-b-wood-grain-face.svg'))

    # ------------------------------------------------------------------ 05-d same-memory-three-meanings
    f = Figure(5, '同じ出来事、異なる意味', '一つの過去が、現在の文脈によって別の意味を持つ', 600, 'd')
    f.blob(260, 370, 90, BLUE, 0.4)
    f.text(260, 362, '学生時代の', 17, INK, anchor='middle', weight=700)
    f.text(260, 386, '失敗', 17, INK, anchor='middle', weight=700)
    rows = [('当時', '恥ずかしい経験', AMBER), ('社会人になって同じ状況で', '判断の手掛かり', TEAL), ('誰かに語る場面で', '教訓を伝える材料', PLUM)]
    for i, (ctx, meaning, color) in enumerate(rows):
        y = 262 + i * 108
        f.path(f'M 350 370 C 450 370 480 {y+28} 560 {y+28}', color=color, width=2, arrow=True)
        f.text(560, y - 2, ctx, 14, MUTED)
        f.rect(560, y + 4, 420, 50, fill='#ffffff', stroke=color, width=2, rx=10)
        f.text(770, y + 36, meaning, 17, color, anchor='middle', weight=700)
    f.footer('出来事が書き換わるのではない。文脈と他の記憶との関係の中で再構成される。')
    made.add(f.save('05-d-same-memory-three-meanings.svg'))

    # ------------------------------------------------------------------ 05-f forgetting
    f = Figure(5, '記憶の二つの層と、三つの働き', '保持するだけでなく、更新し、必要に応じて忘れることで環境に適応する', 540, 'f')
    f.rect(120, 400, 960, 70, fill=SOFT, stroke=MUTED, width=1.5, rx=14)
    f.text(600, 433, '生得的な情報 ── 進化が形成した神経系の構造や行動傾向', 16, INK, anchor='middle', weight=700)
    f.text(600, 456, '生まれた時点で備えている', 13, MUTED, anchor='middle')
    f.rect(120, 220, 960, 160, fill='#ffffff', stroke=BLUE, width=2, rx=14)
    f.text(600, 252, '獲得的な記憶 ── 経験によって形成される（可塑性）', 16, BLUE, anchor='middle', weight=700)
    for i, (lab, sub, color) in enumerate([('保持', '情報を残す', TEAL), ('更新', '新しい経験で意味を変える', AMBER), ('忘却', '役に立たない情報を手放す', PLUM)]):
        x = 170 + i * 300
        f.box(x, 280, 260, 76, lab, sub, color, 18)
        if i < 2:
            f.line(x + 264, 318, x + 296, 318, color=MUTED, width=1.5, arrow=True)
    f.footer('すべてを永久に同じ強度で保持することは効率的とは限らない。')
    made.add(f.save('05-f-forgetting.svg'))

    # ------------------------------------------------------------------ 06-a car-motion
    f = Figure(6, '運動の知覚には、直前の位置が要る', '一つの時刻の位置だけでは、方向も速さも決まらない', 540, 'a')
    def car(x, y, color, op=1.0):
        f.body.append(f'<g opacity="{op}"><rect x="{x-50}" y="{y-18}" width="100" height="30" rx="8" fill="{color}"/><rect x="{x-28}" y="{y-38}" width="52" height="24" rx="6" fill="{color}"/><circle cx="{x-28}" cy="{y+14}" r="9" fill="{INK}"/><circle cx="{x+28}" cy="{y+14}" r="9" fill="{INK}"/></g>')
    f.panel(70, 200, 500, 290, '一つの時刻の位置')
    f.line(110, 420, 530, 420, color=LINE, width=2)
    car(320, 400, BLUE)
    f.text(320, 300, '方向は？ 速さは？', 18, AMBER, anchor='middle', weight=700)
    f.text(320, 460, '位置だけでは決まらない', 14, MUTED, anchor='middle')
    f.panel(630, 200, 500, 290, '直前の位置との差')
    f.line(670, 420, 1090, 420, color=LINE, width=2)
    car(790, 400, BLUE, 0.3)
    car(960, 400, BLUE)
    f.text(790, 450, '直前', 13, MUTED, anchor='middle')
    f.text(960, 450, 'いま', 13, MUTED, anchor='middle')
    f.line(840, 340, 920, 340, color=AMBER, width=3, arrow=True)
    f.text(880, 320, '方向と速さ', 16, AMBER, anchor='middle', weight=700)
    f.footer('運動を知覚している現在には、何らかの形で直前の過去が含まれている。')
    made.add(f.save('06-a-car-motion.svg'))

    # ------------------------------------------------------------------ 06-b reunion-duration
    f = Figure(6, '持続は、瞬間の足し算ではない', '時計の単位は均質で独立。会話の流れでは、前の経験が次に浸透して意味が変わる', 570, 'b')
    f.text(80, 262, '時計の時間', 17, INK, weight=700)
    f.line(280, 270, 1100, 270, color=INK, width=2)
    for k in range(9):
        x = 280 + k * 102.5
        f.line(x, 260, x, 280, color=INK, width=2)
    f.text(690, 304, '同じ長さの単位が、独立して並ぶ', 14, MUTED, anchor='middle')
    f.text(80, 432, '再会した友人', 17, INK, weight=700)
    f.text(80, 454, 'との会話', 17, INK, weight=700)
    f.blob(400, 440, 150, AMBER, 0.28)
    f.blob(690, 440, 170, TEAL, 0.28)
    f.blob(980, 440, 150, BLUE, 0.28)
    for x, w in [(400, 150), (690, 170), (980, 230)]:
        f.rect(x - w / 2, 420, w, 28, fill='#ffffff', stroke='none', width=0, rx=8, opacity=0.8)
    f.text(400, 440, 'ぎこちない会話', 16, INK, anchor='middle', weight=700)
    f.text(690, 440, '昔の話で懐かしさ', 16, INK, anchor='middle', weight=700)
    f.text(980, 440, '関係が新しい意味を持つ', 16, INK, anchor='middle', weight=700)
    f.path('M 470 400 C 540 360 600 360 640 398', color=MUTED, width=1.6, arrow=True)
    f.path('M 770 400 C 840 360 900 360 930 398', color=MUTED, width=1.6, arrow=True)
    f.path('M 900 486 C 800 530 600 530 450 486', color=AMBER, width=1.6, arrow=True, dash=True)
    f.text(690, 540, '後の経験が、先ほどの言葉の意味を変える', 14, AMBER, anchor='middle')
    f.footer('')
    made.add(f.save('06-b-reunion-duration.svg'))

    # ------------------------------------------------------------------ 06-d melody-ending
    f = Figure(6, 'メロディーの終わりは、保持と予感の構造が変わることで経験される', '進行中は次の音への予感がある。終結では予感が変わり、最後の音が全体の印象へ統合される', 550, 'f')
    f.panel(70, 200, 500, 320, '進行中')
    f.line(110, 400, 530, 400, color=LINE, width=2)
    for i, x in enumerate([170, 250, 330]):
        f.circ(x, 380 - (i % 2) * 20, 11, TEAL)
        f.line(x, 380 - (i % 2) * 20, x, 340 - (i % 2) * 20, color=TEAL, width=2.5)
    f.circ(430, 370, 11, TEAL, fill=False, dash=True, width=2.2)
    f.text(430, 330, '次の音？', 14, TEAL, anchor='middle', weight=700)
    f.text(430, 440, '予感がある', 14, MUTED, anchor='middle')
    f.text(320, 490, '続くという期待の中で聴いている', 14, INK, anchor='middle')
    f.panel(630, 200, 500, 320, '終結')
    f.line(670, 400, 1090, 400, color=LINE, width=2)
    for i, x in enumerate([730, 810, 890, 970]):
        f.circ(x, 380 - (i % 2) * 20 + (20 if i == 3 else 0), 11, TEAL)
        f.line(x, 380 - (i % 2) * 20 + (20 if i == 3 else 0), x, 340 - (i % 2) * 20 + (20 if i == 3 else 0), color=TEAL, width=2.5)
    f.text(1040, 376, '×', 22, MUTED, anchor='middle')
    f.text(1040, 440, '予感が消える', 14, MUTED, anchor='middle')
    f.brace(720, 990, 420, down=True)
    f.text(855, 452, '保持 → 全体の印象へ統合', 14, AMBER, anchor='middle', weight=700)
    f.text(880, 490, '終結を示す音型で「ここで終わる」と予測される', 14, INK, anchor='middle')
    f.footer('')
    made.add(f.save('06-f-melody-ending.svg'))

    # ------------------------------------------------------------------ 06-e aspect-imperfective
    f = Figure(6, '時制とアスペクト', '「咲いた」は完了したものとして、「咲きつつある」はまだ出来上がっていないものとして表す', 620, 'g')
    f.line(150, 500, 1050, 500, color=MUTED, width=2, arrow=True)
    for x, t in [(250, '過去'), (600, '現在'), (950, '未来')]:
        f.line(x, 494, x, 506, color=MUTED, width=1.5)
        f.text(x, 530, t, 14, MUTED, anchor='middle')
    f.text(1060, 505, '時制', 14, MUTED)
    f.rect(150, 240, 400, 200, fill='#ffffff', stroke=AMBER, width=2.5, rx=14)
    f.text(350, 276, '「花が咲いた」', 20, AMBER, anchor='middle', weight=700)
    f.text(350, 300, '完了相：出来事は閉じている', 14, MUTED, anchor='middle')
    for k in range(6):
        a = k * math.pi / 3
        f.body.append(f'<ellipse cx="{350 + 28 * math.cos(a):.1f}" cy="{380 + 28 * math.sin(a):.1f}" rx="16" ry="10" transform="rotate({k*60} {350 + 28 * math.cos(a):.1f} {380 + 28 * math.sin(a):.1f})" fill="{AMBER}" opacity="0.8"/>')
    f.circ(350, 380, 10, '#f3d16a')
    f.path('M 650 240 L 940 240 M 650 440 L 940 440 M 650 240 L 650 440', color=TEAL, width=2.5)
    f.path('M 940 240 L 990 240 M 940 440 L 990 440', color=TEAL, width=2.5, dash=True)
    f.text(820, 276, '「花が咲きつつある」', 20, TEAL, anchor='middle', weight=700)
    f.text(820, 300, '未完了相：生じてはいるが、まだ出来上がっていない', 14, MUTED, anchor='middle')
    f.body.append(f'<ellipse cx="760" cy="385" rx="12" ry="22" fill="{TEAL}" opacity="0.8"/>')
    f.line(760, 405, 760, 430, color=TEAL, width=2)
    f.line(800, 385, 840, 385, color=MUTED, width=1.5, arrow=True)
    for k in range(3):
        a = -math.pi / 2 + k * 0.7 - 0.7
        f.body.append(f'<ellipse cx="{900 + 22 * math.cos(a):.1f}" cy="{390 + 22 * math.sin(a):.1f}" rx="13" ry="8" fill="{TEAL}" opacity="0.6"/>')
    f.line(900, 400, 900, 430, color=TEAL, width=2)
    f.text(1010, 350, 'アスペクト', 14, MUTED, anchor='middle')
    f.footer('いつ起きたか（時制）とは別に、どのような進行状態にあるか（アスペクト）がある。')
    made.add(f.save('06-g-aspect-imperfective.svg'))

    # ------------------------------------------------------------------ 06-g layer-switching
    f = Figure(6, '二つの時間階層の切り替え', '左右のループの間にある「配分」のつまみが、右へ動く場面', 600, 'i')
    f.panel(70, 200, 440, 340, '感覚・運動ループ')
    f.text(290, 260, '短い時間スケール', 14, MUTED, anchor='middle')
    loop_nodes(f, 290, 400, 80, ['外界', '感覚', '行動'], TEAL, 110, 40, 14)
    f.panel(690, 200, 440, 340, '記憶の探索')
    f.text(910, 260, '長い時間スケール', 14, MUTED, anchor='middle')
    for i in range(5):
        y = 480 - i * 36
        w = 220 - i * 18
        f.rect(910 - w / 2, y, w, 28, fill=PLUM, stroke='none', width=0, rx=6, opacity=0.25 + i * 0.12)
    f.text(910, 528, '蓄積された記憶の層をたどる', 14, PLUM, anchor='middle', weight=700)
    f.rect(540, 360, 120, 60, fill='#ffffff', stroke=AMBER, width=2, rx=30)
    f.circ(620, 390, 16, AMBER)
    f.text(600, 340, '処理資源の配分', 14, AMBER, anchor='middle', weight=700)
    f.line(560, 448, 650, 448, color=AMBER, width=2, arrow=True)
    f.text(600, 476, '会話を止めて', 13, MUTED, anchor='middle')
    f.text(600, 494, '思い出すとき', 13, MUTED, anchor='middle')
    f.footer('外界との関係を断つのではなく、注意と処理の配分を変えている。')
    made.add(f.save('06-i-layer-switching.svg'))

    # ------------------------------------------------------------------ 07-a cell-boundary
    f = Figure(7, '世界とつながりながら、境界を維持する', '膜が内と外を分け、内側では自己維持と環境適応を複数のシステムが担う', 600, 'a')
    f.rect(300, 210, 600, 340, fill='#ffffff', stroke=BLUE, width=4, rx=120)
    f.text(600, 246, '内部環境（膜で区別された領域）', 15, BLUE, anchor='middle', weight=700)
    f.text(140, 300, '外界', 18, MUTED, weight=700)
    f.line(150, 340, 300, 340, color=TEAL, width=2.2, arrow=True)
    f.text(220, 328, '酸素・食物', 14, TEAL, anchor='middle')
    f.line(300, 420, 150, 420, color=AMBER, width=2.2, arrow=True)
    f.text(225, 446, '不要な物質', 14, AMBER, anchor='middle')
    f.text(1000, 300, '環境の変化', 18, MUTED, anchor='end', weight=700)
    f.line(1050, 340, 900, 340, color=PLUM, width=2.2, arrow=True)
    f.text(975, 328, '温度・光・他者', 14, PLUM, anchor='middle')
    f.box(360, 300, 220, 150, '自己維持', '免疫系・内分泌系', TEAL, 18)
    f.text(470, 428, '内部状態を保つ', 13, MUTED, anchor='middle')
    f.box(620, 300, 220, 150, '環境適応', '神経系', PLUM, 18)
    f.text(730, 428, '外界の変化を捉える', 13, MUTED, anchor='middle')
    f.line(585, 375, 615, 375, color=MUTED, width=2, arrow=True)
    f.line(615, 395, 585, 395, color=MUTED, width=2, arrow=True)
    f.text(600, 500, '分離してはいない。神経系は内部を調節し、ホルモンや免疫は脳の状態を変える', 14, INK, anchor='middle')
    f.footer('生命とは、相互作用を続けながら、自己の境界と内部状態を維持する過程である。')
    made.add(f.save('07-a-cell-boundary.svg'))

    # ------------------------------------------------------------------ 07-d two-factor-emotion
    f = Figure(7, '同じ身体の変化、異なる感情', '心拍の増加は、文脈の解釈によって恐怖にも期待にも疲労にもなる', 580, 'd')
    f.text(600, 372, '♥', 46, '#c23b3b', anchor='middle')
    f.text(600, 416, '心拍が上がる', 17, INK, anchor='middle', weight=700)
    f.text(600, 438, '同じ身体の変化', 13, MUTED, anchor='middle')
    ctx = [('危険な状況', AMBER), ('好きな人と会う直前', TEAL), ('激しい運動の直後', PLUM)]
    emo = [('恐怖', AMBER), ('期待・緊張', TEAL), ('疲労', PLUM)]
    for i, ((c, col), (e, col2)) in enumerate(zip(ctx, emo)):
        y = 270 + i * 100
        f.rect(90, y, 300, 54, fill='#ffffff', stroke=col, width=2, rx=10)
        f.text(240, y + 34, c, 16, col, anchor='middle', weight=700)
        f.path(f'M 395 {y+27} C 460 {y+27} 480 370 540 370', color=col, width=1.6, arrow=True)
        f.path(f'M 660 370 C 720 370 740 {y+27} 810 {y+27}', color=col2, width=1.6, arrow=True)
        f.rect(815, y, 280, 54, fill='#ffffff', stroke=col2, width=2, rx=10)
        f.text(955, y + 34, e, 18, col2, anchor='middle', weight=700)
    f.text(240, 244, '文脈', 15, INK, anchor='middle', weight=700)
    f.text(955, 244, '経験される感情', 15, INK, anchor='middle', weight=700)
    f.text(740, 500, '脳が原因を推定する', 14, MUTED, anchor='middle')
    f.footer('信号をそのまま受け取るのではない。信号が何を意味するかの推定が、感情の形成に関係する。')
    made.add(f.save('07-d-two-factor-emotion.svg'))

    # ------------------------------------------------------------------ 07-e allostasis
    f = Figure(7, '動く基準', '調節の設定値は固定ではなく、状況と将来の要求に応じて変わる', 580, 'e')
    f.line(150, 460, 1080, 460, color=MUTED, width=2, arrow=True)
    f.line(150, 460, 150, 230, color=MUTED, width=2, arrow=True)
    f.text(140, 222, '調節の目標（体温など）', 14, MUTED, anchor='end')
    segs = [('睡眠', 150, 330), ('覚醒', 330, 510), ('運動', 510, 690), ('感染（発熱）', 690, 900), ('回復', 900, 1060)]
    for lab, x0, x1 in segs:
        f.text((x0 + x1) / 2, 488, lab, 14, MUTED, anchor='middle')
        f.line(x1, 455, x1, 465, color=MUTED, width=1)
    f.line(150, 370, 1060, 370, color=LINE, width=1.5, dash=True)
    f.text(1066, 374, '固定の基準？', 13, MUTED)
    f.path('M 150 390 L 330 390 L 345 360 L 510 360 L 530 320 L 690 325 L 710 270 L 900 270 L 930 370 L 1060 370', color=AMBER, width=3)
    f.text(240, 412, '低い', 13, AMBER, anchor='middle')
    f.text(600, 300, '活動に先立つ調節（予測的）', 13, AMBER, anchor='middle')
    f.text(800, 252, '免疫反応で設定値が上がる', 13, AMBER, anchor='middle')
    f.path('M 470 300 C 480 270 500 260 515 262', color=TEAL, width=2, arrow=True, dash=True)
    f.text(440, 262, '先回りの調節', 13, TEAL, anchor='middle', weight=700)
    f.text(440, 280, '（アロスタシス）', 12, TEAL, anchor='middle')
    f.footer('現在の身体状態は、過去の変化の結果であり、未来の要求へ向けた調節の途中にある。')
    made.add(f.save('07-e-allostasis.svg'))

    # ------------------------------------------------------------------ 07-f gut-brain
    f = Figure(7, '腸脳相関', '腸と脳は、神経・ホルモン・免疫の三つの経路で双方向に影響し合う', 600, 'f')
    f.rect(90, 220, 380, 320, fill='#ffffff', stroke=AMBER, width=2.5, rx=18)
    f.text(280, 256, '腸', 22, AMBER, anchor='middle', weight=700)
    for i, lab in enumerate(['腸管神経系（独自の神経ネットワーク）', '多数の免疫細胞', '多様な微生物', 'ホルモンを分泌する細胞']):
        f.rect(120, 280 + i * 60, 320, 44, fill=SOFT, stroke='none', width=0, rx=8)
        f.text(280, 308 + i * 60, lab, 14, INK, anchor='middle')
    f.rect(730, 220, 380, 320, fill='#ffffff', stroke=BLUE, width=2.5, rx=18)
    f.text(920, 256, '脳', 22, BLUE, anchor='middle', weight=700)
    for i, lab in enumerate(['活動状態', '感情', '注意・行動', 'ストレス反応']):
        f.rect(760, 280 + i * 60, 320, 44, fill=SOFT, stroke='none', width=0, rx=8)
        f.text(920, 308 + i * 60, lab, 14, INK, anchor='middle')
    for i, (lab, color) in enumerate([('神経（迷走神経など）', TEAL), ('ホルモン', AMBER), ('免疫系', PLUM)]):
        y = 320 + i * 80
        f.line(480, y, 720, y, color=color, width=2.5, arrow=True)
        f.line(720, y + 14, 480, y + 14, color=color, width=2.5, arrow=True)
        f.text(600, y - 10, lab, 14, color, anchor='middle', weight=700)
    f.footer('腸は思考する「脳」ではない。しかし、心を支える情報処理は脳内で完結していない。')
    made.add(f.save('07-f-gut-brain.svg'))

    # ------------------------------------------------------------------ 07-g salience-threshold
    f = Figure(7, 'サリエンス・スレッシュホールド', '多数の身体信号のうち、閾値を超えた顕著なものだけが意識に上る', 560, 'g')
    f.line(120, 440, 1080, 440, color=MUTED, width=2, arrow=True)
    f.text(1086, 445, '時間', 13, MUTED)
    for k in range(60):
        x = 130 + k * 15.5
        h = 8 + (k * 7) % 23
        if k == 38:
            continue
        f.line(x, 440, x, 440 - h, color=BLUE, width=2, opacity=0.5)
    f.line(719, 440, 719, 262, color=AMBER, width=4)
    f.circ(719, 262, 7, AMBER)
    f.text(719, 240, '激しい空腹・胃の痛み・動悸', 14, AMBER, anchor='middle', weight=700)
    f.line(120, 330, 1080, 330, color=PLUM, width=2, dash=True)
    f.text(1086, 334, '閾値', 14, PLUM)
    f.line(1040, 330, 1040, 296, color=PLUM, width=1.5, arrow=True)
    f.line(1040, 330, 1040, 364, color=PLUM, width=1.5, arrow=True)
    f.text(1000, 300, '注意・予測・文脈で動く', 13, PLUM, anchor='end')
    f.text(400, 470, '意識に上らない多数の信号', 14, MUTED, anchor='middle')
    f.text(719, 470, '意識へ', 15, AMBER, anchor='middle', weight=700)
    f.footer('意識は身体で発生するすべての情報を経験しているのではない。行動や自己維持に関係する情報が選択される。')
    made.add(f.save('07-g-salience-threshold.svg'))

    # ------------------------------------------------------------------ 08-a two-scales
    f = Figure(8, '時間スケールの二つの意味', '現象が進行する速さの尺度と、個体がそれを統合し経験する時間幅の尺度は一致しない', 560, 'a')
    X1 = log_axis(f, 300, 1050, 290, 1e-15, 10, [(1e-15, 'フェムト秒'), (1e-9, 'ナノ秒'), (1e-3, 'ミリ秒'), (1, '秒'), (10, '10秒')], '')
    f.text(80, 296, '現象の進行速度', 16, INK, weight=700)
    f.text(80, 318, '（物理的な尺度）', 13, MUTED)
    X2 = log_axis(f, 300, 1050, 450, 1e-3, 100, [(1e-3, 'ミリ秒'), (1e-2, '10ms'), (0.1, '100ms'), (1, '秒'), (10, '10秒'), (100, '100秒')], '')
    f.text(80, 456, '経験の統合幅', 16, INK, weight=700)
    f.text(80, 478, '（情報処理の尺度）', 13, MUTED)
    pairs = [('光の振動', 2e-15, '色の経験', '数百ミリ秒', 0.3, BLUE, 404), ('神経活動', 2e-3, '心理的現在', '約0.5〜3秒', 1.5, TEAL, 372), ('心拍', 1, '身体状態の認識', '数秒', 8, AMBER, 404)]
    for lab1, v1, lab2, rng, v2, color, ly in pairs:
        f.circ(X1(v1), 290, 8, color)
        f.text(X1(v1), 258, lab1, 14, color, anchor='middle', weight=700)
        f.circ(X2(v2), 450, 8, color)
        f.text(X2(v2), ly, lab2, 14, color, anchor='middle', weight=700)
        f.text(X2(v2), ly + 18, rng, 14, MUTED, anchor='middle')
        f.line(X1(v1), 300, X2(v2), 440, color=color, width=1.4, dash=True)
    f.footer('同じ現象が、二本の軸では別の位置に置かれる。両者の違いがマルチ時間スケールの出発点である。')
    made.add(f.save('08-a-two-scales.svg'))

    # ------------------------------------------------------------------ 08-d delay-bridge
    f = Figure(8, '遅延は、時間スケールを接続する構造である', '短い尺度の入力と長い尺度の記憶を、保持という橋が同じ処理の中へ運ぶ', 560, 'e')
    f.rect(90, 300, 330, 90, fill=TEAL, stroke='none', width=0, rx=14, opacity=0.8)
    f.text(255, 338, '感覚入力', 18, '#ffffff', anchor='middle', weight=700)
    f.text(255, 364, '短い時間スケール（ミリ秒〜秒）', 13, '#ffffff', anchor='middle')
    f.rect(780, 300, 330, 90, fill=PLUM, stroke='none', width=0, rx=14, opacity=0.8)
    f.text(945, 338, '記憶・行動計画', 18, '#ffffff', anchor='middle', weight=700)
    f.text(945, 364, '長い時間スケール（分〜年）', 13, '#ffffff', anchor='middle')
    f.path('M 420 345 C 500 260 700 260 780 345', color=AMBER, width=3)
    f.path('M 420 345 C 500 430 700 430 780 345', color=AMBER, width=3)
    f.text(600, 352, '保持 ・ 照合', 18, AMBER, anchor='middle', weight=700)
    f.text(600, 376, '直前の情報を保持し、長期の記憶を呼び出す', 13, INK, anchor='middle')
    f.brace(430, 770, 450, down=True)
    f.text(600, 486, 'この橋の幅が「遅延」として現れる', 16, INK, anchor='middle', weight=700)
    f.line(600, 300, 600, 240, color=MUTED, width=2, arrow=True)
    f.text(600, 226, '行動の選択へ', 14, MUTED, anchor='middle')
    f.footer('遅延は応答時間の増加ではなく、異なる尺度の情報を同じ処理で扱うための構造である。')
    made.add(f.save('08-e-delay-bridge.svg'))

    # ------------------------------------------------------------------ 08-e extended-memory
    f = Figure(8, '拡張記憶', '左の短い経験が、右の長い帯へ凝縮されて残る。下の軸は時間の長さ', 600, 'f')
    steps = [('一瞬見た顔', '数分後に思い出せる', BLUE), ('数分間の会話', '数年後まで覚えている', TEAL), ('一つの経験', 'その後の人生の判断に影響する', PLUM)]
    for i, (a, b, color) in enumerate(steps):
        y = 500 - i * 100
        x = 100 + i * 250
        f.rect(x, y - 60, 170, 50, fill='#ffffff', stroke=color, width=2, rx=10)
        f.text(x + 85, y - 28, a, 15, color, anchor='middle', weight=700)
        f.line(x + 175, y - 35, x + 225, y - 35, color=color, width=2, arrow=True)
        f.text(x + 200, y - 46, '凝縮', 12, MUTED, anchor='middle')
        f.rect(x + 230, y - 60, 300, 50, fill=color, stroke='none', width=0, rx=10, opacity=0.8)
        f.text(x + 380, y - 28, b, 14, '#ffffff', anchor='middle', weight=700)
    f.line(120, 540, 1080, 540, color=MUTED, width=2, arrow=True)
    for x, t in [(160, '一瞬'), (420, '数分'), (700, '数年'), (1000, '生涯')]:
        f.line(x, 534, x, 546, color=MUTED, width=1.5)
        f.text(x, 568, t, 14, MUTED, anchor='middle')
    f.text(600, 236, '経験の一部が選択され、関係づけられ、意味を持つ情報として保持される', 15, INK, anchor='middle')
    f.footer('')
    made.add(f.save('08-f-extended-memory.svg'))

    # ------------------------------------------------------------------ 08-g prospective-retrospective
    f = Figure(8, '体験中の時間と、振り返りの時間', '没頭と退屈で評価が逆転する。二つの評価は別の仕組みで決まる', 560, 'h')
    f.text(520, 250, '体験中', 17, INK, anchor='middle', weight=700)
    f.text(520, 272, '注意が時間に向くほど長い', 12, MUTED, anchor='middle')
    f.text(880, 250, '振り返り', 17, INK, anchor='middle', weight=700)
    f.text(880, 272, '記憶の密度が高いほど長い', 12, MUTED, anchor='middle')
    rows = [('没頭した活動', 0.3, 0.9, TEAL), ('退屈な待ち時間', 0.9, 0.3, AMBER)]
    for i, (lab, p, r, color) in enumerate(rows):
        y = 320 + i * 110
        f.text(100, y + 28, lab, 17, INK, weight=700)
        f.rect(360, y, 320 * p, 44, fill=color, stroke='none', width=0, rx=8, opacity=0.8)
        f.text(360 + 320 * p + 12, y + 29, '短い' if p < 0.5 else '長い', 15, color, weight=700)
        f.rect(720, y, 320 * r, 44, fill=color, stroke='none', width=0, rx=8, opacity=0.8)
        f.text(720 + 320 * r + 12, y + 29, '短い' if r < 0.5 else '長い', 15, color, weight=700)
    f.line(350, 300, 350, 500, color=LINE, width=1)
    f.line(710, 300, 710, 500, color=LINE, width=1)
    f.footer('主観的な時間の伸縮は、単一の内部時計の速さの変化だけでは説明できない。')
    made.add(f.save('08-h-prospective-retrospective.svg'))

    # ------------------------------------------------------------------ 08-h distributed-time
    f = Figure(8, '時間経験は、一か所にない', '複数の脳領域が異なる働きを担い、身体の状態と行動・環境の循環がそれに影響する', 620, 'i')
    f.body.append(f'<ellipse cx="560" cy="380" rx="300" ry="170" fill="#ffffff" stroke="{BLUE}" stroke-width="2.5"/>')
    f.text(560, 236, '脳', 18, BLUE, anchor='middle', weight=700)
    regions = [('前頭前皮質', '予測・計画', 440, 300), ('補足運動野', 'タイミング', 640, 300), ('基底核', '長さの推定', 380, 400), ('小脳', '運動の時間調整', 700, 410), ('海馬', '順序・想起', 540, 470)]
    for lab, sub, x, y in regions:
        f.rect(x - 80, y - 24, 160, 48, fill=SOFT, stroke='none', width=0, rx=10)
        f.text(x, y - 3, lab, 14, INK, anchor='middle', weight=700)
        f.text(x, y + 15, sub, 11, MUTED, anchor='middle')
    f.text(560, 380, '中央時計はない', 13, MUTED, anchor='middle')
    f.rect(70, 320, 160, 120, fill='#ffffff', stroke=PLUM, width=2, rx=12)
    f.lines(150, 352, ['身体の状態', '心拍・呼吸', 'ホルモン・免疫', '睡眠'], 13, PLUM, anchor='middle', gap=22)
    f.line(235, 380, 262, 380, color=PLUM, width=2, arrow=True)
    f.rect(960, 320, 170, 120, fill='#ffffff', stroke=AMBER, width=2, rx=12)
    f.lines(1045, 352, ['環境', '行動が環境を変え', '新しい入力が', '戻ってくる'], 13, AMBER, anchor='middle', gap=22)
    f.path('M 858 350 C 900 330 930 330 955 350', color=AMBER, width=2, arrow=True)
    f.path('M 955 410 C 930 430 900 430 858 410', color=AMBER, width=2, arrow=True)
    f.text(600, 590, '時間経験を成立させる神経機構を理解するには、身体や環境との相互作用も含めて考える必要がある', 14, INK, anchor='middle')
    f.footer('')
    made.add(f.save('08-i-distributed-time.svg'))

    # ================================================================== 第3回の増補（2026-10-29、4点）

    # ------------------------------------------------------------------ 01-e series-map
    f = Figure(1, '連載の見取り図', '「測る」から「経験する」へ。3部8回で、心の時間的構造から身体と統合へ進む', 620, 'e')
    parts = [('第I部　時間を測る、時間を感じる', BLUE, [('第1回', '時計の時間と経験の時間'), ('第2回', '時間知覚の限界'), ('第3回', '脳による世界の再構成')]),
             ('第II部　心の時間的構造', TEAL, [('第4回', '遅延と行動の選択'), ('第5回', '記憶が現在を構成する'), ('第6回', '厚みのある現在')]),
             ('第III部　身体と統合', AMBER, [('第7回', '身体と環境の相互作用'), ('第8回', 'マルチ時間スケール')])]
    for i, (title, color, rows) in enumerate(parts):
        x = 70 + i * 375
        f.rect(x, 210, 340, 300, fill='#ffffff', stroke=color, width=2.5, rx=18)
        f.text(x + 170, 246, title, 17, color, anchor='middle', weight=700)
        for j, (no, theme) in enumerate(rows):
            y = 292 + j * 64
            f.rect(x + 24, y, 292, 46, fill=SOFT if not (i == 2 and j == 1) else color, stroke='none', width=0, rx=10, opacity=1 if not (i == 2 and j == 1) else 0.85)
            f.text(x + 40, y + 30, no, 14, color if not (i == 2 and j == 1) else '#ffffff', weight=700)
            f.text(x + 112, y + 30, theme, 15, INK if not (i == 2 and j == 1) else '#ffffff')
        if i < 2:
            f.line(x + 346, 360, x + 372, 360, color=MUTED, width=2.2, arrow=True)
    f.text(600, 560, '時間とは何か　→　生物はどのような仕組みで時間を経験するのか', 17, INK, anchor='middle', weight=700)
    f.text(600, 590, '問いは物理学的なものから、生物学的・認知的なものへ移る', 14, MUTED, anchor='middle')
    f.footer('')
    made.add(f.save('01-e-series-map.svg'))

    # ------------------------------------------------------------------ 04-f language-time-range
    f = Figure(4, '言語が広げる、利用できる時間の範囲', '個体の経験は生涯の内側に限られるが、他者の記録と構想によって数百年前から数十年後まで届く', 580, 'g')
    f.line(120, 440, 1080, 440, color=MUTED, width=2, arrow=True)
    ticks = [(180, '数百年前'), (420, '数十年前'), (700, 'いま'), (980, '数十年後')]
    for x, lab in ticks:
        f.line(x, 434, x, 446, color=MUTED, width=1.5)
        f.text(x, 470, lab, 14, MUTED, anchor='middle')
    f.line(700, 250, 700, 434, color=AMBER, width=1.5, dash=True)
    f.rect(420, 370, 280, 36, fill=TEAL, stroke='none', width=0, rx=18, opacity=0.85)
    f.text(560, 394, '個体が直接経験した過去', 14, '#ffffff', anchor='middle', weight=700)
    f.rect(180, 310, 520, 36, fill=BLUE, stroke='none', width=0, rx=18, opacity=0.8)
    f.text(440, 334, '他者の記録から学ぶ過去（歴史）', 14, '#ffffff', anchor='middle', weight=700)
    f.rect(700, 310, 280, 36, fill=AMBER, stroke='none', width=0, rx=18, opacity=0.8)
    f.text(840, 334, '構想できる未来', 14, '#ffffff', anchor='middle', weight=700)
    f.brace(180, 980, 290, down=False)
    f.text(580, 262, '言語によって利用できる時間的情報の範囲', 16, INK, anchor='middle', weight=700)
    f.text(580, 236, '記号化し、他者へ伝達し、記録から学ぶ', 13, MUTED, anchor='middle')
    f.text(560, 420, '自分の生涯の内側', 12, TEAL, anchor='middle')
    f.footer('人間は、現在に存在しない出来事を利用して、現在の行動を決定する生物である。')
    made.add(f.save('04-g-language-time-range.svg'))

    # ------------------------------------------------------------------ 06-c retention-vs-recollection
    f = Figure(6, '保持と想起は、別の働きである', '想起は現在にない過去を呼び戻す。保持は直前の過去が現在の中に残っている', 580, 'c')
    f.panel(70, 200, 500, 320, '想起')
    f.line(110, 420, 530, 420, color=MUTED, width=2, arrow=True)
    f.circ(170, 420, 9, PLUM)
    f.text(170, 452, '昨日聴いた曲', 14, PLUM, anchor='middle', weight=700)
    f.circ(470, 420, 9, INK)
    f.text(470, 452, 'いま', 14, INK, anchor='middle', weight=700)
    f.path('M 462 408 C 400 300 240 300 182 406', color=PLUM, width=2.2, arrow=True, dash=True)
    f.text(320, 318, '意識的に呼び戻す', 15, PLUM, anchor='middle', weight=700)
    f.text(320, 490, '現在の感覚入力としては存在しない過去', 13, MUTED, anchor='middle')
    f.panel(630, 200, 500, 320, '保持')
    f.line(670, 420, 1090, 420, color=MUTED, width=2, arrow=True)
    f.rect(880, 360, 170, 90, fill=TEAL, stroke='none', width=0, rx=16, opacity=0.14)
    f.text(965, 346, '現在の幅', 13, TEAL, anchor='middle')
    f.circ(910, 420, 20, TEAL, opacity=0.45)
    f.text(910, 427, 'ド', 15, INK, anchor='middle', weight=700)
    f.circ(1010, 420, 20, TEAL)
    f.text(1010, 427, 'ミ', 15, '#ffffff', anchor='middle', weight=700)
    f.text(910, 468, '直前', 13, MUTED, anchor='middle')
    f.text(1010, 468, 'いま鳴っている', 13, MUTED, anchor='middle')
    f.text(880, 300, '思い出そうとしなくても残っている', 15, TEAL, anchor='middle', weight=700)
    f.text(880, 490, '現在の経験の一部として持ち越されている', 13, MUTED, anchor='middle')
    f.footer('フッサールの時間意識が扱うのは右の働きである。')
    made.add(f.save('06-c-retention-vs-recollection.svg'))

    # ------------------------------------------------------------------ 08-i terminology-map
    f = Figure(8, '本連載の用語と、平井靖史のMTS解釈の対応', '左が平井の用語、右が本連載の用語。線の種類で対応の仕方を示す', 747, 'j')
    f.text(330, 226, '平井靖史（MTS解釈）', 18, PLUM, anchor='middle', weight=700)
    f.text(870, 226, '本連載', 18, BLUE, anchor='middle', weight=700)
    rows = [('MTS（マルチ時間スケール）解釈', 'マルチ時間スケール', True), ('階層0・1・2・3', '階層0〜3', True), ('凝縮（凝縮説）', '時間的粗視化／凝縮説', True), ('現在という窓／幅のある現在', '心理的現在（幅のある現在）', True), ('未完了相', '未完了相としての現在', True), ('意識の遅延テーゼ', '遅延／意識の遅延テーゼ', True), ('スケールギャップ', '時間スケールギャップ', True), ('複数の時間スケールの積層', '多重時計原理', False), ('純粋記憶のMTS解釈', '拡張記憶', False), ('（対応する用語なし）', 'サリエンス・スレッシュホールド', False)]
    for i, (left, right, same) in enumerate(rows):
        y = 256 + i * 44
        f.rect(110, y, 440, 34, fill='#ffffff', stroke=PLUM if left != '（対応する用語なし）' else LINE, width=1.5, rx=8)
        f.text(330, y + 23, left, 14, INK if left != '（対応する用語なし）' else MUTED, anchor='middle')
        f.rect(650, y, 440, 34, fill='#ffffff', stroke=BLUE, width=1.5, rx=8)
        f.text(870, y + 23, right, 14, INK, anchor='middle')
        if left != '（対応する用語なし）':
            f.line(552, y + 17, 648, y + 17, color=MUTED, width=1.8, dash=not same)
    f.line(110, 712, 150, 712, color=MUTED, width=1.8)
    f.text(160, 717, '同じ名称', 13, MUTED)
    f.line(260, 712, 300, 712, color=MUTED, width=1.8, dash=True)
    f.text(310, 717, '本連載による言い換え', 13, MUTED)
    f.footer('')
    made.add(f.save('08-j-terminology-map.svg'))

    # ================================================================== 第3回の増補・中（2026-10-29、10点）

    # ------------------------------------------------------------------ 02-b frame-sequence
    f = Figure(2, '静止画の列が、動きになる', '60FPSの6コマ。間隔が識別の限界より短いと、独立した静止画ではなく連続した運動として経験される', 600, 'b')
    for k in range(6):
        x = 90 + k * 172
        f.rect(x, 210, 150, 100, fill='#ffffff', stroke=LINE, width=1.5, rx=8)
        bx = x + 20 + k * 22; by = 290 - 60 * math.sin(math.pi * k / 5)
        f.circ(bx, by, 9, AMBER)
        f.text(x + 75, 334, f'{k * 16.7:.1f}ms' if k else '0ms', 13, MUTED, anchor='middle')
    f.line(600, 350, 600, 390, color=MUTED, width=2.2, arrow=True)
    f.text(620, 376, '間隔が識別の限界より短い', 14, INK)
    f.rect(90, 400, 1020, 110, fill='#ffffff', stroke=TEAL, width=2, rx=10)
    f.path('M 130 490 C 400 330 800 330 1070 490', color=TEAL, width=2.5, dash=True)
    for t_ in [0.15, 0.4, 0.65, 0.9]:
        x = 130 + 940 * t_; y = 490 - 160 * 3 * t_ * (1 - t_) * 0.5
        f.circ(x, y, 8, AMBER, opacity=0.3 + 0.7 * t_)
    f.text(600, 540, '経験される滑らかな運動', 15, TEAL, anchor='middle', weight=700)
    f.footer('16.7ミリ秒が視覚の分解能そのものというわけではない。点滅・順序・運動の識別はそれぞれ異なる。')
    made.add(f.save('02-b-frame-sequence.svg'))

    # ------------------------------------------------------------------ 02-h two-operations
    f = Figure(2, '経験を成立させる、二つの働き', '左右の二つの働きが、下の「経験される世界」へ合流する', 620, 'h')
    f.panel(70, 200, 500, 300, 'まとめる働き（時間的粗視化）')
    for k in range(28):
        x = 120 + k * 8
        h = 10 + (k * 11) % 26
        f.line(x, 330, x, 330 - h, color=AMBER, width=2.5, opacity=0.7)
    f.line(360, 310, 400, 310, color=MUTED, width=2, arrow=True)
    f.rect(410, 296, 120, 28, fill=AMBER, stroke='none', width=0, rx=6, opacity=0.8)
    f.text(470, 315, '一つの値', 13, '#ffffff', anchor='middle', weight=700)
    f.text(320, 380, '多数の微細な変動 → 平均的な明るさ', 14, INK, anchor='middle')
    f.panel(630, 200, 500, 300, '統合する働き（持続）')
    for k, (x, y) in enumerate([(690, 330), (740, 300), (790, 320), (840, 290)]):
        f.circ(x, y, 8, TEAL)
    f.text(765, 360, '別々の時点の情報', 13, MUTED, anchor='middle')
    f.line(880, 310, 920, 310, color=MUTED, width=2, arrow=True)
    f.path('M 930 330 C 960 290 1000 290 1030 320 S 1080 330 1100 300', color=TEAL, width=3)
    f.text(1015, 360, '一つの流れ', 13, TEAL, anchor='middle', weight=700)
    f.text(880, 380, '前の音が次の音へ残る → メロディー', 14, INK, anchor='middle')
    f.path('M 320 502 C 320 566 420 566 462 566', color=AMBER, width=2, arrow=True)
    f.path('M 880 502 C 880 566 780 566 738 566', color=TEAL, width=2, arrow=True)
    f.box(470, 542, 260, 48, '経験される世界', '', INK, 16)
    f.footer('')
    made.add(f.save('02-h-two-operations.svg'))

    # ------------------------------------------------------------------ 03-a familiar-room
    f = Figure(3, 'いつもの部屋に入るとき', '破線が入る前の予測、実線が実際の入力。重なる所と、ずれる所を見る', 600, 'a')
    f.rect(140, 210, 700, 340, fill='#ffffff', stroke=INK, width=2.5, rx=6)
    f.rect(240, 230, 160, 24, fill='none', stroke=BLUE, width=2, dash=True)
    f.rect(243, 233, 154, 18, fill=SOFT, stroke=BLUE, width=1.5)
    f.text(320, 280, '窓', 13, BLUE, anchor='middle')
    f.rect(560, 330, 200, 90, fill='none', stroke=BLUE, width=2, dash=True)
    f.rect(563, 333, 194, 84, fill=SOFT, stroke=BLUE, width=1.5, rx=4)
    f.text(660, 380, '机', 14, BLUE, anchor='middle')
    f.circ(480, 240, 18, BLUE, fill=False, dash=True, width=2)
    f.circ(480, 240, 14, '#f3d16a')
    f.text(480, 282, '照明', 13, BLUE, anchor='middle')
    f.rect(300, 440, 60, 60, fill='none', stroke=AMBER, width=2, dash=True)
    f.text(330, 526, '予測した椅子', 12, AMBER, anchor='middle')
    f.rect(420, 460, 60, 60, fill=SOFT, stroke=AMBER, width=2, rx=4)
    f.text(450, 540, '実際の椅子', 12, AMBER, anchor='middle')
    f.line(365, 470, 415, 490, color=AMBER, width=1.8, arrow=True)
    f.text(880, 260, '破線：入る前の予測', 14, BLUE, weight=700)
    f.text(880, 286, '実線：実際の入力', 14, INK, weight=700)
    f.text(880, 340, '窓・机・照明：一致', 14, BLUE)
    f.text(880, 366, '→ 推定を維持', 13, MUTED)
    f.text(880, 420, '椅子：ずれ', 14, AMBER, weight=700)
    f.text(880, 446, '→ 予測誤差で修正', 13, MUTED)
    f.footer('毎回初めて見るものとして解析しているのではない。学習した世界の構造を使って認識が成立する。')
    made.add(f.save('03-a-familiar-room.svg'))

    # ------------------------------------------------------------------ 04-d loosened-chain
    f = Figure(4, '物理的な反応連鎖からの「離脱」', '物質では作用がただちに一つの反作用になる。生物では鎖が緩み、複数の反作用へ枝分かれする', 600, 'd')
    f.text(80, 262, '物質', 18, INK, weight=700)
    f.box(170, 236, 170, 56, '作用', '', MUTED, 18)
    for k in range(9):
        f.circ(380 + k * 34, 264, 11, MUTED, fill=False, width=2.5)
    f.box(720, 236, 190, 56, '反作用', '一つに決まる', MUTED, 18)
    f.text(560, 318, '一本の鎖で直結する', 13, MUTED, anchor='middle')
    f.text(80, 432, '生物', 18, INK, weight=700)
    f.box(170, 406, 170, 56, '刺激', '', BLUE, 18)
    for k in range(4):
        f.circ(380 + k * 34, 434, 11, BLUE, fill=False, width=2.5)
    f.rect(500, 396, 150, 76, fill='none', stroke=BLUE, width=2, rx=14, dash=True)
    f.text(575, 428, '内部状態', 13, BLUE, anchor='middle', weight=700)
    f.text(575, 448, '過去の経験', 13, BLUE, anchor='middle', weight=700)
    for k, (lab, y, color) in enumerate([('反作用 A', 360, TEAL), ('反作用 B', 434, AMBER), ('反作用 C', 508, PLUM)]):
        f.path(f'M 655 434 C 690 434 690 {y} 715 {y}', color=color, width=2, arrow=True)
        f.rect(720, y - 22, 190, 44, fill='#ffffff', stroke=color, width=2, rx=10)
        f.text(815, y + 6, lab, 15, color, anchor='middle', weight=700)
    f.text(1000, 440, '選択の可能性', 15, INK, anchor='middle', weight=700)
    f.footer('物理法則の外に出るのではない。入力と行動の関係が、内部状態と過去の経験によって媒介される。')
    made.add(f.save('04-d-loosened-chain.svg'))

    # ------------------------------------------------------------------ 06-e anticipation-branches
    f = Figure(6, '予感が、現在を変える', '一点から右へ伸びる三本の破線が予感。左のぼかしが、現在に生じるもの', 610, 'e')
    f.line(120, 480, 1080, 480, color=MUTED, width=2, arrow=True)
    f.text(1086, 485, '時間', 13, MUTED)
    f.circ(400, 480, 10, INK)
    f.text(400, 516, '「今日は大切な話がある」', 15, INK, anchor='middle', weight=700)
    f.text(400, 540, 'いま', 13, MUTED, anchor='middle')
    for lab, y, color in [('良い知らせかもしれない', 270, TEAL), ('悪い知らせかもしれない', 350, AMBER), ('相談かもしれない', 430, PLUM)]:
        f.path(f'M 408 472 C 600 472 700 {y} 860 {y}', color=color, width=2, dash=True, arrow=True)
        f.text(880, y + 5, lab, 15, color, weight=700)
    f.text(960, 240, 'まだ言われていない内容', 13, MUTED, anchor='middle')
    f.blob(400, 400, 80, AMBER, 0.45)
    f.text(400, 396, '期待', 15, INK, anchor='middle', weight=700)
    f.text(400, 416, '不安', 15, INK, anchor='middle', weight=700)
    f.text(220, 400, '現在の経験に', 13, MUTED, anchor='middle')
    f.text(220, 420, '生じるもの', 13, MUTED, anchor='middle')
    f.footer('未来の可能性が、実現する前に現在の一部になっている。')
    made.add(f.save('06-e-anticipation-branches.svg'))

    # ------------------------------------------------------------------ 07-h three-signaling-layers
    f = Figure(7, '脳内の情報伝達の三つの層', '高速なシナプス信号、広い範囲の神経修飾、細胞外環境の変化。時間スケールが異なる三つの層が神経系の状態を変える', 620, 'h')
    rows = [('シナプス信号', '一対一の電気化学的な伝達', 'ミリ秒', BLUE), ('神経修飾物質', 'ノルアドレナリン・ドーパミンなどによる広い範囲の調節', '秒〜分', AMBER), ('細胞外環境', 'アストロサイト・細胞外液・老廃物除去', '分〜時間', PLUM)]
    for i, (lab, sub, scale, color) in enumerate(rows):
        y = 230 + i * 118
        f.rect(80, y, 1040, 96, fill='#ffffff', stroke=color, width=2, rx=12)
        f.text(110, y + 36, lab, 17, color, weight=700)
        f.text(110, y + 62, sub, 13, MUTED)
        f.text(1090, y + 36, scale, 14, color, anchor='end', weight=700)
        if i == 0:
            for k in range(26):
                x = 560 + k * 16
                f.line(x, y + 20, x, y + 20 + (12 + (k * 7) % 20), color=color, width=2, opacity=0.8)
        elif i == 1:
            f.blob(800, y + 48, 150, color, 0.4)
            f.text(800, y + 52, '広域', 12, color, anchor='middle')
        else:
            f.wave(560, 1000, y + 48, 14, 1.5, color, 2.5)
    f.footer('脳は固定された回路が入力を処理する装置ではなく、内部環境の変化によって処理の状態を変え続ける。')
    made.add(f.save('07-h-three-signaling-layers.svg'))

    # ------------------------------------------------------------------ 07-j self-reference-loop
    f = Figure(7, '自己参照の輪', '注意が身体反応を変え、変化した身体が感情と時間感覚を変え、それがまた注意を変える', 665, 'j')
    loop_nodes(f, 600, 420, 190, ['危険を感じる', '注意が集中する', '心拍が上がる', '時間が長く感じる'], AMBER, 190, 50, 15)
    f.text(600, 416, '経験する主体', 16, INK, anchor='middle', weight=700)
    f.text(600, 440, '輪の外ではなく、中にいる', 12, MUTED, anchor='middle')
    f.footer('')
    made.add(f.save('07-j-self-reference-loop.svg'))

    # ------------------------------------------------------------------ 07-k cross-scale-examples
    f = Figure(7, '長い尺度が、短い尺度を変える', '睡眠不足、炎症、運動習慣。長い時間で形成された状態が、瞬間の反応を左右する', 578, 'k')
    cols = [('数日の睡眠不足', '日', '翌日の注意・反応速度', '秒', BLUE), ('数日続く炎症', '日〜週', 'いまの疲労感', 'いま', AMBER), ('長年の運動習慣', '年', '一瞬の運動能力', '一瞬', TEAL)]
    for i, (top, ts, bottom, bs, color) in enumerate(cols):
        x = 80 + i * 340
        f.box(x, 230, 300, 76, top, f'尺度：{ts}', color, 17)
        f.line(x + 150, 312, x + 150, 390, color=color, width=2.5, arrow=True)
        f.box(x, 396, 300, 76, bottom, f'尺度：{bs}', color, 17)
    f.path('M 400 400 C 410 360 410 350 400 308', color=MUTED, width=1.8, dash=True, arrow=True)
    f.path('M 740 400 C 750 360 750 350 740 308', color=MUTED, width=1.8, dash=True, arrow=True)
    f.text(600, 520, '逆向きもある ── 短い尺度の反復（学習・習慣）が、長い尺度の状態を変える', 14, MUTED, anchor='middle')
    f.text(600, 548, '短い時間と長い時間は並んでいるのではなく、互いの状態を変えながら一つの生命活動を形成する', 14, INK, anchor='middle')
    f.footer('')
    made.add(f.save('07-k-cross-scale-examples.svg'))

    # ------------------------------------------------------------------ 08-c sequence-vs-melody
    f = Figure(8, '時間の加算ではなく、統合', '同じ長さの音符でも、関係が形成されなければまとまりにならない', 580, 'c')
    f.panel(70, 200, 500, 320, '系列（関係なし）')
    f.line(110, 420, 530, 420, color=LINE, width=2)
    for k, (x, y) in enumerate([(160, 380), (230, 330), (300, 395), (370, 345), (440, 370), (500, 320)]):
        f.circ(x, y, 10, MUTED)
        f.line(x, y, x, y - 34, color=MUTED, width=2.2)
    f.text(320, 470, '長さはあるが、まとまりはない', 14, INK, anchor='middle')
    f.panel(630, 200, 500, 320, 'メロディー（関係あり）')
    f.blob(880, 360, 190, TEAL, 0.3)
    f.line(670, 420, 1090, 420, color=LINE, width=2)
    pts = [(720, 380), (790, 350), (860, 365), (930, 330), (1000, 345), (1060, 320)]
    for k, (x, y) in enumerate(pts):
        f.circ(x, y, 10, TEAL)
        f.line(x, y, x, y - 34, color=TEAL, width=2.2)
        if k < len(pts) - 1:
            nx, ny = pts[k + 1]
            f.path(f'M {x+8} {y-8} Q {(x+nx)/2} {min(y,ny)-40} {nx-8} {ny-8}', color=TEAL, width=1.5, dash=True)
    f.text(880, 256, 'リズム ・ 音程 ・ 反復 ・ 期待', 14, TEAL, anchor='middle', weight=700)
    f.text(880, 470, '関係で結ばれて、一つのまとまりになる', 14, INK, anchor='middle')
    f.footer('短い時間の出来事を並べただけでは、長い時間の現象は成立しない。')
    made.add(f.save('08-c-sequence-vs-melody.svg'))

    # ------------------------------------------------------------------ 08-k three-disciplines
    f = Figure(8, '同じ「時間」をめぐる三つの問い', '物理学、哲学、認知科学はそれぞれ異なる問題を扱う。本連載の位置は認知科学と哲学の重なりにある', 730, 'k')
    f.circ(450, 360, 150, BLUE, fill=False, width=2.5)
    f.circ(750, 360, 150, PLUM, fill=False, width=2.5)
    f.circ(600, 500, 150, TEAL, fill=False, width=2.5)
    f.text(370, 300, '物理学', 20, BLUE, anchor='middle', weight=700)
    f.lines(370, 330, ['出来事の順序と間隔', '物理法則による変化'], 13, INK, anchor='middle', gap=20)
    f.text(830, 300, '哲学', 20, PLUM, anchor='middle', weight=700)
    f.lines(830, 330, ['時間の存在と方向性', '過去・現在・未来の関係'], 13, INK, anchor='middle', gap=20)
    f.text(600, 590, '認知科学', 20, TEAL, anchor='middle', weight=700)
    f.lines(600, 618, ['生物が時間をどう知覚し、', '推定し、記憶するか'], 13, INK, anchor='middle', gap=20)
    f.blob(672, 448, 46, AMBER, 0.8)
    f.text(672, 452, '本連載', 14, '#ffffff', anchor='middle', weight=700)
    f.text(960, 470, '生物にとっての時間経験', 14, AMBER, weight=700)
    f.line(950, 466, 720, 452, color=AMBER, width=1.5, dash=True)
    f.footer('時間の実在や方向性、決定論との関係には、なお別の検討が要る。')
    made.add(f.save('08-k-three-disciplines.svg'))

    missing, extra = expected - made, made - expected
    if missing or extra:
        raise SystemExit(f'figure set mismatch: missing={sorted(missing)} extra={sorted(extra)}')
    print(f'wrote {len(made)} SVG files to {OUT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
