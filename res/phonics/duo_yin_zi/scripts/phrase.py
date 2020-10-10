# -*- coding: utf-8 -*-
#!/usr/bin/env python

class Phrase:
    def __init__(self, phrase, string_pinyin, default_pinyins=[]):
        self.phrase          = phrase
        self.string_pinyin   = string_pinyin.rstrip('\n')
        self.default_pinyins = default_pinyins

    def get_name(self):
        return self.phrase

    def get_string_pinyin(self):
        return self.string_pinyin
    
    def get_list_pinyin(self):
        return self.string_pinyin.split('/')

    def get_default_pinyins(self):
        return self.default_pinyins