# otfcc

```
# Xcode をインストールしておく
mas install 497799835
# Xcode は最初は [Command line Tools:] リストボックスが空欄になっているため、error になってしまう。
# 以下の対処をすると直る。
# [エラー：xcode-select: error: tool 'xcodebuild' requires Xcode, but active developer directory '/Library/Developer/CommandLineTools' is a command line tools instance](https://qiita.com/eytyet/items/59c5bad1c167d5addc68)

brew tap caryll/tap 
brew install otfcc-mac64
```

# otf -> json
```
otfccdump --pretty -o output.json ./res/fonts/SourceHanSerifCN-Regular.ttf

```

```
# 巨大すぎてeditor で読み込めないときは、jq でタグ指定したり、less コマンドで逐次追っていく。
# [jqコマンド(jsonデータの加工, 整形)の使い方](https://www.wakuwakubank.com/posts/676-linux-jq/)
brew install jq
cat output.json | jq > output2.json 
less output2.json 
```

# json -> otf
```
otfccbuild sawarabi_setting.json -o otfbuild.ttf
```
ttx は少しみずらい。ufo がいいけど uvs に対応していないし、、、
基本は glyph は ufo で編集して、設定とかは otfcc で json にするのがいいね.
ufo4 ができたら、統一したい。





# 設定を持つフォントのビルド
otfccbuild sawarabi_setting.json -o otfbuild.ttf
# 設定フォントを ttx に変換
ttx -t GSUB otfbuild.ttf
# 設定フォントの ttx を グリフを持つフォントへマージする
ttx -m SawarabiMincho-Regular.ttf otfbuild.ttx

# 各テーブルごとに出力
ttx -s -d ./output SawarabiMincho-Regular.ttf
# output GSUB table 
# cmap
ttx -t GSUB -d ./output SawarabiMincho-Regular.ttf
# marge
ttx -m test.ttf ./output/SawarabiMincho-Regular.ttx


lookup CNTXT_884C {
    sub uni4E0D uni884C' by uni8846;
    sub uni9280 uni884C' by uni8853;
# same above
#     sub [uni4E0D uni9280]  uni884C' by uni8846;
} CNTXT_884C;




# json で見つけた箇所
不　uni4E0D

## cmap (unicode と グリフの対応)
```
"cmap": {
        "32": "uni0020",
        ...
        "19981": "uni4E0D",
        ...
}
```

## cmap_uvs
```
"cmap_uvs": {
        ...
        "19981 917984": "uni4E0D.ss00",
        "19981 917985": "uni4E0D.ss01",
        "19981 917986": "uni4E0D.ss02",
        "19981 917987": "uni4E0D.ss03",
        ...
}
```

