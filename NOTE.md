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
lookup_0X => pattern one
lookup_1X => pattern two
lookup_2X => exception pattern
にする

- duoyinzi_pattern_one.txt の並びは、marged-mapping-table.txt に従う。1 が標準的な読み. ss01 と合わせる
```
1, 强, qiáng, [~调|~暴|~度|~占|~攻|加~|~奸|~健|~项|~行|~硬|~壮|~盗|~权|~制|~盛|~烈|~化|~大|~劲]
2, 强, qiǎng, [~求|~人|~迫|~辩|~词夺理|~颜欢笑]
3, 强, jiàng, [~嘴|倔~]
```
- lookup_calt は、読みのパターンごとにまとめる。强, qiǎng は異読の最初のパターンなので lookup_calt_0 に入る。 强, jiàng は lookup_calt_1 

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