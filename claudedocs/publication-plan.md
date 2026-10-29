# 連載「時間はどのように生まれるのか」GitHub Pages 公開計画

作成日: 2026-10-29

## 1. 原稿の確認結果

原稿: https://chatgpt.com/share/6ae30834-ce9c-83ee-b123-b00f11aaabe6 （タイトル「章ごとの論旨整理」）

| 回 | 題名 | 共有ページでの状態 |
| --- | --- | --- |
| 第1回 | （時計の時間と主観的時間の区別。第8回の振り返りから推定） | **本文なし** |
| 第2回 | （時間分解能・時間スケールギャップ・蛍光灯の例） | **本文なし** |
| 第3回 | （生成モデル・予測処理による知覚の再構成） | **本文なし** |
| 第4回 | 意識は、反応の「遅延」から生まれたのか？ ――生命が獲得した時間的余白と、心の誕生 | 全文あり（10節） |
| 第5回 | 心は過去でできている ――記憶は保存庫ではなく、現在の世界を構築する仕組みである | 全文あり（10節） |
| 第6回 | 「現在」は、なぜ一瞬ではないのか？（ベルクソンの持続とフッサールの時間意識） | **本文なし**（第7・8回から参照されている） |
| 第7回 | 脳だけでは、心も時間も生まれない ――身体と世界の相互作用が構築する、もう一つの時間 | 全文あり（14節、表1つ） |
| 第8回 | 私たちの中には、複数の時間が流れている ――マルチ時間スケールから考える、時間・意識・心の成立 | 全文あり（14節＋「連載を終えて」＋到達点の箇条書き） |

共有ページ末尾には ChatGPT によるリポジトリ命名の提案が含まれる。
- 推奨リポジトリ名: `multi-scale-time`（作業ディレクトリ名と一致）
- Title: 時間はどのように生まれるのか
- Description: 時間知覚、意識、記憶、身体の相互作用を通じて、マルチ時間スケールから主観的時間の成立を考察する全8回の連載。
- 章ファイル名案: 01-does-time-flow / 02-limits-of-time-perception / 03-brain-reconstructs-reality / 04-consciousness-and-delay / 05-mind-is-made-of-memory / 06-the-thickness-of-now / 07-embodied-time / 08-multiple-times-within-us

### 原稿の特徴（公開時の扱い）
- である調。1文1段落の短い行が続く。番号付き節見出し（「1. 刺激を受けて…」）。
- 各回末尾に「次回｜第N回『…』」の予告と、ChatGPT のメタ注記（「今回の論旨は…」「第5回を書く」）がある。メタ注記は本文から除く。
- 本文に「元資料では…」という表現が複数ある（第7回8節、第8回3・5・6・7節）。公開記事としては出典名に置き換えるか、表現を改めるかの判断が必要。
- 言及される理論・人物: ベルクソン（意識の遅延テーゼ、持続、記憶イメージの投射）、フッサール（原初印象・保持・予感）、シャクター＝シンガー二要因理論、吊り橋実験、ホメオスタシス／アロスタシス、腸脳相関、サリエンシー、自由エネルギー原理（フリストン）、能動的推論、セカンドオーダー・サイバネティクス、時計遺伝子 CLOCK/BMAL1、グリンファティック・システム、エプファティック・コミュニケーション、脳波帯域。

## 2. 参考サイト（relevance）の方式

https://yamaguchiyoshito.github.io/relevance/ ／ https://github.com/yamaguchiyoshito/relevance

- 原本は Markdown（`chapters/NN-slug.md`）と独立 SVG（`assets/illustrations/NN-x-slug.svg`）。SVG は `scripts/draw_figures.py` から決定論的に再生成。
- `scripts/build.py` が Pandoc 3.x で HTML 化し `_site/` を生成。JS なし、外部フォント・外部画像なし。`_site/complete.html` に全回を1ファイル化。
- 図の書き方: Markdown で `![代替テキスト](../assets/illustrations/04-a-slug.svg)` の直後に `*図4-1：…*` を置く。build.py が `<figure><div class="figure-scroll"><a class="figure-link" href=SVG title="図を原寸で開く"><img …></a></div><figcaption>図4-1：…</figcaption></figure>` に変換。
- 前後ナビは `<!-- NAV:TOP -->` / `<!-- NAV:BOTTOM -->` マーカー。目次・部構成・図一覧・出典IDは `series.json` が正本。`scripts/validate.py` が本文・図・脚注・出典の整合を検査。
- 脚注 `[^id]` と `references/sources.json` を同じIDで結び、`references/bibliography.md` を生成。確認範囲（書誌のみ／全文確認）を明記。
- 公開: `.github/workflows/pages.yml`（push to main → validate → unittest → build → check_html → deploy-pages）。Pages の Source は GitHub Actions。Pandoc は 3.7.0.2 に固定。
- ライセンス CC BY 4.0。README に `<!-- SITE-INDEX-END -->` マーカーを置き、それより前だけをサイトのトップに使う。

この環境: Python 3.13.4、pandoc 3.7.0.2（参考サイトと同一版）、gh は yamaguchiyoshito で認証済み。`yamaguchiyoshito/multi-scale-time` は未作成。

## 3. 提案するリポジトリ構成