## glyf
```
{
        ...
        "uni4E0D": {
            "advanceWidth": 1536,
            "advanceHeight": 1024,
            "verticalOrigin": 820,
            "references": [
                {"glyph":"z_bu4","x":1024,"y":0,"a":1,"b":0,"c":0,"d":1},
                {"glyph":"uni4E0D.ss00","x":0,"y":0,"a":1,"b":0,"c":0,"d":1}
            ]
        },
        "uni4E0D.ss00": {
            "advanceWidth": 1536,
            "advanceHeight": 1024,
            "verticalOrigin": 820,
            "contours": [
                [{"x":524,"y":624,"on":true},{"x":383,"y":605,"on":true},{"x":340,"y":599,"on":false},{"x":306,"y":591,"on":true},{"x":276,"y":584,"on":false},{"x":259,"y":584,"on":true},{"x":238,"y":584,"on":false},{"x":216,"y":592,"on":true},{"x":194,"y":601,"on":false},{"x":187,"y":608,"on":true},{"x":184,"y":624,"on":true},{"x":200,"y":628,"on":true},{"x":222,"y":631,"on":true},{"x":517,"y":666,"on":true},{"x":585,"y":674,"on":false},{"x":624,"y":679,"on":true},{"x":681,"y":688,"on":true},{"x":726,"y":695,"on":true},{"x":753,"y":699,"on":false},{"x":770,"y":703,"on":true},{"x":787,"y":707,"on":false},{"x":798,"y":708,"on":true},{"x":804,"y":709,"on":false},{"x":819,"y":708,"on":true},{"x":838,"y":705,"on":false},{"x":856,"y":697,"on":true},{"x":874,"y":689,"on":false},{"x":887,"y":677,"on":true},{"x":898,"y":668,"on":false},{"x":898,"y":660,"on":true},{"x":896,"y":653,"on":false},{"x":887,"y":650,"on":true},{"x":879,"y":647,"on":false},{"x":869,"y":647,"on":true},{"x":860,"y":647,"on":false},{"x":846,"y":645,"on":true},{"x":832,"y":645,"on":false},{"x":804,"y":643,"on":true},{"x":777,"y":643,"on":false},{"x":729,"y":640,"on":true},{"x":682,"y":637,"on":false},{"x":656,"y":635,"on":true},{"x":574,"y":629,"on":true},{"x":589,"y":616,"on":true},{"x":596,"y":609,"on":false},{"x":602,"y":600,"on":true},{"x":605,"y":585,"on":true},{"x":602,"y":576,"on":false},{"x":593,"y":566,"on":true},{"x":558,"y":517,"on":true},{"x":547,"y":501,"on":true},{"x":561,"y":486,"on":false},{"x":570,"y":475,"on":true},{"x":580,"y":465,"on":false},{"x":584,"y":455,"on":true},{"x":588,"y":445,"on":false},{"x":588,"y":436,"on":true},{"x":588,"y":426,"on":false},{"x":586,"y":413,"on":true},{"x":582,"y":383,"on":true},{"x":598,"y":379,"on":false},{"x":617,"y":375,"on":true},{"x":636,"y":371,"on":false},{"x":663,"y":364,"on":true},{"x":690,"y":357,"on":false},{"x":728,"y":342,"on":true},{"x":768,"y":327,"on":false},{"x":796,"y":313,"on":true},{"x":824,"y":299,"on":false},{"x":851,"y":279,"on":true},{"x":878,"y":259,"on":false},{"x":889,"y":241,"on":true},{"x":900,"y":221,"on":false},{"x":902,"y":210,"on":true},{"x":904,"y":199,"on":false},{"x":906,"y":184,"on":true},{"x":906,"y":169,"on":false},{"x":901,"y":162,"on":true},{"x":895,"y":155,"on":false},{"x":879,"y":151,"on":true},{"x":869,"y":151,"on":false},{"x":859,"y":155,"on":true},{"x":844,"y":160,"on":false},{"x":820,"y":178,"on":true},{"x":796,"y":195,"on":false},{"x":776,"y":212,"on":true},{"x":709,"y":269,"on":true},{"x":662,"y":309,"on":false},{"x":637,"y":327,"on":true},{"x":612,"y":345,"on":false},{"x":600,"y":351,"on":true},{"x":580,"y":361,"on":true},{"x":572,"y":105,"on":true},{"x":569,"y":47,"on":true},{"x":568,"y":11,"on":false},{"x":565,"y":-4,"on":true},{"x":562,"y":-19,"on":false},{"x":558,"y":-34,"on":true},{"x":554,"y":-49,"on":false},{"x":548,"y":-53,"on":true},{"x":541,"y":-57,"on":true},{"x":532,"y":-56,"on":true},{"x":524,"y":-51,"on":false},{"x":516,"y":-33,"on":true},{"x":507,"y":-16,"on":false},{"x":503,"y":-6,"on":true},{"x":498,"y":3,"on":false},{"x":495,"y":19,"on":true},{"x":492,"y":34,"on":false},{"x":491,"y":42,"on":true},{"x":491,"y":50,"on":false},{"x":496,"y":65,"on":true},{"x":508,"y":109,"on":false},{"x":512,"y":127,"on":true},{"x":516,"y":145,"on":false},{"x":518,"y":178,"on":true},{"x":522,"y":231,"on":true},{"x":524,"y":264,"on":true},{"x":526,"y":373,"on":true},{"x":526,"y":411,"on":false},{"x":524,"y":435,"on":true},{"x":520,"y":463,"on":true},{"x":472,"y":399,"on":true},{"x":450,"y":372,"on":false},{"x":414,"y":336,"on":true},{"x":377,"y":299,"on":false},{"x":341,"y":270,"on":true},{"x":304,"y":241,"on":false},{"x":272,"y":219,"on":true},{"x":238,"y":197,"on":false},{"x":206,"y":180,"on":true},{"x":173,"y":162,"on":false},{"x":158,"y":157,"on":true},{"x":126,"y":156,"on":true},{"x":145,"y":173,"on":true},{"x":174,"y":193,"on":false},{"x":202,"y":215,"on":true},{"x":232,"y":237,"on":false},{"x":283,"y":281,"on":true},{"x":334,"y":327,"on":false},{"x":380,"y":378,"on":true},{"x":426,"y":429,"on":false},{"x":453,"y":468,"on":true},{"x":480,"y":507,"on":false},{"x":495,"y":535,"on":true},{"x":510,"y":563,"on":false},{"x":515,"y":579,"on":true},{"x":520,"y":596,"on":false},{"x":522,"y":607,"on":true}]
            ]
        },
        "uni4E0D.ss01": {
            "advanceWidth": 1536,
            "advanceHeight": 1024,
            "verticalOrigin": 820,
            "references": [
                {"glyph":"z_bu2","x":1024,"y":0,"a":1,"b":0,"c":0,"d":1},
                {"glyph":"uni4E0D.ss00","x":0,"y":0,"a":1,"b":0,"c":0,"d":1}
            ]
        },
        "uni4E0D.ss02": {
            "advanceWidth": 1536,
            "advanceHeight": 1024,
            "verticalOrigin": 820,
            "references": [
                {"glyph":"z_fou1","x":1024,"y":0,"a":1,"b":0,"c":0,"d":1},
                {"glyph":"uni4E0D.ss00","x":0,"y":0,"a":1,"b":0,"c":0,"d":1}
            ]
        },
        "uni4E0D.ss03": {
            "advanceWidth": 1536,
            "advanceHeight": 1024,
            "verticalOrigin": 820,
            "references": [
                {"glyph":"z_fu1","x":1024,"y":0,"a":1,"b":0,"c":0,"d":1},
                {"glyph":"uni4E0D.ss00","x":0,"y":0,"a":1,"b":0,"c":0,"d":1}
            ]
        },
        ...
}
```

