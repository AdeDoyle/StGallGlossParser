"""Level 1."""

from functools import lru_cache
from Pickle import open_obj, save_obj
from OpenXlsx import list_xlsx
from Clean_Glosses import clean_gloss, clean_word
import time
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


# # Create an ordered list of all unique POS-tag combinations used (takes about 26 minutes to run)
# start_time = time.time()
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
# end_time = time.time()
# time_elapsed = end_time - start_time
# duration_in = 'sec'
# if time_elapsed > 60:
#     time_elapsed = time_elapsed / 60
#     duration_in = 'mins'
#     if time_elapsed > 60:
#         time_elapsed = time_elapsed / 60
#         duration_in = 'hrs'
# print("Time Elapsed: {}{}".format(time_elapsed, duration_in))


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
# "AUX": "auxiliary - accompanies lexical verb 'has/was/got done, should/must/will do, is doing', 'no' if not PVP?",
# "CCONJ": "coordinating conjunction - connect clauses without subordinating one to the other, 'and, or, but'"
# "DET": "determiner - article + cách (every)",
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


# Takes a single tag combination form the Sg. corpus, changes it to a simple POS tag.
def clean_analysis(taglist, test_unknown=False):
    An1 = taglist[0]
    An2 = taglist[1]
    An3 = taglist[2]
    actpas = taglist[3]
    rel = taglist[4]
    trans = taglist[5]
    testlist = [An1, An2, An3, actpas, rel, trans]
    # print("FUCKED: {}".format(testlist))
    pos = "unknown"

    #                                         NOUNS & PRONOUNS
    # Assign Nouns (NOUN)
    if An1 == 'noun':
        if An2 in ['m, o', 'n, o', 'f, ā',
                   'm, i̯o', 'n, i̯o', 'f, i̯ā',
                   'm, i', 'n, i', 'f, i',
                   'f, ī', 'm, u', 'n, u', 'f, u',
                   'm, dent.', 'f, d', 'f, k', 'm, n', 'n, n', 'f, n', 'm, (n)k', 'm, nt', 'n, nt',
                   'm, r', 'f, r', 'n, s', 'n, s (?)', 'm, t', 'n, t', 'f, t',
                   'm', 'f', 'n', 'm and n', 'm and f', 'm, and f', 'f and m',
                   'o', 'i̯o', 'i',
                   'm, o (?)', 'm and n, o', 'm and n, o (?)', 'm, o and u', 'm, o orig. n', 'm, o orig. n, s (?)',
                   'm, o and f, ā', 'm, o, later also f, ā', 'n (?), o', 'n and m, o', 'n, o (m, o?)',
                   'n, o, later m, o',
                   'o (gender uncertain)', 'o [n ?]',
                   'm, i̯o (?)', '[m, ?] i̯o', 'm, i̯o and i', '[m] i', 'm, i (?)', 'm, u and n, o', '[m, ?] u',
                   'm, t and f, t',
                   'n, o (?)', 'n, i̯o & adjective', 'n, u or o', 'n and m, u', 'n, s and n, o',
                   'f, ā; adjective', 'f, ā, later also m, o', 'f, ā and i', 'f, mixed ā-, ī-, i-', 'f, ā and m, u',
                   'f, ā; also f, n', 'f, i̯ā & m, i̯o', 'f, i, ī', 'f, i and n', 'f, n (?)', 'f, i, later also k',
                   'irregular', 'gender not attested in OIr.', 'gender unknown, i-stem', 'unknown declension']:
            if An3 in ['nom.sg.', 'acc.sg.', 'gen.sg.', 'dat.sg.', 'dat.sg. (?)',
                       'nom.pl.', 'voc.pl.', 'acc.pl.', 'acc.pl.masc.', 'acc.pl.neut.', 'gen.pl.', 'dat.pl.',
                       'nom.du.', 'acc.du.', 'gen.du.', 'dat.du.',
                       'acc./dat.sg.',
                       'nom.sg.neut.', 'nom.sg.fem.', 'gen.sg.neut.',
                       'adverbial form', 'composition form']:
                if not actpas:
                    if not rel:
                        pos = "NOUN"
        if An2 in ['f, ā', 'f, i̯ā', 'm, u']:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "NOUN"
    if An1 == 'noun and adjective':
        if An2 in ['i']:
            if An3 in ['acc.sg.']:
                if not actpas:
                    if not rel:
                        pos = "NOUN"

    # Assign Nroper Nouns (NOUN)
    if An1 == 'noun, proper':
        if not An2:
            if An3 in ['nom.sg.', 'voc.sg.', 'acc.sg.', 'gen.sg.', 'dat.sg.']:
                if not actpas:
                    if not rel:
                        pos = "NOUN"
        elif An2 in ['m, i̯o']:
            if An3 in ['nom.pl.']:
                if not actpas:
                    if not rel:
                        pos = "NOUN"

    # Assign Pronouns (PRON)
    # Personal Pronouns
    if An1 == 'pronoun, personal':
        if An2 in ['3sg m', '3sg f', '3sg n',
                   '3pl']:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PRON"
            elif An3 in ['formal pred, immediately after copula']:
                if not actpas:
                    if not rel:
                        pos = "PRON"
    # Assign Indefinite Pronouns (PRON)
    if An1 == 'pronoun, non-neuter':
        if not An2:
            if An3 in ['acc.sg.']:
                if not actpas:
                    if not rel:
                        pos = "PRON"
    # Assign Suffixed Pronouns (PRON)
    if An1 == 'pronoun, suffixed':
        if An2 in ['3sg m, n', '3sg m, n (nasalizing)']:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PRON"
    # Reflexive Pronouns
    if An1 == 'pronoun, reflexive':
        if not An2:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PRON"
            if An3 in ['3sg.masc.', '3sg.neut.', '3sg.fem.', '3pl.']:
                if not actpas:
                    if not rel:
                        pos = "PRON"
    # Possessive Pronouns
    if An1 == 'pronoun, possessive, stressed':
        if An2 in ['3sg and pl']:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PRON"
            elif An3 in ['pl.']:
                if not actpas:
                    if not rel:
                        pos = "PRON"
    if An1 == 'pronoun, possessive, unstressed':
        if An2 in ['1sg (leniting)',
                   '3sg m, n (leniting)', '3sg f',
                   '1pl (nasalizing)',
                   '3pl (nasalizing)']:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PRON"
            elif An3 in ['neut.', '3sg.neut.']:
                if not actpas:
                    if not rel:
                        pos = "PRON"
    # Emphatic Pronouns
    if An1 == 'particle, emphatic pronominal':
        if An2 in ['1sg', '2sg', '3sg m, n', '3sg f',
                   '1pl', '3pl']:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PRON"
            elif An3 in ['3sg.masc.']:
                if not actpas:
                    if not rel:
                        pos = "PRON"
    # Anaphoric Pronouns
    if An1 == 'pronoun, anaphoric':
        if An2 in ['stressed', 'neuter, stressed']:
            if An3 in ['nom.sg.',
                       'acc.sg.', 'acc.sg.masc.',
                       'dat.sg.', 'dat.sg.masc.', 'dat.sg.neut.',
                       'dat.pl.']:
                if not actpas:
                    if not rel:
                        pos = "PRON"
        elif An2 == 'enclitic':
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PRON"
            if An3 in ['nom.sg.masc.', 'nom.sg.neut.', 'nom.sg.fem.',
                       'acc.sg.', 'acc.sg.fem.',
                       'gen.sg.neut.',
                       'dat.sg.fem',
                       'nom.pl.', 'nom.pl.masc.', 'nom.pl.fem.']:
                if not actpas:
                    if not rel:
                        pos = "PRON"
        elif An2 == 'indeclinable neuter enclitic':
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PRON"
    # Assign Prepositional Pronouns (PRON)
    prepprontype = ['acc. + suff.pron.1sg.',
                    'acc. + suff.pron.3sg.masc./neut.',
                    'acc. + suff.pron.3sg.fem.',
                    'acc. + suff.pron.1pl.',
                    'acc. + suff.pron.3pl.',
                    'dat. + suff.pron.1sg.',
                    'dat. + suff.pron.2sg.',
                    'dat. + suff.pron.3sg.masc./neut.',
                    'dat. + suff.pron.3sg.fem.',
                    'dat. + suff.pron.3sg.fem. + -si 1',
                    'dat. + suff.pron.1pl.',
                    'dat. + suff.pron.3pl.',
                    'eter + suff pron 3sg n']
    if An1 in ['preposition, with acc', 'preposition, with acc; leniting', 'preposition, with acc; geminating',
               'preposition, with dat', 'preposition, with dat; leniting', 'preposition, with dat; nasalizing',
               'preposition, with dat; geminating',
               'preposition, with dat and acc; leniting', 'preposition, with dat and acc; nasalizing']:
        if not An2:
            if An3 in prepprontype:
                if not actpas:
                    if not rel:
                        pos = "PRON"
                    elif rel in ['Y']:
                        pos = "PRON"

    #                                        ARTICLES & DETERMINERS
    # Assign Articles (DET)
    if An1 == 'article':
        if An2 in ['m', 'n', 'fem']:
            if An3 in ['nom.sg.', 'acc.sg.', 'gen.sg.', 'dat.sg.',
                       'nom.pl.', 'acc.pl.', 'gen.pl.',
                       'gen.sg. + í 1',
                       'nom.pl. + í 1', 'gen.pl. + í 1',
                       'acc.du.', 'gen.du.']:
                if not actpas:
                    if not rel:
                        pos = "DET"
    # Assign Pronominal Articles - the '(s)in(d) and '(s)naib' endings of pronouns (DET)
    if An1 == 'article':
        if An2 in ['m', 'n', 'fem']:
            if An3 in ['acc.sg. + ar 1',
                       'acc.sg. + for 1', 'acc.pl. + for 1',
                       'acc.sg. + fri', 'acc.pl. + fri',
                       'acc.sg + i 2',
                       'acc.sg. + la', 'acc.pl. + la',
                       'acc.sg. + tre 1',
                       'dat.sg. + a 5',
                       'dat.sg. + ar 1',
                       'dat.sg. + de 1', 'dat.pl + de 1',
                       'dat.sg. + do 1', 'dat.pl + do 1',
                       'dat.sg. + fo 1',
                       'dat.sg. + for 1',
                       'dat.sg. + i 2', 'dat.pl. + i 2',
                       'dat.sg. + ó 1', 'dat.pl. + ó 1',
                       'dat.sg. + oc']:
                if not actpas:
                    if not rel:
                        pos = "DET"
    # Assign Pronominal Adjectives/Determiners - e.g. 'cach'/'cechtar/naich' (DET)
    prad_case = ['nom.sg.', 'nom.sg.masc.', 'nom.sg.neut.', 'nom.sg.fem.',
                 'acc.sg.', 'acc.sg.masc.', 'acc.sg.neut.', 'acc.sg.fem.',
                 'gen.sg.', 'gen.sg.masc.', 'gen.sg.neut.', 'gen.sg.fem.',
                 'dat.sg.', 'dat.sg.masc.', 'dat.sg.neut.', 'dat.sg.fem',
                 'acc.pl.',
                 'dat.pl.masc.',
                 'nom.du.fem.']
    if An1 in ['adjective, pronominal (preceding noun)', 'adjective, indefinite pronominal',
               'pronoun, indefinite', 'pronoun, indeclinable']:
        if not An2:
            if An3 in prad_case:
                if not actpas:
                    if not rel:
                        pos = "DET"
        elif An2 in ['m']:
            if An3 in prad_case:
                if not actpas:
                    if not rel:
                        pos = "DET"
    #                                             ADJECTIVES
    # Assign Adjectives (ADJ)
    if An1 == 'adjective':
        if An2 in ['o, ā', 'i̯o, i̯ā', 'i', 'u',
                   'o, ā, i', 'o, ā and noun',
                   'indeclinable (?)']:
            if An3 in ['nom.sg.', 'nom.sg.masc.', 'nom.sg.neut.', 'nom.sg.fem.',
                       'acc.sg.', 'acc.sg.masc.', 'acc.sg.neut.', 'acc.sg.fem.',
                       'gen.sg.', 'gen.sg.masc.', 'gen.sg.neut.', 'gen.sg.fem.',
                       'dat.sg.', 'dat.sg.masc.', 'dat.sg.neut.', 'dat.sg.fem',
                       'nom.pl.', 'nom.pl.masc.', 'nom.pl.neut.', 'nom.pl.fem.',
                       'acc.pl.', 'acc.pl.masc.', 'acc.pl.neut.',
                       'gen.pl.', 'gen.pl.masc.', 'gen.pl.neut.', 'gen.pl.fem.',
                       'dat.pl.', 'dat.pl.masc.', 'dat.pl.neut.', 'dat.pl.fem.',
                       'acc.du.fem.',
                       'dat.sg.masc + ó 1',
                       'comparative', 'superlative',
                       'adverbial form', 'clitic form', 'composition form']:
                if not actpas:
                    if not rel:
                        pos = "ADJ"
            elif not An3:
                if not actpas:
                    if not rel:
                        pos = "ADJ"
        elif not An2:
            if An3 in ['nom.sg.', 'nom.sg.masc.',
                       'gen.sg.masc.',
                       'in adverbial phrase i recc']:
                if not actpas:
                    if not rel:
                        pos = "ADJ"
    if An1 == 'noun and adjective':
        if An2 in ['o, ā']:
            if An3 == 'composition form':
                if not actpas:
                    if not rel:
                        pos = "ADJ"

    #                                        VERBS, COPULA & ADVERBS
    # Assign Verbs (VERB)
    verb_tensepers = ['1sg.pres.ind.', '1sg.pres.subj.',
                      '1sg.pret.',
                      '1sg.fut.',
                      '2sg.pres.ind.',
                      '2sg.impv.',
                      '3sg.pres.ind.', '3sg.pres.ind.pass.', '3sg.pres.ind.rel.',
                      '3sg.cons.pres.', '3sg.cons.pres.rel.',
                      '3sg.pres.subj.', '3sg.pres.subj.pass.', '3sg.pres.subj.rel.',
                      '3sg.impv.',
                      '3sg.pret.', '3sg.past.subj.',
                      '3sg.perf.', '3sg.pass.perf.',
                      '3sg.imperf.', '3sg.imperf.pass.', '3sg.imperf.subj.', '3sg.imperf.subj.pass.',
                      '3sg.fut.', '3sg.fut.pass.', '3sg.fut.rel.', '3.sg.sec.fut.',
                      '1pl.pres.ind.', '1pl.pres.subj.',
                      '1pl.pret.', '1pl.perf.',
                      '2pl.impv.',
                      '3pl.pres.ind.', '3pl.pres.ind.pass.', '3pl.pres.ind.rel.',
                      '3pl.cons.pres.', '3pl.cons.pres.rel.',
                      '3pl.pres.subj.', '3pl.pres.subj.pass.', '3pl.pres.subj.rel.',
                      '3pl.pret.', '3pl.pret.rel.', '3pl.past.subj.', '3sg.past.subj.rel.',
                      '3pl.perf.', '3pl.perf.pass.',
                      '3pl.imperf.', '3pl.imperf.pass.', 'perf 3pl.perf.rel.',
                      '3pl.fut.', '3pl.fut.rel.', '3pl.sec.fut.pass.',
                      '*']
    verb_tenseperssuffix = ['3sg.pres.ind. + suff.pron. 3sg.masc./neut.']
    verb_tensepersinfix = ['1sg.pres.ind. + infix.pron. Class A 3sg.fem.',
                           '3sg.pres.ind. + inf.pron. class A 3sg.neut.',
                           '3sg.pres.ind. + infix.pron. Class C 3sg.neut.',
                           '3sg.pres.ind. + infix.pron. Class C 3sg.fem.',
                           '3sg.pres.ind.pass. + infix.pron. Class B 1sg.',
                           '3sg.pres.ind.pass. + infix.pron. Class B 3sg.',
                           '3sg.pres.subj. + infix.pron. Class B 3sg.neut.',
                           '3sg.pret./perf. + infix.pron. Class A 1pl.',
                           '3sg.perf. + infix.pron. Class A 3sg.neut.',
                           '3sg.perf. + infix.pron. Class C 1pl.',
                           '3pl.pres.ind. + inf.pron. class A 3pl.',
                           '3pl.pres.ind. + infix.pron. Class C 3sg.neut.',
                           '3pl.pres.ind. + inf.pron. class A',
                           '3pl.imperf. + infix.pron. Class A 3sg.neut.']
    # Substantive Verb
    if An1 == 'verb':
        if An2 in ['substantive verb', 'substantive verb (compound)']:
            if An3 in verb_tensepers:
                if actpas == 'Active':
                    if not rel:
                        pos = "VERB"
                    elif rel == 'Y':
                        pos = "VERB"
            elif An3 in verb_tensepersinfix:
                if actpas == 'Active':
                    if not rel:
                        pos = "VERB"
                    elif rel == 'Y':
                        pos = "VERB"
    # Copula
        elif An2 == 'copula':
            if An3 in verb_tensepers:
                if actpas == 'Active':
                    if not rel:
                        pos = "VERB"
                    elif rel == 'Y':
                        pos = "VERB"
                elif not actpas:
                    if not rel:
                        pos = "VERB"
            elif An3 in verb_tenseperssuffix:
                if actpas == 'Active':
                    if not rel:
                        pos = "VERB"
                    elif rel == 'Y':
                        pos = "VERB"
    # General Verbs
        elif An2 in ['AI', 'AII', 'AIII', 'BI', 'BII', 'BIII', 'BIV', 'BV',
                     'AII (?)', 'defective','inflexion not clear', 'unclear']:
            if An3 in verb_tensepers:
                if actpas == 'Active':
                    if not rel:
                        pos = "VERB"
                    elif rel in ['Y', 'Maybe']:
                        pos = "VERB"
                elif actpas in ['Passive']:
                    if not rel:
                        pos = "VERB"
                    elif rel in ['Y', 'Maybe']:
                        pos = "VERB"
            elif An3 in verb_tensepersinfix:
                if actpas == 'Active':
                    if not rel:
                        pos = "VERB"
                    elif rel == 'Y':
                        pos = "VERB"
                elif actpas in ['Passive']:
                    if not rel:
                        pos = "VERB"
                    elif rel == 'Y':
                        pos = "VERB"
            elif An3 in verb_tenseperssuffix:
                if actpas == 'Active':
                    if not rel:
                        pos = "VERB"
                    elif rel == 'Y':
                        pos = "VERB"
    # Unknown Verbs
        elif not An2:
            if An3 in verb_tensepers:
                if actpas == 'Active':
                    if not rel:
                        pos = "VERB"
                elif actpas == 'Passive':
                    if not rel:
                        pos = "VERB"
    # Verbal of Necessity
    if An1 == 'verbal of necessity':
        if not An2:
            if An3 in ['verbal of necessity: *as·gleinn',
                       'verbal of necessity: *do·edbair',
                       'verbal of necessity: fo-dáli',
                       'verbal of necessity: sásaid',
                       'verbal of necessity: techtaid',
                       '*']:
                if not actpas:
                    if not rel:
                        pos = "VERB"

    # Assign Adverb (ADV)
    if An1 == 'adverb':
        if not An2:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "ADV"
        elif An2 == 'conjunctive':
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "ADV"
    if An1 == 'preposition, with acc; leniting; and conjunction':
        if not An2:
            if An3 == 'acc. + suff.pron.3sg.masc./neut.':
                if not actpas:
                    if not rel:
                        pos = "ADV"
    if An1 == 'particle':
        if An2 in ['asseverative', 'connective', 'transitional']:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "ADV"

    #                                           PREPOSITIONS
    # Assign Prepositions (ADP)
    if An1 in ['preposition, with acc', 'preposition, with acc; leniting', 'preposition, with acc; geminating']:
        if not An2:
            if An3 in ['acc.', 'acc. + rel.part.',
                       'acc. + poss.pron.3sg.masc./neut.', 'acc. + poss.pron.3sg.fem.',
                       'acc. + poss.pron.3pl.',
                       'composition form']:
                if not actpas:
                    if not rel:
                        pos = "ADP"
    if An1 in ['preposition, with dat', 'preposition, with dat; leniting',
               'preposition, with dat; nasalizing', 'preposition, with dat; geminating']:
        if not An2:
            if An3 in ['dat.', 'dat.sg.', 'dat.pl.', 'dat. + rel.part.', 'dat. + alaile',
                       'dat. + poss.pron.3sg', 'dat. + poss.pron.3sg.masc./neut.', 'dat. + poss.pron.3sg.fem.',
                       'dat. + poss.pron.3pl.',
                       'composition form']:
                if not actpas:
                    if not rel:
                        pos = "ADP"
    if An1 in ['preposition, with dat and acc; leniting', 'preposition, with dat and acc; nasalizing']:
        if not An2:
            if An3 in ['acc.', 'acc. + rel.part.', 'acc./dat.',
                       'acc. + poss.pron.3sg.masc./neut.',
                       'dat.', 'dat.sg.', 'dat.pl.', 'dat. + rel.part.', 'dat. (?)',
                       'dat. + poss.pron.3sg.masc./neut.',
                       'dat (?) + poss.pron.3sg.masc./neut.',
                       'i 2 + poss.pron.3sg.fem.']:
                if not actpas:
                    if not rel:
                        pos = "ADP"
    # Assign Deterministic Prepositions - preceding prepositional articles (ADP)
    if An1 in ['preposition, with acc; geminating',
               'preposition, with dat', 'preposition, with dat; leniting', 'preposition, with dat; geminating',
               'preposition, with dat and acc; leniting', 'preposition, with dat and acc; nasalizing']:
        if not An2:
            if An3 in ['acc. + def.art.sg', 'acc. + def.art.pl.',
                       'acc. + def.art.pl. + í 1',
                       'dat. + def.art.sg.', 'dat. + def.art.pl.',
                       'dat. + def.art.sg. + í 1']:
                if not actpas:
                    if not rel:
                        pos = "ADP"

    #                                           CONJUNCTIONS
    # Assign Conjunctions (CCONJ/SCONJ)
    # Coordinating Conjunctions
    if An1 in ['conjunction (leniting)', 'conjunction (disjunct) and discourse marker']:
        if not An2:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "CCONJ"
            elif An3 in ['disjoins members within the clause', 'disjoins co-ordinate clauses']:
                if not actpas:
                    if not rel:
                        pos = "CCONJ"
        elif An2 == 'coordinating':
            if An3 in ['disjoins co-ordinate clauses',
                       'introducing sentence or clause',
                       'joining two adjectives',
                       'joining two Latin lemmata',
                       'joining two nouns', 'joining two nouns (letters of the alphabet)',
                       'joining two nouns with adjectives', 'joining two nouns with articles',
                       'joining two verbs',
                       'joining two sentences or clauses']:
                if not actpas:
                    if not rel:
                        pos = "CCONJ"
            elif not An3:
                if not actpas:
                    if not rel:
                        pos = "CCONJ"
    # Subordinating Conjunctions
    if An1 in ['conjunction', 'conjunction and adverb (conjunctive)', 'conjunction w/ subordinate negation']:
        if not An2:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "SCONJ"
        elif An2 in ['causal', 'causal; coordinating and subordinating',
                     'comparative', 'conditional', 'concessive and explicative (leniting)', 'conditional',
                     'disjunct', 'disjunct (leniting)',
                     'final (purpose), and explicative',
                     'negative subordinating', 'negative (geminating), before non-verbs; na before stressed words',
                     'relative negative, with infixed pronouns Class C',
                     'subordinate negative, with infixed pronouns Class C',
                     'temporal, adversative; (prep la + dem pron so 1 acc sg nt)']:
            if An3 in ['1pl.', 'with 3sg.pres.subj. of copula',
                       'i 2 + def.art. + deictic pron í 1', 'ma + ní + copula',
                       'with negative']:
                if not actpas:
                    if not rel:
                        pos = "SCONJ"
            elif not An3:
                if not actpas:
                    if not rel:
                        pos = "SCONJ"
    if An1 in ['conjunction (leniting, non-conjunct particle)',
               'conjunction (nasalizing)', 'conjunction (nasalizing, conjunct)',
               'conjunction and preposition',
               'preposition, with acc; and conjunction', 'preposition, with acc; leniting; and conjunction',
               'preposition, with acc; and adversative conjunction']:
        if not An2:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "SCONJ"
            elif An3 in ['acc.', 'acc.sg.',
                         'co 4 + copula']:
                if not actpas:
                    if not rel:
                        pos = "SCONJ"
        elif An2 == 'temporal':
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "SCONJ"
    if An1 == 'particle':
        if An2 == 'interrrogative':
            if not An3:
                if not actpas:
                    if not rel:
                        if trans == 'as a correlative conjunction: whether':
                            pos = "SCONJ"

    #                                              PARTICLES
    # Assign Particles (PART)
    # Assign Negative Particles
    if An1 == 'particle':
        if An2 in ['negative', 'relative negative', 'negative dependent relative']:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PART"
            elif An3 in ['ar·cuirethar']:
                if not actpas:
                    if not rel:
                        pos = "PART"
    # Assign Interrogative Particles
    if An1 == 'particle':
        if An2 == 'interrrogative':
            if not An3:
                if not actpas:
                    if not rel:
                        if trans != 'as a correlative conjunction: whether':
                            pos = "PART"
    if An1 in ['pronoun, interrogative and indefinite']:
        if not An2:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PART"
    if An1 in ['pronoun']:
        if An2 in ['interrogative', 'negative interrogative']:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PART"
    # Assign Demonstrative Particles
    if An1 in ['adjective, demonstrative', 'adjective, demonstrative pronominal', 'pronoun, demonstrative']:
        if not An2:
            if An3 in ['dat.pl.fem.']:
                if not actpas:
                    if not rel:
                        pos = "PART"
        elif An2 in ['this, these', 'that, those', 'neuter, indeclinable']:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PART"
            elif An3 in ['nom.sg.masc.', 'nom.sg.neut.',
                         'acc.sg.masc.',
                         'dat.sg.neut.',
                         'nom.pl.fem.',
                         'acc.pl.']:
                if not actpas:
                    if not rel:
                        pos = "PART"
    # Assign Vocative Particles
    if An1 == 'particle':
        if An2 == 'vocative':
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PART"
    # Assign Relative Particles
    if An1 == 'particle':
        if An2 == 'relative':
            if An3 in ['rel part + a 5',
                       'rel part + de 1',
                       'rel part + do 1',
                       'rel part + fri',
                       'rel part + i 2',
                       'rel part + ó 1']:
                if not actpas:
                    if not rel:
                        pos = "PART"
        elif An2 == 'demonstrative relative':
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PART"
    # Assign Deictic Particles
    if An1 == 'pronoun, indeclinable, accented, deictic':
        if not An2:
            if An3 in ['nom.sg.', 'nom.sg.neut.',
                       'acc.sg.', 'acc.sg.masc.', 'acc.sg.neut.',
                       'gen.sg.masc.', 'gen.sg.neut.',
                       'dat.sg.', 'dat.sg.masc.', 'dat.sg.neut.',
                       'nom.pl.masc.', 'nom.pl.neut.',
                       'acc.pl.', 'acc.pl.neut.',
                       'gen.pl.masc.', 'gen.pl.neut.',
                       'dat.pl.', 'dat.pl.neut.']:
                if not actpas:
                    if not rel:
                        pos = "PART"

    #                                   INTERJECTIONS, NUMERALS & ABBREVIATIONS
    # Assign Interjections (INTJ)
    if An1 == 'exclamation form':
        if not An2:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "INTJ"
    if An1 == 'emphasizing particle':
        if not An2:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "INTJ"
    # Assign Numerals (NUM)
    if An1 == 'number':
        if An2 == 'adjective':
            if An3 in ['nom.sg.',
                       'gen.sg.masc.',
                       'dat.sg.',
                       'nom.pl.', 'nom.pl.fem.',
                       'gen.pl.fem.',
                       'nom.du.masc.', 'nom.du.fem.',
                       'acc.du.neut.', 'acc.du.fem.',
                       'gen.du.masc.', 'gen.du.neut.', 'gen.du.fem.', 'gen.du.fem. + in 2',
                       'dat.du.', 'dat.du.masc.', 'dat.du.fem.',
                       'composition form', 'uninflected']:
                if not actpas:
                    if not rel:
                        pos = "NUM"
    if An1 == 'Precedes and forms compd. with qualified noun':
        if not An2:
            if An3 == 'composition form':
                if not actpas:
                    if not rel:
                        pos = "NUM"
    # Assign Abbreviations (SYM)
    if An1 == 'abbreviation':
        if not An2:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "SYM"

    #                                           UNUSED PARTS-OF-SPEECH
    # Assign Pre-verbal Particles (PVP)
    if An1 == 'particle':
        if An2 == 'preverb':
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PVP"
            elif An3 in ['ar·icc', 'at·baill', 'díxnigidir', 'do·ommalgg',
                         '*']:
                if not actpas:
                    if not rel:
                        pos = "PVP"
    if An1 in ['preposition, with dat; leniting']:
        if not An2:
            if An3 in ['díṡruthaigidir']:
                if not actpas:
                    if not rel:
                        pos = "PVP"

    # Assign Infixed Pronouns (IFP)
    if An1 in ['pronoun, infixed, class A',
               'pronoun, infixed, class B',
               'pronoun, infixed, class C']:
        if An2 in ['1sg',
                   '3sg m', '3sg n (leniting)', '3sg f (geminating)', '3sg f (sometimes nasalizing)',
                   '1pl',
                   '3pl']:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "IFP"

    # Assign Prefixing particles (mí-, so-, do-) (PFX)
    if An1 == 'particle':
        if An2 in ['prefix', 'prefix, negative', 'prefix and preverb', 'prefix, privative']:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PFX"
            elif An3 in ['composition form', '*']:
                if not actpas:
                    if not rel:
                        pos = "PFX"

    # Assign Unknown Words (UNK)
    if not An1:
        if not An2:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = 'UNK'
    elif An1 == 'unclear':
        if not An2:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = 'UNK'

    # Break if a UD POS cannot be assigned, else, return POS
    if not test_unknown:
        if pos == "unknown":
            return 1/0
        else:
            return pos
    # Return POS even if it is unknown/no UD POS can be assigned
    elif test_unknown:
        return pos


