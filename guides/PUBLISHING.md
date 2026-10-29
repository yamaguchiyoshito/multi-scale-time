# GitHub登録とPages公開

[連載目次へ](../README.md)

## 方式

公開方式は連載「意味の関連性 ── RELEVANCE」（yamaguchiyoshito/relevance）と同じである。`main` ブランチへのpushで `.github/workflows/pages.yml` が検査・ビルド・配置を行い、GitHub Pagesの Source は **GitHub Actions** にする。配置されるのは `_site/` の読者用出力であり、Markdown原本、スクリプト、テストはサイトへ配置しない。

Git、GitHub CLI、Python 3.11以降、Pandoc 3.xを準備する。GitHub CLIは[公式マニュアル](https://cli.github.com/manual/gh_repo_create)に従って導入・認証する。トークンを原稿・設定・コマンド引数へ貼り付けない。

```sh
gh auth status
git config --get user.name
git config --get user.email
```

## 新規リポジトリを作成する

ローカルで検査とビルドが通ることを確認してから登録する。

```sh
python scripts/validate.py
python -m unittest discover -s tests
python scripts/build.py
python scripts/check_html.py
```

リポジトリを作って現在のブランチをpushする。公開範囲は作成時に決める。GitHub Pagesは公開リポジトリでは無料で使える。非公開リポジトリでのPages利用は契約に依存する。

```sh
gh repo create yamaguchiyoshito/multi-scale-time --public --source=. --remote=origin --push
```

既存コンテンツのあるリポジトリへ強制pushしない。force push、既存ファイルの上書き、公開範囲の変更は手作業で判断する。生成物 `_site/` とPythonキャッシュは `.gitignore` により登録されない。

## GitHub Pagesを有効にする

リポジトリの Settings → Pages → Build and deployment で Source を **GitHub Actions** にする。GitHub CLIからは次のように設定できる。

```sh
gh api -X POST repos/yamaguchiyoshito/multi-scale-time/pages -f build_type=workflow
```

以後、`main` へのpushごとに `.github/workflows/pages.yml` が検査・ビルド・配置を行う。初回は Actions タブから `Publish to GitHub Pages` を手動実行してもよい。公開URLは実際に成功したPagesジョブの `github-pages` 環境から取得する。推測した公開URLを案内しない。

## 公開前に決めること

- **ライセンス。** 本文・図・スクリプトはCC BY 4.0（`LICENSE`）。ライセンスを変える場合はREADMEの記述も同時に更新する。
- **「元資料」の表記。** 本文中で連載の土台となった覚え書きを「元資料」と呼んでいる。公開時にこのままにするか、表現を改めるかを決める（[編集ガイド](EDITING.md)）。
- **参考文献の確認範囲。** `references/sources.json` の `checked` は、リンク先への到達と書誌の一致を確認した範囲を記す。原文で主張を照合した資料はない。公開前に主要な出典を原文で照合する。

## CI設定の保守

検証ワークフロー（`validate.yml`）は `contents: read` のみとし、公開ジョブ（`pages.yml`）にのみ `pages: write` と `id-token: write` を与える。Pandocはローカル検証に使った3.7.0.2へ固定した。GitHub Actionsの主要バージョンは作成時点の公開情報に基づく。

## 途中で失敗した場合

認証・ネットワーク・権限により、リポジトリ作成またはpushが失敗することがある。`gh repo create --source --push` はリモートを自動削除して取り消さない。GitHub上に空のリポジトリができているかを確認し、対象が空であると確認した場合に限り、通常の `git push -u origin main` で再開する。
