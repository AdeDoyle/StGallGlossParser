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


# Cleans tags in Bernhard's tag-set by removing whitespace and replacing unattested forms with a *
def clean_onetag(taglist):
    cleaned_tag = list()
    C = taglist[2]
    for tag_piece in taglist:
        if tag_piece:
            if tag_piece != C:
                tag_piece = tag_piece.strip()
            else:
                tag_piece = tag_piece.strip()
                if tag_piece[0] == "*":
                    tag_piece = "*"
        cleaned_tag.append(tag_piece)
    return cleaned_tag


# # Collect lists of Bernhard's original POS-tags, levels 1-3, incl. verb information (active/passive, and relativity)
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
#         # testA1.append(False)
#     elif A1.strip() not in testA1:
#         testA1.append(A1.strip())
#     if not A2:
#         noA2.append(i)
#         # testA2.append(False)
#     elif A2.strip() not in testA2:
#         testA2.append(A2.strip())
#     if not A3:
#         noA3.append(i)
#         # testA3.append(False)
#     elif A3.strip() not in testA3:
#         A3_clean = A3.strip()
#         if A3_clean[0] != "*":
#             testA3.append(A3.strip())
#         else:
#             testA3.append("*")
#     if vb_actpas:
#         testActPas.append(vb_actpas.strip())
#     # else:
#     #     testActPas.append(False)
#     if vb_rel:
#         testRel.append(vb_rel.strip())
#     # else:
#     #     testRel.append(False)
#     # output = [word, A1, A2, A3, vb_actpas, vb_actpas]
#     # if glossnum == lastnum:
#     #     print(output)
#     # else:
#     #     lastnum = glossnum
#     # print(output)


# # Sort lists of Bernhard's original POS-tags, levels 1-3, as well as verb information (active/passive, and relativity)
# # Save these sorted lists
# sorted_A1 = sorted(list(set(testA1))) + [False]
# # save_obj("A1 List", sorted_A1)
# sorted_A2 = sorted(list(set(testA2))) + [False]
# # save_obj("A2 List", sorted_A2)
# sorted_A3 = sorted(list(set(testA3))) + [False]
# # save_obj("A3 List", sorted_A3)
# sorted_actpas = sorted(list(set(testActPas))) + [False]
# # save_obj("Active_Passive List", sorted_actpas)
# sorted_rel = sorted(list(set(testRel))) + [False]
# # save_obj("Relative Options List", sorted_rel)


A1_list = open_obj("A1 List.pkl")
A2_list = open_obj("A2 List.pkl")
A3_list = open_obj("A3 List.pkl")
actpas_list = open_obj("Active_Passive List.pkl")
rel_list = open_obj("Relative Options List.pkl")


# # Test contents of POS tag-set and which entries have no tags.
# print("Entries, no A1: {}".format(len(noA1)))
# print("Unique A1 Types: {}".format(len(A1_list)))
#
# print("Entries, no A2: {}".format(len(noA2)))
# print("Unique A2 Types: {}".format(len(A2_list)))
#
# print("Entries, no A3: {}".format(len(noA3)))
# print("Unique A3 Types: {}".format(len(A3_list)))
#
# print("Unique Active/Passive Types: {}".format(len(actpas_list)))
# print("Unique Relativity Types: {}".format(len(rel_list)))


# for i in A1_list:
#     print(i)
# for i in noA1:
#     output = [i[1]] + i[3:8]
#     print(output)

# for i in A2_list:
#     print(i)
# for i in noA2:
#     output = [i[1]] + i[3:8]
#     print(output)

# for i in A3_list:
#     print(i)
# for i in noA3:
#     output = [i[1]] + i[3:8]
#     print(output)

# for i in actpas_list:
#     print(i)
# for i in rel_list:
#     print(i)