# Loops through all glossed words, finds their tags and passes them to the clean_analysis function.
# Where tags cannot be cleaned by the function, all instances of the tag are printed.
def loop_tags(taglist, test_unknown=False):
    # all_pos = open_obj("All POS Combos Used.pkl")
    new_poslist = list()
    for full_tag in taglist:
        glossnum = full_tag[0]
        word = clean_word(full_tag[1])
        trans = full_tag[2]
        tag = clean_onetag(full_tag[3:8] + [trans])
        gloss = clean_gloss(full_tag[8])
        # glosstrans = full_tag[9]
        # assembled_tag = [glossnum, word, trans, tag, gloss, glosstrans]
        try:
            pos_tag = clean_analysis(tag, test_unknown)
            full_tag.append(pos_tag)
            new_poslist.append(full_tag)
        except:
            print("Broke at gloss no. {}\n'{}', in gloss, '{}'.\n"
                  "url: http://www.stgallpriscian.ie/index.php?id={}&an=1\n"
                  "Analysis: {}\n\nSimilar tags:".format(glossnum, word, gloss, glossnum, tag))
            for comp in taglist:
                if clean_onetag(comp[3:8]) == tag[:-1]:
                    comp_glossnum = comp[0]
                    comp_word = clean_word(comp[1])
                    comp_trans = str(comp[2])
                    comp_tag = clean_onetag(comp[3:8])
                    comp_gloss = clean_gloss(comp[8])
                    print(comp_tag, comp_glossnum, "'" + comp_word + "',", "'" + comp_trans + "',",
                          "in: '" + comp_gloss +
                          "' - http://www.stgallpriscian.ie/index.php?id={}&an=1".format(comp_glossnum))
            return "\nLoop Broken!\n"
    return new_poslist


