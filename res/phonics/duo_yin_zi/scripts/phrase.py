# -*- coding: utf-8 -*-
#!/usr/bin/env python

class Phrase:
    def __init__(self, phrase, string_pinyin, normal_pronunciations=[]):
        self.phrase          = phrase
        self.string_pinyin   = string_pinyin.rstrip('\n')
        self.normal_pronunciations = normal_pronunciations

    def get_name(self):
        return self.phrase

    def get_string_pinyin(self):
        return self.string_pinyin
    
    def get_list_pinyin(self):
        return self.string_pinyin.split('/')

    def get_normal_pronunciations(self):
        return self.normal_pronunciations