```
multi-scale-time/
├── README.md                 # 表紙図・タグライン・全8回の目次（SITE-INDEX-END より前がサイトのトップ）
├── series.json               # id/code/title/parts/chapters(figures, sources)
├── chapters/
│   ├── 01-does-time-flow.md
│   ├── 02-limits-of-time-perception.md
│   ├── 03-brain-reconstructs-reality.md
│   ├── 04-consciousness-and-delay.md
│   ├── 05-mind-is-made-of-memory.md
│   ├── 06-the-thickness-of-now.md
│   ├── 07-embodied-time.md
│   └── 08-multiple-times-within-us.md
├── assets/illustrations/     # 00-cover.svg, 04-a-*.svg … draw_figures.py から生成
├── references/
│   ├── sources.json
│   └── bibliography.md       # 生成物
├── guides/
│   ├── READING.md / EDITING.md / PUBLISHING.md / SERIES-DESIGN.md
├── scripts/
│   ├── build.py / validate.py / check_html.py / draw_figures.py / bibliography.py
├── site-src/styles.css       # 配色を relevance の藍から別系統（例: 琥珀〜深青）へ
├── tests/
├── .github/workflows/pages.yml
├── LICENSE (CC BY 4.0) / .gitignore / .editorconfig / CHANGELOG.md
└── claudedocs/
```

relevance のスクリプトは「全12回」が文字列として埋め込まれているため、回数・連載コード・配色を `series.json` から読む形に書き直す（コピーではなく、同じ設計で新規作成）。

## 4. 部構成（案）

| 部 | 回 | 主題 |
| --- | --- | --- |
| I 時間を測る、時間を感じる | 1〜3 | 客観的時間と主観的時間、時間分解能、予測による知覚の再構成 |
| II 心の時間的構造 | 4〜6 | 遅延と行動選択、記憶による現在の構成、現在の厚み |
| III 身体と統合 | 7〜8 | 身体・環境との相互作用、マルチ時間スケールによる統合 |

第1〜3回の本文が揃った時点で確定する。

## 5. 図版の案（判読できた4回分）

| 図 | 内容 |
| --- | --- |
| 図4-1 | 刺激→反応の直結経路と、記憶・予測が介在する「時間的余白」付き経路の対比 |
| 図4-2 | 三つの時間尺度（瞬間的反応／経験による修正／長期計画）が同じ身体で並行する図 |
| 図4-3 | 毎日1,000円を使い切る場合と、三か月分をまとめて扱う場合の実現可能な行動の差 |
| 図5-1 | 「倉庫としての記憶」と「現在を構成する記憶」の対比 |
| 図5-2 | 「海」を中心に、類似・近接・感情で結ばれる多次元ネットワーク |
| 図5-3 | 想起→照合→再構成→蓄積の自己回帰ループ |
| 図7-1 | 神経・内分泌・免疫・代謝・成長の時間尺度を対数軸に並べた帯図（本文の表に対応） |
| 図7-2 | 外受容・自己受容・内受容の三感覚と行動調整（坂道を走る例） |
| 図7-3 | 知覚と行動の循環（能動的推論）に観察者自身を含める二次サイバネティクスの図 |
| 図8-1 | 一人の内部の複数の時計（ミリ秒〜年）と相互影響の矢印 |
| 図8-2 | 階層0〜3の時間的凝縮（下位の多数の変化が上位で一つのまとまりになる） |
| 図8-3 | 現在の構成（原初印象・保持・予感に長期記憶と予測が重なる） |
| 図8-4 | 全8回の論理の到達点（6段階の流れ） |
| 表紙 | 異なる周期の波が重なり合い、一つの「いま」を形づくる図 |

1枚につき主張1つ、パネル2枚まで、ラベル10個前後。本文の該当段落の直後に置く。

## 6. 本文の編集方針

- 文章は無改変。見出しの Markdown 化、図・キャプションの挿入、脚注、前後ナビの付与のみ行う。
- 短い1文段落は原稿どおり維持する（まとめ直さない）。
- 「次回｜…」の予告は「次回へ」節として残す。ChatGPT のメタ注記（論旨要約、「第N回を書く」）は除く。
- 「元資料では」の扱いは著者判断を待つ（出典名への置換、または「本連載の土台となるノートでは」等への表現変更）。
- 理論・人物への言及には脚注を付け、`references/sources.json` に書誌と確認範囲を登録する。

## 7. 作業手順

1. 足場: series.json、scripts（build/validate/check_html/bibliography/draw_figures）、styles.css、tests、workflow、LICENSE、README、guides。
2. 第4・5・7・8回を Markdown 化し、図を描いて挿入。validate → unittest → build → check_html をローカルで通す。
3. 第1〜3・6回の原稿を受け取り、同じ手順で追加。部構成と README 目次を確定。
4. 脚注・参考文献の整備。「元資料」表現の確定。
5. ローカル `_site/` をデスクトップ幅・スマートフォン幅で確認。
6. `gh repo create yamaguchiyoshito/multi-scale-time`（公開範囲は要確認）→ push → Pages の Source を GitHub Actions に設定 → 初回ワークフロー成功を確認して公開URLを取得。

## 8. 決めてもらうこと

1. 第1〜3回と第6回の本文の入手方法（ファイルを作業ディレクトリに置く、またはチャットに貼る）。
2. 「元資料では」の扱い。
3. リポジトリの公開範囲（public で Pages 無料／private は契約依存）とライセンス（relevance と同じ CC BY 4.0 を既定とする）。
4. 連載コード（relevance の「RELEVANCE」に相当する英字。案: MULTI-SCALE TIME）と配色。
