"""Level 2."""

from OpenXlsx import list_xlsx
from SaveXlsx import save_xlsx
import math
import re


gloss_heads = ["recordID", "book", "subsection", "code", "ms_ref", "ms_num", "keil_vol", "keil_page", "keil_line",
               "types", "text", "thesaurus_ref", "irish", "keil_ref", "thesaurus_page", "translation", "has_analysis"]
gloss_keeplist = ["recordID", "ms_ref", "text", "thesaurus_ref", "irish", "translation", "has_analysis"]
gloss_droptup = ("book", "subsection", "code", "ms_num", "keil_vol", "keil_page", "keil_line", "types",
                 "keil_ref", "thesaurus_page")

word_heads = ["recordID", "glossID", "word_instance", "headword", "DIL_headword", "wordclass", "subclass", "breakdown",
              "meaning", "submeaning", "analysis", "mutation", "voice", "rel", "dep", "old_recordID",
              "word_instance_index", "headword_index"]
word_keeplist = ["glossID", "word_instance", "wordclass", "subclass", "meaning", "analysis",
                 "voice", "rel", "headword_index"]
word_droptup = ("recordID", "headword", "DIL_headword", "breakdown", "submeaning", "mutation",
                "dep", "old_recordID", "word_instance_index")


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
fix_trans_list = list()
for i in glosslist:
    if i[4]:
        fix_trans_list.append(i)
    else:
        i[4] = "* no translation available *"
        fix_trans_list.append(i)
glosslist = fix_trans_list
# Gets only required fields from analysis spreadsheet, puts them in preferable order, removes replaces NaN instances
wordlist = [word_keeplist] + list_xlsx("glosses_words", "words", word_droptup)
wordlist = [[w[0], w[1], w[8], w[4], w[2], w[3], w[5], w[6], w[7]] for w in wordlist]
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
combolist = [['GlossNo', 'TPH_ref', 'Token', 'Headword', 'Meaning', 'POS', 'Sub_POS', 'Analysis', 'Voice', 'Relative',
              "GlossText", "GlossTranslation", "GlossHand"]]
for analysis in wordlist:
    wordnum = analysis[0]
    for gloss in glosslist:
        glossnum = gloss[0]
        if glossnum == wordnum:
            if gloss[2]:
                tph_ref = gloss[2].strip()
                if len(tph_ref) == 6:
                    tph_ref = f"{int(tph_ref[:3])}{tph_ref[3]}{int(tph_ref[4:])}"
                elif tph_ref in ["f.50 bottom marg. (TPH p.xx)",
                                 "f.52 top marg. (TPH p.xx)",
                                 "f.64a, not in Thesaurus Palaeohibernicus",
                                 "f.70 top marg. (TPH p.xx)",
                                 "f.110a not in Thesaurus Palaeohibernicus",
                                 "f.112 top marg. (TPH p.290)",
                                 "f.113b not in Thesaurus Palaeohibernicus",
                                 "f.114 top marg. (TPH p.xx)",
                                 "f.158 top marg. (TPH p.xx)",
                                 "f.159 top marg. (TPH p.xx)",
                                 "f.165 bottom marg. (TPH p.xxi)",
                                 "f.170 top marg. (TPH p.xxi)",
                                 "f.176 top marg. (TPH p.xxi)",
                                 "f.182 top marg. (TPH p.xxi)",
                                 "f.189 top marg. (TPH p.xxi)",
                                 "f.190 top marg. (TPH p.xxi)",
                                 "f.193 top marg. (TPH p.xxi)",
                                 "f.194 bottom marg. (TPH p.xxi)",
                                 "f.194 top marg. I (TPH p.xxi)",
                                 "f.194 top marg. II (TPH p.xxi)",
                                 "f.195 top marg. I (TPH p.xxi)",
                                 "f.195 top marg. II (TPH p.xxi)",
                                 "f.195 bottom marg. (TPH p.xxi)",
                                 "f.196 top marg. (TPH p.xxi)",
                                 "f.199 bottom marg. (TPH p.xxi)",
                                 "f.203 bottom marg. I (TPH p.xxi)",
                                 "f.203-204 bottom marg. (TPH p.290)",
                                 "f.203 bottom marg. II (TPH p.xxii)",
                                 "f.204 top marg. (TPH p.xxii)",
                                 "f.207 top marg. (TPH p.xxii)",
                                 "209b19–21",
                                 "f.210 bottom marg. (TPH p.xxii)",
                                 "f.211 bottom marg. (TPH p.xxii)",
                                 "f.213 top marg. (TPH p.xxii)",
                                 "f.214 top marg. (TPH p.xxii)",
                                 "f.217 bottom marg. (TPH p.xxii)",
                                 "f.219 top marg. I (TPH p.xxii)",
                                 "f.219 top marg. II (TPH p.xxii)",
                                 "f.220 top marg. (TPH p.xxii)",
                                 "f.223 top marg. (TPH p.xxii)",
                                 "f.226 top marg. (TPH p.xxii)",
                                 "f.228 top marg. (TPH p.xxii)",
                                 "f.229 top marg. (TPH p.290)",
                                 "f.231 top marg. (TPH p.xxii)",
                                 "f.233 top marg. (TPH p.xxii)",
                                 "f.247 top marg. (TPH p.xxii)",
                                 "f.248 top marg. (TPH p.xxii)"]:
                    pass
                else:
                    print(f"{gloss[2]}\nlength: {len(gloss[2])}")
                    raise RuntimeError()
            else:
                tph_ref = "Not in Thesaurus Palaeohibernicus"
            hand = "Main Glossator"
            if "+" in gloss[3]:
                hand = "Alternate Glossator"
            combolist.append([analysis[0]] + [tph_ref] + analysis[1:] + gloss[3:5] + [hand])
            break


def create_data_combo():
    save_xlsx("SG. Combined Data", combolist, True)
    return "Created file: 'SG. Combined Data.xlsx'"


# #                                             CREATE RESOURCES

# # Save a .xlsx file containing the combined data from glosses_full.xlsx and glosses_words.xlsx
# print(create_data_combo())

# #                                             TEST RESOURCES

# for i in glosslist[:5]:
#     print(i)
#
# for i in wordlist[:25]:
#     print(i)
#
# for i in combolist[:25]:
#     print(i)