# Glyph Order
.ss00 が無印のグリフ。設定を変更するだけで拼音を変更できる。
.ss01 が標準の読みの拼音

```
"glyph_order": [
  ...
  "uni4E0D","uni4E0D.ss00","uni4E0D.ss01","uni4E0D.ss02","uni4E0D.ss03",
  ...
]
```

## GSUB aalt

aalt_0 は拼音が一つのみの漢字 + 記号とか。置き換え対象が一つのみのとき
aalt_1 は拼音が複数の漢字

```
"GSUB": {
        "languages": {
            "DFLT_DFLT": {
                "features": ["ss10_00006","ss01_00001","ss02_00002","ss03_00003","ss04_00004","ss05_00005","vert_00007","vrt2_00008","aalt_00000"]
            }
        },
        "features": {
            "aalt_00000": ["lookup_aalt_0","lookup_aalt_1"],
            "ss01_00001": ["lookup_ss01_2"],
            "ss02_00002": ["lookup_ss02_3"],
            "ss03_00003": ["lookup_ss03_4"],
            "ss04_00004": ["lookup_ss04_5"],
            "ss05_00005": ["lookup_ss05_6"],
            "ss10_00006": ["lookup_ss10_7"],
            "vert_00007": ["lookup_vert_8"],
            "vrt2_00008": ["lookup_vrt2_9"]
        },
        "lookup_aalt_1": {
                "type": "gsub_alternate",
                "flags": {},
                "subtables": [
                    {
                       ...
                        "uni4E0D": ["uni4E0D.ss00","uni4E0D.ss01","uni4E0D.ss02","uni4E0D.ss03"],
                        ...
                    }
                ]
        },
        "lookup_ss10_7": {
                "type": "gsub_single",
                "flags": {},
                "subtables": [
                    {
                        ...
                        "uni4E0D": "uni4E0D.ss00",
                        ...
                    }
                ]
        },
        "lookup_ss01_2": {
                "type": "gsub_single",
                "flags": {},
                "subtables": [
                    {
                        ...
                        "uni4E0D": "uni4E0D.ss01",
                        ...
                    }
                ]
        },
        "lookup_ss02_3": {
                "type": "gsub_single",
                "flags": {},
                "subtables": [
                    {
                        ...
                        "uni4E0D": "uni4E0D.ss02",
                        ...
                    }
                ]
        },
        "lookup_ss03_4": {
                "type": "gsub_single",
                "flags": {},
                "subtables": [
                    {
                        "uni4E0D": "uni4E0D.ss03",
                        ...
                    }
                ]
        },
        "lookupOrder": [
            "lookup_vert_8",
            "lookup_vrt2_9",
            "lookup_aalt_0",
            "lookup_aalt_1",
            "lookup_ss10_7",
            "lookup_ss01_2",
            "lookup_ss02_3",
            "lookup_ss03_4",
            "lookup_ss04_5",
            "lookup_ss05_6"
        ]
}
```



