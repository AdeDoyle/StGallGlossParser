
from Clean_ExcelLists import create_data_combo
from Pickle import open_obj, save_obj
from OpenXlsx import list_xlsx
from Clean_Glosses import clean_gloss, clean_word, clean_lemma
import matplotlib.pyplot as plt
import re
from conllu import parse


try:
    analyses = list_xlsx("SG. Combined Data", "Sheet 1")
except FileNotFoundError:
    print(create_data_combo())
    analyses = list_xlsx("SG. Combined Data", "Sheet 1")
# # Run the functions below to create the following .pkl files from spreadsheet, "SG. Combined Data"
try:
    A1_list = open_obj("A1 List.pkl")
    A2_list = open_obj("A2 List.pkl")
    A3_list = open_obj("A3 List.pkl")
    actpas_list = open_obj("Active_Passive List.pkl")
    rel_list = open_obj("Relative Options List.pkl")
    Tr_list = open_obj("Translations List.pkl")
except FileNotFoundError:
    pass


# Collect lists of Bauer's original POS-tags, including:
#    Analysis levels 1-3,
#    Verb information (active/passive, relativity),
#    Translation/word-meaning
def list_tag_levels(excel_list):
    noA1 = list()
    testA1 = list()
    noA2 = list()
    testA2 = list()
    noA3 = list()
    testA3 = list()
    testActPas = list()
    testRel = list()
    testTrans = list()
    for i in excel_list:
        A1 = i[5]
        A2 = i[6]
        A3 = i[7]
        vb_actpas = i[8]
        vb_rel = i[9]
        Tr = i[4]
        if not A1:
            noA1.append(i)
        elif A1.strip() not in testA1:
            testA1.append(A1.strip())
        if not A2:
            noA2.append(i)
        elif A2.strip() not in testA2:
            testA2.append(A2.strip())
        if not A3:
            noA3.append(i)
        elif A3.strip() not in testA3:
            A3_clean = A3.strip()
            if A3_clean[0] != "*":
                testA3.append(A3.strip())
            else:
                testA3.append("*")
        if vb_actpas:
            testActPas.append(vb_actpas.strip())
        if vb_rel:
            testRel.append(vb_rel.strip())
        if Tr:
            testTrans.append(Tr.strip())
    return [testA1, testA2, testA3, testActPas, testRel, testTrans, noA1, noA2, noA3]


raw_lists = list_tag_levels(analyses)
noA1 = raw_lists[6]
noA2 = raw_lists[7]
noA3 = raw_lists[8]


# Sort lists of Bauer's original POS-tags, including:
#    Analysis levels 1-3,
#    Verb information (active/passive, relativity),
#    Translation/word-meaning
def sort_tag_levels(tag_levels_list):
    sorted_A1 = sorted(list(set(tag_levels_list[0]))) + [False]
    sorted_A2 = sorted(list(set(tag_levels_list[1]))) + [False]
    sorted_A3 = sorted(list(set(tag_levels_list[2]))) + [False]
    sorted_actpas = sorted(list(set(tag_levels_list[3]))) + [False]
    sorted_rel = sorted(list(set(tag_levels_list[4]))) + [False]
    sorted_trans = sorted(list(set(tag_levels_list[5]))) + [False]
    return [sorted_A1, sorted_A2, sorted_A3, sorted_actpas, sorted_rel, sorted_trans]


# Save lists of Bauer's original POS-tags as .pkl files, including:
    # Analysis levels 1-3,
    # Verb information (active/passive, relativity),
    # Translation/word-meaning
def save_sorted_tags(sorted_tags):
    sorted_A1 = sorted_tags[0]
    save_obj("A1 List", sorted_A1)
    sorted_A2 = sorted_tags[1]
    save_obj("A2 List", sorted_A2)
    sorted_A3 = sorted_tags[2]
    save_obj("A3 List", sorted_A3)
    sorted_actpas = sorted_tags[3]
    save_obj("Active_Passive List", sorted_actpas)
    sorted_rel = sorted_tags[4]
    save_obj("Relative Options List", sorted_rel)
    sorted_trans = sorted_tags[5]
    save_obj("Translations List", sorted_trans)
    return "Created files:\n   'A1 List.pkl'\n   'A2 List.pkl'\n   'A3 List.pkl'" \
           "\n   'Active_Passive List.pkl'\n   'Relative Options List.pkl'\n   'Translations List.pkl'"


# Cleans tags in Bauer's tag-set by removing whitespace
#    Optionally reduce recreated forms in level A3 to * to reduce complexity
def clean_onetag(taglist, clean_contractions=True):
    cleaned_tag = list()
    l3_analysis = taglist[2]
    for tag_piece in taglist:
        if tag_piece:
            tag_piece = tag_piece.strip()
            if tag_piece == l3_analysis and clean_contractions and tag_piece[0] == "*":
                tag_piece = "*"
        cleaned_tag.append(tag_piece)
    return cleaned_tag


# Create an ordered list of all unique POS-tag combinations used
def save_all_pos_combos_list(excel_list):
    alltag_combos = list()
    for entry in excel_list:
        tag_combo = entry[5:10] + [entry[4]]
        tag_combo_clean = clean_onetag(tag_combo)
        if tag_combo_clean not in alltag_combos:
            alltag_combos.append(tag_combo_clean)
    sorted_tag_combos = sorted(alltag_combos, key=lambda s: [(e is False, e is True, e) for e in s])
    save_obj("All POS Combos Used", sorted_tag_combos)
    return "Created file: 'All POS Combos Used.pkl'"


# Count total potential POS tag combinations, print total
# Count the number times each unique POS tag is used, return a list of unique tags with their use-count
def count_tag_usage(ordered_list, full_list):
    print(f"Total Tags: {len(ordered_list)}")
    tag_usage = list()
    for tag in ordered_list:
        # for each tag combination used by Bauer
        count = 0
        for an in full_list:
            # check each analysis against each possible tag combination used
            if tag == clean_onetag(an[5:10] + [an[4]]):
                # if the tags match, increase the usage-count for this tag
                count += 1
        # add the total useage-count to the tag
        tag = [count] + tag
        # save the updated tag to the tag_usage list
        tag_usage.append(tag)
    return tag_usage


# As above for new UD POS tags only
def count_pos_usage(file):
    with open(file, "r", encoding="utf-8") as conllu_file:
        sentences = parse(conllu_file.read())
    ordered_list = list()
    full_list = list()
    for tok_list in sentences:
        for tok_data in tok_list:
            tok_pos = tok_data["upos"]
            if tok_pos not in ordered_list:
                ordered_list.append(tok_pos)
            full_list.append(tok_pos)
    ordered_list.sort()
    print(f"Total Tags: {len(ordered_list)}")
    pos_usage = list()
    # for each unique POS
    for pos in ordered_list:
        count = 0
        # check the unique POS against every POS used
        for an in full_list:
            # if the POS match, increase the usage-count for this POS by one
            if pos == an:
                count += 1
        # add the total useage-count to the POS
        pos = [count] + [pos]
        # save the updated tag to the tag_usage list
        pos_usage.append(pos)
    return pos_usage


# As above for new UD POS tags with features
def count_feat_usage(file):
    with open(file, "r", encoding="utf-8") as conllu_file:
        sentences = parse(conllu_file.read())
    ordered_list = list()
    full_list = list()
    for tok_list in sentences:
        for tok_data in tok_list:
            tok_pos = tok_data["upos"]
            tok_feats_dict = tok_data["feats"]
            tok_feats_list = list()
            if tok_feats_dict:
                for key in tok_feats_dict:
                    tok_feats_list.append(f'{key}={tok_feats_dict[key]}')
            tok_feats = " | ".join(tok_feats_list)
            combined_pos = tok_pos
            if tok_feats:
                combined_pos = f'{tok_pos} {tok_feats}'
            if combined_pos not in ordered_list:
                ordered_list.append(combined_pos)
            full_list.append(combined_pos)
    ordered_list.sort()
    print(f"Total Tags: {len(ordered_list)}")
    pos_usage = list()
    # for each unique POS
    for pos in ordered_list:
        count = 0
        # check the unique POS against every POS used
        for an in full_list:
            # if the POS match, increase the usage-count for this POS by one
            if pos == an:
                count += 1
        # add the total useage-count to the POS
        pos = [count] + [pos]
        # save the updated tag to the tag_usage list
        pos_usage.append(pos)
    return pos_usage


# Count, print and graph the number of POS tag combinations which are used a given number of times
# e.g. if there are 18 tags used only once, 10 tags used 5 times, and 2 tags used 50 times, count and graph this info
def plot_tag_use(tags_with_use_count):
    tag_usage = list()
    for use_count_tag in tags_with_use_count:
        tag_usage.append(use_count_tag[0])
    # count the number of tags used each given number of times and add [count of use-count, use-count] to ordered list
    tags_usecount = list()
    alltagcount = sorted(tag_usage)
    uniquetagscount = sorted(set(tag_usage))
    for i in uniquetagscount:
        tagusecount = alltagcount.count(i)
        tags_usecount.append([i, tagusecount])
    # plot 'use-count' and 'count of use-count' on X and Y axes respectively
    X = list()
    Y = list()
    # identify highest number 'count of use-count' to use as an upper limit
    high_usecount = tags_usecount[-1][0]
    for i in range(high_usecount + 1):
        for j in tags_usecount:
            usecount = j[0]
            if usecount == i:
                countnum = j[1]
                X.append(usecount)
                Y.append(countnum)
                print("No. of tags used {} time(s): {}".format(usecount, countnum))
            elif usecount < i:
                X.append(i)
                Y.append(0)
            else:
                break
    plt.plot(X, Y)
    plt.title("Graph of Tag Usage in St. Gall Glosses")
    plt.xlabel("Number of Times a Tag Is Used")
    plt.ylabel("Number of Tags Used X Times")
    plt.show()


