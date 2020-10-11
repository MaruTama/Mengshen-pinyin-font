# -*- coding: utf-8 -*-
#!/usr/bin/env python

import pinyin_getter
import phrase as p

PINYIN_MAPPING_TABLE = pinyin_getter.get_pinyin_table_with_mapping_table()

class PhraseHolder:
    def __init__(self, PHRASE_TABLE_FILE):
        self.PINYIN_MAPPING_TABLE = pinyin_getter.get_pinyin_table_with_mapping_table()
        self.phrases = []
        with open(PHRASE_TABLE_FILE, mode='r', encoding='utf-8') as read_file:
            for line in read_file:
                [word, string_pinyin] = line.rstrip('\n').split(': ')                
                default_pinyins = []
                for charactor in word:
                    default_pinyins.append( self.__get_default_pinyin(charactor) )
                self.add_phrase( p.Phrase(word, string_pinyin, default_pinyins) )

    def add_phrase(self, p):
        self.phrases.append(p)

    def remove_phrase(self, phrase):
        del self.phrases[phrase]

    def __get_default_pinyin(self, hanzi=""):
        return self.PINYIN_MAPPING_TABLE[hanzi][0] if (hanzi in self.PINYIN_MAPPING_TABLE) else ""

    def get_list_instance_phrases(self):
        return self.phrases

    def get_all_phrases(self):
        return [phrase.get_phrase() for phrase in self.phrases]