# About Pinyin table

```bash
python make_unicode_pinyin_map_table.py  
```

## Creation procedure of Pinyin table

1. Download the unicode table from the sites(e.g. [traditional chinese](https://moztw.org/docs/big5/table/big5_2003-u2b.txt), [simplified chinese](http://hanzidb.org/TGSCC-Unicode.txt))
2. Create traditional and simplified chinese unicode tables
3. Create the integrated unicode table(i.e. [marged-mapping-table.txt](https://github.com/MaruTama/Mengshen-pinyin-font/blob/master/outputs/marged-mapping-table.txt)) that traditional and simplified Chinese
4. Overwrite the integrated Unicode table (i.e. [marged-mapping-table.txt](https://github.com/MaruTama/Mengshen-pinyin-font/blob/master/outputs/marged-mapping-table.txt)) with [overwrite.txt](overwrite.txt)

## Outputs

The format of the unicode table conforms to [pinyin-data](https://github.com/mozillazg/pinyin-data/blob/master/pinyin.txt).  
overwrite.txt is used for the following purposes.

- Add hanzi that cannot be obtained with pypinyin
- Adjust pronunciation priority  
- Add the `儿's 'r'`
- Add a light tone, And unify the pronunciation of duplicate hanzi
- Readings whose letters have no precomposed Unicode code point (e.g. `呣/m̀`, `嘸/m̄`, `欸/ê̄`) are kept. Their pinyin glyphs come from the pinyin font, or from the bundled composed glyphs in [res/fonts/custom_pinyin_glyphs/](../../fonts/custom_pinyin_glyphs) when the font lacks them. Capitalized forms (e.g. Ḿ, Ế, Ề) are not used.  

### File directories

```text
outputs
   └── marged-mapping-table.txt -> integrated unicode table of traditional and simplified chinese unicode tables(Overwrite.txt was reflected)
```

```text
download_unicode_tables
         ├── big5_2003-u2b.txt -> Scope of traditional Chinese
         └── TGSCC-Unicode.txt -> Scope of Simplified Chinese
```

```text
.
├── BIG5-mapping-table.txt           -> Traditional Chinese target scope unicode table  
├── README.md
├── TGSCC-mapping-table.txt          -> Simplified Chinese target scope unicode table   
├── make_unicode_pinyin_map_table.py -> script for creation unicode table
└── overwrite.txt                    -> Table for modification. Overwrite marged-mapping-table.txt. (Editable)
```
