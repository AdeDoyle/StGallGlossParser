"""Level 2."""

from OpenXlsx import list_xlsx
from SaveXlsx import save_xlsx
import math


gloss_heads = ["recordID", "book", "subsection", "code", "ms_ref", "ms_num", "keil_vol", "keil_page", "keil_line",
               "types", "text", "thesaurus_ref", "irish", "keil_ref", "thesaurus_page", "translation", "has_analysis"]
gloss_keeplist = ["recordID", "ms_ref", "text", "thesaurus_ref", "irish", "translation", "has_analysis"]
gloss_droptup = ("book", "subsection", "code", "ms_num", "keil_vol", "keil_page", "keil_line", "types",
                 "keil_ref", "thesaurus_page")

word_heads = ["recordID", "glossID", "word_instance", "headword", "DIL_headword", "wordclass", "subclass", "breakdown",
              "meaning", "submeaning", "analysis", "mutation", "voice", "rel", "dep", "old_recordID",
              "word_instance_index", "headword_index"]
word_keeplist = ["glossID", "word_instance", "wordclass", "subclass", "meaning", "analysis", "voice", "rel"]
word_droptup = ("recordID", "headword", "DIL_headword", "breakdown", "submeaning", "mutation",
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
                else:
                    tempi.append(j)
            except TypeError:
                tempi.append(j)
        templist.append(tempi)
    return templist


# Gets only required fields from gloss spreadsheet, puts them in preferable order, removes replaces NaN instances
glosslist = [gloss_keeplist] + list_xlsx("glosses_full", "glosses", gloss_droptup)
glosslist = [[g[0], g[1], g[3], g[2], g[5], g[4], g[6]] for g in glosslist]
glosslist = clean_nan(glosslist)
# Gets only required fields from analysis spreadsheet, puts them in preferable order, removes replaces NaN instances
wordlist = [word_keeplist] + list_xlsx("glosses_words", "words", word_droptup)
wordlist = [[w[0], w[1], w[4], w[2], w[3], w[5], w[6], w[7]] for w in wordlist]
wordlist = clean_nan(wordlist)
# Identifies all gloss numbers that have been analysed, stores in recordnumlist, then sorts list
recordnumlist = list()
for record in wordlist:
    recnum = record[0]
    if recnum not in recordnumlist:
        recordnumlist.append(recnum)
recordnumlist = sorted(recordnumlist[1:])
# Identifies all glosses not analysed and removes them from glosslist
nonglossnumlist = list(i[0] for i in glosslist[1:] if i[0] not in recordnumlist)
glosslist = list(i for i in glosslist if i[0] not in nonglossnumlist)
# Combines data from glosslist with related info from analysis list in one combined list
combolist = [['GlossNo', 'Token', 'Meaning', 'POS', 'sub_POS', 'Analysis', 'Voice', 'Relative',
              "GlossText", "GlossTranslation"]]
for analysis in wordlist:
    wordnum = analysis[0]
    for gloss in glosslist:
        glossnum = gloss[0]
        if glossnum == wordnum:
            combolist.append(analysis + gloss[3:5])
            break


# for i in glosslist[:5]:
#     print(i)
#
# for i in wordlist[:25]:
#     print(i)
#
# for i in combolist[:25]:
#     print(i)
#
# save_xlsx("SG. Combined Data", combolist, True)