def plot_all_tag_use(tags_with_use_count, tags2, tags3):
    tag_usage = list()
    for use_count_tag in tags_with_use_count:
        tag_usage.append(use_count_tag[0])
    # count the number of tags used each given number of times and add [count of use-count, use-count] to ordered list
    tags_usecount = list()
    alltagcount = sorted(tag_usage)
    uniquetagscount = sorted(set(tag_usage))
    for i in uniquetagscount:
        tagusecount = alltagcount.count(i)
        tags_usecount.append([i, tagusecount])
    # plot 'use-count' and 'count of use-count' on X and Y axes respectively
    X = list()
    Y = list()
    # identify highest number 'count of use-count' to use as an upper limit
    high_usecount = tags_usecount[-1][0]
    for i in range(high_usecount + 1):
        for j in tags_usecount:
            usecount = j[0]
            if usecount == i:
                countnum = j[1]
                X.append(usecount)
                Y.append(countnum)
                print("No. of tags used {} time(s): {}".format(usecount, countnum))
            elif usecount < i:
                X.append(i)
                Y.append(0)
            else:
                break
    tag_usage = list()
    for use_count_tag in tags2:
        tag_usage.append(use_count_tag[0])
    # count the number of tags used each given number of times and add [count of use-count, use-count] to ordered list
    tags_usecount = list()
    alltagcount = sorted(tag_usage)
    uniquetagscount = sorted(set(tag_usage))
    for i in uniquetagscount:
        tagusecount = alltagcount.count(i)
        tags_usecount.append([i, tagusecount])
    # plot 'use-count' and 'count of use-count' on X and Y axes respectively
    Q = list()
    U = list()
    # identify highest number 'count of use-count' to use as an upper limit
    high_usecount = tags_usecount[-1][0]
    for i in range(high_usecount + 1):
        for j in tags_usecount:
            usecount = j[0]
            if usecount == i:
                countnum = j[1]
                Q.append(usecount)
                U.append(countnum)
                print("No. of tags used {} time(s): {}".format(usecount, countnum))
            elif usecount < i:
                Q.append(i)
                U.append(0)
            else:
                break
    tag_usage = list()
    for use_count_tag in tags3:
        tag_usage.append(use_count_tag[0])
    # count the number of tags used each given number of times and add [count of use-count, use-count] to ordered list
    tags_usecount = list()
    alltagcount = sorted(tag_usage)
    uniquetagscount = sorted(set(tag_usage))
    for i in uniquetagscount:
        tagusecount = alltagcount.count(i)
        tags_usecount.append([i, tagusecount])
    # plot 'use-count' and 'count of use-count' on X and Y axes respectively
    M = list()
    N = list()
    # identify highest number 'count of use-count' to use as an upper limit
    high_usecount = tags_usecount[-1][0]
    for i in range(high_usecount + 1):
        for j in tags_usecount:
            usecount = j[0]
            if usecount == i:
                countnum = j[1]
                M.append(usecount)
                N.append(countnum)
                print("No. of tags used {} time(s): {}".format(usecount, countnum))
            elif usecount < i:
                M.append(i)
                N.append(0)
            else:
                break
    plt.plot(X, Y, Q, U, M, N)
    plt.title("Graph of Tag Usage in St. Gall Glosses")
    plt.xlabel("Number of Times a Tag Is Used")
    plt.ylabel("Number of Tags Used X Times")
    plt.show()


# Get all entries for a given POS-tag at any level
def findall_thistag(wordlist, tag, tag_level=1):
    tag_level = tag_level - 1
    taglist = list()
    for word_data in wordlist:
        entry_tag = word_data[5 + tag_level]
        if entry_tag == tag:
            taglist.append(word_data)
    return taglist


# Get any entries excluding a given POS-tag at any level
def findall_excltag(wordlist, excl_tag, tag_level=1):
    tag_level = tag_level - 1
    taglist = list()
    for word_data in wordlist:
        tag = word_data[5 + tag_level]
        if tag != excl_tag:
            taglist.append(word_data)
    return taglist


# Get all entries that are not null for a given level of POS-tag
def findall_notnulltag(wordlist, tag_level=1):
    tag_level = tag_level - 1
    taglist = list()
    for word_data in wordlist:
        search_tag = word_data[5 + tag_level]
        if search_tag:
            taglist.append(word_data)
    return taglist


# Reduces contents of wordlist to only include gloss number, word and POS-tag information
def clean_wordlist(wordlist):
    new_wordlist = list()
    for i in wordlist:
        new_wordlist.append([i[0], clean_word(i[2])] + clean_onetag(i[5:10]))
    return new_wordlist


