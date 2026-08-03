<p align="right"><strong>日本語</strong> | <a href="./README.en.md">English</a></p>

# Comprehensible Documents

人間とAIが、同じ一つのHTMLを正本として直接読める技術文書を作成、改訂、監査するCodex Skillです。

![Comprehensible Documentsで作成したADRのデスクトップ表示](./assets/readme/example-desktop.png)

## このSkillが解決する問題

技術文書は、情報が不足しているときだけ読みにくくなるわけではありません。
同じ決定が概要、本文、図、AI向け要約へ複製されると、読者はどれが正しいかを推論し、作成者はすべての写しを更新する必要があります。

Comprehensible Documentsは、この負担を**理解負債**として扱います。
情報を削って短く見せるのではなく、正本、状態、理由、例外、次の行動へ迷わず到達できる一つの自己完結HTMLへ整理します。

| 起きている問題 | このSkillの扱い |
|---|---|
| 要求や決定が複数箇所で言い換えられている | 正本本文を一か所に置き、他の箇所は安定IDで参照します。 |
| 人間用文書とAI用要約が分かれている | 人間とAIが同じ可視本文を読みます。 |
| 色、図、配置だけが意味を持っている | 重要な意味を見出し、本文、表、代替テキストにも記録します。 |
| 確定事項と未確定事項が混在している | 種別、状態、規範強度、適用範囲を可視化します。 |
| 文書を読むたびに作成時の会話やSkillが必要になる | 完成HTMLだけを渡したコールドリード監査を行います。 |

## 三つの単一性

このSkillの設計は、三つの単一性を中心にしています。

1. **正本は一つ**：同じ要求、決定、制約を別の文章として複製しません。
2. **成果物は一つ**：一つの目的に対し、原則として一つの自己完結HTMLを生成します。
3. **読者は一つ**：人間用とAI用の派生文書を作らず、同じ可視情報を判断根拠にします。

文書が長い場合も、長さだけを理由に分割しません。
文書契約、見出し、索引、安定ID、段階的開示によって、必要な情報への到達経路を設計します。

設計規則と研究上の根拠、その適用限界は[研究根拠マップ](./references/evidence-map.html)で対応付けています。
認知研究から固定の項目数や万能な配色を導くのではなく、観測された効果と文書設計上の判断を分けて扱います。

## 実際の出力例

[単一HTMLを正本にする設計判断のADR](./examples/ADR-0001-SINGLE-HTML-SOURCE-OF-TRUTH.html)は、このSkillの手順と文書体系を使って作成した完成例です。
CSS、図、正本レコードを一つのHTMLへ内包しており、JavaScript、外部フォント、外部画像を必要としません。

| デスクトップ | モバイル | モバイル索引 |
|---|---|---|
| ![固定サイドレールを表示したデスクトップ画面](./assets/readme/example-desktop.png) | ![通常フローの索引を表示したモバイル画面](./assets/readme/example-mobile.png) | ![索引を展開したモバイル画面](./assets/readme/example-mobile-index.png) |

HTMLをダウンロードしてブラウザで開くと、ネットワーク接続なしで内容とレイアウトを確認できます。

## 対応する文書

文書名ではなく、読者が完了すべき判断または作業から構成を選びます。

| 文書種別 | 読者が行うこと | 主な正本単位 |
|---|---|---|
| 要求仕様 | 何を満たせば承認できるか判断する | 要求、制約、受入条件 |
| 概要設計 | 境界と主要構造を理解する | 設計決定、境界、主要フロー |
| 詳細設計 | 実装可能な契約と例外を確認する | インターフェース、データ、状態 |
| ADR | 採用した決定と理由を追跡する | 一つの意思決定 |
| ランブック | 同じ操作結果へ安全に到達する | 開始条件、操作、期待結果、停止条件 |
| 運用・セキュリティ | 責任、権限、監視、復旧を判断する | 統制、責任境界、検知、対応 |
| API・参照 | 値や契約を素早く検索する | 定義、署名、フィールド、制約 |
| 調査・分析 | 証拠から結論の妥当性を評価する | 問い、観測、推論、結論 |
| 教育・解説 | 概念を理解し、別の課題へ適用する | 概念モデル、完成例、練習 |

このSkillは、通常のHTML参照、単純な要約や翻訳、WebアプリのUI設計、固有形式のまま扱うDOCX、PDF、スライド、表計算には使用しません。

## インストール

Codexは、リポジトリ単位の `.agents/skills` と利用者単位の `$HOME/.agents/skills` からSkillを読み込みます。
以下は、利用者単位でインストールする手順です。

### Windows PowerShell

