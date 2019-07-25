# oss-pinyin-font-tools
Tools for to create OpenSource Pinyin Font

元のフォント
- [source-han-serif(源ノ明朝) otf](https://github.com/adobe-fonts/source-han-serif/tree/release/OTF)
- [source-han-sans(源ノ角ゴシック) otf](https://github.com/adobe-fonts/source-han-sans/tree/release/OTF)
<!-- otf->ttf にしてあるフォント
- [Source-Han-TrueType](https://github.com/Pal3love/Source-Han-TrueType) -->

<!-- # 変換方法
```
#otf -> ttf
$ python otf2ttf.py SourceHanSerif-Regular.otf
```

```
#ttf -> ttx
$ ttx SourceHanSerif-Regular.ttf
#ttx -> ttf #n の名前をつけてくれるので、上書きされない
$ ttx SourceHanSerif-Regular.ttx
#テーブルを指定して変換
ttx -t GSUB SourceHanSerif-Regular.otf
```

```
#ttc -> ttx の場合 n はttxにしたい番号
ttx -y n ./NotoSansCJK-Regular.ttc
``` -->


# pinyin font 作り方
## 依存関係
```
$ pyenv global 3.7.2
$ pip install -r requirements.txt
```
```
#GUI で使う
$ brew cask install xquartz
#fontforgeのインストール
$ brew install fontforge
#GUI 版のインストール
$ brew cask install fontforge
```

## 設定ファイルの生成
```
# 中国語の漢字の一覧を作る
$ python createHanziUnicodeJson.py
# CMAP テーブルからunicodeとcidのマッピングテーブルを作る.
$ python createUnicode2cidJson.py fonts/SourceHanSerifSC-Regular.otf
```

## 拼音表示のための文字を抽出する
固定幅の英字フォントのみ対応
```
$ python font2svgs.py fonts/mplus-1m-medium.ttf
```
以下のsvgを取り出して、リネームする。その後、pinyinディレクトリ配下に置く。  
そして、SVGsを削除する  

```
$ python getPinyinAlphbets.py
```

|文字|ファイル名|変更名|
|:--:|:-----:|:-----:|
|a| A.svg | a.svg |
|ā| Amacron.svg | ā.svg |
|á| Aacute.svg  | á.svg |
|ǎ| uni01CE.svg | ǎ.svg |
|à| Agrave.svg  | à.svg |
|b| B.svg | b.svg |
|c| C.svg | c.svg |
|d| D.svg | d.svg |
|e| E.svg | e.svg |
|ē| Emacron.svg | ē.svg |
|é| Eacute.svg  | é.svg |
|ě| Ecaron.svg  | ě.svg |
|è| Egrave.svg  | è.svg |
|f| F.svg | f.svg |
|g| G.svg | g.svg |
|h| H.svg | h.svg |
|i| I.svg | i.svg |
|ī| Imacron.svg | ī.svg |
|í| Iacute.svg  | í.svg |
|ǐ| uni01D0.svg | ǐ.svg |
|ì| Igrave.svg  | ì.svg |
|j| J.svg | j.svg |
|k| K.svg | k.svg |
|l| L.svg | l.svg |
|m| M.svg | m.svg |
|n| N.svg | n.svg |
|o| O.svg | o.svg |
|ō| Omacron.svg | ō.svg |
|ó| Oacute.svg  | ó.svg |
|ǒ| uni01D2.svg | ǒ.svg |
|ò| Ograve.svg  | ò.svg |
|p| P.svg | p.svg |
|q| Q.svg | q.svg |
|r| R.svg | r.svg |
|s| S.svg | s.svg |
|t| T.svg | t.svg |
|u| U.svg | u.svg |
|ū| Umacron.svg | ū.svg |
|ú| Uacute.svg  | ú.svg |
|ǔ| uni01D4.svg | ǔ.svg |
|ù| Ugrave.svg  | ù.svg |
|ü| Udieresis.svg | ü.svg |
|v| V.svg | v.svg |
|w| W.svg | w.svg |
|x| X.svg | x.svg |
|y| Y.svg | y.svg |
|z| Z.svg | z.svg |
|ǖ| uni01D6.svg | ǖ.svg |
|ǘ| uni01D8.svg | ǘ.svg |
|ǚ| uni01DA.svg | ǚ.svg |
|ǜ| uni01DC.svg | ǜ.svg |
|ḿ| uni1E3F.svg | ḿ.svg |
|ń| Nacute.svg  | ń.svg |
|ở| uni1EDF.svg | ở.svg |


ピンインの配置をするために、文字に関する位置情報をまとめる。AI上の情報をまとめてる。  
jsons/pinyin-alphabet-size.json を編集する  

## 拼音を書き込む漢字のSVGを抽出する
漢字のSVGを取り出す
```
$ python font2svgs.py fonts/SourceHanSerifSC-Regular.otf
```

## 拼音を書き込む
```
$ python pinyinFont.py
```

## 中国語の(拼音を書き込んだ)漢字以外のsvgを消す
```
$ python removeWithoutHanziSVG.py
```

## SVG -> glif に置き換える
ufoの中の各文字のアウトラインを持つのがglif
Ref.[extract rotation, scale values from 2d transformation matrix](https://stackoverflow.com/questions/4361242/extract-rotation-scale-values-from-2d-transformation-matrix)  
Matrix can calculate the scale, rotation, and shift at one time by raising the dimension.  
-t "a b c d e f"  
/x'\   /a c e\   /x\  
\y'/ = \b b f/ × |y|  
                 \1/  

## SVG の容量を削除する
transformが多重に掛かっているので、一つにまとめる
SVGCleaner.appを使う

```
$ python svgs2glifs.py fonts/SVGs jsons/unicode-cid-mapping.json -w 2048 -H 2048 -t "2 0 0
-2 0 0"
```
<!-- ```
$ python svg2glif.py fonts/SVGs/cid09502.svg out.glif -w 2048 -H 2048 -t "2 0 0 -2 0 0"
``` -->
## otf -> UFO
fontforge を用いて変換

## 各glifをufoに移動する

## ufo -> otf

# pypinyinで拼音が見つからない漢字まとめ
[FIX_PINYIN.md](FIX_PINYIN.md)

# やること
[] 文字のサイズの設定を外部におく
