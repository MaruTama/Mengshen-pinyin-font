# Mengshen(萌神)-pinyin(拼音)-font

OSS の多音字に対応した拼音フォント及びその作成ツールです。 / OpenSource Pinyin font and creation tool that supports homograph (多音字).

**[Download/下载](https://github.com/MaruTama/pinyin-font-tools/releases)**
<!-- [![Download/下载](https://img.shields.io/badge/Download-↓-yellow.svg)](https://github.com/MaruTama/pinyin-font-tools/releases)   -->

[![version](https://img.shields.io/badge/Version-v2.0.0-brightgreen.svg)](https://github.com/MaruTama/Mengshen-pinyin-font/releases/tag/v20250816-153246)
![updated](https://img.shields.io/badge/Updated-Aug_16,_2025-green.svg)

![explain_han_serif](./imgs/explain_han_serif.png)
![explain_handwritten](./imgs/explain_handwritten.png)
![characteristic_point](./imgs/characteristic_point.png)

私達は中国語の学習や普及を目的としているグループです。/ We are a group dedicated to learning and promoting the Chinese language.

- [萌神PROJECT](https://mengshen-project.com/)
- [「萌神フォント」誕生しました！](https://note.com/geekzhongwen/n/n7a6f26a885d1)
- [「萌神フォント」Ver.2ができました！](https://note.com/geekzhongwen/n/nf9552d4bdf66)
- [メイカーのための中国語入門 フォント指定だけで拼音がつく萌神フォント開発秘話編](https://booth.pm/ja/items/1888270)

----

## 目的 / Purpose

基本的な日本語、簡体字、繁体字を表示できるフォントであり、
簡体字と繁体字には拼音を併記するフォントの作成です。/
This fonts can display basic Japanese, Simplified Chinese and Traditional Chinese, and We created a font that includes Chinese romanization for both Simplified and Traditional chinese characters.

----

### 想定利用者 / Target User

日本語、中国語の学習者 / Japanese and Chinese language learners

----

## フォントのインストール方法 / Font Installation Instructions

- [macOS](https://support.apple.com/en-us/HT201749)
- [Windows](https://support.microsoft.com/en-us/help/314960/how-to-install-or-remove-a-font-in-windows)
- [Linux/Unix-based systems](https://github.com/adobe-fonts/source-code-pro/issues/17#issuecomment-8967116)
- [Android](./docs/HOW_TO_APPLY_FONT_ON_ANDROOID.md)

----

## 使用例 / Use Case

e.g. 微博, Netflix, Lyrics, News and MS Word etc.

Improve your skills on your own, effectively and enjoyably, by watching films and series in the language you study.
Subtitles are shown Chinese characters and pinyin.
[Language Learning with Netflix](https://chrome.google.com/webstore/detail/language-learning-with-ne/hoombieeljmmljlkjmnheibnpciblicm?hl=en)
![An-example-of-how-to-use](./imgs/An-example-of-how-to-use.png)

- [Microsoft Word Setup for Homograph Features](./docs/MICROSOFT_WORD_SETUP.md)

----

## 技術的要素 / Technical Elements

多音字をサポートするためにコンテキスト置換(feature tag of "rclt" at GSUB)を実装しました。
また、Unicode IVS（表意文字バリアントセレクター）を使用して、異なる拼音に切り替えることもできます。/
Implemented contextual replacing to support homograph (多音字).
You can also use Unicode IVS (ideographic variant selector) to switch other different pinyin.  
![using_contextual_replacing](./imgs/using_contextual_replacing.gif)
![using_ideographic_variant_selector](./imgs/using_ideographic_variant_selector.gif)

## 各OSでの動作 / Works on each OS

|Platform|Automatic pinyin switching (using Contextual Replacement)|Manual pinyin switching (using IVS)|Notes|
|:-:|:-:|:-:|:-:|
|Windows|<video src="https://github.com/user-attachments/assets/7478707f-091b-43e5-ab6f-117281ba67ee">|<video src="https://github.com/user-attachments/assets/19b9a839-2504-4f44-96ea-ec28b3836865">|Use [IME Pad for IVS](./docs/IVS_SETUP_GUIDE.md)|
|Mac|<video src="https://github.com/user-attachments/assets/9d791b54-76f4-43ba-bd1b-dd5db270bf5b">|<video src="https://github.com/user-attachments/assets/62c5567e-5ba0-48b0-b196-fd3db5322dae">|Use [Character Viewer for IVS](./docs/IVS_SETUP_GUIDE.md)|
|Android|![android-chrome-rclt](imgs/android-chrome-rclt.png)|-|・[zFont Setup Guide](./docs/HOW_TO_APPLY_FONT_ON_ANDROOID.md) </br>・[Magisk module](https://github.com/MaruTama/magisk-module-mengshen-font) (root required, IVS works in Chrome only)|

----

## 対応している多音字の一覧 / List of Supported Homographs

- [supported homograph](./docs/DUOYINZI_DICTIONARY.md)

## 生成方法 / How to Make Fonts

- [日本語](./docs/HOW_TO_MAKE_JP.md)
- [English](./docs/HOW_TO_MAKE_EN.md)

## リファクタコード構成 / Refactored Code Architecture

プロジェクトは現在、レガシー版とリファクタ版の両方をサポートしています。リファクタ版は、モジュラー設計、型安全性、セキュリティ強化を特徴としています。

The project currently supports both legacy and refactored versions. The refactored version features modular design, type safety, and enhanced security.

### ディレクトリ構成 / Directory Structure

```shell
src/refactored/
├── __init__.py            # Package initialization and version
├── font_types.py          # Font type definitions and enums
├── cli/                   # Command Line Interface
│   ├── __init__.py
│   └── main.py           # CLI entry point with dependency injection
├── config/                # Configuration Management
│   ├── __init__.py
│   ├── font_config.py    # Font types, canvas settings, constants
│   ├── font_name_tables.py # Font naming and metadata
│   └── paths.py          # Project path management
├── data/                  # Data Processing Layer
│   ├── __init__.py
│   ├── character_data.py # Character and pronunciation management
│   ├── mapping_data.py   # Unicode to glyph mapping
│   └── pinyin_data.py    # Pinyin data handling
├── generation/            # Font Generation Core
│   ├── __init__.py
│   ├── font_assembler.py # Font assembly and metadata
│   ├── font_builder.py   # Main font construction orchestrator
│   └── glyph_manager.py  # Glyph generation and management
├── scripts/               # Build Scripts
│   ├── __init__.py
│   ├── make_template_jsons.py     # Font to JSON conversion
│   └── retrieve_latin_alphabet.py # Latin alphabet extraction
├── tables/                # OpenType Table Generation
│   ├── __init__.py
│   ├── cmap_manager.py   # Character mapping table management
│   └── gsub_table_generator.py # OpenType GSUB table generation
└── utils/                 # Utilities and Support
    ├── __init__.py
    ├── logging_config.py # Structured logging configuration
    ├── pinyin_utils.py   # Pinyin processing utilities
    ├── shell_utils.py    # Secure shell command execution
    └── version_utils.py  # Version management utilities
```

#### リファクタ版コマンド / Refactored Commands

```bash
# フォント生成 / Font generation
PYTHONPATH=src python -m refactored.cli.main -t han_serif
PYTHONPATH=src python -m refactored.cli.main -t handwritten

# Dockerでの生成（推奨） / Docker generation (recommended)
docker-compose -f docker/docker-compose.yml up pipeline-han-serif
docker-compose -f docker/docker-compose.yml up pipeline-handwritten
```

----

## 謝辞 / Acknowledgments

Thank you to the following people and repositories.

- [@NightFurySL2001](https://github.com/NightFurySL2001)-san
- [@lanyizi](https://github.com/lanyizi)-san
- [BPMF IVS](https://github.com/ButTaiwan/bpmfvs)
- [kose-font](https://github.com/lxgw/kose-font)
- [SetoFontSP](https://ja.osdn.net/projects/setofont/releases/p14368)
- [Source-Han-TrueType](https://github.com/Pal3love/Source-Han-TrueType)
- [M+ M Type-1](https://mplus-fonts.osdn.jp/about.html)

----

## カンパ/打赏/Donate

[点击进入打赏页面](./docs/DONATE.md)
