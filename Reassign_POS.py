"""Level 1."""

from functools import lru_cache
from Pickle import open_obj, save_obj
from OpenXlsx import list_xlsx
from Clean_Glosses import clean_gloss, clean_word
import re
import matplotlib.pyplot as plt


glossdict = open_obj("Clean_GlossDict.pkl")
glosslist = open_obj("Gloss_List.pkl")
worddict = open_obj("Clean_WordDict.pkl")
wordslist = open_obj("Words_List.pkl")
analyses = list_xlsx("SG. Combined Data", "Sheet 1")


def clean_analysis():
    pass


# POS_list = ["AF", "BR", "CPL", "AID", "FRA", "ALT", "TSP", "DBR", "RFH", "CN", "NOD", "MBR",
#             "UMR", "INT", "SNL", "BRS", "PNC"]
Parole_tags_TL = ["NOUN", "VERB", "ADJ", "PRON", "DET", "Article", "ADV", "ADP",
                  "Conjunction", "NUM", "INTJ", "Unique Membership Class", "Residuals", "PUNCT",
                  "Abbreviation", "Copula", "Verbal Particle"]
UD_tags_TL = ['ADJ', 'ADP', 'ADV', 'AUX', 'CCONJ', 'DET', 'INTJ', 'NOUN', 'NUM',
              'PART', 'PRON', 'PROPN', 'PUNCT', 'SCONJ', 'SYM', 'VERB', 'X']


# "ADJ": "adjective",
# "ADP": "adposition - Pre-verbal particles? Infixed Pronouns",
# "ADV": "adverb",
# "AUX": "auxiliary - accompanies lexical verb 'has/was/got done, should/must/will do, is doing'",
# "CCONJ": "coordinating conjunction - connect clauses without subordinating one to the other, 'and, or, but'"
# "DET": "determiner",
# "INTJ": "interjection",
# "NOUN": "noun",
# "NUM": "numeral",
# "PART": "particle - negative, possessive, interrogative, demonstrative(?)",
# "PRON": "pronoun",
# "PROPN": "proper noun",
# "PUNCT": "punctuation",
# "SCONJ": "subordinating conjunction - subordinates one clause to another 'that/if/when/since/before he will come'",
# "SYM": "symbol",
# "VERB": "verb",
# "X": "other - meaningless foreign word or word fragment"


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


A1_list = open_obj("A1 List.pkl")
A2_list = open_obj("A2 List.pkl")
A3_list = open_obj("A3 List.pkl")


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
def findall_notnulltag(wordlist, tag_level=1):
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
        new_wordlist.append(i[0:2] + i[3:8])
    return new_wordlist


# # Loops through all potential tags, finds them where they appear in a given list, deals with them as appropriate
# # Where tags cannot be dealt with, all instances of the tag are printed
# def loop_tags(taglist):
#     count = 0
#     alltags = open_obj("All POS Combos Used.pkl")
#     for i in taglist:
#         tag = i[3:8]
#         if tag not in alltags:
#             print(tag)
#             count += 1
#     print(count)
#     return "Done!"


# notlist = [i[3:8] for i in analyses if i[3:8] not in open_obj("All POS Combos Used.pkl")]
# print(notlist[0])
# for i in open_obj("All POS Combos Used.pkl"):
#     print(i)


# loop_tags(analyses)


# l1_taglist = findall_thistag(analyses, "verb")
# l2_taglist = findall_thistag(l1_taglist, "copula", 2)
# l3_taglist = findall_thistag(l2_taglist, "3sg.pres.ind.", 3)
# l4_taglist = findall_excltag(l3_taglist, "Active", 4)
# l5_taglist = findall_notnulltag(l3_taglist, 5)

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


# # Create an ordered list of all unique POS-tag combinations used (takes a long time to run)
# alltag_combos = list()
# for entry in analyses:
#     tag_combo = entry[3:8]
#     tag_combo_clean = list()
#     for i in tag_combo:
#         if i:
#             i = i.strip()
#             tag_combo_clean.append(i)
#         else:
#             tag_combo_clean.append(i)
#     if tag_combo_clean not in alltag_combos:
#         alltag_combos.append(tag_combo_clean)
# sorted_tag_combos = list()
# for t1 in A1_list:
#     for t2 in A2_list:
#         for t3 in A3_list:
#             for actpas in ["Active", "Pass", "Passive", False]:
#                 for rel in ["Maybe", "Y", False]:
#                     possible_combo = [t1, t2, t3, actpas, rel]
#                     if possible_combo in alltag_combos:
#                         sorted_tag_combos.append(possible_combo)
# # save_obj("All POS Combos Used", sorted_tag_combos)


# # Count total potential POS tag combinations
# ordered_tagcombos = open_obj("All Pos Combos Used.pkl")
# print("Total Tags: {}".format(len(ordered_tagcombos)))

# # Count, print and graph the number of POS tag combinations which are used a given number of times
# # e.g. if there are 18 tags used only once, 10 tags used 5 times, and 2 tags used 50 times, count and graph this info.
# tag_usage = list()
# for tag in ordered_tagcombos:
#     # for each used tag combination
#     count = 0
#     for an in analyses:
#         # check each analysis against each possible tag combination used
#         if tag == an[3:8]:
#             # if the tags match, increase the usage-count for this tag
#             count += 1
#     # save the total usage-count for this tag to the tag_usage list
#     tag_usage.append(count)
# # now count the number of tags used each given number of times and add [count of use-count, use-count] to ordered list
# tags_usecount = list()
# alltagcount = sorted(tag_usage)
# uniquetagscount = sorted(set(tag_usage))
# for i in uniquetagscount:
#     tagusecount = alltagcount.count(i)
#     tags_usecount.append([i, tagusecount])
# # plot 'use-count' and 'count of use-count' on X and Y axes respectively
# X = list()
# Y = list()
# # identify highest number 'count of use-count' to use as an upper limit
# high_usecount = tags_usecount[-1][0]
# for i in range(high_usecount + 1):
#     for j in tags_usecount:
#         usecount = j[0]
#         if usecount == i:
#             countnum = j[1]
#             X.append(usecount)
#             Y.append(countnum)
#             print("No. of tags used {} time(s): {}".format(usecount, countnum))
#         elif usecount < i:
#             X.append(i)
#             Y.append(0)
#         else:
#             break
# plt.plot(X, Y)
# plt.title("Graph of Tag Usage in St. Gall Glosses")
# plt.xlabel("Number of Times a Tag Is Used")
# plt.ylabel("Number of Tags Used X Times")
# plt.show()


# # find all instances of a given tag
# test_taglist = findall_thistag(analyses, A1_list[2])
# # find all instances of a given tag where another tag level is not null
# test_taglist = findall_thistag(analyses, A1_list[1])
# test_taglist = findall_notnulltag(test_taglist, 4)
# for tag in clean_wordlist(test_taglist):
#     print(tag)

