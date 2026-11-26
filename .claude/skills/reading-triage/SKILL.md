---
name: reading-triage
description: Mengshen 拼音フォントの漢字の読み（overwrite.txt と pinyin-data の pinyin.txt の差）を監査し、修正先（overwrite.txt に残す / 削除 / フォーク MaruTama/pinyin-data 経由で本家 mozillazg/pinyin-data に PR / 台湾向けリポジトリ）を決めて回帰を検証するスキル。Issue #63–#74（追跡 #75、upstream 候補 #81）のような「この字の読み・既定の読みは正しいか」「間違った拼音を見つけた」「overwrite の行を消してよいか」「読みの順序を変えたら何が壊れるか」「pinyin-data に PR を出したい」を扱うときに使う。$ARGUMENTS に漢字を渡せる。
---

<!-- cspell:words Hanyu Pinlu TGHZ cedict moedict uharfbuzz shèn mozillazg unihan wàng -->

# reading-triage

`res/phonics/unicode_mapping_table/overwrite.txt`（以下 overwrite）と `res/pinyin-data/pinyin.txt`（以下 pinyin-data）の読みの差を 1 字ずつ判定し、直す場所を決めて検証する。読みは NFC 正規化して比較する。

## 目標とする最終形

読みの誤りはすべて pinyin-data 側（本家 mozillazg/pinyin-data）で直し、overwrite には次の 2 種類だけを残す。

| 残す種類 | 例 | 理由を書く場所 |
| --- | --- | --- |
| プロジェクト固有の読み | 诶 U+8BF6（#30）、ê/ḿ/ń 系（PR #54）、地 dì を先頭（#18） | 判定フロー 1 |
| グリフ上限のための読みの絞り込み | #64–#66 の subset 行（pinyin-data にある古い読みを外す） | 判定フロー 2 の subset |

それ以外の行（読みの誤り・既定の読みの誤り）は **本家に採用されるまでの一時的な行**。本家で採用されたら submodule を進めて消す（下の「修正の行き先」5）。フォークだけに入れた修正を submodule に先取りしない（本家採用後に反映する方針）。

## 前提

- 読みの並び: 1 番目 = 既定グリフ（文脈なしで出る読み）、n 番目 = IVS `U+E01E0+n`（`U+E01E0` は拼音なし）。順序を変えると既定の読みと IVS 番号が変わる。
- グリフ数上限 65,535（#38）。残りは Handwritten 約 736、HanSerif 約 2,794。読みの追加・削除はグリフ数を増減させるので、意図しない増減は不可。
- overwrite の大半は PR #17（b07db87）で取り込んだ ToneOZ 表で、台湾 国语 順に寄っていることが多い（括 guā、茄 qié、盛 chéng）。ToneOZ の並びは独立した根拠にならない。
- 判断が割れるもの（根拠が分かれる・必要な読みか）は既定値を選ばず `AskUserQuestion` でユーザーに返す。

## 判定フロー

まず `lookup.py` で材料を揃える（カテゴリと判定ヒントが出る。ヒントは機械判定なので最終判断は下のフローで行う）。

1. **プロジェクト固有の読み** → overwrite に残す。upstream には出さない。
   - 诶 U+8BF6（#30）、PR #54 で戻した ê/ḿ/ń 系（呣 哏 哽 唔 嗯 嘸 欸 誒）、地 dì を先頭（#18）。
2. **読みの集合が違う**（過不足がある）
   - overwrite にしかない読みが他の pinyin-data ファイル（kMandarin, kMandarin_8105, kTGHZ2013, kXHC1983, kHanyuPinyin, kHanyuPinlu, zdic, cc_cedict, kMandarin_overwrite, overwrite …）で裏付けられ、必要な読み → upstream PR 候補（「修正の行き先」へ）。採用されるまで overwrite に残す。
   - どこにも裏付けがない読み → その読みを削除する。
   - overwrite に無い読みが pinyin-data にある（subset）→ 行を消すと読みが増える（グリフ数 +）。要否をユーザーに確認する。
     - 欠けている読みの多くは ToneOZ が外した 漢語大字典（kHanyuPinyin）だけの古い読み（#64 調査）。戻す候補は kTGHZ2013 / kHanyuPinlu / kMandarin で裏付けのある読みに限り、1985 年の审音表 で廃止された読み（往 wàng、啥 shà 等）や別字の異体項目（已 sì＝巳）は戻さない。
     - 戻さない読みは本家に削除提案しない（pinyin-data としては正しいデータ）。overwrite に「グリフ上限のための絞り込み」として残す。