# calt を追加するために
```
lookup lookup_0 {
  sub A by X;
  sub uni884C by uni8846;
} lookup_0;

lookup calt0 {
	sub [uni4E0D uni9280] uni884C' lookup lookup_0 ;
} calt0;
lookup calt1 {
	sub A' lookup lookup_0 F ;
} calt1;
```
## json から抽出
```
"GSUB": {
    "languages": {
      "DFLT_DFLT": {
        "features": ["calt_00000","ccmp_00002"]
      },
      "latn_DFLT": {
        "features": ["calt_00001","ccmp_00003"]
      }
    },
    "features": {
      "calt_00000": ["lookup_calt_0","lookup_calt_1"],
      "calt_00001": ["lookup_calt_0","lookup_calt_1"],
      "ccmp_00002": ["lookup_ccmp_2"],
      "ccmp_00003": ["lookup_ccmp_2"]
    },
    "lookups": {
      "lookup_calt_0": {
        "type": "gsub_chaining",
        "flags": {},
        "subtables": [
          {
            "match": [
              ["uni4E0D","uni9280"],
              ["uni884C"]
            ],
            "apply": [
              {
                "at": 1,
                "lookup": "lookup_11_3"
              }
            ],
            "inputBegins": 1,
            "inputEnds": 2
          }
        ]
      },
      "lookup_calt_1": {
        "type": "gsub_chaining",
        "flags": {},
        "subtables": [
          {
            "match": [
              ["A"],["F"]
            ],
            "apply": [
              {
                "at": 0,
                "lookup": "lookup_11_3"
              }
            ],
            "inputBegins": 0,
            "inputEnds": 1
          }
        ]
      },
      "lookup_ccmp_2": {
        "type": "gsub_ligature",
        "flags": {},
        "subtables": [
          {
            "substitutions": [
              {
                "from": ["A","C"],
                "to": "D"
              }
            ]
          }
        ]
      },
      "lookup_11_3": {
        "type": "gsub_single",
        "flags": {},
        "subtables": [
          {
            "A": "X",
            "uni884C": "uni8846"
          }
        ]
      }
    },
    "lookupOrder": [
      "lookup_calt_0",
      "lookup_calt_1",
      "lookup_ccmp_2",
      "lookup_11_3"
    ]
  }
```




# 注音の合成方法について
zyt ㄊ（t） を例に
unicode だと uni310A だけど注音用に別グリフになっている。

zyt ㄊ
```
        "zyt": {
            "advanceWidth": 306,
            "advanceHeight": 1024,
            "verticalOrigin": 901,
            "contours": [
                [{"x":242,"y":29,"on":false},{"x":235,"y":45,"on":true},{"x":226,"y":65,"on":true},{"x":187,"y":55,"on":false},{"x":163,"y":50,"on":true},{"x":98,"y":34,"on":true},{"x":78,"y":29,"on":false},{"x":73,"y":29,"on":true},{"x":67,"y":29,"on":false},{"x":60,"y":34,"on":false},{"x":56,"y":39,"on":false},{"x":55,"y":41,"on":true},{"x":47,"y":55,"on":false},{"x":48,"y":60,"on":true},{"x":55,"y":71,"on":true},{"x":81,"y":107,"on":false},{"x":103,"y":174,"on":true},{"x":83,"y":171,"on":true},{"x":57,"y":168,"on":true},{"x":54,"y":167,"on":false},{"x":35,"y":162,"on":false},{"x":30,"y":165,"on":true},{"x":19,"y":172,"on":false},{"x":1,"y":190,"on":true},{"x":-3,"y":194,"on":false},{"x":-3,"y":196,"on":true},{"x":-3,"y":202,"on":false},{"x":19,"y":202,"on":true},{"x":53,"y":202,"on":true},{"x":87,"y":204,"on":false},{"x":115,"y":207,"on":true},{"x":121,"y":222,"on":false},{"x":135,"y":268,"on":false},{"x":138,"y":282,"on":true},{"x":138,"y":285,"on":false},{"x":139,"y":303,"on":false},{"x":142,"y":305,"on":true},{"x":143,"y":305,"on":true},{"x":147,"y":305,"on":false},{"x":161,"y":297,"on":false},{"x":167,"y":291,"on":true},{"x":186,"y":272,"on":false},{"x":178,"y":261,"on":true},{"x":174,"y":260,"on":false},{"x":161,"y":228,"on":true},{"x":160,"y":226,"on":false},{"x":154,"y":210,"on":true},{"x":162,"y":211,"on":false},{"x":212,"y":217,"on":true},{"x":235,"y":219,"on":false},{"x":247,"y":222,"on":true},{"x":264,"y":227,"on":false},{"x":274,"y":227,"on":true},{"x":282,"y":227,"on":false},{"x":292,"y":216,"on":false},{"x":294,"y":214,"on":true},{"x":297,"y":211,"on":false},{"x":301,"y":202,"on":true},{"x":305,"y":195,"on":false},{"x":304,"y":192,"on":true},{"x":300,"y":186,"on":false},{"x":290,"y":186,"on":true},{"x":257,"y":188,"on":false},{"x":211,"y":184,"on":true},{"x":191,"y":182,"on":false},{"x":181,"y":180,"on":true},{"x":142,"y":176,"on":true},{"x":133,"y":149,"on":true},{"x":122,"y":125,"on":true},{"x":117,"y":113,"on":false},{"x":105,"y":89,"on":false},{"x":102,"y":81,"on":true},{"x":101,"y":79,"on":false},{"x":101,"y":75,"on":true},{"x":101,"y":70,"on":false},{"x":107,"y":70,"on":true},{"x":115,"y":70,"on":false},{"x":162,"y":79,"on":true},{"x":199,"y":85,"on":true},{"x":216,"y":89,"on":true},{"x":207,"y":114,"on":false},{"x":197,"y":128,"on":false},{"x":196,"y":130,"on":true},{"x":202,"y":136,"on":true},{"x":241,"y":111,"on":false},{"x":265,"y":85,"on":true},{"x":272,"y":76,"on":false},{"x":277,"y":60,"on":false},{"x":276,"y":50,"on":true},{"x":274,"y":41,"on":false},{"x":269,"y":36,"on":true},{"x":267,"y":31,"on":false},{"x":257,"y":29,"on":true}]
            ]
        },
```