- 作業ディレクトリ：`$HOME\.agents\skills`
- 作成されるSkill：`comprehensible-documents\SKILL.md`
- 前提：GitとPython 3がコマンドとして利用できること

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\.agents\skills" | Out-Null
Set-Location "$HOME\.agents\skills"
git clone <repository-url> comprehensible-documents
python .\comprehensible-documents\scripts\validate_skill_bundle.py .\comprehensible-documents
```

`<repository-url>` には、GitHubの「Code」からコピーしたURLを指定します。
期待される検証結果は、末尾が `ERROR 0` になることです。

```text
BUNDLE ...\comprehensible-documents
ERROR 0
```

### macOS / Linux

- 作業ディレクトリ：`$HOME/.agents/skills`
- 作成されるSkill：`comprehensible-documents/SKILL.md`
- 前提：GitとPython 3がコマンドとして利用できること

```bash
mkdir -p "$HOME/.agents/skills"
cd "$HOME/.agents/skills"
git clone <repository-url> comprehensible-documents
python3 ./comprehensible-documents/scripts/validate_skill_bundle.py ./comprehensible-documents
```

`<repository-url>` には、GitHubの「Code」からコピーしたURLを指定します。
期待される検証結果は、末尾が `ERROR 0` になることです。

```text
BUNDLE .../comprehensible-documents
ERROR 0
```

CodexがSkillを自動検出します。
一覧へ現れない場合はCodexを再起動してください。

公式のSkill配置場所、明示呼び出し、暗黙呼び出しについては、OpenAIの[Build skills](https://learn.chatgpt.com/docs/build-skills)を参照してください。

## 使い方

Codexでは、プロンプト内でSkill名を明示できます。

```text
$comprehensible-documents を使用して、この要件メモを自己完結HTMLの要求仕様へ整理してください。
```

Skillの説明と依頼内容が一致する場合は、Codexが暗黙に選択することもあります。
出力形式と監査範囲を確実に指定したい場合は、明示呼び出しを推奨します。

### 新規文書を作る

```text
$comprehensible-documents を使用して、障害復旧ランブックを新規作成してください。
開始条件、停止条件、各手順の期待結果、失敗時分岐、ロールバックを正本として含めてください。
```

### 既存HTMLを改訂する

```text
$comprehensible-documents を使用して、@HLD.html を改訂してください。
既存の正本IDとファイル名を維持し、変更対象の決定と参照箇所だけを更新してください。
```

### 理解負債を監査する

```text
$comprehensible-documents を使用して、@REQUIREMENTS.html の正本性と理解負債を監査してください。
監査だけを行い、ファイルは変更しないでください。
```

## 作業フロー

1. Skillバンドルの完全性を検証します。
2. 文書の目的、読者、対象範囲、正本、状態、未確定事項を文書契約として確定します。
3. 読者が判断または作業する順序から文書種別と章立てを選びます。
4. 要求、決定、制約、前提、禁止、推奨、未確定事項へ必要な安定IDを付けます。
5. テンプレートと文書トークンを使い、一つの自己完結HTMLへ組み立てます。
6. HTML単体を渡すコールドリード監査と機械監査を行います。
7. レイアウトが作業対象に含まれる場合は、対象画面幅で実際に表示して目視確認します。

機械監査は構文と検査可能な構造を確認します。
人間またはAIが内容を正しく判断できることを点数で保証するものではないため、コールドリード監査を別に行います。

## 作成したHTMLを監査する

- 作業ディレクトリ：監査対象HTMLがあるディレクトリ
- 対象ファイル：`<DOCUMENT-NAME>.html`
- 使用するスクリプト：`<skill-directory>/scripts/audit_document.py`

```text
python <skill-directory>/scripts/audit_document.py <DOCUMENT-NAME>.html
```

期待される結果は `ERROR 0` です。
警告がある場合は無視せず、意図した例外か修正対象かを判断します。

```text
AUDIT <DOCUMENT-NAME>.html
ERROR 0 / WARNING 0
```

## リポジトリ構成

```text
comprehensible-documents/
├── SKILL.md                       # 発火境界と作業フロー
├── agents/openai.yaml             # Codexの表示情報と呼び出し方針
├── assets/document-system/        # HTMLテンプレートとデザイントークン
├── examples/                      # Skillで作成した完成例
├── references/                    # 設計規則、文書種別、根拠、品質ゲート
└── scripts/                       # バンドル検証、HTML監査、回帰テスト
```

主要な設計資料：

- [単一ドキュメントモデル](./references/single-document-model.html)
- [人間・AI共通文書モデル](./references/human-ai-document-model.html)
- [文書種別マトリクス](./references/document-genre-matrix.html)
- [Hallmark文書プロファイル](./references/hallmark-document-profile.html)
- [文書品質ゲート](./references/quality-gates.html)
- [研究根拠マップ](./references/evidence-map.html)
- [文書ファイル命名規則](./references/naming-policy.html)

## 開発時の検証

- 作業ディレクトリ：このリポジトリのルート
- 対象：Skillバンドル全体と `scripts/test_*.py`

```text
python scripts/validate_skill_bundle.py .
python -m unittest discover -s scripts -p "test_*.py" -v
```

期待される結果は、バンドル検証が `ERROR 0`、すべての回帰テストが `OK` になることです。