3. **順序だけ違う**（order-only）: 基準は「pinyin-data の先頭が、単独で読むときの普通话の通常の読みか」。
   - 根拠に使う: kMandarin、kHanyuPinlu（頻度順、件数付き）。
   - 根拠に使わない: kXHC1983 / kTGHZ2013 の先頭（ページ順）、ToneOZ の並び、台湾 MOE（国语）の並び（`--moe` は ToneOZ 由来かを見分けるための参考）。
   - Yes → overwrite の行を削除する。
   - No → 集合を pinyin-data と同じにした上で並べ替えて残し、upstream 候補として #81 の表に加える（残した例: 似 sì、茄 qié、伺 sì、尽 jìn、藉 jiè、俟 sì、柞 zuò、葚 shèn、切 qiē）。kMandarin / Pinlu が pinyin-data と同じでも、常用語（无尽・耗尽 等）で普通话の単独読みが別なら No になり得る。
   - 台湾 国语 の読み・並び（教育部 moedict と一致し、普通话とは違う）だと分かったもの → overwrite には入れず、台湾向けリポジトリの候補として記録する（「修正の行き先」4）。
4. **既定の読みを変えたら回帰を潰す**
   - プロジェクトの熟語データに無い常用語も含めて確認する（`sim_regress.py`）。
   - 壊れた語は熟語パターンを足して直す: `res/phonics/duo_yin_zi/phrase_of_pattern_one.txt`（非既定字が 1 つ）/ `phrase_of_pattern_two.txt`（2 つ以上）→ `make_pattern_table.py`。
   - ある字のパターンが 1 つの読みしか持たないと `compress_pattern_one_table()` がその字を畳んで別の字へ移すので、既定の読みの「アンカー」語も足す。アンカーではその字が語中で最初の多音字である必要がある（几乎→几、盛饭→盛）。粮 人 哥 他 米 のように軽声を持つ字は多音字扱いになるので隣接字に注意（俩人は俩のアンカーになる、粮囤は囤のアンカーにならない）。
   - アンカーが作れない語（囤积、树杈 等）は既知の残課題として PR / issue に記録する。
5. **upstream に採用されたら** → 「修正の行き先」5 の手順で submodule を進め、overwrite の該当行を削除する。

## 修正の行き先（間違った拼音を見つけたとき）

1. **Mengshen で一時対応する**: overwrite を直し、「再生成」「検証チェックリスト」を通して PR を出す。PR 本文に「本家採用待ちの一時行」と書く。
2. **候補を記録する**: 普通话の修正は #81 の表に 1 行足す（字 / cp / 提案する読み / pinyin-data の今の読み / 根拠）。
3. **フォーク MaruTama/pinyin-data で本家向けの PR を作る**（submodule `res/pinyin-data` の origin がフォーク）
   - 作業は submodule 内ではなく、フォークの別 clone か worktree で行う（submodule のコミットを動かさない）。始める前に `gh repo sync MaruTama/pinyin-data` でフォークを本家に追従させ、本家 master からブランチを切る。
   - 直すファイル（`merge_unihan.py` の合成規則に基づく。`overwrite.txt` > 先頭調整 > 元データの順で効く）:

     | 直したいこと | ファイル |
     | --- | --- |
     | 通用规范汉字表 8105 字の既定（先頭）の読み | `kMandarin_8105.txt`（その字の先頭に来る読みを 1 つ書く） |
     | 8105 字以外の既定の読み | `kMandarin_overwrite.txt` |
     | 読みの集合（足す・消す・全部置き換える） | `overwrite.txt`（書いた読みでその字の読みが丸ごと置き換わる） |
     | zdic 由来の誤り | `zdic.txt` |

   - `make merge_unihan`（= `python3 merge_unihan.py`）で `pinyin.txt` を作り直し、変更した字の行だけが変わったことを `git diff pinyin.txt` で確認する。
   - PR はフォークのブランチから `mozillazg/pinyin-data` の master へ。本文は中国語で、字ごとに根拠を書く（kMandarin / kHanyuPinlu の件数、通用规范汉字字典・现代汉语词典 の見出し、常用語の例）。本家の最近の例: mozillazg/pinyin-data#63「修正若干汉字拼音」。
   - 出した PR の URL を #81 の該当行に書く。
4. **台湾 国语 向けの読み**: 本家にも overwrite にも入れず、フォークの issue MaruTama/pinyin-data#1（台湾向けリポジトリの切り出し）の候補表に足す。台湾向けリポジトリができたらそちらに反映する。
5. **本家に採用されたら**
   - `gh repo sync MaruTama/pinyin-data` でフォークを本家に追従させる。
   - `cd res/pinyin-data && git fetch origin && git checkout <採用後のフォーク master のコミット> && cd -`、その後 `git submodule update --recursive`（`--init` は付けない。pinyin-data と phrase-pinyin-data が互いを submodule に持つので深い循環 clone になる）。
   - overwrite の該当行を消し、`lookup.py` で `no-overwrite`（pinyin.txt と一致）になることを確認してから「再生成」「検証チェックリスト」を通す。submodule の更新と行の削除は同じ PR にする。
   - #81 の該当行を完了にする。

## 再生成

overwrite を変えたら、この順で再生成する（mapping が先。pattern は `outputs/merged-mapping-table.txt` を読む）。