zya ㄚ
```
        "zya": {
            "advanceWidth": 306,
            "advanceHeight": 1024,
            "verticalOrigin": 901,
            "contours": [
                [{"x":154,"y":-1,"on":false},{"x":148,"y":7,"on":false},{"x":147,"y":8,"on":true},{"x":137,"y":22,"on":false},{"x":138,"y":35,"on":true},{"x":139,"y":43,"on":false},{"x":141,"y":78,"on":true},{"x":142,"y":126,"on":true},{"x":141,"y":137,"on":false},{"x":139,"y":142,"on":false},{"x":131,"y":151,"on":true},{"x":115,"y":171,"on":false},{"x":94,"y":192,"on":true},{"x":70,"y":216,"on":false},{"x":63,"y":224,"on":true},{"x":63,"y":224,"on":false},{"x":33,"y":254,"on":true},{"x":30,"y":257,"on":false},{"x":30,"y":260,"on":true},{"x":30,"y":265,"on":false},{"x":43,"y":272,"on":false},{"x":50,"y":271,"on":true},{"x":70,"y":269,"on":false},{"x":83,"y":264,"on":false},{"x":89,"y":254,"on":true},{"x":95,"y":244,"on":false},{"x":118,"y":217,"on":false},{"x":124,"y":210,"on":true},{"x":149,"y":180,"on":false},{"x":159,"y":170,"on":true},{"x":177,"y":191,"on":false},{"x":204,"y":230,"on":true},{"x":226,"y":258,"on":false},{"x":230,"y":276,"on":true},{"x":234,"y":289,"on":false},{"x":242,"y":289,"on":true},{"x":246,"y":289,"on":false},{"x":254,"y":284,"on":true},{"x":280,"y":268,"on":false},{"x":280,"y":258,"on":true},{"x":280,"y":252,"on":false},{"x":267,"y":243,"on":true},{"x":249,"y":230,"on":false},{"x":237,"y":214,"on":true},{"x":217,"y":189,"on":true},{"x":197,"y":165,"on":false},{"x":187,"y":151,"on":true},{"x":182,"y":142,"on":false},{"x":182,"y":125,"on":true},{"x":182,"y":64,"on":true},{"x":182,"y":24,"on":true},{"x":183,"y":17,"on":false},{"x":166,"y":-1,"on":false},{"x":161,"y":-1,"on":true}]
            ]
        },
```

z_ta1 ㄊㄚ
# [Apple-The 'glyf' table](https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6glyf.html)
{"glyph":"zya","x":0,"y":50,"a":1,"b":0,"c":0,"d":1}

a-d ってなんだ？
> The transformation entries determine the values of an affine transformation applied to the component prior to its being incorporated into the parent glyph. Given the component matrix [a b c d e f], the transformation applied to the component is:

アフィン変換でした


```
        "z_ta1": {
            "advanceWidth": 512,
            "advanceHeight": 1024,
            "verticalOrigin": 900,
            "references": [
                {"glyph":"zyt","x":0,"y":400,"a":1,"b":0,"c":0,"d":1},
                {"glyph":"zya","x":0,"y":50,"a":1,"b":0,"c":0,"d":1}
            ]
        },
```

