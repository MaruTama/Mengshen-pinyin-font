# Mengshen Pinyin Font（萌神拼音フォント）

OSS の多音字に対応した拼音フォント及びその作成ツールです。

[![version](https://img.shields.io/badge/Version-v2.0.0-brightgreen.svg)](https://github.com/MaruTama/Mengshen-pinyin-font/releases/tag/v20250816-153246)
![updated](https://img.shields.io/badge/Updated-Aug_16,_2025-green.svg)

> 英語・中国語版: [README.md](./README.md)

----

## 目次

- [フォントのプレビュー](#フォントのプレビュー)
- [特徴](#特徴)
- [フォントの種類](#フォントの種類)
- [ダウンロード](#ダウンロード)
- [インストール方法](#インストール方法)
- [使用例](#使用例)
- [多音字の仕組み](#多音字の仕組み)
- [各OSでの動作](#各osでの動作)
- [ガイド](#ガイド)
- [対応多音字一覧](#対応多音字一覧)
- [生成方法](#生成方法)
- [プロジェクトについて](#プロジェクトについて)
- [謝辞](#謝辞)
- [カンパ](#カンパ)

----

## フォントのプレビュー

![explain_han_serif](./imgs/explain_han_serif.png)
![explain_handwritten](./imgs/explain_handwritten.png)
![characteristic_point](./imgs/characteristic_point.png)

----

## 特徴

日本語・簡体字・繁体字の表示に対応したフォントです。
簡体字・繁体字には拼音（ピンイン）を自動で付与します。
多音字（同じ文字で複数の発音がある漢字）は、文脈に応じて自動的に読みを切り替えます。
中国語・日本語の学習者を主な対象としています。

- 16,026字の漢字に拼音を自動付与
- 多音字を文脈で自動切替
- IVS で手動切替も可能
- 簡体字・繁体字・日本語漢字・ひらがな・カタカナに対応
- 2スタイル（宋体・手書き）

----

## フォントの種類

| バリアント | スタイル | ベースフォント |
| :-: | :-: | :-: |
| Mengshen-HanSerif | 宋体 | Source Han Serif + M+ M Type-1 |
| Mengshen-Handwritten | 手書き | Xiaolai Font + SetoFontSP |

----

## ダウンロード

**[Download/下载](https://github.com/MaruTama/Mengshen-pinyin-font/releases)**

----

## インストール方法

- [macOS](https://support.apple.com/en-us/HT201749)
- [Windows](https://support.microsoft.com/en-us/help/314960/how-to-install-or-remove-a-font-in-windows)
- [Linux/Unix-based systems](https://github.com/adobe-fonts/source-code-pro/issues/17#issuecomment-8967116)
- [Android](./docs/HOW_TO_APPLY_FONT_ON_ANDROOID.md)

----

## 使用例

微博、Netflix、歌詞、ニュース、MS Word などでご利用いただけます。

[Language Learning with Netflix](https://chrome.google.com/webstore/detail/language-learning-with-ne/hoombieeljmmljlkjmnheibnpciblicm?hl=en) と組み合わせることで、字幕に漢字と拼音を同時表示できます。

![An-example-of-how-to-use](./imgs/An-example-of-how-to-use.png)

- [Microsoft Word での設定](./docs/MICROSOFT_WORD_SETUP.md)

----

## 多音字の仕組み

多音字をサポートするため、OpenType の文脈置換（GSUB テーブルの "rclt" 機能）を実装しています。
また、Unicode IVS（表意文字バリアントセレクター）で手動切替も可能です。
詳細は [IVS セットアップガイド](./docs/IVS_SETUP_GUIDE.md) を参照してください。

![using_contextual_replacing](./imgs/using_contextual_replacing.gif)
![using_ideographic_variant_selector](./imgs/using_ideographic_variant_selector.gif)

----

## 各OSでの動作

|プラットフォーム|自動拼音切替（文脈置換）|手動拼音切替（IVS）|備考|
|:-:|:-:|:-:|:-:|
|Windows|<video src="https://github.com/user-attachments/assets/7478707f-091b-43e5-ab6f-117281ba67ee">お使いのブラウザは video タグに対応していません。</video>|<video src="https://github.com/user-attachments/assets/19b9a839-2504-4f44-96ea-ec28b3836865">お使いのブラウザは video タグに対応していません。</video>|[IME パッドで IVS 入力](./docs/IVS_SETUP_GUIDE.md)|
|Mac|<video src="https://github.com/user-attachments/assets/9d791b54-76f4-43ba-bd1b-dd5db270bf5b">お使いのブラウザは video タグに対応していません。</video>|<video src="https://github.com/user-attachments/assets/62c5567e-5ba0-48b0-b196-fd3db5322dae">お使いのブラウザは video タグに対応していません。</video>|[文字ビューアで IVS 入力](./docs/IVS_SETUP_GUIDE.md)|
|Android|![android-chrome-rclt](imgs/android-chrome-rclt.png)|-|・[zFont 設定ガイド](./docs/HOW_TO_APPLY_FONT_ON_ANDROOID.md) ・[Magisk モジュール](https://github.com/MaruTama/magisk-module-mengshen-font)（root 必要、IVS は Chrome のみ対応）|

----

## ガイド

| ドキュメント | 日本語 | English |
| :-: | :-: | :-: |
| フォントの生成方法 | [日本語](./docs/HOW_TO_MAKE_JP.md) | [English](./docs/HOW_TO_MAKE_EN.md) |
| IVS 手動切替ガイド | - | [English](./docs/IVS_SETUP_GUIDE.md) |
| Word での設定 | - | [English](./docs/MICROSOFT_WORD_SETUP.md) |
| Android へのインストール | - | [English](./docs/HOW_TO_APPLY_FONT_ON_ANDROOID.md) |

----

## 対応多音字一覧

- [対応多音字一覧](./docs/DUOYINZI_DICTIONARY.md)

----

## 生成方法

```bash
# Dockerでの生成（推奨）
docker-compose -f docker/docker-compose.yml up pipeline-han-serif
docker-compose -f docker/docker-compose.yml up pipeline-handwritten
```

詳細は [フォント生成ガイド（日本語）](./docs/HOW_TO_MAKE_JP.md) を参照してください。

----

## プロジェクトについて

私達は中国語の学習や普及を目的としているグループです。

- [萌神PROJECT](https://mengshen-project.com/)
- [「萌神フォント」誕生しました！](https://note.com/geekzhongwen/n/n7a6f26a885d1)
- [「萌神フォント」Ver.2ができました！](https://note.com/geekzhongwen/n/nf9552d4bdf66)
- [メイカーのための中国語入門 フォント指定だけで拼音がつく萌神フォント開発秘話編](https://booth.pm/ja/items/1888270)

----

## 謝辞

以下の方々・リポジトリに感謝します。

- [@NightFurySL2001](https://github.com/NightFurySL2001)-san
- [@lanyizi](https://github.com/lanyizi)-san
- [BPMF IVS](https://github.com/ButTaiwan/bpmfvs)
- [kose-font](https://github.com/lxgw/kose-font)
- [SetoFontSP](https://ja.osdn.net/projects/setofont/releases/p14368)
- [Source-Han-TrueType](https://github.com/Pal3love/Source-Han-TrueType)
- [M+ M Type-1](https://mplus-fonts.osdn.jp/about.html)

----

## カンパ

[点击进入打赏页面](./docs/DONATE.md)