```bash
cd res/phonics/unicode_mapping_table && python make_unicode_pinyin_map_table.py && cd -
cd res/phonics/duo_yin_zi/scripts && python make_pattern_table.py && cd -
```

既定の読みが変わると熟語の振り分けも変わる: 非既定字の数が 2 以上 → `phrase_of_pattern_two.txt`、1 → pattern_one。`make_pattern_table.py` が「2文字以上 多音字を含んでいます」で止まったら移す。

## スクリプト

すべてリポジトリのルートから実行する。出力はスクラッチパッドに置く。

### lookup.py — 1 字ずつの材料（stdlib のみ）

```bash
python .claude/skills/reading-triage/scripts/lookup.py 似 尽 冠 --unihan <Unihan.zip|展開dir> [--moe]
python .claude/skills/reading-triage/scripts/lookup.py --all-overwrite --tsv --category order-only
```

- 出力: pinyin.txt / overwrite / merged の行、各読みを裏付ける pinyin-data ファイル、Unihan kMandarin・kHanyuPinlu（件数）、`--moe` で moedict.tw `/a/<字>.json` の `h[].p`（繁体字は kTraditionalVariant で引く）、カテゴリ、通用规范汉字表の級（1–3500 一级 / 3501–6500 二级 / 6501–8105 三级、`res/pinyin-data/tools/china-8105-06062014.txt`）、判定ヒント。
- カテゴリ: `identical` / `order-only` / `subset` / `attested-addition` / `unattested` / `missing`（pinyin.txt に無い）/ `no-overwrite`。
- Unihan は `--unihan`、環境変数 `UNIHAN_PATH`、`~/.cache/mengshen-reading-triage/Unihan.zip` の順に探す。無ければ `--download-unihan` で <https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip> を取得（無くても pinyin-data の kMandarin.txt / kHanyuPinlu.txt で動く。件数は出ない）。`--json` / `--tsv` あり。

### sim_regress.py — 常用語の回帰見積り（stdlib + pypinyin の phrases_dict.json）

```bash
python .claude/skills/reading-triage/scripts/sim_regress.py --base origin/master [--head .] [--chars 似尽] [--json out.json]
```

- `--base` / `--head` は git ref（`git show` で読む）か checkout ディレクトリ。`--head` の既定は作業ツリー。
- pattern_two → pattern_one → 既定の順でフォントの置換を近似し、pypinyin の熟語（4 字以下）の読みと比較。base で正しく head で誤る語 = REGRESSED、逆 = IMPROVED を字ごと・級ごとに出す（一级・二级を列挙、`--levels 1,2,3,0`）。
- overwrite と merged が食い違うと WARNING（再生成忘れ）。近似なので文脈連鎖の相互作用は見ない。最終確認は phrase_check.py。

### phrase_check.py — フォントを作って HarfBuzz で比較（venv: fontTools, uharfbuzz）

```bash
.venv/bin/python .claude/skills/reading-triage/scripts/phrase_check.py all \
  --base origin/master --head . --work <scratchpad>/pc --otfcc-bin <otfcc-rs の target/release> --chars 似尽
```

- `build <ref|dir> --out DIR`（ref なら一時 worktree を作って消す。`template_glyf_*.json` はメインの checkout からリンク）、`compare --base DIR --head DIR`、`all`（両方 build して compare）。
- otfcc-rs が必須（caryll otfcc 0.10.4 は aalt を壊す）。`--otfcc-bin` か `OTFCC_BIN`。
- 比較内容: numGlyphs と残り、银行サニティ（银行 → 行 háng）、既定/集合が変わった字と `--chars` の単独表示、base+head の pattern_one/two・testcase（+ `--extra`）全語。newly broken（base OK・head NG）があるか numGlyphs が変わると exit 1（意図した増減は `--allow-glyph-change`）。
- 1 スタイルの build は otfcc-rs で約 10 秒（初回は handwritten の template 生成が加わる）。スタイルは順番に作る（同時に作ると中間ファイルが混ざる）。

## 検証チェックリスト（PR 前に全部）

- [ ] グリフ数が base と同じ（読みの追加・削除を意図したときは差分が期待どおり）
- [ ] `phrase_check.py` で newly broken 0（base 比）、银行サニティ OK
- [ ] `sim_regress.py` の REGRESSED を確認し、一级・二级の語はパターン追加で直すか残課題として記録
- [ ] `python -m pytest tests/unit/data -q` と `python -m pytest tests/ -q`
- [ ] integration テスト後に `git status` を見て、書き換わった `tmp/json/alphabet_for_pinyin_han_serif.json` / `tmp/json/template_main_handwritten.json` を `git checkout --` で戻す
- [ ] 本家採用待ちの一時行（順序・集合の修正）は #81 の upstream 候補表に追記し、PR 本文にも書く
- [ ] 台湾 国语 の読みは overwrite に入れず MaruTama/pinyin-data#1 に記録