# # Create an ordered list of all unique POS-tag combinations used (takes a long time to run)
# alltag_combos = list()
# for entry in analyses:
#     tag_combo = entry[3:8]
#     tag_combo_clean = clean_onetag(tag_combo)
#     if tag_combo_clean not in alltag_combos:
#         alltag_combos.append(tag_combo_clean)
# sorted_tag_combos = list()
# for t1 in A1_list:
#     for t2 in A2_list:
#         for t3 in A3_list:
#             for actpas in actpas_list:
#                 for rel in rel_list:
#                     possible_combo = [t1, t2, t3, actpas, rel]
#                     if possible_combo in alltag_combos:
#                         sorted_tag_combos.append(possible_combo)
# # save_obj("All POS Combos Used", sorted_tag_combos)


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
        new_wordlist.append([i[0], clean_word(i[1])] + clean_onetag(i[3:8]))
    return new_wordlist


# POS_list = ["AF", "BR", "CPL", "AID", "FRA", "ALT", "TSP", "DBR", "RFH", "CN", "NOD", "MBR",
#             "UMR", "INT", "SNL", "BRS", "PNC"]
# Parole_tags_TL = ["NOUN", "VERB", "ADJ", "PRON", "DET", "Article", "ADV", "ADP",
#                   "Conjunction", "NUM", "INTJ", "Unique Membership Class", "Residuals", "PUNCT",
#                   "Abbreviation", "Copula", "Verbal Particle"]
# UD_tags_TL = ['ADJ', 'ADP', 'ADV', 'AUX', 'CCONJ', 'DET', 'INTJ', 'NOUN', 'NUM',
#               'PART', 'PRON', 'PROPN', 'PUNCT', 'SCONJ', 'SYM', 'VERB', 'X']
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


# takes a single tag combination form the Sg. corpus, changes it to a simple POS tag.
def clean_analysis(taglist):
    An1 = taglist[0]
    An2 = taglist[1]
    An3 = taglist[2]
    actpas = taglist[3]
    rel = taglist[4]
    pos = "unknown"
    # assign nouns
    if An1 == 'noun':
        if An2 in ['m, o', 'f, ā', 'm, i']:
            if An3 in ['dat.sg.', 'acc.pl.', 'gen.pl.']:
                if not actpas:
                    if not rel:
                        pos = "NOUN"
    # assign articles
    if An1 == 'article':
        if An2 == 'm':
            if An3 == 'gen.pl.':
                if not actpas:
                    if not rel:
                        pos = "DET"
    # assign verbs
    verb_tensepers = ["3sg.pres.ind.", '3pl.pres.ind.']
    if An1 == 'verb':
        if An2 == 'substantive verb':
            if An3 in verb_tensepers:
                if actpas == 'Active':
                    if not rel:
                        pos = "VERB"
        elif An2 == 'BII':
            if An3 in verb_tensepers:
                if actpas == 'Active':
                    if not rel:
                        pos = "VERB"
    # assign adjectives
    if An1 == 'adjective':
        if An2 in ['o, ā', 'i̯o, i̯ā', 'i', 'u']:
            pos = 'ADJ'
        else:
            pass
            # print(taglist)
    # assign prepositions
    if An1 == 'preposition, with dat; leniting':
        if not An2:
            if An3 == 'dat.':
                if not actpas:
                    if not rel:
                        pos = "ADP"
    elif An1 == 'preposition, with acc; geminating':
        if not An2:
            if An3 == 'acc.':
                if not actpas:
                    if not rel:
                        pos = "ADP"
    # assign conjunctions
    if An1 == 'conjunction (nasalizing, conjunct)':
        if not An2:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "SCONJ"
    # assign pre-verbal particles
    if An1 == 'particle':
        if An2 == 'preverb':
            if An3 == '*':
                if not actpas:
                    if not rel:
                        pos = "PVP"
    if pos == "unknown":
        return 1/0
    else:
        return pos
    # return pos