# Find Percentage of Corpus POS Tagged
def percent_complete(excel_data):
    tagged_list = loop_tags(excel_data, True)
    tagged_count = 0
    all_count = len(tagged_list)
    for i in tagged_list:
        if i[-1] != 'unknown':
            tagged_count += 1
    tagged_percent = (100/all_count) * tagged_count
    print("Total number of analysed tokens in Bauer's corpus: {}".format(all_count))
    print("Number of tokens POS tagged: {}".format(tagged_count))
    print("Percentage of tokens tagged: {}%".format(tagged_percent))
    print()


percent_complete(analyses)

# # POS Tag Each Gloss and Return either POS list or Breakpoint
# loop_tags(analyses)
print(loop_tags(analyses))

# # List each Token and its POS
# for i in loop_tags(analyses, True):
#     print("'" + i[1] + "',", i[-1])


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


# # Count total potential POS tag combinations
# # Count, print and graph the number of POS tag combinations which are used a given number of times
# # e.g. if there are 18 tags used only once, 10 tags used 5 times, and 2 tags used 50 times, count and graph this info.
# ordered_tagcombos = open_obj("All Pos Combos Used.pkl")
# print("Total Tags: {}".format(len(ordered_tagcombos)))
# tag_usage = list()
# for tag in ordered_tagcombos:
#     # for each tag combination used by Bauer
#     count = 0
#     for an in analyses:
#         # check each analysis against each possible tag combination used
#         if tag == clean_onetag(an[3:8]):
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


# # FUNCTION TESTS:


# # Test clean_onetag function
# for tag in analyses:
#     print(clean_onetag(tag[3:8]))


# # Test findall_thistag, findall_nulltag, findall_excltag and clean_wordlist functions

# # Finds all of a given tag type from various levels
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


# # Find all instances of a given tag
# test_taglist = findall_thistag(analyses, A1_list[2])
# # # find all instances of a given tag where another tag level is not null
# # test_taglist = findall_thistag(analyses, A1_list[1])
# # test_taglist = findall_notnulltag(test_taglist, 4)
# for tag in clean_wordlist(test_taglist):
#     print(tag)


# # Test all POS combinations utilised in the corpus to ensure they are captured in all .pkl files
# # notlist should be empty, if not check to see combos in notlist do not appear in allpos, and why not
# # allpos is the sorted list of all POS combinations used by Bauer
# # notlist is a collection of cleaned tags taken straight from 'SG. Combined Data.xlsx'
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

