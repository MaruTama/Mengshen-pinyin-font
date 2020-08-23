# pinyin font 作り方
## 要件

- 簡体字と繁体字の漢字は拼音が付く
- 簡体字の対象範囲は [通用规范汉字表](https://blogs.adobe.com/CCJKType/2014/03/china-8105.html) に準拠する
- 繁体字の対象範囲は [Big5( 大五碼 )-2003](https://moztw.org/docs/big5/) に準拠する
- 日本の漢字は[当用漢字字体表（新字体）](https://kotobank.jp/word/%E6%96%B0%E5%AD%97%E4%BD%93-537633)に準拠する
- 新字体は[常用漢字](https://kanji.jitenon.jp/cat/joyo.html)が表示できる程度の範囲とする
- 「ひらがな」「カタカナ」を表示できる


拼音を表示する対象は16026個ある。

ベースにしたフォント  
ttfだし容量が削減されている。ピンインを表示する漢字に関しては削減されてない。
- [Source-Han-TrueType](https://github.com/Pal3love/Source-Han-TrueType)

Source-Han-TrueType の基のフォント
- [source-han-serif(源ノ明朝) otf](https://github.com/adobe-fonts/source-han-serif/tree/release/OTF)
- [source-han-sans(源ノ角ゴシック) otf](https://github.com/adobe-fonts/source-han-sans/tree/release/OTF)


<!-- # 変換方法

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
#fontforgeコマンドが動かないとき
$ brew link fontforge
#GUI 版のインストール
$ brew cask install fontforge
```

## 設定ファイルの生成
```
# 中国語の漢字の一覧を作る
$ python createHanziUnicodeJson.py
# CMAP テーブルからunicodeとcidのマッピングテーブルを作る.
$ python createUnicode2cidJson.py fonts/SourceHanSerifCN-Regular.ttf
```

## 拼音表示のための文字を抽出する
固定幅の英字フォントのみ対応  
fonts/pinyin_alphbets に保存する
```
$ python getPinyinAlphbets.py fonts/mplus-1m-medium.ttf
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
|ḿ| uni1E3F.svg | ḿ.svg |
|n| N.svg | n.svg |
|ń| Nacute.svg  | ń.svg |
|o| O.svg | o.svg |
|ō| Omacron.svg | ō.svg |
|ó| Oacute.svg  | ó.svg |
|ǒ| uni01D2.svg | ǒ.svg |
|ò| Ograve.svg  | ò.svg |
|ở| uni1EDF.svg | ở.svg |
|p| P.svg | p.svg |
|q| Q.svg | q.svg |
|r| R.svg | r.svg |
|s| S.svg | s.svg |
|t| T.svg | t.svg |
|u| U.svg | u.svg |
|ū| Umacron.svg   | ū.svg |
|ú| Uacute.svg    | ú.svg |
|ǔ| uni01D4.svg   | ǔ.svg |
|ù| Ugrave.svg    | ù.svg |
|ü| Udieresis.svg | ü.svg |
|ǖ| uni01D6.svg   | ǖ.svg |
|ǘ| uni01D8.svg   | ǘ.svg |
|ǚ| uni01DA.svg   | ǚ.svg |
|ǜ| uni01DC.svg   | ǜ.svg |
|v| V.svg | v.svg |
|w| W.svg | w.svg |
|x| X.svg | x.svg |
|y| Y.svg | y.svg |
|z| Z.svg | z.svg |


metadata-for-pinyin.json を制作する。  
![outline](./imgs/outline.png)  

```
{
  "AI":{
    "Canvas":{
      <!-- Canvasの横幅 -->
      "Width": 722.489,
      "Pinyin":{
        <!-- 拼音表示部分のcanvasの横・縦幅 -->
        "Width":614.4,
        "Height":204.8,
        <!-- Canvas下部から拼音表示部分までの高さ -->
        "BaseLine":675.84,
        <!-- 拼音表示のアルファベットの字間 -->
        "DefaultTracking":16
      }
    },
    "Alphbet":{
      <!-- 拼音表示に使うアルファベットのcanvasの横幅 -->
      "Width":176.389,
      <!-- 拼音表示に使うアルファベットで最も高いの(多分 ǘ ǚ ǜ)の高さ -->
      "MaxHeight":319.264
    }
  },
  "SVG":{
    <!-- viewBoxの横幅 -->
    "Width":2048,
    <!-- 漢字の伸縮率 -->
    "Hanzi":{
      "Scale":{
        "X":1,
        "Y":1
      },
      <!-- 漢字の移動量 -->
      "Translate":{
        "X":0,
        "Y":0
      }
    }
  }
}
```
## 拼音を書き込む漢字のSVGを抽出する
漢字のSVGを取り出す
```
$ python font2svgs.py fonts/SourceHanSerifCN-Regular.ttf
```

## 漢字に拼音を書き込む
```
$ python pinyinFont.py fonts/SVGs fonts/pinyin_alphbets jsons/unicode-cid-mapping.json jsons/hanzi-and-pinyin-mapping.json jsons/metadata-for-pinyin.json
```

## 中国語の(拼音を書き込んだ)漢字以外のsvgを消す
```
$ python removeWithoutHanziSVG.py fonts/SVGs jsons/unicode-cid-mapping.json jsons/hanzi-and-pinyin-mapping.json
```

## SVGの最適化する
transformが多重に掛かっているので、一つにまとめる.  
簡単なので[SVGCleaner.app](https://github.com/RazrFalcon/svgcleaner-gui/releases)を使う。

## SVG -> glif に置き換える
ufoの中の各文字のアウトラインを持つのがglif  
Ref.[extract rotation, scale values from 2d transformation matrix](https://stackoverflow.com/questions/4361242/extract-rotation-scale-values-from-2d-transformation-matrix)  
Matrix can calculate the scale, rotation, and shift at one time by raising the dimension.  
<!--
\begin{align*}
  \begin{pmatrix}
    x' \\
    y' \\
  \end{pmatrix}
    =
  \begin{pmatrix}
    a & c & e \\
    b & d & f \\
  \end{pmatrix}
  \begin{pmatrix}
    x \\
    y \\
    1 \\
  \end{pmatrix}
\end{align*}
 -->
![matrix](./imgs/texclip20190728183918.png)  
Transformation matrix as a list of six. float values (e.g. -t "0.1 0 0 -0.1 -50 200", -t "a b c d e f")   
```
$ python svgs2glifs.py fonts/SVGs jsons/unicode-cid-mapping.json -w 2048 -H 2048 -t "1 0 0
1 0 0"
```
<!-- ```
$ python svg2glif.py fonts/SVGs/cid09502.svg out.glif -w 2048 -H 2048 -t "2 0 0 -2 0 0"
``` -->
<!-- ## otf -> ttf
```
$ python otf2ttf.py fonts/SourceHanSerifSC-Regular.otf
``` -->

## ttf -> UFO
fontforge を用いて変換.
<!-- ```
$ fontforge -script ttf2ufo.pe fonts/SourceHanSerifCN-Regular.ttf
``` -->
![ttf-to-ufo-img0.png](./imgs/ttf-to-ufo-img0.png)
![ttf-to-ufo-img1.png](./imgs/ttf-to-ufo-img1.png)
![ttf-to-ufo-img2.png](./imgs/ttf-to-ufo-img2.png)
![ttf-to-ufo-img3.png](./imgs/ttf-to-ufo-img3.png)
![ttf-to-ufo-img4.png](./imgs/ttf-to-ufo-img4.png)
![ttf-to-ufo-img5.png](./imgs/ttf-to-ufo-img5.png)

## 各glifをufoに移動する
先程、出力した glyphs/\*.glif を fonts/ufo/glyphs\*.glif の下に上書きする。  
glyphs ごと上書きするとうまく行かない。なぜ？Finderのせい？なので、ファイル単位で移動またはコピーする。  
16026個ある。

## ufo -> ttf
<!-- ```
$ fontforge -script ufo2ttf.pe fonts/SourceHanSerifCN-Regular.ufo
``` -->
![ufo-to-ttf-img0.png](./imgs/ufo-to-ttf-img0.png)
![ufo-to-ttf-img1.png](./imgs/ufo-to-ttf-img1.png)
![ufo-to-ttf-img2.png](./imgs/ufo-to-ttf-img2.png)
![ufo-to-ttf-img3.png](./imgs/ufo-to-ttf-img3.png)
![ufo-to-ttf-img4.png](./imgs/ufo-to-ttf-img4.png)
![ufo-to-ttf-img5.png](./imgs/ufo-to-ttf-img5.png)
![ufo-to-ttf-img6.png](./imgs/ufo-to-ttf-img6.png)
![ufo-to-ttf-img7.png](./imgs/ufo-to-ttf-img7.png)

# pypinyinで拼音が見つからない漢字まとめ
[FIX_PINYIN.md](FIX_PINYIN.md)


# ligatures
- [OpenType Cookbook](http://opentypecookbook.com/)
- [glyphs Ligatures](https://glyphsapp.com/tutorials/ligatures)
- [github ligatures](https://github.com/topics/ligatures)
- [kiliman/operator-mono-lig](https://github.com/kiliman/operator-mono-lig)
- [【完全版】Ligature Symbols フォントセットの自作方法](https://kudakurage.hatenadiary.com/entry/20120720/1342749116)

<!-- fontforge
ctrl + Shift + F -> Lookups
cid59875 -->

## 多音字
- [中国語の多音字辞典（Chinese Duoyinzi Dictionary）](https://dokochina.com/duoyinzi.htm)
- [常用多音字表](http://xh.5156edu.com/page/18317.html)
- [104个汉字多音字一句话总结](http://news.sina.com.cn/c/2017-03-19/doc-ifycnikk1155875.shtml)