# Loops through all glossed words, finds their tags and passes them to the clean_analysis function.
# Where tags cannot be cleaned by the function, all instances of the tag are printed.
def loop_tags(taglist):
    # all_pos = open_obj("All POS Combos Used.pkl")
    new_poslist = list()
    for full_tag in taglist:
        glossnum = full_tag[0]
        word = clean_word(full_tag[1])
        # trans = full_tag[2]
        tag = clean_onetag(full_tag[3:8])
        gloss = clean_gloss(full_tag[8])
        # glosstrans = full_tag[9]
        # assembled_tag = [glossnum, word, trans, tag, gloss, glosstrans]
        try:
            pos_tag = clean_analysis(tag)
            full_tag.append(pos_tag)
            new_poslist.append(full_tag)
        except:
            print("Broke at gloss no. {}\n'{}', in gloss, '{}'.\n"
                  "Analysis: {}\n\nSimilar tags:".format(glossnum, word, gloss, tag))
            for comp in taglist:
                if clean_onetag(comp[3:8]) == tag:
                    comp_glossnum = comp[0]
                    comp_word = clean_word(comp[1])
                    comp_trans = comp[2]
                    comp_tag = clean_onetag(comp[3:8])
                    comp_gloss = clean_gloss(comp[8])
                    print(comp_tag, comp_glossnum, "'" + comp_word + "'", comp_trans, "in, '" + comp_gloss + "'")
            return "Loop Broken!\n"
    return new_poslist


loop_tags(analyses)
# print(loop_tags(analyses))
# for i in loop_tags(analyses):
#     print("'" + i[1] + "',", i[-1])

# # Find Percentage of Corpus POS tagged
# tagged_list = loop_tags(analyses)
# tagged_count = 0
# all_count = len(tagged_list)
# for i in tagged_list:
#     if i[-1] != 'unknown':
#         tagged_count += 1
# tagged_percent = (100/all_count) * tagged_count
# print("Total number of words in corpus: {}".format(all_count))
# print("Number of words tagged: {}".format(tagged_count))
# print("Percentage of words tagged: {}".format(tagged_percent))


# l1_taglist = findall_thistag(analyses, "adjective")
# l2_taglist = findall_thistag(l1_taglist, False, 2)
# print(len(l2_taglist))
# for tag in l2_taglist:
#     found_glossnum = tag[0]
#     found_word = clean_word(tag[1])
#     found_trans = tag[2]
#     found_tag = clean_onetag(tag[3:8])
#     found_gloss = clean_gloss(tag[8])
#     print(found_tag, found_glossnum, "'" + found_word + "'/'" + found_trans + "'", "in, '" + found_gloss + "'")


# # test all POS combinations in the corpus (notlist - should be empty. if not...)
# # (... check to see that do not appear in the collected list of all POS combinations used (allpos) and why)
# allpos = open_obj("All POS Combos Used.pkl")
# notlist = list()
# for i in analyses:
#     itag_noisy = i[3:8]
#     itag = list()
#     for j in itag_noisy:
#         if j:
#             clean_j = j.strip()
#             if j == itag_noisy[2]:
#                 if clean_j[0] == "*":
#                     clean_j = "*"
#             itag.append(clean_j)
#         else:
#             itag.append(j)
#     if itag not in allpos:
#         notlist.append(itag)
# # print(notlist[0])
# unique_notlist = list()
# for i in notlist:
#     if i not in unique_notlist:
#         unique_notlist.append(i)
#         print(i)
# # for i in allpos:
# #     print(i)
# print(len(allpos))
# print(len(notlist))
# print(len(unique_notlist))


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


# # Test clean_onetag function
# for tag in analyses:
#     print(clean_onetag(tag[3:8]))


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
# # # find all instances of a given tag where another tag level is not null
# # test_taglist = findall_thistag(analyses, A1_list[1])
# # test_taglist = findall_notnulltag(test_taglist, 4)
# for tag in clean_wordlist(test_taglist):
#     print(tag)

