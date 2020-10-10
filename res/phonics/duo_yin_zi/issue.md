The implementation we are considering is as follows:
Predefine a standard pinyin for each character.
Store the polysyllabic pattern in lookup table.
If the pattern matches, replace it with another glyph.



We think ["calt"](https://docs.microsoft.com/en-us/typography/opentype/spec/features_ae#tag-calt) is appropriate as a feature tag. ccmp, slat, and aalt also We believe it can be done, but it is not suitable.


The reason is follows:

1.  It can use ["Chaining contextual substitution (GSUB LookupType 6)"](http://adobe-type-tools.github.io/afdko/OpenTypeFeatureFileSpecification.html#5f-gsub-lookuptype-6-chaining-contextual-substitution).
2. The purpose is not a ligature, but a context-dependent character substitution.
Refer to [Syntax for OpenType features in CSS](https://helpx.adobe.com/fonts/user-guide.html/fonts/using/open-type-syntax.ug.html#calt)
> This feature, in specified situations, replaces default glyphs with alternate forms which provide better joining behavior. Like ligatures (though not strictly a ligature feature), contextual alternates are commonly used to harmonize the shapes of glyphs with the surrounding context.

3. Many environments are expected to support it.
(slat is not supported; aalt requires the user to select the replacement character.
Refer to [calt](https://docs.microsoft.com/en-us/typography/opentype/spec/features_ae#tag-calt)
> UI suggestion: This feature should be active by default.

4. Does not affect other GSUB feature
> Feature interaction: This feature may be used in combination with other substitution (GSUB) features, whose results it may override.

(5. Chinese is't ideographic scripts. I don't have to worry about following)
> Script/language sensitivity: Not applicable to ideographic scripts.

Implementation example

Statement of Expectations
行啊 => xíng a
★银行 => yín háng
★道行 => dào, héng
长城 => cháng chéng
★行长 => xíng zhǎng
(If you want the user to choose between "xíng zhǎng" or "háng cháng", I assume you can use aalt.)
☆了得 => liǎo de

Standard Pinyin
行 => xíng
长 => cháng
了 => le
得 => dé

```

# ★ Describes a substitution pattern for the different pinyin of "行".
lookup CNTXT_884C {
    substitute 银 行’ by 行.ha2ng;
    substitute 道 行’ by 行.he2ng;
} CNTXT_884C;
lookup CNTXT_957F {
    substitute 行 长' by 长.zha3ng;
} CNTXT_957F;

# ☆ Describes a substitution pattern for idiom.
lookup CNTXT_ 4E86_ 5F97 {
    substitute 了' 得 by 了.lia3o;
    substitute 了.lia3o 得’ by 得.de;
} CNTXT_884C_957F;

# Describe the context
feature calt {
    substitute 银' lookup CNTXT_884C 行’;
    substitute 道' lookup CNTXT_884C 行’;
    substitute 行' lookup CNTXT_957F 长’;
    substitute 了' lookup CNTXT_884C_957F 得’;
} calt;
```



Appendix

- [注音符號數位化顯示計畫](https://github.com/cmex-30/Bopomofo_on_Web)

I found an example on the web that uses OpenType Ruby tags.
I think it's an interesting example, like the IVS @NightFurySL2001 mentioned it.

> Recently there has been a repo that makes bopomofo with newer OpenType technology, [BPMF IVS](https://github.com/ButTaiwan/bpmfvs). It utilize the IVS (ideographic variant selector) in Unicode to change between different pinyin (eg providing 4 glyphs: zháo zhāo zhe zhuó for 着) and also put the variant glyphs in stylistic set (SS01-04). You can visit that repo and check how it works. BPMF IVS has a pinyin standard in bopomofo, so that all fonts generated with that program can be used interchangably without losing the tonal marks (if using IVD). Is it possible to recreate it in this program? (and maybe use the same pinyin standard, which will make conversion between bopomofo and hanyu pinyin a ton easier by just changing fonts)