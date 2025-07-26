# 多音字制御ロジック

[このツール](https://github.com/mozillazg/python-pinyin)で使っているデータを使ったら簡単に作成できそうだけどどうしよう。。。

ここには取得までの手順が書かれている
<https://github.com/mozillazg/python-pinyin/blob/master/docs/develop.rst>

> 实现思路/主逻辑
主逻辑:
对输入的字符串按是否是汉字进行分词（seg）
对分词结果的每个词条进行获取词条拼音的逻辑
检查词条是否是汉字，不是汉字则走处理没有拼音数据的逻辑（handle_nopinyin）
检查词条是否在 PHRASES_DICT 中，如果在直接取 PHRASES_DICT 中这个词条的拼音数据
如果词条不在 PHRASES_DICT 中，遍历词条包含的字符，每个字符进行 single_pinyin 逻辑处理
single_pinyin 的逻辑：
检查字符是否在 PINYIN_DICT 中，如果在的话，取 PINYIN_DICT 中这个字符的拼音数据
如果不在的话，走 handle_nopinyin 逻辑
handle_nopinyin 逻辑: 根据 errors 参数的值返回不同的结果。
对上面的步骤获得的拼音数据按指定的拼音风格进行转换。
PHRASES_DICT：词组拼音数据
PINYIN_DICT: 单个汉字的拼音数据
TODO: 画流程图

词语 を拼音に変換するのはここ
<https://github.com/mozillazg/python-pinyin/blob/master/pypinyin/converter.py#L221>

[データ](https://github.com/mozillazg/pinyin-data/tree/master) から生成した PINYIN_DICT はこれのこと
<https://raw.githubusercontent.com/mozillazg/python-pinyin/master/pypinyin/phrases_dict.py>

## 以下作業メモ

検証につかったサイト

- [](https://zhongwenzhuanpinyin.51240.com/)　多音字の対応が多い気がする？
- [](https://hanyu.baidu.com/)　例文まである
- [](http://www.cihai123.com/)　ここは出典まで記述されていていい
- [](https://cjjc.weblio.jp/content/%E5%88%92)
- [](https://www.zdic.net/)

- 儿、子、不起もパターン化できそう
刨根儿
- 子 は 末尾だと zǐ になる？

これの軽声はいらない？、とりあえず、今回は除外
差不多: chà/bu/duō
差不离: chà/bu/lí

一致せず、考慮の余地がある箇所の記録
not match
pypintin   : 藏掖, ['cáng', 'yè']
baidu-hanzi: 藏掖, ['cáng', 'yē']
not match
pypintin   : 调门儿, ['diào', 'mén', 'ér']
baidu-hanzi: 调门儿, ['diào', 'ménr']
not match
pypintin   : 走调儿, ['zǒu', 'diào', 'ér']
baidu-hanzi: 走调儿, ['zǒu', 'diàor']
not match
pypintin   : 分散, ['fēn', 'sǎn']
baidu-hanzi: 分散, ['fēn', 'sàn']
not match
pypintin   : 白干儿, ['bái', 'gān', 'ér']
baidu-hanzi: 白干儿, ['bái', 'gānr']
not match
pypintin   : 包干儿, ['bāo', 'gān', 'ér']
baidu-hanzi: 包干儿, ['bāo', 'gānr']
not match
pypintin   : 号子, ['hào', 'zǐ']
baidu-hanzi: 号子, ['hào', 'zi']
not match
pypintin   : 看不起, ['kàn', 'bù', 'qǐ']
baidu-hanzi: 看不起, ['kàn', 'bu', 'qǐ']
not match
pypintin   : 罪行累累, ['zuì', 'xíng', 'lěi', 'lèi']
baidu-hanzi: 罪行累累, ['zuì', 'xíng', 'lěi', 'lěi']
not match
pypintin   : 要不是, ['yào', 'bú', 'shì']
baidu-hanzi: 要不是, ['yào', 'bù', 'shì']
not match
pypintin   : 中间儿, ['zhōng', 'jiān', 'ér']
baidu-hanzi: 中间儿, ['zhōng', 'jiànr']
not match
pypintin   : 中兴, ['zhōng', 'xìng']
baidu-hanzi: 中兴, ['zhōng', 'xīng']

全然違うけどベトナムの漢字サイトがある。
<https://hvdic.thivien.net/>

基本的に[中国語の多音字辞典（Chinese Duoyinzi Dictionary）](https://dokochina.com/duoyinzi.htm)をベースにした。
さらに、[ユーウェン中国語講座 多音字](https://yuwen.zaich.com/intermediate/duoyinzi)からも抜粋した。

### pypinyin

漂 piào が piāo  になっている。PRを出す予定
为 wéi が wèi
拓 tuò が tà
舍 shè が shě
兴 xīng が xìng
咽 yān が yàn
长 cháng が zhǎng

#### 対応していない多音字

弹指 当年　倒栽葱　情分　缘分　身分　发行 号哭 说和 强辩 结果 乐理 私了
蒙骗 困难 拆散 舍得 踏实 旋风 中肯 中签 中选 中意 大轴子 转盘 转轴 佰划 果实累累 估量 接应

以下が境界値になっている。U+2B851以降は拼音が表示されない. CJK 扩展 E:[2B820-2CEAF] が表示されない。
U+2B81C: ní  # 𫠜
U+2B851: yīn  # 𫡑

### [中国語の多音字辞典（Chinese Duoyinzi Dictionary）](https://dokochina.com/duoyinzi.htm) でおかしい？やつ

#### よくわからなかったやつ

你得当心 これは本当か？文章じゃん
藕粉里和点糖 なんだこれ
打折了腿 ?

#### 単純に間違いのやつ

搭理 -> 答理
战栗 -> 颤栗
挑唆 -> 调唆
委屈　-> 委曲
成分 -> chéng fèn
弄里 -> 里弄

#### ピンイン書き間違いのやつ

「tuà 拓荒,开拓」 は tuò の間違い
「zhou 大轴子,压轴子」 は zhòu の間違い
「zhā 挣扎」 は zhá の間違い
「qiǎo 翘首」 は qiáo の間違い
「bǐng 除」 は 屏除
帖 tiē が足りない

#### 曖昧なやつ

作死,作揖 作料 書き言葉だと違う
调配　両方ある。仕方ない？
好事　両方ある。仕方ない？
温和　両方ある。仕方ない？
弄里 lǐ lòng ? そもそも一般的な言葉じゃない？
