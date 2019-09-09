"""Level 2."""

from OpenXlsx import list_xlsx
import math


gloss_heads = ["recordID", "book", "subsection", "code", "ms_ref", "ms_num", "keil_vol", "keil_page", "keil_line",
               "types", "text", "thesaurus_ref", "irish", "keil_ref", "thesaurus_page", "translation", "has_analysis"]
gloss_keeplist = ["ms_ref", "text", "thesaurus_ref", "irish", "translation", "has_analysis"]
gloss_droptup = ("recordID", "book", "subsection", "code", "ms_num", "keil_vol", "keil_page", "keil_line", "types",
                 "keil_ref", "thesaurus_page")

word_heads = ["recordID", "glossID", "word_instance", "headword", "DIL_headword", "wordclass", "subclass", "breakdown",
              "meaning", "submeaning", "analysis", "mutation", "voice", "rel", "dep", "old_recordID",
              "word_instance_index", "headword_index"]
word_keeplist = ["word_instance", "wordclass", "subclass", "meaning", "analysis", "voice", "rel"]
word_droptup = ("recordID", "glossID", "headword", "DIL_headword", "breakdown", "submeaning", "mutation",
                "dep", "old_recordID", "word_instance_index", "headword_index")


def clean_nan(somelist):
    """Replaces instances of nan (not a number) with False in a given list of lists"""
    templist = []
    for i in somelist:
        tempi = []
        for j in i:
            try:
                if math.isnan(j):
                    tempi.append(False)
            except TypeError:
                tempi.append(j)
        templist.append(tempi)
    return templist


glosslist = [gloss_keeplist] + list_xlsx("glosses_full", "glosses", gloss_droptup)
glosslist = [[g[0], g[2], g[1], g[4], g[3], g[5]] for g in glosslist]
glosslist = clean_nan(glosslist)
wordlist = [word_keeplist] + list_xlsx("glosses_words", "words", word_droptup)
wordlist = [[w[0], w[3], w[1], w[2], w[4], w[5], w[6]] for w in wordlist]
wordlist = clean_nan(wordlist)


# for i in glosslist[:5]:
#     print(i)
#
# for i in wordlist[:5]:
#     print(i)