他 ㄊㄚ
```
        "uni4ED6": {
            "advanceWidth": 1536,
            "advanceHeight": 1024,
            "verticalOrigin": 820,
            "references": [
                {"glyph":"z_ta1","x":1024,"y":0,"a":1,"b":0,"c":0,"d":1},
                {"glyph":"uni4ED6.ss00","x":0,"y":0,"a":1,"b":0,"c":0,"d":1}
            ]
        },
        "uni4ED6.ss00": {
            "advanceWidth": 1536,
            "advanceHeight": 1024,
            "verticalOrigin": 820,
            "contours": [
                [{"x":247,"y":491,"on":true},{"x":259,"y":483,"on":false},{"x":267,"y":477,"on":true},{"x":275,"y":470,"on":false},{"x":282,"y":461,"on":true},{"x":289,"y":447,"on":true},{"x":289,"y":438,"on":false},{"x":285,"y":420,"on":true},{"x":283,"y":413,"on":false},{"x":281,"y":397,"on":true},{"x":279,"y":379,"on":false},{"x":278,"y":368,"on":true},{"x":277,"y":357,"on":false},{"x":277,"y":325,"on":true},{"x":275,"y":171,"on":true},{"x":275,"y":159,"on":false},{"x":276,"y":125,"on":true},{"x":277,"y":90,"on":false},{"x":278,"y":73,"on":true},{"x":279,"y":55,"on":false},{"x":279,"y":47,"on":true},{"x":278,"y":35,"on":false},{"x":274,"y":21,"on":true},{"x":270,"y":9,"on":false},{"x":265,"y":-2,"on":true},{"x":257,"y":-15,"on":true},{"x":239,"y":-18,"on":true},{"x":230,"y":-6,"on":false},{"x":225,"y":5,"on":true},{"x":221,"y":15,"on":false},{"x":218,"y":25,"on":true},{"x":212,"y":46,"on":true},{"x":210,"y":59,"on":true},{"x":210,"y":69,"on":false},{"x":215,"y":85,"on":true},{"x":219,"y":101,"on":false},{"x":221,"y":118,"on":true},{"x":223,"y":134,"on":false},{"x":226,"y":161,"on":true},{"x":228,"y":189,"on":false},{"x":229,"y":205,"on":true},{"x":235,"y":365,"on":true},{"x":235,"y":405,"on":true},{"x":234,"y":427,"on":false},{"x":232,"y":436,"on":true},{"x":230,"y":447,"on":true},{"x":225,"y":461,"on":true},{"x":195,"y":423,"on":true},{"x":176,"y":399,"on":false},{"x":157,"y":380,"on":true},{"x":107,"y":337,"on":true},{"x":93,"y":325,"on":false},{"x":87,"y":321,"on":true},{"x":69,"y":309,"on":true},{"x":55,"y":308,"on":true},{"x":55,"y":315,"on":false},{"x":61,"y":321,"on":true},{"x":75,"y":337,"on":true},{"x":83,"y":345,"on":false},{"x":107,"y":376,"on":true},{"x":146,"y":426,"on":true},{"x":161,"y":446,"on":false},{"x":177,"y":471,"on":true},{"x":215,"y":539,"on":true},{"x":237,"y":582,"on":false},{"x":246,"y":604,"on":true},{"x":255,"y":626,"on":false},{"x":262,"y":645,"on":true},{"x":268,"y":663,"on":false},{"x":272,"y":678,"on":true},{"x":277,"y":693,"on":false},{"x":277,"y":706,"on":true},{"x":279,"y":721,"on":true},{"x":284,"y":727,"on":false},{"x":294,"y":728,"on":true},{"x":303,"y":728,"on":false},{"x":310,"y":724,"on":true},{"x":319,"y":720,"on":false},{"x":331,"y":712,"on":true},{"x":344,"y":705,"on":false},{"x":354,"y":694,"on":true},{"x":364,"y":684,"on":false},{"x":364,"y":675,"on":true},{"x":363,"y":667,"on":false},{"x":350,"y":656,"on":true},{"x":335,"y":643,"on":false},{"x":323,"y":621,"on":true},{"x":293,"y":564,"on":true},{"x":263,"y":515,"on":true}],
                [{"x":423,"y":386,"on":true},{"x":422,"y":454,"on":true},{"x":421,"y":479,"on":true},{"x":419,"y":502,"on":false},{"x":415,"y":514,"on":true},{"x":411,"y":528,"on":true},{"x":412,"y":537,"on":false},{"x":423,"y":539,"on":true},{"x":430,"y":540,"on":false},{"x":437,"y":537,"on":true},{"x":447,"y":533,"on":false},{"x":454,"y":531,"on":true},{"x":461,"y":527,"on":false},{"x":475,"y":516,"on":true},{"x":489,"y":504,"on":false},{"x":488,"y":492,"on":true},{"x":481,"y":476,"on":true},{"x":474,"y":461,"on":false},{"x":472,"y":438,"on":true},{"x":469,"y":407,"on":true},{"x":563,"y":453,"on":true},{"x":568,"y":633,"on":true},{"x":568,"y":648,"on":false},{"x":565,"y":670,"on":true},{"x":563,"y":691,"on":false},{"x":560,"y":701,"on":true},{"x":558,"y":711,"on":false},{"x":551,"y":724,"on":true},{"x":544,"y":741,"on":true},{"x":547,"y":751,"on":true},{"x":552,"y":756,"on":false},{"x":564,"y":755,"on":true},{"x":579,"y":753,"on":false},{"x":587,"y":751,"on":true},{"x":595,"y":749,"on":false},{"x":614,"y":742,"on":true},{"x":633,"y":735,"on":false},{"x":638,"y":728,"on":true},{"x":644,"y":721,"on":false},{"x":643,"y":711,"on":true},{"x":639,"y":697,"on":true},{"x":635,"y":687,"on":false},{"x":630,"y":665,"on":true},{"x":625,"y":644,"on":false},{"x":624,"y":616,"on":true},{"x":617,"y":484,"on":true},{"x":677,"y":518,"on":true},{"x":701,"y":531,"on":false},{"x":717,"y":543,"on":true},{"x":733,"y":555,"on":false},{"x":741,"y":559,"on":true},{"x":749,"y":563,"on":false},{"x":759,"y":565,"on":true},{"x":775,"y":563,"on":true},{"x":787,"y":561,"on":false},{"x":805,"y":556,"on":true},{"x":823,"y":551,"on":false},{"x":834,"y":545,"on":true},{"x":847,"y":537,"on":true},{"x":853,"y":527,"on":true},{"x":854,"y":519,"on":false},{"x":843,"y":506,"on":true},{"x":836,"y":499,"on":false},{"x":829,"y":486,"on":true},{"x":822,"y":474,"on":false},{"x":807,"y":441,"on":true},{"x":791,"y":409,"on":false},{"x":782,"y":389,"on":true},{"x":772,"y":370,"on":false},{"x":757,"y":346,"on":true},{"x":742,"y":323,"on":false},{"x":722,"y":303,"on":true},{"x":696,"y":277,"on":true},{"x":685,"y":280,"on":true},{"x":699,"y":312,"on":true},{"x":711,"y":339,"on":true},{"x":718,"y":356,"on":false},{"x":726,"y":380,"on":true},{"x":735,"y":404,"on":false},{"x":739,"y":421,"on":true},{"x":747,"y":459,"on":true},{"x":752,"y":473,"on":false},{"x":751,"y":484,"on":true},{"x":736,"y":494,"on":true},{"x":719,"y":489,"on":false},{"x":710,"y":483,"on":true},{"x":613,"y":432,"on":true},{"x":605,"y":326,"on":true},{"x":603,"y":291,"on":true},{"x":597,"y":261,"on":true},{"x":592,"y":227,"on":false},{"x":585,"y":223,"on":true},{"x":576,"y":219,"on":true},{"x":569,"y":219,"on":false},{"x":565,"y":235,"on":true},{"x":563,"y":243,"on":false},{"x":563,"y":265,"on":true},{"x":561,"y":294,"on":true},{"x":560,"y":300,"on":false},{"x":560,"y":308,"on":true},{"x":560,"y":316,"on":false},{"x":561,"y":327,"on":true},{"x":563,"y":407,"on":true},{"x":531,"y":392,"on":false},{"x":518,"y":385,"on":true},{"x":489,"y":369,"on":true},{"x":466,"y":357,"on":true},{"x":465,"y":309,"on":false},{"x":463,"y":277,"on":true},{"x":463,"y":247,"on":false},{"x":462,"y":214,"on":true},{"x":462,"y":186,"on":false},{"x":473,"y":164,"on":true},{"x":479,"y":149,"on":false},{"x":490,"y":138,"on":true},{"x":501,"y":126,"on":false},{"x":526,"y":115,"on":true},{"x":551,"y":105,"on":false},{"x":591,"y":101,"on":true},{"x":631,"y":97,"on":false},{"x":666,"y":97,"on":true},{"x":701,"y":97,"on":false},{"x":742,"y":102,"on":true},{"x":783,"y":107,"on":false},{"x":809,"y":116,"on":true},{"x":836,"y":125,"on":false},{"x":851,"y":138,"on":true},{"x":867,"y":151,"on":false},{"x":875,"y":166,"on":true},{"x":885,"y":181,"on":false},{"x":889,"y":202,"on":true},{"x":897,"y":259,"on":true},{"x":900,"y":283,"on":true},{"x":907,"y":298,"on":true},{"x":917,"y":297,"on":false},{"x":919,"y":290,"on":true},{"x":924,"y":259,"on":true},{"x":930,"y":223,"on":false},{"x":933,"y":214,"on":true},{"x":936,"y":205,"on":false},{"x":946,"y":183,"on":true},{"x":957,"y":161,"on":false},{"x":964,"y":151,"on":true},{"x":972,"y":137,"on":true},{"x":973,"y":130,"on":false},{"x":969,"y":121,"on":true},{"x":965,"y":110,"on":false},{"x":947,"y":91,"on":true},{"x":929,"y":73,"on":false},{"x":885,"y":57,"on":true},{"x":841,"y":40,"on":false},{"x":796,"y":32,"on":true},{"x":756,"y":24,"on":false},{"x":705,"y":24,"on":true},{"x":647,"y":24,"on":false},{"x":603,"y":33,"on":true},{"x":559,"y":41,"on":false},{"x":524,"y":55,"on":true},{"x":489,"y":69,"on":false},{"x":466,"y":93,"on":true},{"x":443,"y":116,"on":false},{"x":431,"y":147,"on":true},{"x":419,"y":178,"on":false},{"x":419,"y":229,"on":true},{"x":420,"y":267,"on":true},{"x":422,"y":333,"on":true},{"x":391,"y":318,"on":true},{"x":362,"y":301,"on":true},{"x":352,"y":299,"on":true},{"x":339,"y":299,"on":false},{"x":325,"y":303,"on":true},{"x":311,"y":307,"on":false},{"x":303,"y":311,"on":true},{"x":294,"y":322,"on":true},{"x":305,"y":330,"on":true}]
            ]
        },
```

