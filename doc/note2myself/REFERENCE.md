# Reference of to make font

UFO関係
UFO -> OpenType, TrueType

- [googlefonts/ufo2ft](https://github.com/googlefonts/ufo2ft)
- [googlefonts/fontmake](https://github.com/googlefonts/fontmake)
.glyphs -> UFOs
A bridge from Glyphs source files (.glyphs) to UFOs
- [googlefonts/glyphsLib](https://github.com/googlefonts/glyphsLib)

RoboFont(5万) otf -> ufo
TruFont で ufo を読み込める。RoboFont以外のツール(FontForge, Glyphs)で吐き出した ufo は読み込めない.
FontForge で吐き出した ufo は Glyphs で読み込める。

python でufoからotfを作っている

- [Pythonでフォントを作る](https://qiita.com/irori/items/5518c242e0244838783b)
- [googlefonts/glyphsLib](https://github.com/googlefonts/glyphsLib)

otf -> svg
[fontTools のペンを使ってグリフのアウトラインを取得する](https://shiromoji.hatenablog.jp/entry/2017/11/26/221902)

これに従って作るのが一番いいかも
SVG -> otf
これはsvgの領域に書き込むものだった。なぜか2000個までしか追加できない。[OpenType-SVG カラーフォント](https://helpx.adobe.com/jp/fonts/using/ot-svg-color-fonts.html)

- [SVGフォントを作ってみよう。](https://ten5963.wordpress.com/2017/07/25/svg%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88%E3%82%92%E4%BD%9C%E3%81%A3%E3%81%A6%E3%81%BF%E3%82%88%E3%81%86%E3%80%82/)

SVG -> ttf

- [pteromys/svgs2ttf](https://github.com/pteromys/svgs2ttf)
これはfontforgeを使ってsvg->ttfとしている。しかし中国語がない
- [M+ TESTFLIGHT](http://mplus-fonts.osdn.jp/cgi-bin/blosxom.cgi)
- [アウトラインのSVGからフォントを生成 #かな書いてみる](https://shiromoji.hatenablog.jp/entry/20120314/1331744357)
- [Inkscape+FontForgeでフォントを作成してみたときの手順メモ](https://sites.google.com/site/mieki256wiki/home/inkscape-fontforgedefontowo-zuo-chengshitemitatokino-shou-shunmemo)
- [適当に書いてフォントを作る](https://nixeneko.hatenablog.com/entry/2016/02/06/114348)

ttf　glyfテーブル -> SVGPath

- [TrueTypeフォントのフォーマットを調べる その20](https://project-the-tower2.hatenadiary.org/entry/20100630/1277838854)

ttf　glyfテーブル -> WKT(Polygon)

- [How to generate WKT geometries from true type font glyphs (python)](https://gis.stackexchange.com/questions/258076/how-to-generate-wkt-geometries-from-true-type-font-glyphs-python)

作り方ノウハウ

- [御琥祢屋で公開している源暎フォントを製作したノウハウまとめ](https://okoneya.jp/font/knowhow.html)

otfのttx

- [OpenType/CFFのフォントを読んでみる](https://nixeneko.hatenablog.com/entry/2018/06/20/000000)
- [The CFF2 CharString Format](https://docs.microsoft.com/en-us/typography/opentype/spec/cff2charstr)
- [OpenType/CFFの仕様の解説](https://project-the-tower2.hatenadiary.org/entry/20101204/1291482945)

源ノ角ゴシックについて
CIDフォントをOTFにビルドする。

- [源ノ角ゴシック Source Han Sansをビルド、サブセット化してからのWebフォント化](https://birdwing3.com/201506171/)
- [source-han-sans/COMMANDS.txt](https://github.com/adobe-fonts/source-han-sans/blob/master/COMMANDS.txt)
- [AFDKO入門《CIDキー方式のOpenTypeフォントの作り方》 後篇：makeotf](https://shiromoji.hatenablog.jp/entry/20111210/1323520587)
- [OpenTypeフォント作成のすべて](http://blogs.adobe.com/CCJKType/files/2012/06/afdko-mhattori-20120625.pdf)

## ttf/otfどっちで記述する？

TrueType Format の方が簡単そう.
しかし、OpenType は サブルーチン呼び出しできるので、共通のパスを使える。かなり圧縮できるはず。

OTF/CFFのフォントサイズは平均してTrueTypeより20～50%小さいという
[OpenType/CFFとTrueType](https://blogs.yahoo.co.jp/lcskawamura/15689271.html)
合字の話. 内部にある発音記号を組み合わせるだけでうまく動きそう
GSUBテーブルとGPOSテーブル Script／Feature／Lookup
別のグリフに差し替える GSUB
位置を移動する GPOS
サイズを変更する BASE(上付き、下付き、混植)

TTF のアウトラインは Quadratic Bézier Curve(2次ベジエ曲線)  on_curve is "whether this point lies on the curve or is a control point"
OTF/CFF のアウトラインのデータフォーマットは Type2CharString という。中身はThe Cubic Bézier Curve(3次ベジエ曲線)

- [Curve Types](https://help.fontlab.com/fontlab-vi/Curve-Types/)

### OpenType

テーブルや合字について、わかりやすいドキュメント

- [フォントのしくみ　第３回 DTPの勉強会　狩野宏樹（株式会社イワタ）](https://www.iwatafont.co.jp/news/img/about_font.pdf)
- [KMC Font Project 3 - FontForgeで欧文書体製作](https://www.slideshare.net/kmaztani/kmc-font-project-3-fontforge)
- [OpenTypeの仕様入門 (後編)](https://qiita.com/496_/items/02f2d63fe4bd5603e4dc)
- [D言語的なフォントを作ってみた](https://qiita.com/zr_tex8r/items/ace02d114ea25a3ae4ac)
- [About Apple Advanced Typography FontsIntroduction](https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6AATIntro.html)
規格の書き方がわかりやすい
![How to caculate vertical middle of em square relative to baseline](https://html.spec.whatwg.org/images/baselines.png)
- [OpenTypeフォント](https://www.morisawa.co.jp/culture/dictionary/1904)
- [How OpenType Works](https://simoncozens.github.io/fonts-and-layout/opentype.html)
- [OpenTypeフォントの続き(2)・・・OpenTypeテーブル](http://vanillasky-room.cocolog-nifty.com/blog/2008/02/opentype2openty.html)
- [OpenTypeのテーブル](http://kanji-database.sourceforge.net/fonts/opentype.html)
- [OpenType/CFFの仕様の解説](https://project-the-tower2.hatenadiary.org/entry/20101204/1291482945)
- [OpenType/CFFのフォントを読んでみる](https://nixeneko.hatenablog.com/category/%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88)
- [The CFF2 CharString Format](https://docs.microsoft.com/en-us/typography/opentype/spec/cff2charstr)
役に立ちそうなツールとドキュメント
OpenType なら AFDKO ツールは使えそう。ドキュメントもしっかりしてる
- [OpenType™ Feature File Specification](http://adobe-type-tools.github.io/afdko/OpenTypeFeatureFileSpecification.html#5.d)
- [Adobe Font Development Kit for OpenType (AFDKO) Overview](http://adobe-type-tools.github.io/afdko/AFDKO-Overview.html)
役に立つかも
- [フォントで FizzBuzz する方法（1）:OpenType 機能](https://nixeneko.sakura.ne.jp/data/c93-fizzbuzz_otfeat/fizzbuzz_gsub.pdf)

### TrueType

- [TrueTypeフォントのフォーマットを調べる その20](https://project-the-tower2.hatenadiary.org/entry/20100630/1277838854)
- [TrueTypeFontで遊んでみた。](http://graphics.hatenablog.com/entry/2016/11/05/193540)
- [An Introduction to TrueType Fonts: A look inside the TTF format](http://scripts.sil.org/cms/scripts/page.php?site_id=nrsi&id=iws-chapter08)
- [フォントのアウトラインを法線方向に太らせたり細らせたりしてみる](https://nixeneko.hatenablog.com/entry/2017/12/13/000000)
- [Converting Outlines to the TrueType Format](https://developer.apple.com/fonts/TrueType-Reference-Manual/RM08/appendixE.html)

### etc

fontに関するツールが書いてある

- [フォントいじり用ソフトウェア・技術情報](https://nixeneko.hatenablog.com/entry/2015/12/29/231141)
めちゃくちゃかっこいいサイト
- [源ノ明朝　オープンソース Pan-CJK 書体](https://source.typekit.com/source-han-serif/jp/)
コミュニティとかも書いてある
- [フォントまわりのツールの探し方](https://shiromoji.hatenablog.jp/entry/2018/08/12/235803)
TTXや日本の現行法におけるフォントの扱いについて書いてある
- [TTXによるフォントのぞき基礎](https://shiromoji.net/font/mojiben0503/fontnozoki-with-ttx/#/)

## 文字コード

### 簡体字

mapping table がある

- [Table of General Standard Chinese Characters](http://hanzidb.org/character-list/general-standard)
- [China’s 通用规范汉字表 (Tōngyòng Guīfàn Hànzìbiǎo)](https://blogs.adobe.com/CCJKType/2014/03/china-8105.html)
- [簡体字中国語（GB2312）の文字コード表](http://ash.jp/code/cn/gb2312tbl.htm)

### 繁体字

どれに従うのがよのだろうか。
Big5(大五碼)かCNS11643, 前者の方がメジャー

- [繁体字](https://www.wikizero.com/ja/%E7%B9%81%E4%BD%93%E5%AD%97)
ここが一番いい
- [Mozilla 系列與 Big5 中文字碼](https://moztw.org/docs/big5/)
右側がuncode
- [big5 to unicode mapping table](https://www.csie.ntu.edu.tw/~r92030/project/big5/)
- [繁体字中国語（Big5）の文字コード表](http://ash.jp/code/cn/big5tbl.htm)
拼音とかもあるけど、足りてない
- [CNS11643・UCS対応表](http://kanji-database.sourceforge.net/charcode/cns.html)
常用國字標準字體表 と 次常用國字標準字體表
- [台湾の漢字表](http://kanji-database.sourceforge.net/tables/taiwan.html)
画像しかない
- [台湾の「漢字表」](http://kanji.zinbun.kyoto-u.ac.jp/~yasuoka/kanjibukuro/taiwan.html#BIG5)

## 得た知識

フォールバックフォント
> 文字列描画システムは、対応するグリフが存在しない場合には他のフォントからグリフを持ってきて穴埋めすると言う処理を行います。

- [文字サイズの比率と調和](https://standard.shiftbrain.com/blog/harmonious-proportions-in-type-sizes)
- [フォントの歴史から見えること～文字の誕生から活版印刷、手動写植機の登場まで](https://creatorzine.jp/article/detail/62)

[源ノ明朝をいろいろなフォントと縦組みで比較してみた](https://silight.hatenablog.jp/entry/2017/04/04/170908)
> 私がTTFバージョンを配布することも考えたのですが、源ノ明朝のライセンスはSIL Open Font Licenseとなっており、修正を加えたフォントの名前にオリジナルの名前を含めてはいけないというルールが定められています。このルールは、中身はほとんど同じなのに名前だけ違うフォントの乱立を招きます。そういった事態を避けるためにも現時点では私からは配布しません。

### その他

- [グループ:全漢字](https://glyphwiki.org/wiki/Group:%E5%85%A8%E6%BC%A2%E5%AD%97)
- [zi.tools 字統网](https://zi.tools/zi/%F0%AE%8E%B5)
　　-> 関係図とかもあってすごい

### 異体字

- [東京文化財研究所-異体字リスト](https://www.tobunken.go.jp/archives/%E7%95%B0%E4%BD%93%E5%AD%97%E3%83%AA%E3%82%B9%E3%83%88/)
- [國際電腦漢字及異體字知識庫](https://chardb.iis.sinica.edu.tw/)

### 総合情報(異体字・unicode・読み)

- [Unihan Database](https://www.unicode.org/charts/unihan.html)
- [文字情報技術促進協議会-文字情報基盤検索システム](https://moji.or.jp/mojikibansearch/basic)
- [zi.tools 字統网](https://zi.tools/)
- [汉辞宝](https://www.hancibao.com/)
- [Chinese Text Project](https://ctext.org/dictionary.pl?if=en)
- [CHISE / 漢字構造情報データベース](https://www.chise.org/ids/)
　　-> 高度な部首検索ができる
