# 注意点
- pinyin に使えるフォントは等幅のみ
- ss00 - 20 まで
- glyf table 内の ピンイン は簡易表記
- 呣 m̀, 嘸 m̄　は unicode に含まれていないので除外
- overwrite.txt は色々な目的のために追加している。pypinyin で取得できない漢字、発音の優先度の調整、儿 の r の追加、軽声の追加、重複する漢字は同じ発音にする。呣 m̀, 嘸 m̄　を除外するため（追加してもいいがピンイングリフを作るのが面倒になる）。
- glyf table は 65536 までしか格納できない
- IVS は 
       0xE01E0 => 何もないグリフ
       0xE01E1 => 標準的なピンイン
       0xE01E2 => 以降、異読のピンイン
- GSUB の置換と cmap_uvs の置換はどっちが後？
       　-> cmap_uvs で標準の読みに戻すと、すぐにGSUBが効いて元に戻ってしまう。標準に戻す用のグリフを用意する.
       hanzi_glyf　　　　標準の読みの拼音
       hanzi_glyf.ss00　ピンインの無い漢字グリフ。設定を変更するだけで拼音を変更できる
       hanzi_glyf.ss01　（異読のピンインがあるとき）標準の読みの拼音（uni4E0D と重複しているが GSUB の置換（多音字のパターン）を無効にして強制的に置き換えるため）
       hanzi_glyf.ss02　（異読のピンインがあるとき）以降、異読　

- lookup table の名前は自由
       lookup_pattern_0X <= pattern one
       lookup_pattern_1X <= pattern two
       lookup_pattern_2X <= exception pattern
       にする

- duoyinzi_pattern_one.txt の並びは、marged-mapping-table.txt に従う。1 が標準的な読み. ss01 と合わせる
       ```
       1, 强, qiáng, [~调|~暴|~度|~占|~攻|加~|~奸|~健|~项|~行|~硬|~壮|~盗|~权|~制|~盛|~烈|~化|~大|~劲]
       2, 强, qiǎng, [~求|~人|~迫|~辩|~词夺理|~颜欢笑]
       3, 强, jiàng, [~嘴|倔~]
       ```
- lookup rclt は、読みのパターンごとにまとめる。 rclt0 は pattern one。 rclt1 は pattern two。 rclt2 は exception pattern.
- pattern.json はGraphs like
- 横書きのみ想定

# error:

このエラーがあったが、[de0090a43d8a6a359d85d45e26e7cfa17b4cf5d8] で解消した
```
Exception: otfccbuild : Build : [WARNING] [Stat] Circular glyph reference found in gid 11663 to gid 11664. The reference will be dropped.
       |-Build : [WARNING] [Stat] Circular glyph reference found in gid 11664 to gid 11664. The reference will be dropped.
       |-Build : [WARNING] [Stat] Circular glyph reference found in gid 11665 to gid 11664. The reference will be dropped.
       |-Build : [WARNING] [Stat] Circular glyph reference found in gid 13827 to gid 13828. The reference will be dropped.
       |-Build : [WARNING] [Stat] Circular glyph reference found in gid 13828 to gid 13828. The reference will be dropped.
       |-Build : [WARNING] [Stat] Circular glyph reference found in gid 13829 to gid 13828. The reference will be dropped.
```
gid は glyph_order の添字
解決策としては二回繰り返さないようにする。
前提として、すべての文字に対して同じ発音が登録されていること。overwrite.txt で調整した。
- 11663 => cid10849 ⺎(U+2E8E) 兀(U+5140) 兀(U+FA0C)
- 11664 => cid10849.ss00
- 11665 => cid10849.ss01
- 13827 => cid12670 嗀(U+55C0) 嗀(U+FA0D)
- 13828 => cid12670.ss00
- 13829 => cid12670.ss01





ttx で出力した => ChainContextSubst Format="3" -> overage-based Glyph Contexts　って書いてある。
[6.3 Chaining Context Substitution Format 3](https://docs.microsoft.com/en-us/typography/opentype/spec/gsub#63-chaining-context-substitution-format-3-coverage-based-glyph-contexts)
[5.f. [GSUB LookupType 6] Chaining contextual substitution](http://adobe-type-tools.github.io/afdko/OpenTypeFeatureFileSpecification.html#5f-gsub-lookuptype-6-chaining-contextual-substitution)
[otfcc](https://github.com/caryll/otfcc/blob/master/lib/table/otl/subtables/chaining/read.c#L228)


backtrack, input, and lookahead.
a prefix (also known as backtrack) glyph sequence may be specified, as well as a suffix (also known as lookahead) glyph sequence
接頭辞と、グリフシーケンス、および接尾辞

"inputBegins", "inputEnds" は？

置換で影響する文字列のインデックスかな？
inputBegins はシーケンスが開始される添字、inputEnds はシーケンスが終わる長さ
inputBegins = min(at) 
inputEnds   = max(at) + 1

ignore のときは inputBegins,inputEnds を計算してから at を消す

調査方法
Glyphs で記述して、出力->otfcc で dump して取り出し
```
otfccdump -o Sawarabi.json --pretty SawarabiMincho-Regular.otf
cat Sawarabi.json | jq '.GSUB' > Sawarabi_GSUB.json
```
詳しくは、tmp/json/Sawarabi_GSUB.json を参照

lookup lookup_0 {
	sub uni884C by uni8846;
} lookup_0;
lookup lookup_1 {
	sub A by X;
} lookup_1;
lookup lookup_2 {
	sub A by Y;
} lookup_2;


ttx から rclt は Chaining Context Substitution Format 3
lookup rclt0 {
	sub [uni4E0D uni9280] uni884C' lookup lookup_0 ;
       　-> "at": 1,
       　　　"inputBegins": 1,
       　　　"inputEnds": 2
	sub uni884C' lookup lookup_0 [uni4F1A uni8A71];
       　-> "at": 0,
       　　　"inputBegins": 0,
       　　　"inputEnds": 1

       sub uni4E0D uni884C' lookup lookup_0 uni9280 ;
       　-> "at": 1,
       　　　"inputBegins": 1,
       　　　"inputEnds": 2
        },
} rclt0;
lookup rclt1 {
	sub A' lookup lookup_1 A' lookup lookup_2 F;
       　-> "at": 0,1
       　　　"inputBegins": 0,
       　　　"inputEnds": 2
	sub [A B C] A' lookup lookup_1 A' lookup lookup_2 F;
       　-> "at": 1,2
       　　　"inputBegins": 1,
       　　　"inputEnds": 3
	sub A' lookup lookup_1 A' lookup lookup_2 [F G H];
       　-> "at": 0,1
       　　　"inputBegins": 0,
       　　　"inputEnds": 2
       sub A' lookup lookup_1 A' lookup lookup_2 [F G H] I;
       　-> "at": 0,1
       　　　"inputBegins": 0,
       　　　"inputEnds": 2
       sub [A B C] D A' lookup lookup_1 A' lookup lookup_2;
       　-> "at": 2,3
       　　　"inputBegins": 2,
       　　　"inputEnds": 4
       sub [A B C] A' lookup lookup_1 D' A' lookup lookup_2;
       　-> "at": 1,3
       　　　"inputBegins": 1,
       　　　"inputEnds": 4
} rclt1;
lookup rclt2 {
	ignore sub uni80CC uni7740' uni624B;
       　-> "at": None
       　　　"inputBegins": 1,
       　　　"inputEnds": 2
	sub uni7740' uni624B by d;
       　-> "at": 0,
       　　　"inputBegins": 0,
       　　　"inputEnds": 1
} rclt2;