uni310A ㄊ
```
        "uni310A": {
            "advanceWidth": 1536,
            "advanceHeight": 1024,
            "verticalOrigin": 880,
            "contours": [
                [{"x":263,"y":31,"on":false},{"x":252,"y":35,"on":true},{"x":245,"y":37,"on":false},{"x":229,"y":59,"on":true},{"x":211,"y":88,"on":false},{"x":213,"y":100,"on":true},{"x":219,"y":113,"on":false},{"x":239,"y":142,"on":true},{"x":244,"y":150,"on":false},{"x":247,"y":154,"on":true},{"x":314,"y":257,"on":false},{"x":383,"y":459,"on":true},{"x":286,"y":449,"on":true},{"x":232,"y":444,"on":false},{"x":207,"y":437,"on":true},{"x":187,"y":432,"on":false},{"x":162,"y":428,"on":true},{"x":136,"y":424,"on":false},{"x":146,"y":428,"on":true},{"x":130,"y":427,"on":false},{"x":105,"y":440,"on":false},{"x":85,"y":460,"on":true},{"x":74,"y":471,"on":false},{"x":76,"y":492,"on":false},{"x":91,"y":495,"on":true},{"x":106,"y":496,"on":false},{"x":153,"y":495,"on":true},{"x":188,"y":495,"on":false},{"x":200,"y":495,"on":true},{"x":286,"y":498,"on":false},{"x":399,"y":511,"on":true},{"x":454,"y":661,"on":false},{"x":467,"y":736,"on":true},{"x":469,"y":788,"on":false},{"x":477,"y":792,"on":true},{"x":488,"y":794,"on":false},{"x":525,"y":767,"on":true},{"x":540,"y":755,"on":false},{"x":553,"y":711,"on":false},{"x":543,"y":701,"on":true},{"x":528,"y":687,"on":false},{"x":492,"y":598,"on":true},{"x":487,"y":583,"on":false},{"x":466,"y":532,"on":false},{"x":460,"y":515,"on":true},{"x":502,"y":519,"on":false},{"x":583,"y":527,"on":true},{"x":643,"y":533,"on":false},{"x":668,"y":536,"on":true},{"x":730,"y":543,"on":false},{"x":777,"y":554,"on":true},{"x":807,"y":562,"on":false},{"x":825,"y":562,"on":true},{"x":862,"y":562,"on":false},{"x":883,"y":538,"on":true},{"x":897,"y":521,"on":false},{"x":898,"y":511,"on":true},{"x":903,"y":500,"on":false},{"x":901,"y":496,"on":true},{"x":898,"y":489,"on":false},{"x":890,"y":489,"on":true},{"x":793,"y":492,"on":false},{"x":658,"y":483,"on":true},{"x":649,"y":482,"on":false},{"x":630,"y":481,"on":true},{"x":591,"y":478,"on":false},{"x":569,"y":476,"on":true},{"x":560,"y":475,"on":false},{"x":542,"y":473,"on":true},{"x":478,"y":467,"on":false},{"x":441,"y":462,"on":true},{"x":437,"y":451,"on":false},{"x":430,"y":430,"on":true},{"x":413,"y":381,"on":false},{"x":408,"y":370,"on":true},{"x":403,"y":356,"on":false},{"x":362,"y":257,"on":true},{"x":319,"y":156,"on":false},{"x":311,"y":139,"on":true},{"x":303,"y":120,"on":false},{"x":313,"y":114,"on":true},{"x":320,"y":109,"on":false},{"x":344,"y":112,"on":true},{"x":445,"y":123,"on":false},{"x":558,"y":146,"on":true},{"x":588,"y":153,"on":false},{"x":630,"y":163,"on":true},{"x":689,"y":177,"on":false},{"x":706,"y":185,"on":true},{"x":684,"y":220,"on":false},{"x":652,"y":261,"on":true},{"x":637,"y":281,"on":false},{"x":629,"y":292,"on":true},{"x":643,"y":305,"on":true},{"x":721,"y":250,"on":false},{"x":796,"y":168,"on":true},{"x":825,"y":123,"on":false},{"x":824,"y":75,"on":true},{"x":822,"y":57,"on":false},{"x":810,"y":45,"on":true},{"x":802,"y":34,"on":false},{"x":791,"y":33,"on":true},{"x":772,"y":34,"on":false},{"x":755,"y":72,"on":true},{"x":748,"y":86,"on":false},{"x":740,"y":108,"on":true},{"x":730,"y":132,"on":false},{"x":723,"y":146,"on":true},{"x":697,"y":140,"on":false},{"x":645,"y":126,"on":true},{"x":554,"y":101,"on":false},{"x":516,"y":93,"on":true},{"x":325,"y":46,"on":true}]
            ]
        },
```