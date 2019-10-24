"""Level 1."""

from functools import lru_cache
from Pickle import open_obj, save_obj
from OpenXlsx import list_xlsx
from Clean_Glosses import clean_gloss, clean_word
import re


glossdict = open_obj("Clean_GlossDict.pkl")
glosslist = open_obj("Gloss_List.pkl")
worddict = open_obj("Clean_WordDict.pkl")
wordslist = open_obj("Words_List.pkl")
analyses = list_xlsx("SG. Combined Data", "Sheet 1")


def clean_analysis():
    pass


POS_list = ["AF", "BR", "CPL", "AID", "FRA", "ALT", "TSP", "DBR", "RFH", "CN", "NOD", "MBR",
            "UMR", "INT", "SNL", "BRS", "PNC"]


# # Collect lists of Bernhard's original POS-tags, levels 1-3, incl. verb information (active/passive and relativity)
# noA1 = list()
# testA1 = list()
# noA2 = list()
# testA2 = list()
# noA3 = list()
# testA3 = list()
# testActPas = list()
# testRel = list()
# lastnum = False
# for i in analyses:
#     glossnum = i[0]
#     word = worddict.get(i[1])
#     A1 = i[3]
#     A2 = i[4]
#     A3 = i[5]
#     vb_actpas = i[6]
#     vb_rel = i[7]
#     if not A1:
#         noA1.append(i)
#     elif A1.strip() not in testA1:
#         testA1.append(A1.strip())
#     if not A2:
#         noA2.append(i)
#     elif A2.strip() not in testA2:
#         testA2.append(A2.strip())
#     if not A3:
#         noA3.append(i)
#     elif A3.strip() not in testA3:
#         A3_clean = A3.strip()
#         if A3_clean[0] != "*":
#             testA3.append(A3.strip())
#     if vb_actpas:
#         testActPas.append(vb_actpas.strip())
#     if vb_rel:
#         testRel.append(vb_rel.strip())
#     # output = [word, A1, A2, A3, vb_actpas, vb_actpas]
#     # if glossnum == lastnum:
#     #     print(output)
#     # else:
#     #     lastnum = glossnum
#     # print(output)


# # Sort lists of Bernhard's original POS-tags, levels 1-3, as well as verb information (active/passive and relativity)
# # Save these sorted lists
# sorted_A1 = sorted(list(set(testA1)))
# # save_obj("A1 List", sorted_A1)
# sorted_A2 = sorted(list(set(testA2)))
# # save_obj("A2 List", sorted_A2)
# sorted_A3 = sorted(list(set(testA3)))
# # save_obj("A3 List", sorted_A3)
# sorted_actpas = sorted(list(set(testActPas)))
# sorted_rel = sorted(list(set(testRel)))


# # Test contents of POS tag-set and which entries have no tags.
# print("Entries, no A1: {}".format(len(noA1)))
# print("Unique A1 Types: {}".format(len(sorted_A1)))
#
# print("Entries, no A2: {}".format(len(noA2)))
# print("Unique A2 Types: {}".format(len(sorted_A2)))
#
# print("Entries, no A3: {}".format(len(noA3)))
# print("Unique A3 Types: {}".format(len(sorted_A3)))
#
# print("Unique Active/Passive Types: {}".format(len(sorted_actpas)))
# print("Unique Relativity Types: {}".format(len(sorted_rel)))


# for i in sorted_A1:
#     print(i)
# for i in noA1:
#     output = [i[1]] + i[3:8]
#     print(output)

# for i in sorted_A2:
#     print(i)
# for i in noA2:
#     output = [i[1]] + i[3:8]
#     print(output)

# for i in sorted_A3:
#     print(i)
# for i in noA3:
#     output = [i[1]] + i[3:8]
#     print(output)

# for i in sorted_actpas:
#     print(i)
# for i in sorted_rel:
#     print(i)


A1_list = open_obj("A1 List.pkl")


# Get all entries for a given POS-tag at any level
def findall_thistag(wordlist, tag, tag_level=1):
    tag_level = tag_level - 1
    taglist = list()
    for word_data in wordlist:
        entry_tag = word_data[3 + tag_level]
        if entry_tag == tag:
            taglist.append(word_data)
    return taglist


# Get any entries excluding a given POS-tag at any level
def findall_excltag(wordlist, excl_tag, tag_level=1):
    tag_level = tag_level - 1
    taglist = list()
    for word_data in wordlist:
        tag = word_data[3 + tag_level]
        if tag != excl_tag:
            taglist.append(word_data)
    return taglist


# Get all entries that are not null for a given level of POS-tag
def findall_anytag(wordlist, tag_level=1):
    tag_level = tag_level - 1
    taglist = list()
    for word_data in wordlist:
        search_tag = word_data[3 + tag_level]
        if search_tag:
            taglist.append(word_data)
    return taglist


# Reduces contents of wordlist to only include word and POS-tag information
def clean_wordlist(wordlist):
    new_wordlist = list()
    for i in wordlist:
        new_wordlist.append([i[1]] + i[3:8])
    return new_wordlist


l1_taglist = findall_thistag(analyses, "verb")
l2_taglist = findall_thistag(l1_taglist, "copula", 2)
l3_taglist = findall_thistag(l2_taglist, "3sg.pres.ind.", 3)
l4_taglist = findall_excltag(l3_taglist, "Active", 4)
l5_taglist = findall_anytag(l3_taglist, 5)

# for tag in clean_wordlist(l1_taglist):
#     print(tag)
# for tag in clean_wordlist(l2_taglist):
#     print(tag)
# for tag in clean_wordlist(l3_taglist):
#     print(tag)
# for tag in clean_wordlist(l4_taglist):
#     print(tag)
# for tag in clean_wordlist(l5_taglist):
#     print(tag)

