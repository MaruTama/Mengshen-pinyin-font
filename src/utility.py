# -*- coding: utf-8 -*-
#!/usr/bin/env python

SIMPLED_ALPHABET = {
    "a":"a", "ā":"a1", "á":"a2", "ǎ":"a3", "à":"a4",
    "b":"b",
    "c":"c",
    "d":"d",
    "e":"e", "ē":"e1", "é":"e2", "ě":"e3", "è":"e4",
    "f":"f",
    "g":"g",
    "h":"h",
    "i":"i", "ī":"i1", "í":"i2", "ǐ":"i3", "ì":"i4",
    "j":"j",
    "k":"k",
    "l":"l",
    "m":"m", "m̄":"m1", "ḿ":"m2", "m̀":"m4",
    "n":"n",           "ń":"n2", "ň":"n3", "ǹ":"n4",
    "o":"o", "ō":"o1", "ó":"o2", "ǒ":"o3", "ò":"o4",
    "p":"p",
    "q":"q",
    "r":"r",
    "s":"s",
    "t":"t",
    "u":"u", "ū":"u1", "ú":"u2" ,"ǔ":"u3", "ù":"u4", "ü":"v", "ǖ":"v1", "ǘ":"v2", "ǚ":"v3", "ǜ":"v4",
    "v":"v",
    "w":"w",
    "x":"x",
    "y":"y",
    "z":"z"
}


# ピンイン表記の簡略化、e.g.: wěi -> we3i
def simplification_pronunciation(pronunciation):
    return  "".join( [SIMPLED_ALPHABET[c] for c in pronunciation] )