# How to make pinyin-font

## Requirements

- Display pinyin for both Simplified and Traditional Chinese
- The scope of Simplified Chinese characters is based on the *[Table of General Standard Chinese Characters](https://en.wikipedia.org/wiki/Table_of_General_Standard_Chinese_Characters)* ([通用规范汉字表](https://blogs.adobe.com/CCJKType/2014/03/china-8105.html))
- The scope of Traditional Chinese characters is based on the *[Big-5-2003](https://en.wikipedia.org/wiki/Big5)* ([五大碼-2003](https://moztw.org/docs/big5/))
- The scope of Japanese Kanji is based on the *[Jōyō_kanji](https://en.wikipedia.org/wiki/J%C5%8Dy%C5%8D_kanji)* ([常用漢字表（平成22年内閣告示第2号）](https://www.bunka.go.jp/kokugo_nihongo/sisaku/joho/joho/kijun/naikaku/kanji/))
- Hiragana (e.g.:あ) and katakana (e.g.:ア) are available

There are 16,026 characters targeted for pinyin display.

### Base Fonts

#### han-serif

The font used here is based on [Source-Han-TrueType](https://github.com/Pal3love/Source-Han-TrueType).
This is a TTF version of [Source Han Sans](https://github.com/adobe-fonts/source-han-sans)/[Source Han Serif](https://github.com/adobe-fonts/source-han-serif) with reduced file size. All required Chinese characters are included.
[M+ M Type-1's mplus-1m-medium.ttf](https://mplus-fonts.osdn.jp/about.html) is used for the pinyin part of this font.

#### handwritten

The font used here is based on [小赖字体/Xiaolai Font](https://github.com/lxgw/kose-font).
And remove Hangul characters(a960 #ꥠ ~ d7fb #ퟻ) from this font to reduce glyphs.
[SetoFontSP](https://ja.osdn.net/projects/setofont/releases/p14368) is used for the pinyin part of this font.

## Dependencies

### Test Commands

```bash
# Run all tests
python -m pytest tests/ -v

# Run tests with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run security tests
python -m pytest tests/security/ -v

# Run specific test categories
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest tests/performance/ --benchmark-only

# Watch tests during development
pytest-watch --clear
```

### Font Development TDD Workflow (Complete Pipeline)

```bash
# 1. 🔴 Red: Create characterization tests for existing functionality
python -m pytest tests/integration/test_font_output_baseline.py

# 2. 🔴 Red: Write tests for new features/refactoring
python -m pytest tests/unit/test_new_feature.py  # Should fail (Red)

# 3. 🟢 Green: Implement minimum code to pass tests
# Edit source files...
python -m pytest tests/unit/test_new_feature.py  # Should pass (Green)

# 4. 🔵 Refactor: Improve code while keeping tests passing
# Refactor source files...
python -m pytest tests/unit/ tests/security/  # All should pass

# 5. 🧪 Pipeline: Complete pipeline validation
# Dictionary generation
cd res/phonics/duo_yin_zi/scripts/
python make_pattern_table.py

cd res/phonics/unicode_mapping_table/
python make_unicode_pinyin_map_table.py

# Dump base fonts to editable state (json)
# glyf table is large and inconvenient for browsing, so separate from other tables
# han-serif
PYTHONPATH=src python -m refactored.scripts.make_template_jsons --style han_serif
# handwritten
PYTHONPATH=src python -m refactored.scripts.make_template_jsons --style handwritten

# Extract characters for pinyin display
# Only fixed-width English fonts supported
# han-serif
PYTHONPATH=src python -m refactored.scripts.retrieve_latin_alphabet --style han_serif
# handwritten
PYTHONPATH=src python -m refactored.scripts.retrieve_latin_alphabet --style handwritten

# Font generation
cd ../../../..
python src/main.py -t han_serif
python src/main.py -t handwritten

# 6. 🎯 Integration: Run complete test suite
python -m pytest tests/ --cov=src

# 7. ✅ Validation: Ensure no regression
python -m pytest tests/integration/test_complete_pipeline.py
```

## Build Commands

### Font Generation

#### Legacy Version

```bash
# Generate han_serif font
python3 src/main.py -t han_serif

# Generate handwritten font
python3 src/main.py -t handwritten

# Measure build process time
time python3 src/main.py
```

#### Refactored Version

```bash
# Generate han_serif font
PYTHONPATH=src python -m refactored.cli.main -t han_serif

# Generate handwritten font
PYTHONPATH=src python -m refactored.cli.main -t handwritten
```

### Dependency Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install external dependencies (macOS)
brew tap caryll/tap
brew install otfcc-mac64
brew install jq
```

### Pattern Table Generation

```bash
# Generate polyphone pattern table
cd res/phonics/duo_yin_zi/scripts
python3 make_pattern_table.py
```

### Python

```bash
pyenv global 3.11.2
pip install -r requirements.txt
```

## Development Environment Setup

### Install Development Dependencies

```bash
# Install development and testing tools
$ pip install -r requirements-dev.txt
```

### Development Support Tools Used

#### Code Quality & Formatting

- **black** (>=22.0.0) - Code formatter
- **isort** (>=5.0.0) - Import statement organizer
- **flake8** (>=5.0.0) - Python linter
- **mypy** (>=1.0.0) - Type checker

#### Security

- **bandit** (>=1.7.0) - Security vulnerability detection

#### Testing

- **pytest** (>=7.0.0) - Testing framework
- **pytest-cov** (>=4.0.0) - Coverage measurement
- **pytest-mock** (>=3.0.0) - Mock functionality
- **pytest-benchmark** (>=4.0.0) - Performance testing
- **pytest-watch** (>=4.2.0) - File watching test execution
- **hypothesis** (>=6.0.0) - Property-based testing

#### Git Hook Management

- **lefthook** - Git hook management (auto-execution on pre-commit/pre-push)

### VS Code Configuration

When using VS Code, the following extensions are recommended:

```bash
# Recommended extensions (defined in .vscode/extensions.json)
- ms-python.black-formatter  # Black code formatter
- ms-python.isort           # Import statement organizer
- ms-python.flake8          # Linter
- ms-python.mypy-type-checker # Type checker
- streetsidesoftware.code-spell-checker # Spell checker
```

The project includes `.vscode/settings.json` with the following automatic configuration:

- Auto-format on save (Black + isort)
- Python 3.11 compatible type annotation settings
- Formatters configured to use environment tools

### Code Formatting Configuration

- **Black**: Code formatter (88 character width, auto-format)
- **isort**: Import statement organizer (Black-compatible profile)
- **flake8**: Code linter (.flake8 configuration file)
- **Configuration files**: `pyproject.toml`, `.flake8`
- **VS Code integration**: Auto-format on save

### Spell Check Configuration

- **VS Code integration**: Real-time spell checking (Code Spell Checker extension)
- **Configuration files**: `.vscode/settings.json`, `cspell.json`
- **Scope**: `src/`, `tests/`, `*.md` files

### VS Code Integration

**Automatic Setup**:

1. Install Code Spell Checker extension (included in recommended extensions)
2. Project settings are automatically applied

**VS Code Configuration Files**:

- `.vscode/settings.json` - Workspace settings and project-specific words
- `cspell.json` - Code Spell Checker detailed configuration
- `.vscode/extensions.json` - Recommended extensions

### Git Hooks (Lefthook)

For development quality management, Lefthook can be used to set up Git hooks:

```bash
# Install Lefthook (macOS)
$ brew install lefthook

# Enable Git hooks
$ lefthook install

# Verify configuration
$ lefthook version
```

Configured hooks:

- **pre-commit**: Code formatting (Black + isort), linting (flake8), security checks
- **pre-push**: Core functionality tests (unit + security)

### Development Workflow

```bash
# Automatically executed before commit:
# - Python code formatting (isort + black)
# - Python syntax checking
# - Python linting (flake8)
# - Security checks (shell=True detection, etc.)

# Automatically executed before push:
# - Core functionality tests (unit + security)

# Spell checking is integrated with VS Code for real-time checking

# Manual formatting execution
black src/ tests/
isort src/ tests/
flake8 src/ tests/

# Manual hook testing
lefthook run pre-commit
lefthook run pre-push
```

### otfcc

[otfcc](https://github.com/caryll/otfcc) is lightweight and support IVS

### jq

[jq](https://stedolan.github.io/jq/) can mangle the data format that you have into the one that you want with very little effort

### mac only

```shell
# Install Xcode by mas-cli
$ mas install 497799835
# Note: Xcode initially gets an error because the [Command line Tools:] list box is blank.
# The following solutions will fix this problem.
# Refer to [エラー：xcode-select: error: tool 'xcodebuild' requires Xcode, but active developer directory '/Library/Developer/CommandLineTools' is a command line tools instance](https://qiita.com/eytyet/items/59c5bad1c167d5addc68)

# Install otfcc
$ brew tap caryll/tap
$ brew install otfcc-mac64
```

## Generation procedure

1. Making a homograph dictionary (optional)

   [Details](../res/phonics/duo_yin_zi/README_EN.md)

   ```bash
   cd <PROJECT-ROOT>/res/phonics/duo_yin_zi/scripts/
   python make_pattern_table.py
   ```

2. Make a Unicode table of the target Chinese characters (optional)

   [Details](../res/phonics/unicode_mapping_table/README_EN.md)

   ```bash
   cd <PROJECT-ROOT>/res/phonics/unicode_mapping_table/
   python make_unicode_pinyin_map_table.py
   ```

3. Dump the base font to an editable file (json)

   The glyf table is too large and inconvenient to browse, so it should be separated from the other tables.

   ### Font Dump (Legacy Version)

   ```bash
   $ cd <PROJECT-ROOT>
   $ python src/make_template_jsons.py <BASE-FONT-NAME>
   # e.g.:
   # python src/make_template_jsons.py ./res/fonts/han-serif/SourceHanSerifCN-Regular.ttf
   ```

   ### Font Dump (Refactored Version)

   ```bash
   $ cd <PROJECT-ROOT>
   # han-serif
   $ PYTHONPATH=src python -m refactored.scripts.make_template_jsons --style han_serif
   # handwritten
   $ PYTHONPATH=src python -m refactored.scripts.make_template_jsons --style handwritten
   ```

4. Extraction of Latin characters for pinyin display

   **Note: Fixed-width Latin alphabet fonts only**

   ### Character Extraction (Legacy Version)

   ```bash
   $ cd <PROJECT-ROOT>
   $ python src/retrieve_latin_alphabet.py <FONT-NAME-FOR-PINYIN>
   # e.g.:
   # python src/retrieve_latin_alphabet.py ./res/fonts/han-serif/mplus-1m-medium.ttf
   ```

   ### Character Extraction (Refactored Version)

   ```bash
   $ cd <PROJECT-ROOT>
   # han-serif
   $ PYTHONPATH=src python -m refactored.scripts.retrieve_latin_alphabet --style han_serif
   # handwritten
   $ PYTHONPATH=src python -m refactored.scripts.retrieve_latin_alphabet --style handwritten
   ```

5. Build the font

   ```bash
   cd <PROJECT ROOT>
   ```

   ### Build (Legacy Version)

   ```bash
   time python src/main.py --style han_serif
   ```

   or

   ```bash
   time python src/main.py --style handwritten
   ```

   ### Build (Refactored Version)

   ```bash
   time PYTHONPATH=src python -m refactored.cli.main -t han_serif
   ```

   or

   ```bash
   time PYTHONPATH=src python -m refactored.cli.main -t handwritten
   ```

   ### Docker Version (Complete Pipeline)

   ```bash
   $ cd <PROJECT ROOT>
   # Generate han_serif font only
   $ docker-compose -f docker/docker-compose.yml up pipeline-han-serif

   # Generate handwritten font only
   $ docker-compose -f docker/docker-compose.yml up pipeline-handwritten

   # Generate both fonts
   $ docker-compose -f docker/docker-compose.yml up pipeline-all
   ```

## Technical Notes

### How to set the canvas size of the pinyin display area

![Pinyin display area size configuration diagram](../imgs/outline.png)

```json
    METADATA_FOR_PINYIN = {
        "pinyin_canvas":{
            "width"    : 850,   # The width of the canvas.
            "height"   : 283.3, # The height of the canvas.
            "base_line": 935,   # The height from the bottom of the Chinese character canvas to pinyin canvas.
            "tracking" : 22.145 # Character spacing in the pinyin display area (Tracking is about uniform spacing across a text selection).
        },
        "expected_hanzi_canvas":{
            "width" : 1000, # Expected Width of the Chinese character canvas.
            "height": 1000, # Expected height of the Chinese character canvas.
        }
    }
```

refer to [pinyin_glyph.py](https://github.com/MaruTama/Mengshen-pinyin-font/blob/e5d6e9e1770d849d6c17016683faf7c04d028473/src/pinyin_glyph.py#L10-L13), [config.py](https://github.com/MaruTama/Mengshen-pinyin-font/blob/e5d6e9e1770d849d6c17016683faf7c04d028473/src/config.py#L11-L41)

### Componentization of the glyfs

glyf can be componentized and referenced.
You can reduce the volume by reusing them, and since they are placed by affine transformation, you can easily set their size and position.

Reference usage examples:

```json
"cid48219": {
  "advanceWidth": 2048,
  "advanceHeight": 2628.2,
  "verticalOrigin": 1803,
  "references": [
    {
      "glyph": "arranged_ji1", "x": 0, "y": 0, "a": 1, "b": 0, "c": 0, "d": 1
    },
    {
      "glyph": "cid48219.ss00", "x": 0, "y": 0, "a": 1, "b": 0, "c": 0, "d": 1
    }
  ]
},
```

[Apple-The 'glyf' table](https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6glyf.html)
> The transformation entries determine the values of an affine transformation applied to the component prior to its being incorporated into the parent glyph. Given the component matrix [a b c d e f], the transformation applied to the component is:

In the reference, a-d is the value of the affine transformation.
In this tool, using a,d (scale) and x,y (move).

```math
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
 ```

<!-- Ref.[extract rotation, scale values from 2d transformation matrix](https://stackoverflow.com/questions/4361242/extract-rotation-scale-values-from-2d-transformation-matrix)
Matrix can calculate the scale, rotation, and shift at one time by raising the dimension.   -->

> [!CAUTION]
> For unknown reasons, otfccbuild or OpenType specification causes glyphs to disappear if `a` and `d` have the same value. As long as the sizes are slightly different, it will be reflected, so for 90% scaling, set `a=0.9, d=0.91`.
>
> Refer to [pinyin_glyph.py](https://github.com/MaruTama/Mengshen-pinyin-font/blob/e5d6e9e1770d849d6c17016683faf7c04d028473/src/pinyin_glyph.py#L148-L154)

### feature tag

`aalt` is set to display the alternative characters.

- `aalt_0` is set to "gsub_single". In use case, a symbol character and when the pronunciation changes only one Chinese character.
- `aalt_1` is set to `gsub_alternate`. In use case, When the pronunciation changes more than two Chinese characters.

`rclt` is used for homograph substitution.
This feature is used for chaining contextual substitution

- `pattern one` is pattern of the pronunciation changes only one Chinese character.
- `pattern two` is pattern of the pronunciation changes more than two Chinese characters.
- `exception pattern` is pattern of the duplicates that affect phrases of pattern one or two.
  [to details](../res/phonics/duo_yin_zi/README_EN.md)

## Specifications (Constraints)

- This font assumes horizontal writing only
- The glyf table can only store up to 65536
- The glyf table is large, save it as another json
- Duplicately defined Chinese characters refer to the same glyph to reduce the number of glyphs.
 (⺎:U+2E8E, 兀:U+5140, 兀:U+FA0C and 嗀:U+55C0, 嗀:U+FA0D )
- The only font that can be used as a glyf is Fixed-width latin alphabet only
- The json of the standard python library becomes bloated and slow when converted to dict, so use [orjson](https://github.com/ijl/orjson)
    Refer to [Choosing a faster JSON library for Python](https://pythonspeed.com/articles/faster-json-library/),
    [PythonのJSONパーサのメモリ使用量と処理時間を比較してみる](https://postd.cc/memory-use-and-speed-of-json-parsers/)
- ssNN range from ss00 - 20
    Refer to [Tag: 'ss01' - 'ss20'](https://docs.microsoft.com/en-us/typography/opentype/spec/features_pt#-tag-ss01---ss20)
- Chinese Pinyin is simplified in the glyf table (yī -> yi1)
- Exclude the specific pronunciations(e.g: 呣 m̀, 嘸 m̄) as that is not included in unicode

- [overwrite.txt](/res/phonics/unicode_mapping_table/overwrite.txt) has been added phrase for various purposes
    1. Register Pinyin that can not be acquired by pypinyin
    2. Adjust the priority of pronunciation
    3. Add the pronunciation of the "儿" as "r"
    4. Add light tone(轻声), Integrate pronounce of the duplicate Chinese characters
    5. Exclude the specific pronunciations(e.g: 呣 m̀, 嘸 m̄)

- IVS responds as follows:

| code | Pinyin glyf |
| ---: | :--- |
| 0xE01E0 | None. Chinese character only |
| 0xE01E1 | With the standard pronunciation |
| 0xE01E2 | With the variational pronunciation |

- The correspondence between ssNN and Pinyin is as follows:

    -> If you don't put the standard pronunciation in ssNN, GSUB will immediately return to the original state when reverting to the standard reading in cmap_uvs.
       Therefore, prepare a glyph for reverting to the standard pronunciation in ss01.

| Naming Rules | glyf type |
| :--- | :--- |
| hanzi_glyf | Chinese character glyf with the standard pronunciation |
| hanzi_glyf.ss00 | Chinese character glyf without Pinyin. Pinyin can be changed by simply changing the IVS code. |
| hanzi_glyf.ss01 | (When Chinese character has the variational pronunciation) Chinese character glyf with the standard pronunciation (duplicates with hanzi_glyf, but replaces it by overriding GSUB replacements) |
| hanzi_glyf.ss02 | (When Chinese character has the variational pronunciation) After that, Chinese character glyf with the variational pronunciation |

- The name of the lookup table is free, but it obeys the following rules to reveal the reference source

| lookup table name | reference source |
| ---: | :--- |
| lookup_pattern_0N | pattern one |
| lookup_pattern_1N | pattern two |
| lookup_pattern_2N | exception pattern |

- The order of 1~n in [duoyinzi_pattern_one.txt](../outputs/duoyinzi_pattern_one.txt) follows [marged-mapping-table.txt](../outputs/marged-mapping-table.txt), If order is 1 as the standard reading. Is order sequence match with ss0N.

e.g.:

```csv
U+5F3A: qiáng,qiǎng,jiàng  #强
```

```csv
1, 强, qiáng, [~调|~暴|~度|~占|~攻|加~|~奸|~健|~项|~行|~硬|~壮|~盗|~权|~制|~盛|~烈|~化|~大|~劲]
2, 强, qiǎng, [~求|~人|~迫|~辩|~词夺理|~颜欢笑]
3, 强, jiàng, [~嘴|倔~]
```

- lookup rclt summarizes the reading pattern by. `rclt0` is `pattern one`.  `rclt1` is `pattern two`。 `rclt2` is `exception pattern`.
- [duoyinzi_pattern_two.json](../outputs/duoyinzi_pattern_two.json) and [duoyinzi_exceptional_pattern.json](../outputs/duoyinzi_exceptional_pattern.json) a notation similar to [Glyphs](https://glyphsapp.com/) and [OpenType™ Feature File](http://adobe-type-tools.github.io/afdko/OpenTypeFeatureFileSpecification.html#5.f)
- ignore tag specifies the phrase to be affected. And attach a single quote to a specific character that is affected.
    Refer to ignore tag in [duoyinzi_exceptional_pattern.json](../outputs/duoyinzi_exceptional_pattern.json).

## Terminology Used

![Typography terminology diagram](../imgs/terminology.png)

## Collection of Chinese Characters Not Found in `pypinyin`

[FIX_PINYIN.md](./FIX_PINYIN.md)

## References

## Heteronyms ([多音字](https://zh.wikipedia.org/wiki/%E5%A4%9A%E9%9F%B3%E5%AD%97))

- [中国語の多音字辞典（Chinese Duoyinzi Dictionary）](https://dokochina.com/duoyinzi.htm)
- [ユーウェン中国語講座 - 多音字](https://yuwen.zaich.com/intermediate/duoyinzi)
- [常用多音字表](http://xh.5156edu.com/page/18317.html)
- [104个汉字多音字一句话总结](http://news.sina.com.cn/c/2017-03-19/doc-ifycnikk1155875.shtml)

## Dictionary Sites

- [baidu汉语](https://hanyu.baidu.com/)
- [汉典](https://www.zdic.net/)

## Opentype Specification

- [OpenType™ Feature File Specification](http://adobe-type-tools.github.io/afdko/OpenTypeFeatureFileSpecification.html#5f-gsub-lookuptype-6-chaining-contextual-substitution)
- [西暦表記を元号による表記にするフォント](http://mottainaidtp.seesaa.net/article/425166883.html)
- [IVD/IVSとは](https://mojikiban.ipa.go.jp/1292.html)
- [OpenType フォント・フォーマット](https://aznote.jakou.com/prog/opentype/index.html)