# Takes a single tag combination form the Sg. corpus, changes it to a simple POS tag.
def clean_analysis(taglist, test_unknown=False):
    An1 = taglist[0]
    An2 = taglist[1]
    An3 = taglist[2]
    actpas = taglist[3]
    rel = taglist[4]
    trans = taglist[5]
    pos = "unknown"

    #                                         NOUNS & PRONOUNS
    # Assign Nouns (NOUN)
    if An1 == 'noun':
        if An2 in ['m, o', 'n, o', 'f, ā', 'm, i̯o', 'n, i̯o', 'f, i̯ā',
                   'm, i', 'n, i', 'f, i', 'f, ī', 'm, u', 'n, u', 'f, u',
                   'm, dent.', 'f, d', 'm, k', 'f, k', 'm, n', 'n, n', 'f, n', 'm, (n)k', 'm, nt', 'n, nt', 'f, nt',
                   'm, g', 'm, r', 'f, r', 'n, s', 'n, s (?)', 'm, t', 'n, t', 'f, t',
                   'm', 'f', 'n', 'm and n', 'm and f', 'm, and f', '[n] ?', 'f, ?', 'f and m', 'f and n',
                   'o', 'o (?)', 'o (gender uncertain)', 'o [n ?]', 'i̯o', 'i', 'u (?)',
                   'm, o (?)', '[m] o', '[m, o]', 'm and n, o', 'm and n, o (?)', 'm, o and u', 'm, o orig. n',
                   'm, o orig. n, s (?)', 'm, o and f, ā', 'm, o, later also f, ā', 'm, o also f, ā and i',
                   'n, o (?)', 'n (?), o', '[n], o', '[n, o]', 'n and m, o', 'n, o (m, o?)', 'n, o, later m, o',
                   'n, o and u', 'n, o and f, ā',
                   'm, i̯o (?)', '[m, ?] i̯o', 'm or n, i̯o', 'm, i̯o and i',
                   'm, [i]', '[m] i', 'm, i (?)', 'm, and f, i',
                   'm, u (?)', 'm u (?)', '[m] u', '[m, ?] u', '[m, u]', 'm, u and o', 'm, u and n, o',
                   'm, t and f, t',
                   '[n], i̯o', 'n, i̯o & adjective', 'n, u or o', 'n and m, u', 'n, s and n, o',
                   'f, ā (?)', '[f, ā]', 'f, ā; adjective', 'f, ā, later also m, o', 'f, ā and i',
                   'f, mixed ā-, ī-, i-', 'f, ā and m, u', 'f, ā; also f, n',
                   'f, i̯a (?)', 'f, i̯ā (?)', '[f, i̯ā]', 'f, i̯ā & m, i̯o',
                   'f, i (?)', 'f, i, ī', 'f, i and n', 'f, i, later also k', 'f, n (?)',
                   'gender not attested in OIr.', 'gender unknown, i-stem', 'uncertain gender',
                   'unknown declension', 'irregular']:
            if An3 in ['nom.sg.', 'nom.sg.masc.',
                       'voc.sg.',
                       'acc.sg.',
                       'gen.sg.',
                       'dat.sg.', 'dat.sg.masc.', 'dat.sg. (?)',
                       'nom.pl.', 'nom.pl.neut.',
                       'voc.pl.',
                       'acc.pl.', 'acc.pl.masc.', 'acc.pl.neut.',
                       'gen.pl.',
                       'dat.pl.',
                       'nom.du.', 'acc.du.', 'gen.du.', 'dat.du.',
                       'acc./dat.sg.',
                       'nom.sg.neut.', 'nom.sg.fem.',
                       'gen.sg.neut.',
                       'dat.sg.neut.',
                       'gen.pl.fem.',
                       'composition form']:
                if An3 == 'acc./dat.sg.':
                    An3 = 'dat.sg.'
                case = False
                casepat = re.compile(r'(nom|voc|acc|gen|dat)\.')
                casepatiter = casepat.finditer(An3)
                for find_case in casepatiter:
                    case = find_case.group()
                number = False
                numdict = {'.sg.': 'Sing', '.du.': 'Dual', '.pl.': 'Plur'}
                numpat = re.compile(r'\.(sg|du|pl)\.')
                numpatiter = numpat.finditer(An3)
                for find_num in numpatiter:
                    number = find_num.group()
                features = False
                if An3 == 'composition form':
                    features = 'Prefix=Yes'
                elif case and number:
                    features = f'Case={case.capitalize()[:-1]} | Number={numdict.get(number)}'
                if not actpas:
                    if not rel:
                        pos = f'NOUN {features}'
            elif not An3:
                if not actpas:
                    if not rel:
                        pos = "NOUN"
    if An1 == 'noun and adjective':
        if An2 in ['o, ā', 'i']:
            if An3 in ['nom.sg.neut.', 'acc.sg.', 'nom.pl.']:
                case = False
                casepat = re.compile(r'(nom|acc)\.')
                casepatiter = casepat.finditer(An3)
                for find_case in casepatiter:
                    case = find_case.group()
                number = False
                numdict = {'.sg.': 'Sing', '.pl.': 'Plur'}
                numpat = re.compile(r'\.(sg|pl)\.')
                numpatiter = numpat.finditer(An3)
                for find_num in numpatiter:
                    number = find_num.group()
                features = f'Case={case.capitalize()[:-1]} | Number={numdict.get(number)}'
                if not actpas:
                    if not rel:
                        pos = f'NOUN {features}'
        elif not An2:
            if An3 in ['nom.sg.fem.']:
                if not actpas:
                    if not rel:
                        pos = "NOUN Case=Nom | Number=Sing"
    if An1 == 'adjective':
        if An2 == 'u':
            if An3 in ['nom.sg.', 'nom.sg.neut.', 'dat.sg.']:
                case = False
                casepat = re.compile(r'(nom|dat)\.')
                casepatiter = casepat.finditer(An3)
                for find_case in casepatiter:
                    case = find_case.group()
                if not actpas:
                    if not rel:
                        if "as noun:" in trans:
                            pos = f'NOUN Case={case.capitalize()[:-1]} | Number=Sing'

    # Assign Proper Nouns (PROPN)
    if An1 == 'noun, proper':
        if not An2:
            if An3 in ['nom.sg.', 'voc.sg.', 'acc.sg.', 'gen.sg.', 'dat.sg.']:
                case = False
                casepat = re.compile(r'(nom|voc|acc|gen|dat)\.')
                casepatiter = casepat.finditer(An3)
                for find_case in casepatiter:
                    case = find_case.group()
                if not actpas:
                    if not rel:
                        pos = f'PROPN Case={case.capitalize()[:-1]} | Number=Sing'
        elif An2 in ['m, i̯o', 'f, i']:
            if An3 in ['nom.sg.masc.', 'gen.sg.', 'nom.pl.']:
                case = False
                casepat = re.compile(r'(nom|gen)\.')
                casepatiter = casepat.finditer(An3)
                for find_case in casepatiter:
                    case = find_case.group()
                number = False
                numdict = {'.sg.': 'Sing', '.pl.': 'Plur'}
                numpat = re.compile(r'\.(sg|pl)\.')
                numpatiter = numpat.finditer(An3)
                for find_num in numpatiter:
                    number = find_num.group()
                if not actpas:
                    if not rel:
                        pos = f'PROPN Case={case.capitalize()[:-1]} | Number={numdict.get(number)}'
    if An1 == 'noun, proper':
        if not An2:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PROPN"

    # Assign Pronouns (PRON)
    # Personal Pronouns
    numdict = {'sg': 'Sing', 'pl': 'Plur'}
    gend_dict = {"m": "Masc", "n": "Neut", "f": "Fem"}
    if An1 == 'pronoun, personal':
        person = False
        number = False
        gender = False
        if An2 in ['1sg',
                   '2sg',
                   '3sg m', '3sg f', '3sg n',
                   '3pl']:
            perspat = re.compile(r'\d\w{2}')
            perspatiter = perspat.finditer(An2)
            for persfind in perspatiter:
                person = persfind.group()[:1]
            numpat = re.compile(r'\d\w{2}')
            numpatiter = numpat.finditer(An2)
            for numfind in numpatiter:
                number = numdict.get(numfind.group()[1:3])
            gendpat = re.compile(r'\d\w{2}( \w)?')
            gendpatiter = gendpat.finditer(An2)
            for gendfind in gendpatiter:
                gender = gend_dict.get(gendfind.group()[-1:])
            feat_list = list()
            if gender:
                feat_list.append(f'Gender={gender}')
            if number:
                feat_list.append(f'Number={number}')
            if person:
                feat_list.append(f'Person={person}')
            feat_list.append("PronType=Prs")
            features = " | ".join(feat_list)
            if not An3:
                if not actpas:
                    if not rel:
                        pos = f"PRON {features}"
            elif An3 in ['voc.sg.', 'composition form', 'formal pred, immediately after copula']:
                if not actpas:
                    if not rel:
                        pos = f"PRON {features}"
    # Assign Indefinite Pronouns (PRON)
    if An1 == 'pronoun, non-neuter':
        if not An2:
            if An3 in ['nom.sg.', 'acc.sg.', 'dat.sg.']:
                if not actpas:
                    if not rel:
                        pos = "PRON PronType=Ind"
    indpron_case = ['nom.sg.', 'nom.sg.masc.', 'nom.sg.neut.', 'nom.sg.fem.',
                    'acc.sg.', 'acc.sg.masc.', 'acc.sg.neut.', 'acc.sg.fem.',
                    'gen.sg.', 'gen.sg.masc.', 'gen.sg.neut.', 'gen.sg. masc./neut.', 'gen.sg.fem.',
                    'dat.sg.', 'dat.sg.masc.', 'dat.sg.neut.', 'dat.sg.fem',
                    'nom.pl.',
                    'acc.pl.', 'acc.pl.masc.',
                    'dat.pl.masc.', 'dat.pl.fem.',
                    'nom.du.fem.',
                    'composition form']
    if An1 in ['adjective, pronominal (preceding noun)', 'adjective, indefinite pronominal',
               'pronoun, indefinite', 'pronoun, indeclinable']:
        if not An2:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PRON PronType=Ind"
            elif An3 in indpron_case:
                if not actpas:
                    if not rel:
                        pos = "PRON PronType=Ind"
        elif An2 == 'm':
            case = False
            number = False
            if An3 in indpron_case:
                casepat = re.compile(r'\w{3}\.')
                casepatiter = casepat.finditer(An3)
                for casefind in casepatiter:
                    case = casefind.group()[:-1].capitalize()
                numpat = re.compile(r'\.\w{2}\.')
                numpatiter = numpat.finditer(An3)
                for numfind in numpatiter:
                    number = numdict.get(numfind.group()[1:-1])
                if not actpas:
                    if not rel:
                        pos = f"PRON Case={case} | Gender=Masc | Number={number} | PronType=Ind"
    # Assign Suffixed Pronouns (PRON)
    if An1 == 'pronoun, suffixed':
        if An2 in ['3sg m, n', '3sg m, n (nasalizing)']:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PRON Gender=Masc,Neut | Number=Sing | Person=3 | PronType=Prs"
    # Reflexive Pronouns
    if An1 == 'pronoun, reflexive':
        if not An2:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PRON PronType=Prs | Reflex=Yes"
            elif An3 in ['1sg.', '2sg.', '3sg.', '3sg.masc.', '3sg.neut.', '3sg.fem.', '3pl.']:
                if not actpas:
                    if not rel:
                        pos = "PRON PronType=Prs | Reflex=Yes"
    # Possessive Pronouns
    if An1 == 'pronoun, possessive, stressed':
        if An2 in ['3sg and pl']:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PRON Person=3 | Poss=Yes | PronType=Prs"
            elif An3 in ['sg.', 'pl.']:
                person = False
                numdict = {'sg.': 'Sing', 'pl.': 'Plur'}
                perspat = re.compile(r'(sg|pl)\.')
                perspatiter = perspat.finditer(An3)
                for pers_find in perspatiter:
                    person = numdict.get(pers_find.group())
                if not actpas:
                    if not rel:
                        pos = f"PRON Number={person} | Person=3 | Poss=Yes | PronType=Prs"
    if An1 == 'pronoun, possessive, unstressed':
        if An2 in ['1sg (leniting)',
                   '2sg',
                   '3sg m, n (leniting)', '3sg f',
                   '1pl (nasalizing)',
                   '3pl (nasalizing)']:
            person = False
            number = False
            gender = False
            numdict = {'sg': 'Sing', 'pl': 'Plur'}
            perspat = re.compile(r'\d(sg|pl)( \w)?')
            perspatiter = perspat.finditer(An2)
            for pers_find in perspatiter:
                pers_combo = pers_find.group()
                person = pers_combo[0]
                number = numdict.get(pers_combo[1:3])
                if " " in pers_combo:
                    gender = pers_combo[-1]
                    if gender == "f":
                        gender = "Fem"
                    else:
                        gender = "Masc,Neut"
            feat_list = list()
            if not An3:
                if gender:
                    feat_list.append(f'Gender={gender}')
                if number:
                    feat_list.append(f'Number={number}')
                if person:
                    feat_list.append(f'Person={person}')
                features = " | ".join(feat_list)
                if not actpas:
                    if not rel:
                        pos = f"PRON {features} | Poss=Yes | PronType=Prs"
            elif An3 in ['neut.', '3sg.neut.']:
                gender = "Neut"
                feat_list.append(f'Gender={gender}')
                if number:
                    feat_list.append(f'Number={number}')
                if person:
                    feat_list.append(f'Person={person}')
                features = " | ".join(feat_list)
                if not actpas:
                    if not rel:
                        pos = f"PRON {features} | Poss=Yes | PronType=Prs"
    # Emphatic Pronouns
    if An1 == 'particle, emphatic pronominal':
        if An2 in ['1sg', '2sg', '3sg m, n', '3sg f',
                   '1pl', '2pl', '3pl']:
            person = An2[0]
            number = False
            gender = False
            feat_list = list()
            if " m, n" in An2:
                gender = "Masc,Neut"
            elif " f" in An2:
                gender = "Fem"
            if "sg" in An2:
                number = "Sing"
            elif "pl" in An2:
                number = "Plur"
            if not An3:
                if gender:
                    feat_list.append(f'Gender={gender}')
                if number:
                    feat_list.append(f'Number={number}')
                feat_list.append(f'Person={person}')
                feat_list.append("PronType=Emp")
                features = " | ".join(feat_list)
                if not actpas:
                    if not rel:
                        pos = f"PRON {features}"
            elif An3 in ['masc.', '3sg.masc.']:
                feat_list.append(f'Gender=Masc')
                if number:
                    feat_list.append(f'Number={number}')
                feat_list.append(f'Person={person}')
                feat_list.append("PronType=Emp")
                features = " | ".join(feat_list)
                if not actpas:
                    if not rel:
                        pos = f"PRON {features}"
    # Anaphoric Pronouns
    if An1 == 'pronoun, anaphoric':
        if An2 in ['stressed', 'neuter, stressed']:
            if An3 in ['nom.sg.',
                       'acc.sg.', 'acc.sg.masc.', 'acc.sg.neut.',
                       'dat.sg.', 'dat.sg.masc.', 'dat.sg.neut.', 'dat.sg.fem',
                       'acc.pl.', 'acc.pl.masc.',
                       'dat.pl.', 'dat.pl.neut.']:
                case = False
                gender = False
                number = False
                feat_list = list()
                case = An3[:3].capitalize()
                if ".masc." in An3:
                    gender = "Masc"
                elif ".neut." in An3:
                    gender = "Neut"
                elif ".fem" in An3:
                    gender = "Fem"
                if ".sg." in An3:
                    number = "Sing"
                elif ".pl." in An3:
                    number = "Plur"
                if case:
                    feat_list.append(f'Case={case}')
                if gender:
                    feat_list.append(f'Gender={gender}')
                if number:
                    feat_list.append(f'Number={number}')
                feat_list.append("PronType=Ana")
                features = " | ".join(feat_list)
                if not actpas:
                    if not rel:
                        pos = f"PRON {features}"
            elif not An3:
                if not actpas:
                    if not rel:
                        pos = "PRON PronType=Ana"
        if An2 == 'neuter, stressed':
            if An3 in ['acc.sg.', 'dat.sg.']:
                if not actpas:
                    if not rel:
                        pos = "PRON PronType=Ana"
        elif An2 == 'enclitic':
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PRON PronType=Ana"
            elif An3 in ['nom.sg.', 'nom.sg.masc.', 'nom.sg.neut.', 'nom.sg.fem.',
                         'acc.sg.', 'acc.sg.fem.',
                         'gen.sg.', 'gen.sg.neut.', 'gen.sg.fem.',
                         'dat.sg.fem',
                         'nom.pl.', 'nom.pl.masc.', 'nom.pl.fem.',
                         'acc.pl.fem.',
                         'dat.pl.fem.']:
                if not actpas:
                    if not rel:
                        pos = "PRON PronType=Ana"
        elif An2 == 'indeclinable neuter enclitic':
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PRON PronType=Ana"
    # Assign Interrogative Pronouns
    if An1 in ['pronoun, interrogative and indefinite']:
        if not An2:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PRON PronType=Int"
    if An1 == 'pronoun':
        if An2 == 'interrogative':
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PRON PronType=Int"
        elif An2 == 'negative interrogative':
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PRON Polarity=Neg | PronType=Int"

    #                                        ARTICLES & DETERMINERS
    # Assign Articles (DET)
    gend_dict = {"m": "Masc", "n": "Neut", "fem": "Fem"}
    numdict = {'.sg.': 'Sing', '.du.': 'Dual', '.pl.': 'Plur'}
    if An1 == 'article':
        if An2 in ['m', 'n', 'fem']:
            gender = gend_dict.get(An2)
            if An3 in ['nom.sg.', 'nom.sg', 'nom.sg. + í 1',
                       'acc.sg.', 'acc.',
                       'gen.sg.', 'gen.sg. + í 1',
                       'dat.sg.',
                       'nom.pl.', 'nom.pl. + í 1',
                       'acc.pl.',
                       'gen.pl.', 'gen.pl. + í 1',
                       'nom.du.', 'acc.du.', 'gen.du.']:
                case = False
                casepat = re.compile(r'(nom|acc|gen|dat)\.')
                casepatiter = casepat.finditer(An3)
                for find_case in casepatiter:
                    case = find_case.group()
                number = False
                numpat = re.compile(r'\.(sg|du|pl)\.?')
                numpatiter = numpat.finditer(An3)
                for find_num in numpatiter:
                    number = find_num.group()
                    if number[-1] != ".":
                        number = number + "."
                    number = numdict.get(number)
                if not actpas:
                    if not rel:
                        try:
                            pos = f'DET Case={case.capitalize()[:-1]} | Gender={gender} ' \
                                  f'| Number={number} | PronType=Art'
                        except UnboundLocalError:
                            pos = f'DET Case={case.capitalize()[:-1]} | Gender={gender} | PronType=Art'
    # Assign Pronominal Articles - the '(s)in(d) and '(s)naib' endings of pronouns (DET)
    if An1 == 'article':
        if An2 in ['m', 'n', 'fem']:
            gender = gend_dict.get(An2)
            if An3 in ['acc.sg. + ar 1',
                       'acc.pl. + fo 1',
                       'acc.sg. + for 1', 'acc.pl. + for 1',
                       'acc.sg. + fri', 'acc.pl. + fri',
                       'acc.sg + i 2', 'acc.pl. + i 2',
                       'acc.sg. + imm 1',
                       'acc.sg. + la', 'acc.pl. + la',
                       'acc.pl. + tar',
                       'acc.sg. + tre 1',
                       'dat.sg. + a 5',
                       'dat.sg. + ar 1',
                       'dat.sg. + de 1', 'dat.pl + de 1',
                       'dat.sg. + do 1', 'dat.pl + do 1',
                       'dat.sg. + fo 1',
                       'dat.sg. + for 1', 'dat.pl + for 1',
                       'dat.sg. + i 2', 'dat.pl. + i 2',
                       'dat.sg. + íar 1',
                       'dat.sg. + ó 1', 'dat.pl. + ó 1',
                       'dat.sg. + oc', 'dat.pl. + oc']:
                case = False
                casepat = re.compile(r'(nom|acc|gen|dat)\.')
                casepatiter = casepat.finditer(An3)
                for find_case in casepatiter:
                    case = find_case.group()
                number = False
                numpat = re.compile(r'\.(sg|du|pl)[. ]')
                numpatiter = numpat.finditer(An3)
                for find_num in numpatiter:
                    numcheck = find_num.group()
                    if numcheck[-1] == " ":
                        numcheck = numcheck[:-1] + "."
                    number = numdict.get(numcheck)
                if not actpas:
                    if not rel:
                        pos = f'DET AdpType=Prep | Case={case.capitalize()[:-1]} | Gender={gender} ' \
                              f'| Number={number} | PronType=Art'

    #                                             ADJECTIVES
    # Assign Adjectives (ADJ)
    if An1 == 'adjective':
        if An2 in ['o, ā', 'i̯o, i̯ā', 'i', 'u',
                   'o, ā, i', 'o, ā and noun', 'o, ā and adverb',
                   'prefix',
                   'u (?)', 'indeclinable (?)']:
            if An3 in ['nom.sg.', 'nom.sg.masc.', 'nom.sg.neut.', 'nom.sg.fem.',
                       'voc.sg.', 'voc.sg.fem.',
                       'acc.sg.', 'acc.sg.masc.', 'acc.sg.neut.', 'acc.sg.fem.', 'acc.sg.fem',
                       'gen.sg.', 'gen.sg.masc.', 'gen.sg.neut.', 'gen.sg.fem.',
                       'dat.sg.', 'dat.sg.masc.', 'dat.sg.neut.', 'dat.sg.fem',
                       'nom.pl.', 'nom.pl.masc.', 'nom.pl.neut.', 'nom.pl.fem.',
                       'acc.pl.', 'acc.pl.masc.', 'acc.pl.neut.', 'acc.pl.fem.',
                       'gen.pl.', 'gen.pl.masc.', 'gen.pl.neut.', 'gen.pl.fem.',
                       'dat.pl.', 'dat.pl.masc.', 'dat.pl.neut.', 'dat.pl.fem.',
                       'nom.du.neut.', 'nom.du.fem.',
                       'acc.du.masc.', 'acc.du.fem.',
                       'dat.du.', 'dat.du.neut.',
                       'dat.sg.masc + ó 1',
                       'comparative', 'superlative',
                       'clitic form', 'composition form']:
                case = False
                casepat = re.compile(r'(nom|voc|acc|gen|dat)\.')
                casepatiter = casepat.finditer(An3)
                for find_case in casepatiter:
                    case = find_case.group()
                    case = case.capitalize()[:-1]
                degree = "Pos"
                if An3 == "comparative":
                    degree = "Cmp"
                elif An3 == "superlative":
                    degree = "Sup"
                gend_dict = {"masc.": "Masc", "neut.": "Neut", "fem.": "Fem"}
                gender = False
                gendpat = re.compile(r'(masc|neut|fem)\.')
                gendpatiter = gendpat.finditer(An3)
                for gend_find in gendpatiter:
                    gender = gend_dict.get(gend_find.group())
                numdict = {'.sg.': 'Sing', '.du.': 'Dual', '.pl.': 'Plur'}
                number = False
                numpat = re.compile(r'\.(sg|du|pl)\.')
                numpatiter = numpat.finditer(An3)
                for find_num in numpatiter:
                    number = find_num.group()
                    number = numdict.get(number)
                prefix = False
                if An3 == "composition form":
                    prefix = "Yes"
                if not actpas:
                    if not rel:
                        if "as noun:" not in trans:
                            feat_list = list()
                            if case:
                                feat_list.append(f'Case={case}')
                            feat_list.append(f'Degree={degree}')
                            if gender:
                                feat_list.append(f'Gender={gender}')
                            if number:
                                feat_list.append(f'Number={number}')
                            if prefix:
                                feat_list.append(f'Prefix={prefix}')
                            features = " | ".join(feat_list)
                            pos = f'ADJ {features}'
            elif not An3:
                if not actpas:
                    if not rel:
                        pos = "ADJ Degree=Pos"
        elif not An2:
            if An3 in ['nom.sg.', 'nom.sg.masc.', 'nom.sg.neut.',
                       'acc.sg.',
                       'gen.sg.', 'gen.sg.masc.',
                       'dat.pl.masc.',
                       'in adverbial phrase i recc']:
                case = False
                casepat = re.compile(r'(nom|acc|gen|dat)\.')
                casepatiter = casepat.finditer(An3)
                for find_case in casepatiter:
                    case = find_case.group()
                    case = case.capitalize()[:-1]
                degree = "Pos"
                gend_dict = {"masc.": "Masc", "neut.": "Neut"}
                gender = False
                gendpat = re.compile(r'(masc|neut)\.')
                gendpatiter = gendpat.finditer(An3)
                for gend_find in gendpatiter:
                    gender = gend_dict.get(gend_find.group())
                numdict = {'.sg.': 'Sing', '.pl.': 'Plur'}
                number = False
                numpat = re.compile(r'\.(sg|pl)\.')
                numpatiter = numpat.finditer(An3)
                for find_num in numpatiter:
                    number = find_num.group()
                    number = numdict.get(number)
                feat_list = list()
                if case:
                    feat_list.append(f'Case={case}')
                feat_list.append(f'Degree={degree}')
                if gender:
                    feat_list.append(f'Gender={gender}')
                if number:
                    feat_list.append(f'Number={number}')
                features = " | ".join(feat_list)
                if not actpas:
                    if not rel:
                        pos = f'ADJ {features}'
            elif not An3:
                if not actpas:
                    if not rel:
                        pos = "ADJ Degree=Pos"
    if An1 == 'adjective and noun':
        if An2 in ['u']:
            if An3 in ['nom.sg.']:
                if not actpas:
                    if not rel:
                        pos = "ADJ Case=Nom | Degree=Pos | Number=Sing"
    if An1 == 'noun and adjective':
        if An2 in ['o, ā']:
            if An3 in ['comparative', 'composition form']:
                degree = "Pos"
                if An3 == "comparative":
                    degree = "Cmp"
                prefix = False
                if An3 == "composition form":
                    prefix = "Yes"
                feat_list = list()
                feat_list.append(f'Degree={degree}')
                if prefix:
                    feat_list.append(f'Prefix={prefix}')
                features = " | ".join(feat_list)
                if not actpas:
                    if not rel:
                        pos = f'ADJ {features}'

    #                                        VERBS, COPULA & ADVERBS
    # Assign Verbs (VERB)
    verb_tensepers = ['1sg.pres.ind.', '1sg.pres.subj.',
                      '1sg.pret.', '1sg.past.subj.',
                      '1sg.perf.',
                      '1sg.fut.',
                      '2sg.pres.ind.',
                      '2sg.pres.subj.',
                      '2sg.impv.',
                      '2sg.past.subj.',
                      '2sg.perf.',
                      '2sg.imperf.subj.',
                      '2sg.fut.',
                      '3sg.pres.ind.', '3sg.pres.ind.pass.', '3sg.pres.ind.rel.', '3sg.pres.pass.rel.',
                      '3sg.pres.ind.pass.rel.',
                      '3sg.cons.pres.', '3sg.cons.pres.rel.',
                      '3sg.pres.subj.', '3sg.pres.subj.pass.', '3sg.pres.subj.rel.',
                      '3sg.impv.',
                      '3sg.pret.', '3sg.pret.pass.', '3sg.pret./perf.', '3sg.past.subj.',
                      '3sg.perf.', '3sg.pass.perf.',
                      '3sg.imperf.', '3sg.imperf.pass.',
                      '3sg.imperf.subj.', '3sg.imperf.subj.pass.', '3sg.imperf.subj.pass. (perfective)',
                      '3sg.fut.', '3sg.fut.pass.', '3sg.fut.rel.', '3sg.sec.fut.', '3sg.sec.fut.pass.', '3sg.cond.',
                      '1pl.pres.ind.', '1pl.pres.ind.rel.', '1pl.pres.subj.',
                      '1pl.pret.', '1pl.past.subj.',
                      '1pl.perf.',
                      '1pl.imperf.subj.',
                      '1pl.fut.',
                      '2pl.impv.',
                      '3pl.pres.ind.', '3pl.pres.ind.pass.', '3pl.pres.ind.rel.', '3pl.pres.ind.pass.rel.',
                      '3pl.cons.pres.', '3pl.cons.pres.rel.',
                      '3pl.pres.subj.', '3pl.pres.subj.pass.', '3pl.pres.subj.rel.',
                      '3pl.pret.', '3pl.pret.pass.', '3pl.pret.rel.', '3pl.past.subj.', '3sg.past.subj.rel.',
                      '3pl.perf.', '3pl.perf.pass.', 'perf 3pl.perf.rel.',
                      '3pl.imperf.', '3pl.imperf.pass.', '3pl.imperf.subj.pass.',
                      '3pl.fut.', '3pl.fut.pass.', '3pl.fut.rel.', '3pl.sec.fut.pass.', '3pl.cond.',
                      '*']
    verb_tenseperssuffix = ['3sg.pres.ind. + suff.pron. 3sg.masc./neut.']
    verb_tensepersinfix = ['1sg.pres.ind. + infix.pron. Class A 2sg.',
                           '1sg.pres.ind. + infix.pron. Class A 3sg.masc.',
                           '1sg.pres.ind. + infix pron Class A 3sg.neut.',
                           '1sg.pres.ind. + infix.pron. Class A 3sg.fem.',
                           '1sg.pres.ind. + infix.pron. Class A 3pl.',
                           '1sg.pres.ind. + infix pron Class C 3sg.neut.',
                           '2sg.pres.ind. + infix.pron. class C 3sg.neut.',
                           '3sg.pres.ind. + inf.pron. class A 1sg.',
                           '3sg.pres.ind. + inf.pron. class A 3sg.neut.',
                           '3sg.pres.ind. + inf.pron. class A 3sg.fem.',
                           '3sg.pres.ind. + infix.pron. Class A 3pl.',
                           '3sg.pres.ind. + infix.pron. Class B 3sg.neut.',
                           '3sg.pres.ind. + infix.pron. Class B 3pl.',
                           '3sg.pres.ind. + inf.pron. class C 3sg.neut.',
                           '3sg.pres.ind. + infix.pron. Class C 3sg.neut.',
                           '3sg.pres.ind. + infix.pron. Class C 3sg.fem.',
                           '3sg.pres.ind. + infix.pron. Class C 3pl.',
                           '1pl.pres.ind. + infix.pron. Class C 3sg.neut.',
                           '3pl.pres.ind. + infix.pron. Class A 3sg.masc.',
                           '3pl.pres.ind. + infix.pron. Class A 3sg.neut.',
                           '3pl.pres.ind. + infix.pron. Class A 3pl.',
                           '3pl.pres.ind. + infix.pron. Class B 3sg.neut.',
                           '3pl.pres.ind. + infix.pron. Class C 3sg.masc.',
                           '3pl.pres.ind. + infix.pron. Class C 3sg.neut.',
                           '3pl.pres.ind. + infix.pron. Class C 3sg.fem.',
                           '3pl.pres.ind. + infix.pron. Class C 3pl.',
                           '3sg.pres.ind.pass. + inf.pron. Class A 1sg.',
                           '3sg.pres.ind.pass. + infix.pron. class A 1sg.',
                           '3sg.pres.ind.pass. + infix.pron. Class B 1sg.',
                           '3sg.pres.ind.pass. + infix pron Class B 1sg',
                           '3sg.pres.ind.pass. + infix.pron. Class B 3sg.',
                           '3pl.pres.ind.pass. + infix.pron. class C 3sg.neut.',
                           '3sg.pres.ind.rel. + inf.pron. class C 3sg.',
                           '3sg.pres.ind.rel. + petr.i.nfix.pron.',
                           '3sg.pres.subj. + infix.pron. Class A 1sg.',
                           '3sg.pres.subj. + infix.pron. Class B 3sg.neut.',
                           '3sg.pret./perf. + infix.pron. Class A 1pl.',
                           '3sg.pret./perf. + infix.pron. Class C 3sg.neut.',
                           '1sg.perf. + infix pron Class C 3sg.neut.',
                           '3sg.perf. + infix.pron. Class A 2sg.',
                           '3sg.perf. + infix.pron. Class A 3sg.masc.',
                           '3sg.perf. + infix.pron. Class A 3sg.neut.',
                           '3sg.perf. + infix.pron. Class C 3sg.neut.',
                           '3sg.perf. + infix.pron. Class C 1pl.',
                           '1pl.perf. + infix.pron. Class C 3sg.masc.',
                           '3pl.perf. + infix.pron. Class A 3sg.neut.',
                           '3pl.perf. + infix.pron. Class B 3pl.',
                           '3pl.perf. + infix.pron. Class C 3sg.neut.',
                           '3pl.imperf. + infix.pron. Class A 3sg.neut.',
                           '3pl.imperf. + infix.pron. Class C 3sg.neut.',
                           '3pl.imperf. + infix.pron. Class C 3pl.',
                           '1pl.fut. + infix.pron. Class B 3sg.neut.',
                           '3sg.sec.fut. + infix pron Class C 3sg nt']
    tensedict = {'cons.pres.': 'Pres', 'pres.': 'Pres',
                 'past.': 'Past', 'pret.': 'Past', 'perf.': 'Past', 'imperf.': 'Past',
                 'fut.': 'Fut', 'sec.fut.': 'Fut'}
    numdict = {'pl.': 'Plur', 'sg.': 'Sing'}
    mooddict = {'cond.': 'Cnd', 'sec.fut.': 'Cnd', 'impv.': 'Imp', 'ind.': 'Ind', 'subj.': 'Sub'}
    aspdict = {'cons.pres.': 'Hab', 'imperf.': 'Imp', 'perf.': 'Perf'}
    # Substantive Verb
    if An1 == 'verb':
        if An2 == 'substantive verb':
            if An3 in verb_tensepers:
                number = False
                person = False
                persnumpat = re.compile(r'\d(sg|pl)\.')
                persnumpatiter = persnumpat.finditer(An3)
                for find_persnum in persnumpatiter:
                    persnum = find_persnum.group()
                    person = persnum[:1]
                    number = numdict.get(persnum[1:])
                tense = False
                tensepat = re.compile(r'((cons\.)?pres|pret|past|(sec\.)?fut|imperf|(pret\./)?perf)\.')
                tensepatiter = tensepat.finditer(An3)
                for find_tense in tensepatiter:
                    tense = tensedict.get(find_tense.group())
                aspect = False
                asppat = re.compile(r'(cons\.pres|imperf|perf)\.')
                asppatiter = asppat.finditer(An3)
                for asp_find in asppatiter:
                    aspect = aspdict.get(asp_find.group())
                mood = False
                moodpat = re.compile(r'(ind|subj|cond|sec\.fut|impv)\.')
                moodpatiter = moodpat.finditer(An3)
                for find_mood in moodpatiter:
                    mood = mooddict.get(find_mood.group())
                voice = False
                if actpas == 'Active':
                    voice = "Act"
                elif actpas in ['Passive', 'Pass']:
                    voice = "Pass"
                relative = False
                if rel in ['Y', 'Maybe']:
                    relative = "Rel"
                feat_list = list()
                if aspect:
                    feat_list.append(f'Aspect={aspect}')
                if mood:
                    feat_list.append(f'Mood={mood}')
                else:
                    feat_list.append('Mood=Ind')
                if number:
                    feat_list.append(f'Number={number}')
                if person:
                    feat_list.append(f'Person={person}')
                if relative:
                    feat_list.append(f'PronType={relative}')
                if tense:
                    feat_list.append(f'Tense={tense}')
                elif mood == "Imp":
                    tense = "Pres"
                    feat_list.append(f'Tense={tense}')
                elif mood == "Cnd":
                    tense = "Fut"
                    feat_list.append(f'Tense={tense}')
                if voice:
                    feat_list.append(f'Voice={voice}')
                features = " | ".join(feat_list)
                pos = f'VERB {features}'
            elif An3 in verb_tensepersinfix:
                An3_only = An3.split(" + ")[0]
                number = False
                person = False
                persnumpat = re.compile(r'\d(sg|pl)\.')
                persnumpatiter = persnumpat.finditer(An3_only)
                for find_persnum in persnumpatiter:
                    persnum = find_persnum.group()
                    person = persnum[:1]
                    number = numdict.get(persnum[1:])
                tense = 'Pres'
                mood = 'Ind'
                voice = False
                if actpas == 'Active':
                    voice = "Act"
                elif actpas in ['Passive', 'Pass']:
                    voice = "Pass"
                relative = False
                if rel in ['Y', 'Maybe']:
                    relative = "Rel"
                feat_list = list()
                if mood:
                    feat_list.append(f'Mood={mood}')
                if number:
                    feat_list.append(f'Number={number}')
                if person:
                    feat_list.append(f'Person={person}')
                if relative:
                    feat_list.append(f'PronType={relative}')
                if tense:
                    feat_list.append(f'Tense={tense}')
                if voice:
                    feat_list.append(f'Voice={voice}')
                features = " | ".join(feat_list)
                pos = f'VERB {features}'
    # Copula
        elif An2 == 'copula':
            polarity = "Pos"
            if trans and "negative" in trans:
                polarity = "Neg"
            if An3 in verb_tensepers:
                number = False
                person = False
                persnumpat = re.compile(r'\d(sg|pl)\.')
                persnumpatiter = persnumpat.finditer(An3)
                for find_persnum in persnumpatiter:
                    persnum = find_persnum.group()
                    person = persnum[:1]
                    number = numdict.get(persnum[1:])
                tense = False
                tensepat = re.compile(r'((cons\.)?pres|pret|past|(sec\.)?fut|imperf|(pret\./)?perf)\.')
                tensepatiter = tensepat.finditer(An3)
                for find_tense in tensepatiter:
                    tense = tensedict.get(find_tense.group())
                aspect = False
                asppat = re.compile(r'(cons\.pres|imperf|perf)\.')
                asppatiter = asppat.finditer(An3)
                for asp_find in asppatiter:
                    aspect = aspdict.get(asp_find.group())
                mood = False
                moodpat = re.compile(r'(ind|subj|cond|sec\.fut|impv)\.')
                moodpatiter = moodpat.finditer(An3)
                for find_mood in moodpatiter:
                    mood = mooddict.get(find_mood.group())
                relative = False
                if rel in ['Y', 'Maybe']:
                    relative = "Rel"
                feat_list = list()
                if aspect:
                    feat_list.append(f'Aspect={aspect}')
                if mood:
                    feat_list.append(f'Mood={mood}')
                else:
                    feat_list.append('Mood=Ind')
                if number:
                    feat_list.append(f'Number={number}')
                if person:
                    feat_list.append(f'Person={person}')
                feat_list.append(f'Polarity={polarity}')
                if relative:
                    feat_list.append(f'PronType={relative}')
                if tense:
                    feat_list.append(f'Tense={tense}')
                elif mood == "Imp":
                    tense = "Pres"
                    feat_list.append(f'Tense={tense}')
                elif mood == "Cnd":
                    tense = "Fut"
                    feat_list.append(f'Tense={tense}')
                feat_list.append(f'VerbType=Cop')
                features = " | ".join(feat_list)
                pos = f'AUX {features}'
            elif An3 in verb_tensepersinfix:
                if actpas == 'Active':
                    if not rel:
                        pos = "AUX Mood=Ind | Number=Sing | Person=3 | Polarity=Pos | Tense=Pres | VerbType=Cop"
            elif An3 in verb_tenseperssuffix:
                if actpas == 'Active':
                    if not rel:
                        pos = "AUX Mood=Ind | Number=Sing | Person=3 | Polarity=Pos | Tense=Pres | VerbType=Cop"
    # General Verbs
        elif An2 in ['AI', 'AII', 'AIII', 'BI', 'BII', 'BIII', 'BIV', 'BV',
                     'AII (?)', 'BI (?)', 'BII (?)', 'defective', 'inflexion not clear', 'unclear',
                     'substantive verb (compound)']:
            if An3 in verb_tensepers:
                number = False
                person = False
                persnumpat = re.compile(r'\d(sg|pl)\.')
                persnumpatiter = persnumpat.finditer(An3)
                for find_persnum in persnumpatiter:
                    persnum = find_persnum.group()
                    person = persnum[:1]
                    number = numdict.get(persnum[1:])
                tense = False
                tensepat = re.compile(r'((cons\.)?pres|pret|past|(sec\.)?fut|imperf|(pret\./)?perf)\.')
                tensepatiter = tensepat.finditer(An3)
                for find_tense in tensepatiter:
                    tense = tensedict.get(find_tense.group())
                aspect = False
                asppat = re.compile(r'(cons\.pres|imperf|perf)\.')
                asppatiter = asppat.finditer(An3)
                for asp_find in asppatiter:
                    aspect = aspdict.get(asp_find.group())
                mood = False
                moodpat = re.compile(r'(ind|subj|cond|sec\.fut|impv)\.')
                moodpatiter = moodpat.finditer(An3)
                for find_mood in moodpatiter:
                    mood = mooddict.get(find_mood.group())
                voice = False
                if actpas == 'Active':
                    voice = "Act"
                elif actpas in ['Passive', 'Pass']:
                    voice = "Pass"
                relative = False
                if rel in ['Y', 'Maybe']:
                    relative = "Rel"
                feat_list = list()
                if aspect:
                    feat_list.append(f'Aspect={aspect}')
                if mood:
                    feat_list.append(f'Mood={mood}')
                else:
                    feat_list.append('Mood=Ind')
                if number:
                    feat_list.append(f'Number={number}')
                if person:
                    feat_list.append(f'Person={person}')
                if relative:
                    feat_list.append(f'PronType={relative}')
                if tense:
                    feat_list.append(f'Tense={tense}')
                elif mood == "Imp":
                    tense = "Pres"
                    feat_list.append(f'Tense={tense}')
                elif mood == "Cnd":
                    tense = "Fut"
                    feat_list.append(f'Tense={tense}')
                if voice:
                    feat_list.append(f'Voice={voice}')
                features = " | ".join(feat_list)
                pos = f'VERB {features}'
            elif An3 in verb_tensepersinfix:
                An3_only = An3.split(" + ")[0]
                number = False
                person = False
                persnumpat = re.compile(r'\d(sg|pl)\.')
                persnumpatiter = persnumpat.finditer(An3_only)
                for find_persnum in persnumpatiter:
                    persnum = find_persnum.group()
                    person = persnum[:1]
                    number = numdict.get(persnum[1:])
                tense = False
                tensepat = re.compile(r'((cons\.)?pres|pret|past|(sec\.)?fut|imperf|(pret\./)?perf)\.')
                tensepatiter = tensepat.finditer(An3_only)
                for find_tense in tensepatiter:
                    tense = tensedict.get(find_tense.group())
                aspect = False
                asppat = re.compile(r'(cons\.pres|imperf|perf)\.')
                asppatiter = asppat.finditer(An3_only)
                for asp_find in asppatiter:
                    aspect = aspdict.get(asp_find.group())
                mood = False
                moodpat = re.compile(r'(ind|subj|cond|sec\.fut|impv)\.')
                moodpatiter = moodpat.finditer(An3_only)
                for find_mood in moodpatiter:
                    mood = mooddict.get(find_mood.group())
                voice = False
                if actpas == 'Active':
                    voice = "Act"
                elif actpas in ['Passive', 'Pass']:
                    voice = "Pass"
                relative = False
                if rel in ['Y', 'Maybe']:
                    relative = "Rel"
                feat_list = list()
                if aspect:
                    feat_list.append(f'Aspect={aspect}')
                if mood:
                    feat_list.append(f'Mood={mood}')
                else:
                    feat_list.append('Mood=Ind')
                if number:
                    feat_list.append(f'Number={number}')
                if person:
                    feat_list.append(f'Person={person}')
                if relative:
                    feat_list.append(f'PronType={relative}')
                if tense:
                    feat_list.append(f'Tense={tense}')
                elif mood == "Imp":
                    tense = "Pres"
                    feat_list.append(f'Tense={tense}')
                elif mood == "Cnd":
                    tense = "Fut"
                    feat_list.append(f'Tense={tense}')
                if voice:
                    feat_list.append(f'Voice={voice}')
                features = " | ".join(feat_list)
                pos = f'VERB {features}'
            elif An3 in verb_tenseperssuffix:
                number = 'Sing'
                person = '3'
                tense = 'Pres'
                mood = 'Ind'
                voice = 'Act'
                relative = False
                if rel == 'Y':
                    relative = "Rel"
                feat_list = list()
                feat_list.append(f'Mood={mood}')
                feat_list.append(f'Number={number}')
                feat_list.append(f'Person={person}')
                if relative:
                    feat_list.append(f'PronType={relative}')
                feat_list.append(f'Tense={tense}')
                feat_list.append(f'Voice={voice}')
                features = " | ".join(feat_list)
                pos = f'VERB {features}'
    # Unknown Verbs
        elif not An2:
            if An3 == '3sg.pres.ind.pass.':
                number = 'Sing'
                person = '3'
                tense = 'Pres'
                mood = 'Ind'
                voice = False
                if actpas == 'Active':
                    voice = "Act"
                elif actpas in ['Passive', 'Pass']:
                    voice = "Pass"
                feat_list = list()
                feat_list.append(f'Mood={mood}')
                feat_list.append(f'Number={number}')
                feat_list.append(f'Person={person}')
                feat_list.append(f'Tense={tense}')
                feat_list.append(f'Voice={voice}')
                features = " | ".join(feat_list)
                pos = f'VERB {features}'
    # Verbal of Necessity
    if An1 == 'verbal of necessity':
        if not An2:
            if An3 in ['verbal of necessity: *ar·eim',
                       'verbal of necessity: *as·gleinn',
                       'verbal of necessity: caraid',
                       'verbal of necessity: con·certa',
                       'verbal of necessity: *do·edbair',
                       'verbal of necessity: fo-dáli',
                       'verbal of necessity: sásaid',
                       'verbal of necessity: sernaid',
                       'verbal of necessity: techtaid',
                       '*']:
                if not actpas:
                    if not rel:
                        pos = "VERB VerbForm=Gdv"

    # Assign Adverb (ADV)
    if An1 == 'adverb':
        if not An2:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "ADV"
                    elif rel == 'Y':
                        pos = "ADV"
            elif An3 in ['acc.', 'dat.sg.', 'dat.sg.neut.']:
                if not actpas:
                    if not rel:
                        pos = "ADV"
        elif An2 == 'conjunctive':
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "ADV"
        elif An2 == 'autonomous negative':
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "ADV Polarity=Neg"
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
    if An1 == 'adverb; preposition, with accusative':
        if not An2:
            if An3 == 'adverbial form':
                if not actpas:
                    if not rel:
                        pos = "ADV"
    if An1 == 'noun':
        if An2 in ['f, ā', 'n, u or o', 'gender unknown, i-stem']:
            if An3 == 'adverbial form':
                if not actpas:
                    if not rel:
                        pos = "ADV"
    if An1 == 'adjective':
        if An2 in ['i̯o, i̯ā']:
            if An3 == 'adverbial form':
                if not actpas:
                    if not rel:
                        pos = "ADV"
    if An1 == 'noun and adjective':
        if An2 in ['i']:
            if An3 == 'adverbial form':
                if not actpas:
                    if not rel:
                        pos = "ADV"
    if An1 == 'preposition, with acc; leniting':
        if not An2:
            if An3 == 'adverbial form':
                if not actpas:
                    if not rel:
                        pos = "ADV"
    # Assign Abbreviations (ADV)
    if An1 == 'abbreviation':
        if not An2:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "ADV Abbr=Yes | Typo=Yes"

    #                                           PREPOSITIONS
    # Assign Prepositions (ADP)
    if An1 in ['preposition, with acc', 'preposition, with acc; leniting', 'preposition, with acc; geminating']:
        if not An2:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "ADP AdpType=Prep | Definite=Ind"
            elif An3 in ['acc.', 'acc. + rel.part.', 'acc. + so 1',
                         'acc. + poss.pron.3sg.masc./neut.', 'acc. + poss.pron.3sg.fem.',
                         'acc. + poss.pron.3pl.',
                         'composition form']:
                if not actpas:
                    if not rel:
                        pos = "ADP AdpType=Prep | Definite=Ind"
    if An1 in ['preposition, with dat', 'preposition, with dat; leniting',
               'preposition, with dat; nasalizing', 'preposition, with dat; geminating']:
        if not An2:
            if An3 in ['dat.', 'dat.sg.', 'dat.pl.', 'dat.du.',
                       'dat. + rel.part.',
                       'dat. + alaile',
                       'dat. + poss.pron.3sg', 'dat. + poss.pron.3sg.',
                       'dat. + poss.pron.3sg.masc./neut.', 'dat. + poss.pron.3sg.fem.',
                       'dat. + poss.pron.3pl.',
                       'composition form', '*']:
                if not actpas:
                    if not rel:
                        pos = "ADP AdpType=Prep | Definite=Ind"
    if An1 in ['preposition, with dat and acc; leniting', 'preposition, with dat and acc; nasalizing']:
        if not An2:
            if An3 in ['acc.', 'acc.sg.', 'acc. + rel.part.',
                       'acc. + poss.pron.3sg.masc./neut.',
                       'acc. + poss.pron.3pl.',
                       'acc./dat.', 'acc./dat. + rel.part.',
                       'dat.', 'dat.sg.', 'dat.pl.', 'dat. + rel.part.', 'dat. (?)',
                       'dat. + poss.pron.2sg.',
                       'dat. + poss.pron.3sg.masc./neut.',
                       'dat (?) + poss.pron.3sg.masc./neut.',
                       'dat. + poss.pron.3pl.',
                       'i 2 + poss.pron.3sg.fem.']:
                if not actpas:
                    if not rel:
                        pos = "ADP AdpType=Prep | Definite=Ind"
    if An1 == 'preposition, nominal, with gen':
        if An2 == 'nasalizing':
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "ADP AdpType=Prep | Definite=Ind"
    if An1 == 'preposition, with gen; and conjunction':
        if not An2:
            if An3 == 'gen.':
                if not actpas:
                    if not rel:
                        pos = "ADP AdpType=Prep | Definite=Ind"
    if An1 == 'adverb; preposition, with accusative':
        if not An2:
            if An3 == 'acc.':
                if not actpas:
                    if not rel:
                        pos = "ADP AdpType=Prep | Definite=Ind"
    # Assign Prepositional Pronouns (ADP)
    prepprontype = ['acc. + suff.pron.1sg.',
                    'acc. + suff.pron.2sg.',
                    'acc. + suff.pron.3sg.masc./neut.',
                    'acc. + suff.pron.3sg.fem.',
                    'acc. + suff.pron.1pl.',
                    'acc. + suff.pron.3pl.',
                    'dat. + suff.pron.1sg.',
                    'dat. + suff.pron.2sg.',
                    'dat. + suff.pron.3sg.',
                    'dat. + suff.pron.3sg.masc./neut.',
                    'dat. + suff.pron.3sg.fem.',
                    'dat. + suff.pron.3sg.fem. + -si 1',
                    'dat. + suff.pron.1pl.',
                    'dat. + suff.pron.2pl.',
                    'dat. + suff.pron.3pl.',
                    'eter + suff pron 3sg n']
    if An1 in ['preposition, with acc', 'preposition, with acc; leniting', 'preposition, with acc; geminating',
               'preposition, with dat', 'preposition, with dat; leniting', 'preposition, with dat; nasalizing',
               'preposition, with dat; geminating',
               'preposition, with dat and acc; leniting', 'preposition, with dat and acc; nasalizing']:
        if not An2:
            if An3 in prepprontype:
                gender = False
                number = False
                person = False
                numdict = {'sg': 'Sing', 'pl': 'Plur'}
                if ".masc./neut." in An3 or "3sg n" in An3:
                    gender = "Masc,Neut"
                elif ".fem." in An3:
                    gender = "Fem"
                persnumpat = re.compile(r'[. ]\d\w{2}[. ]')
                persnumpatiter = persnumpat.finditer(An3)
                for persnumfind in persnumpatiter:
                    persnum = persnumfind.group()
                    number = numdict.get(persnum[2:4])
                    person = persnum[1:2]
                feat_list = list()
                feat_list.append("AdpType=Prep")
                feat_list.append("Definite=Ind")
                if gender:
                    feat_list.append(f'Gender={gender}')
                if number:
                    feat_list.append(f'Number={number}')
                if person:
                    feat_list.append(f'Person={person}')
                if not actpas:
                    if not rel:
                        feat_list.append("PronType=Prs")
                        features = " | ".join(feat_list)
                        pos = f"ADP {features}"
                    elif rel == 'Y':
                        feat_list.append("PronType=Prs,Rel")
                        features = " | ".join(feat_list)
                        pos = f"ADP {features}"
    # Assign Deterministic Prepositions - preceding prepositional articles (ADP)
    if An1 in ['preposition, with acc', 'preposition, with acc; leniting', 'preposition, with acc; geminating',
               'preposition, with dat', 'preposition, with dat; leniting', 'preposition, with dat; nasalizing',
               'preposition, with dat; geminating',
               'preposition, with dat and acc; leniting', 'preposition, with dat and acc; nasalizing']:
        if not An2:
            if An3 in ['acc. + def.art.sg', 'acc. + def.art.pl.',
                       'acc. + def.art.sg. + í 1', 'acc. + def.art.pl. + í 1',
                       'dat. + def.art.sg.', 'dat. + def.art.pl.',
                       'dat. + def.art.du.', 'dat. + def.art.sg. + í 1']:
                if not actpas:
                    if not rel:
                        pos = "ADP AdpType=Prep | Definite=Def | Prefix=Yes"

    #                                           CONJUNCTIONS
    # Assign Conjunctions (CCONJ/SCONJ)
    # Coordinating Conjunctions
    if An1 == 'conjunction':
        if An2 == 'introducing an optative clause':
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "CCONJ"
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
                       'joining conj prep and noun',
                       'joining two adjectives',
                       'joining two Latin lemmata',
                       'joining two Latin phrases',
                       'joining two nouns', 'joining two nouns (letters of the alphabet)',
                       'joining two nouns with adjectives', 'joining two nouns with articles',
                       'joining two nouns with prepositions',
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
    if An1 == 'conjunction':
        if not An2:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "SCONJ"
        elif An2 in ['accumulative, adversative',
                     'causal', 'causal; coordinating and subordinating',
                     'comparative',
                     'concessive and explicative (leniting)',
                     'conditional', 'conditional, temporal',
                     'disjunct', 'disjunct (leniting)',
                     'final (purpose), and explicative',
                     'temporal', 'temporal, adversative; (prep la + dem pron so 1 acc sg nt)']:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "SCONJ"
            elif An3 in ['1pl.', '2sg.', '3pl.',
                         'i 2 + def.art. + deictic pron í 1',
                         'ma + ní + copula',
                         'with copula', 'with 3sg.pres.subj. of copula', 'with 3pl.pres.sub. of copula',
                         'with negative']:
                if not actpas:
                    if not rel:
                        pos = "SCONJ"
        elif An2 == 'negative subordinating':
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "SCONJ Polarity=Neg"
        elif An2 == 'negative (geminating), before non-verbs; na before stressed words':
            if An3 == 'joining two nouns':
                if not actpas:
                    if not rel:
                        pos = "SCONJ Polarity=Neg"
            elif not An3:
                feat_list = list()
                feat_list.append('Polarity=Neg')
                feat_list.append('PronGend=Neut')
                feat_list.append('PronNum=Sing')
                feat_list.append('PronPers=3')
                feat_list.append('PronType=Prs')
                if not actpas:
                    if not rel:
                        features = " | ".join(feat_list)
                        pos = f"SCONJ {features}"
        elif An2 == 'subordinate negative, with infixed pronouns Class C':
            feat_list = list()
            feat_list.append('Polarity=Neg')
            feat_list.append('PronClass=C')
            feat_list.append('PronGend=Neut')
            feat_list.append('PronNum=Sing')
            feat_list.append('PronPers=3')
            feat_list.append('PronType=Prs')
            if not An3 or An3 == 'infix pron Class C 3sg n':
                if not actpas:
                    if not rel:
                        features = " | ".join(feat_list)
                        pos = f"SCONJ {features}"
            elif An3 == 'infix pron class C 3sg m':
                feat_list[2] = 'PronGend=Masc'
                if not actpas:
                    if not rel:
                        features = " | ".join(feat_list)
                        pos = f"SCONJ {features}"
    if An1 == 'conjunction w/ subordinate negation':
        if not An2:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "SCONJ Polarity=Neg"
    if An1 in ['conjunction and adverb (conjunctive)',
               'preposition, with gen; and conjunction']:
        if not An2:
            if not An3:
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

    #                                              PARTICLES
    # Assign Particles (PART)
    # Assign Negative Particles
    if An1 == 'particle':
        if An2 in 'negative':
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PART Polarity=Neg"
            elif An3 == 'ar·cuirethar':
                if not actpas:
                    if not rel:
                        pos = "PART Polarity=Neg"
        elif An2 in ["relative negative", "negative dependent relative"]:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PART Polarity=Neg | PronType=Rel"
        elif An2 == 'relative negative, with infixed pronouns Class C':
            feat_list = list()
            feat_list.append('Polarity=Neg')
            feat_list.append('PronClass=C')
            feat_list.append('PronGend=Neut')
            feat_list.append('PronNum=Sing')
            feat_list.append('PronPers=3')
            feat_list.append('PronType=Prs')
            if not An3:
                if not actpas:
                    if not rel:
                        features = " | ".join(feat_list)
                        pos = f"PART {features}"
    # Assign Interrogative Particles
    if An1 == 'particle':
        if An2 == 'interrrogative':  # Yes, really, three.
            if not An3:
                if not actpas:
                    if not rel:
                        if trans == 'as a correlative conjunction: whether':
                            pos = "PART PronType=Int"
                        elif trans != 'as a correlative conjunction: whether':
                            pos = "PART PronType=Int"
    # Assign Vocative Particles
    if An1 == 'particle':
        if An2 == 'vocative':
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PART Case=Voc"
    # Assign Numerical Particles
    if An1 == 'particle':
        if An2 == 'numerical':
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PART PartType=Num"
    # Assign Relative Particles
    if An1 == 'particle':
        if An2 == 'relative':
            if An3 in ['rel part + a 5',
                       'rel part + ar 1',
                       'rel part + co 1',
                       'rel part + de 1',
                       'rel part + do 1',
                       'rel part + for 1',
                       'rel part + fri',
                       'rel part + i 2',
                       'rel part + ó 1',
                       'rel part + ro 1',
                       'rel part + tre 1']:
                if not actpas:
                    if not rel:
                        pos = "PART PronType=Rel"
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PART PronType=Rel"
        elif An2 == 'demonstrative relative':
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PART PronType=Dem,Rel"
    # Assign Deictic Particles
    if An1 == 'pronoun, indeclinable, accented, deictic':
        if not An2:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PART PartType=Dct"
            elif An3 in ['nom.sg.', 'nom.sg.masc.', 'nom.sg.neut.', 'nom.sg.fem.',
                         'acc.sg.', 'acc.sg.masc.', 'acc.sg.neut.', 'acc.sg.fem.',
                         'gen.sg.', 'gen.sg.masc.', 'gen.sg.neut.',
                         'dat.sg.', 'dat.sg.masc.', 'dat.sg.neut.', 'dat.sg.fem',
                         'nom.pl.', 'nom.pl.masc.', 'nom.pl.neut.',
                         'acc.pl.', 'acc.pl.masc.', 'acc.pl.neut.',
                         'gen.pl.masc.', 'gen.pl.neut.',
                         'dat.pl.', 'dat.pl.masc.', 'dat.pl.neut.']:
                if not actpas:
                    if not rel:
                        pos = "PART PartType=Dct"
    # Assign Prefixing particles (mí-, so-, do-, neph-) (PART)
    if An1 == 'particle':
        if An2 in ['prefix', 'prefix, intensive', 'prefix and preverb', 'prefix, privative']:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PART Prefix=Yes"
            elif An3 == 'composition form':
                if not actpas:
                    if not rel:
                        pos = "PART Prefix=Yes"
        elif An2 == 'prefix, negative':
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PART Polarity=Neg | Prefix=Yes"
    # Assign Demonstrative Adjectives (PART)
    if An1 in ['adjective, demonstrative', 'adjective, demonstrative pronominal']:
        if not An2:
            if An3 in ['nom.pl.neut.', 'dat.pl.fem.']:
                if not actpas:
                    if not rel:
                        pos = "PART PronType=Dem"
        elif An2 == 'this, these':
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PART PronType=Dem"
            elif An3 in ['nom.sg.', 'nom.sg.masc.', 'nom.sg.neut.',
                         'acc.sg.masc.', 'acc.sg.neut.', 'acc.sg.fem.',
                         'nom.pl.masc.', 'nom.pl.fem.',
                         'acc.pl.',
                         'dat.pl.masc.', 'dat.pl.neut.']:
                if not actpas:
                    if not rel:
                        pos = "PART PronType=Dem"
    # Assign Demonstrative Pronouns (PART)
    if An1 == 'pronoun, demonstrative':
        if An2 in ['that, those', 'neuter, indeclinable']:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "PART PronType=Dem"
            elif An3 in ['nom.sg.', 'nom.sg.masc.', 'nom.sg.neut.', 'nom.sg.fem.',
                         'acc.sg.masc.', 'acc.sg.neut.', 'acc.sg.fem.',
                         'dat.sg.neut.',
                         'nom.pl.', 'nom.pl.masc.']:
                if not actpas:
                    if not rel:
                        pos = "PART PronType=Dem"

    #                                   INTERJECTIONS, NUMERALS & ABBREVIATIONS
    # Assign Interjections (INTJ)
    if An1 == 'interjection':
        if not An2:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "INTJ"
            elif An3 in ['nom.sg.']:
                if not actpas:
                    if not rel:
                        pos = "INTJ"
    if An1 == 'particle':
        if An2 == 'interjection':
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "INTJ"
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
            if An3 in ['nom.sg.', 'nom.sg.masc.', 'nom.sg.neut.',
                       'acc.sg.', 'acc.sg.fem.',
                       'gen.sg.masc.',
                       'dat.sg.', 'dat.sg.masc.', 'dat.sg.fem',
                       'nom.pl.', 'nom.pl.masc.', 'nom.pl.neut.', 'nom.pl.fem.',
                       'acc.pl.', 'acc.pl.neut.',
                       'gen.pl.masc.', 'gen.pl.fem.',
                       'dat.pl.masc.', 'dat.pl.fem.',
                       'nom.du.masc.', 'nom.du.neut.', 'nom.du.fem.',
                       'acc.du.', 'acc.du.masc.', 'acc.du.neut.', 'acc.du.fem.',
                       'gen.du.masc.', 'gen.du.neut.', 'gen.du.fem.', 'gen.du.fem. + in 2',
                       'dat.du.', 'dat.du.masc.', 'dat.du.neut.', 'dat.du.fem.',
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

    #                                           UNUSED PARTS-OF-SPEECH
    # Assign Pre-verbal Particles (PVP)
    if An1 == 'particle':
        if An2 == 'preverb':
            if not An3:
                relative = False
                if rel == "Y":
                    relative = "Rel"
                feat_list = list()
                if trans:
                    if trans in ["perfective particle", "subjunctive ro", "ro of possibility", "conditional ro"]:
                        feat_list.append('PartType=Aug')
                if relative:
                    feat_list.append(f'PronType={relative}')
                if not actpas:
                    pos = "PVP"
                    if trans in ["dummy particle", "dummy particle: before secondary tenses"]:
                        pos = "PART"
                        feat_list.append("PartType=Vb")
                        feat_list.sort()
                    if feat_list:
                        features = " | ".join(feat_list)
                        pos = f'{pos} {features}'
            elif An3 in ['ar·cela', 'ar·icc', 'at·baill',
                         'díṡruthaigidir', 'díxnigidir', 'do·ommalgg',
                         'ro·finnadar',
                         'sechmo·ella',
                         'téit (do·coaid)',
                         'subjunctive ro', '*']:
                mood = False
                if An3 == 'subjunctive ro':
                    mood = 'Sub'
                aspect = False
                if trans:
                    if trans == "perfective particle":
                        aspect = "Perf"
                feat_list = list()
                if aspect:
                    feat_list.append(f'Aspect={aspect}')
                if mood:
                    feat_list.append(f'Mood={mood}')
                if not actpas:
                    if not rel:
                        pos = "PVP"
                        if feat_list:
                            features = " | ".join(feat_list)
                            pos = f'{pos} {features}'
    # includes only exceptions 'tris-' (rare preverb) and 'me' (mí prefix used as infixed preverb)
    if An1 == 'particle':
        if An2 in ['prefix', 'prefix and preverb']:
            if An3 == '*':
                if not actpas:
                    if not rel:
                        pos = "PVP"

    # Assign Infixed Pronouns (IFP)
    gend_dict = {"m": "Masc", "n": "Neut", "f": "Fem"}
    if An1 in ['pronoun, infixed, class A',
               'pronoun, infixed, class B',
               'pronoun, infixed, class C']:
        pronclass = False
        classpat = re.compile(r'[ABC]')
        classpatiter = classpat.finditer(An1)
        for classfind in classpatiter:
            pronclass = classfind.group()
        if An2 in ['1sg',
                   '2sg',
                   '3sg m', '3sg n (leniting)', '3sg f (geminating)', '3sg f (sometimes nasalizing)',
                   '1pl',
                   '3pl', '3pl (geminating)']:
            pronnum = False
            pronpers = False
            prongend = False
            numperspat = re.compile(r'\d(sg|pl)( [mnf])?')
            numperspatiter = numperspat.finditer(An2)
            for numpersfind in numperspatiter:
                numpers = numpersfind.group()
                pronnum = numdict.get(f'{numpers[1:3]}.')
                pronpers = numpers[0]
                if " " in numpers:
                    prongend = gend_dict.get(numpers[-1])
            feat_list = list()
            feat_list.append(f'PronClass={pronclass}')
            if prongend:
                feat_list.append(f'PronGend={prongend}')
            feat_list.append(f'PronNum={pronnum}')
            feat_list.append(f'PronPers={pronpers}')
            feat_list.append('PronType=Prs')
            features = " | ".join(feat_list)
            if not An3:
                if not actpas:
                    if not rel:
                        pos = f"IFP {features}"

    # Assign Unnecessary Repetitions of Words (UNR)
    if An1 == 'see amail':
        if not An2:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "UNR"

    # Assign Unknown Words (UNK)
    if not An1:
        if not An2:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "UNK"
    elif An1 == 'unclear':
        if not An2:
            if not An3:
                if not actpas:
                    if not rel:
                        pos = "UNK"

    # Break if a UD POS cannot be assigned, else, return POS
    if not test_unknown:
        if pos == "unknown":
            raise RuntimeError(f"POS could not be assigned:\n    {taglist}")
        else:
            return pos
    # Return POS even if it is unknown/no UD POS can be assigned
    elif test_unknown:
        return pos


# Loops through all glossed words, finds their analyses, and passes this to the clean_analysis function.
# Where tags cannot be cleaned by the function, all instances of the original analysis are printed.
def loop_tags(taglist, test_unknown=False):
    new_poslist = list()
    for full_tag in taglist:
        glossnum = full_tag[0]
        gloss_ref = full_tag[1]
        word = clean_word(full_tag[2])
        trans = full_tag[4]
        tag = clean_onetag(full_tag[5:10] + [trans])
        gloss = clean_gloss(full_tag[10])
        gloss_trans = full_tag[11]
        try:
            pos_tag = clean_analysis(tag, test_unknown)
            full_tag.append(pos_tag)
            new_poslist.append(full_tag)
        except ZeroDivisionError:
            print(f"Broke at gloss no. {glossnum}: {gloss_ref}\nWord: '{word}', in Gloss: '{gloss}' - {gloss_trans}.\n"
                  f"url: http://www.stgallpriscian.ie/index.php?id={glossnum}&an=1\n"
                  f"Analysis: {tag}\n\nSimilar tags:")
            for comp in taglist:
                if clean_onetag(comp[5:10]) == tag[:-1]:
                    comp_glossnum = comp[0]
                    comp_tph_ref = comp[1]
                    comp_word = clean_word(comp[2])
                    comp_trans = str(comp[4])
                    comp_tag = clean_onetag(comp[5:10])
                    comp_gloss = clean_gloss(comp[10])
                    print(f"{comp_tag} {comp_tph_ref} '{comp_word}', '{comp_trans}, in: '{comp_gloss}'"
                          f" - http://www.stgallpriscian.ie/index.php?id={comp_glossnum}&an=1")
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


# Save a list containing each Token and its assigned UD POS
def create_pos_taglist():
    pos_list = list()
    for i in loop_tags(analyses, True):
        tagged_i = i[2], i[12]
        pos_list.append(tagged_i)
    save_obj("POS_taglist", pos_list)
    return "Created file: 'POS_taglist.pkl'"


# Create and save an ordered list of glosses (uncleaned) with translations and TPH references
def create_glosslist(excel_combo):
    glosslist = list()
    lastgloss = ""
    for i in excel_combo:
        thisref = i[1]
        thisgloss = i[10]
        thistrans = i[11]
        if thisgloss != lastgloss:
            lastgloss = thisgloss
            glosslist.append([thisref, thisgloss, thistrans])
    save_obj("Gloss_List", glosslist)
    return "Created file: 'Gloss_List.pkl'"


# Create and save an ordered list of word-lists
# words-list = [word, headword, [analysis (levels 1-5) and translation/meaning]] (all uncleaned)
def create_wordlist(excel_combo):
    wordslist = list()
    thesewords = list()
    lastgloss = ""
    for i in excel_combo:
        # For each analysis (word)
        thisgloss = i[10]
        thisword = i[2]
        thisheadword = i[3]
        thistrans = i[4]
        thistag = i[5:10] + [thistrans]
        # if this is a new gloss, i.e. it's different from the last gloss checked in the loop
        if thisgloss != lastgloss:
            # set the current gloss as this (new) gloss
            lastgloss = thisgloss
            # if there is a list of words left over from the last gloss (it isn't blank/false)
            if thesewords:
                # add it to the list of all glosses' word-lists
                wordslist.append(thesewords)
            # if there is a word to start the new gloss
            if thisword:
                # create a new these-words list for this new gloss, and add the new gloss's first word's word-list
                thesewords = [[thisword, thisheadword, thistag]]
            # if there's a missing word at beginning of the new gloss
            else:
                # create a new these-words list for this new gloss, but leave it empty
                thesewords = list()
        # if this word is from the same gloss as the last one, i.e. it's the same as the last gloss checked in the loop
        # and there actually is a word, i.e. it's not a blank entry
        elif thisword:
            # add the word's word-list to the current these-words list for the gloss
            thesewords.append([thisword, thisheadword, thistag])
        # if this word was the last word in the corpus
        if i == excel_combo[-1]:
            # add the last gloss's list of words to the list of all glosses' word-lists
            wordslist.append(thesewords)
    save_obj("Words_List", wordslist)
    return "Created file: 'Words_List.pkl'"


# #                                             CREATE RESOURCES


# # Run the functions above which create .pkl files of gloss-word analyses from spreadsheet, "SG. Combined Data":
# print(save_sorted_tags(sort_tag_levels(list_tag_levels(analyses))))
#
# # Run the function to create a .pkl file listing all unique POS-tag combinations used in order
# print(save_all_pos_combos_list(analyses))
#
# # Save a list containing each Token and its assigned UD POS
# print(create_pos_taglist())
#
# # Save ordered lists of uncleaned glosses, and uncleaned words with analysis and translation
# create_glosslist(analyses)
# create_wordlist(analyses)


# #                                               OUTPUT TESTS:


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
# print("Unique Translations/Word-meanings: {}".format(len(Tr_list)))


# # Test contents of individual tag level analyses (1-3)
# #    Print all sorted A1 level entries
# #    Then print all analysis for tags with no A1 level analysis
# for i in A1_list:
#     print(i)
# for i in noA1:
#     output = [i[1]] + [i[0]] + i[5:10]
#     print(output)

# for i in A2_list:
#     print(i)
# for i in noA2:
#     output = [i[1]] + [i[0]] + i[5:10]
#     print(output)

# for i in A3_list:
#     print(i)
# for i in noA3:
#     output = [i[1]] + [i[0]] + i[5:10]
#     print(output)

# # Test all entries for verb information (active/passive, relative) and translations
# for i in actpas_list:
#     print(i)
# for i in rel_list:
#     print(i)
# for i in Tr_list:
#     print(i)


# # Counts the number of times each unique tag is used
# for i in count_tag_usage(open_obj("All POS Combos Used.pkl"), analyses):
#     print(i)

# # Count, print and plot tag usage figures
# plot_tag_use(count_tag_usage(open_obj("All POS Combos Used.pkl"), analyses))

# # Counts the number of times each unique POS or feature-set is used for the new corpora
# for i in count_pos_usage("sga_dipsgg-ud-test_combined_POS.conllu"):
#     print(i)
# for i in count_feat_usage("sga_dipsgg-ud-test_combined_POS.conllu"):
#     print(i)

# # Count, print and plot tag usage figures for the new corpora
# plot_tag_use(count_pos_usage("sga_dipsgg-ud-test_combined_POS.conllu"))
# plot_tag_use(count_pos_usage("sga_dipsgg-ud-test_split_POS.conllu"))
# plot_tag_use(count_feat_usage("sga_dipsgg-ud-test_combined_POS.conllu"))
# plot_tag_use(count_feat_usage("sga_dipsgg-ud-test_split_POS.conllu"))
# plot_all_tag_use(count_tag_usage(open_obj("All POS Combos Used.pkl"), analyses),
#                  count_feat_usage("sga_dipsgg-ud-test_combined_POS.conllu"),
#                  count_feat_usage("sga_dipsgg-ud-test_split_POS.conllu"))


# #                                                FUNCTION TESTS:


# # Functions for creating and saving .pkl lists of gloss-word analyses
# print(list_tag_levels(analyses))

# print(sort_tag_levels(list_tag_levels(analyses)))


# # Test clean_onetag function
# for tag in analyses:
#     print(clean_onetag(tag[5:10]))


# # Function to create a .pkl file listing all unique POS-tag combinations used in order
# print(save_all_pos_combos_list(analyses))

# # Counts the number of times each unique tag is used
# print(count_tag_usage(open_obj("All POS Combos Used.pkl"), analyses))


# # Test findall_thistag, findall_nulltag, findall_excltag and clean_wordlist functions

# # Finds all of a given tag type (eg. adjective) with another given tag type at another given level
# # Prints number of matches found, and each match
# l1_taglist = findall_thistag(analyses, "adjective")
# l2_taglist = findall_thistag(l1_taglist, False, 2)
# print(len(l2_taglist))
# for tag in l2_taglist:
#     found_glossnum = tag[0]
#     found_tph_ref = tag[1]
#     found_word = clean_word(tag[2])
#     found_trans = tag[4]
#     found_tag = clean_onetag(tag[5:10])
#     found_gloss = clean_gloss(tag[10])
#     print(found_tag, found_tph_ref, found_glossnum, f"'{found_word}'/'{found_trans}' in, '{found_gloss}'")

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
#     itag_noisy = i[5:10] + [i[4]]
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


# # Test the loop_tags function
# loop_tags(analyses, True)
# print(loop_tags(analyses, True))


# # Test how many tokens in Bauer's analysed corpus can be successfully assigned UD POS tags by the loop_tags function
# percent_complete(analyses)

# # POS Tag Each Gloss and Return either POS list or Breakpoint
# loop_tags(analyses)
# print(loop_tags(analyses))

# # List each Token and its POS
# for i in loop_tags(analyses, False):
#     print(f"'{i[2]}', {i[12]}")
