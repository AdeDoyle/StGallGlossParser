"""Level 1"""


from OpenXlsx import list_xlsx
from Pickle import open_obj
import re
from nltk import edit_distance as ed
from Map_GlossWords import map_glosswords
from Clean_Glosses import clean_gloss, clean_word


analyses = list_xlsx("SG. Combined Data", "Sheet 1")
glosslist = open_obj("Gloss_List.pkl")
wordslist = open_obj("Words_List.pkl")


# Changes all characters in Hoffman's glosses to a common set
def standardise_glosschars(gloss):
    gloss = gloss.lower()
    chardict = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ḟ': 'f', 'ṁ': 'm', 'ṅ': 'n', 'ṡ': 's', '⁊': 'ocus'}
    for char in gloss:
        if char in chardict:
            replacement = chardict.get(char)
            gloss = gloss.replace(char, replacement)
    return gloss


# Changes all characters in Bauer's glosses to a common set
def standardise_wordchars(word):
    # chars = sorted(list(set(word.lower())))
    word = word.lower()
    chardict = {'á': 'a', 'æ': 'ae', 'ǽ': 'ae', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
                'ċ': 'c', 'ḟ': 'f', 'ṁ': 'm', 'ṅ': 'n', 'ṡ': 's', '⁊': 'ocus', 'ɫ': 'no'}
    for char in word:
        if char in chardict:
            replacement = chardict.get(char)
            word = word.replace(char, replacement)
    return word


# Removes hyphens from Hofman's glosses with respect to the specific reason for hyphenation
def remove_glosshyphens(gloss):
    words = gloss.split(" ")
    word_ending = False
    for word in words:
        if "-" in word:
            word_index = words.index(word)
            reconstruct = False
            # If there's more than one hyphen in a word
            if word.count("-") > 1:
                first_deconstruct = word.split("-")
                if first_deconstruct[0] == "n":
                    nazal_word = first_deconstruct[:2]
                    remaining_words = first_deconstruct[2:]
                    first_reconstruct = "-".join(["".join(nazal_word), "-".join(remaining_words)])
                    if first_reconstruct.count("-") > 1:
                        word = " ".join(first_reconstruct.split("-"))
                        reconstruct = word
                    else:
                        word = first_reconstruct
                elif first_deconstruct[0] == "nisn":
                    first_word_fix = "nis n"
                    remaining_words = first_deconstruct[1:]
                    first_reconstruct = "".join([first_word_fix, "-".join(remaining_words)])
                    word = first_reconstruct
                elif word == "syl-laib-":
                    word = "".join(word.split("-"))
                    reconstruct = word
                else:
                    word = " ".join(word.split("-"))
                    reconstruct = word
            # If there's only one hyphen in a word
            if word.count("-") == 1:
                # Specialty removals (requiring more than hyphen removal and possible spacing)
                # If the word ends in a hyphen, remove without adding a space
                if word[-1] in ["-", "…"]:
                    small_prob_list = ['mael-', 'cua-', 'b-', 'alde-', 'neph-', 'gen-…', 'memr-', 'brig-', 'col-',
                                       'el-', 'incomṡuig-']
                    if word in small_prob_list:
                        reconstruct = "".join(word.split("-"))
                    # If the following word should be conjoined, concatenate the two, removing hyphen and space
                    big_prob_list = ['indfrec-', 'ṡechma-', 'adrodar-', 'in-', 'preter-', 'thech-', 'tim-', 'di-']
                    big_fix_list = ['indfrec- ndairc', 'ṡechma- dachtu', 'adrodar- car', 'in- narómae', 'preter- itum',
                                    'thech- taite', 'tim- morte', 'di- gal']
                    if word in big_prob_list:
                        for wordfix in big_fix_list:
                            if word in wordfix:
                                reconstruct = "".join(wordfix.split("- "))
                                word_ending = True
                if word[0] == "-":
                    reconstruct = word[1:]
                # If the hyphen seems to be misplaced and should be altered
                if not reconstruct:
                    splitpat = re.compile(r'\b(aran|asan|asech|dian|huan|niaisṅdius|niro|nádn)-')
                    splitpatitir = splitpat.finditer(word)
                    if splitpatitir:
                        for patfind in splitpatitir:
                            wrong_prefix = patfind.group()
                            wrong_remainder = "".join(word.split(wrong_prefix))
                            if wrong_prefix == "aran-":
                                word = "ara-n" + wrong_remainder
                            elif wrong_prefix == "asan-":
                                word = "asa-n" + wrong_remainder
                            elif wrong_prefix == "asech-":
                                word = "a sech" + wrong_remainder
                            elif wrong_prefix == "dian-":
                                word = "dia-n" + wrong_remainder
                            elif wrong_prefix == "huan-":
                                word = "hua-n" + wrong_remainder
                            elif wrong_prefix == "niaisṅdius-":
                                word = "niaisṅdiu-s" + wrong_remainder
                            elif wrong_prefix == "niro-":
                                word = "ni-ro" + wrong_remainder
                            elif wrong_prefix == "nádn-":
                                word = "nád-n" + wrong_remainder
                            reconstruct = " ".join(word.split("-"))
                # If the prefix attached to the hyphen occurs more than once and needs to be treated differently
                if not reconstruct:
                    splitpat = re.compile(r'\b(conro|in)-')
                    splitpatitir = splitpat.finditer(word)
                    if splitpatitir:
                        for patfind in splitpatitir:
                            check_prefix = patfind.group()
                            check_remainder = "".join(word.split(check_prefix))
                            if check_prefix == "conro-":
                                if check_remainder == "thinoll":
                                    reconstruct = "con ro" + check_remainder
                            if check_prefix == "in-":
                                if check_remainder in ["chrut", "remṡuidigud", "tan"]:
                                    reconstruct = " ".join(word.split("-"))
                                elif check_remainder == "na":
                                    reconstruct = "".join(word.split("-"))
                                elif check_remainder == "nabet":
                                    reconstruct = "inna bet"
                # Non-specialty removals
                deconstruct = word.split("-")
                # If the hyphen marks nazalisation, remove the hyphen without inserting a space
                if not reconstruct:
                    splitpat = re.compile(r'\b(nn|n|ṅ)-\w')
                    splitpatitir = splitpat.finditer(word)
                    if splitpatitir:
                        for patfind in splitpatitir:
                            nazalisation_marks = ["nn-", "n-", "ṅ-"]
                            if patfind.group()[:-1] in nazalisation_marks:
                                reconstruct = "".join(deconstruct)
                # If the hyphen marks a prefixed noun, remove the hyphen and insert a space
                if not reconstruct:
                    splitpat = re.compile(r'\b(athir|huasal|iar|medón|sethar|tuistid)-\w.*\b')
                    splitpatitir = splitpat.finditer(word)
                    if splitpatitir:
                        for _ in splitpatitir:
                            reconstruct = " ".join(deconstruct)
                # If the hyphen marks a prefix, remove the hyphen and insert a space
                if not reconstruct:
                    splitpat = re.compile(r'\b(ar|bith|cach|con|cosmail|derb|etar|il|lán|llán|leth|mi|mí|neph|ní|nil|'
                                          r'noen|nóen|nue|oen|óen|oin|óin|oín|ṡain|sechta|sen)-\w.*\b')
                    splitpatitir = splitpat.finditer(word)
                    if splitpatitir:
                        for _ in splitpatitir:
                            reconstruct = " ".join(deconstruct)
                # If the hyphen marks a suffix, remove the hyphen and insert a space
                if not reconstruct:
                    splitpat = re.compile(r'\b.*\w-(ni|sa|se|sem|si|sí|ssí|sidi|sin|siu|síu|so|som|son|són)\b')
                    splitpatitir = splitpat.finditer(word)
                    if splitpatitir:
                        for _ in splitpatitir:
                            reconstruct = " ".join(deconstruct)
                # If the hyphen marks the deictic particle, remove the hyphen and insert a space
                if not reconstruct:
                    splitpat = re.compile(r'\b.*\w-(í|hí)\b')
                    splitpatitir = splitpat.finditer(word)
                    if splitpatitir:
                        for _ in splitpatitir:
                            reconstruct = " ".join(deconstruct)
                # If the hyphen marks a pre-verbal particle, remove the hyphen without inserting a space
                if not reconstruct:
                    splitpat = re.compile(r'\b(for)-\w.*\b')
                    splitpatitir = splitpat.finditer(word)
                    if splitpatitir:
                        for _ in splitpatitir:
                            reconstruct = "".join(deconstruct)
                if not reconstruct:
                    word = "".join(word.split("-"))
                    reconstruct = word
            if not reconstruct:
                print("Fucking What?")
            elif reconstruct:
                words[word_index] = reconstruct
            if word_ending:
                del words[word_index + 1]
                word_ending = False
    return " ".join(words)


# Takes a mapping of POS to gloss from the map_glosswords function,
# POS tags the Hofman gloss by comparing each tagged word in the Bauer gloss to each word in the Hofman gloss.
# ORIGINAL VERSION (this function has been improved)
def matchword_levdist_original(gloss_mapping):
    gloss_string = gloss_mapping[0]
    gloss_list = gloss_string.split(" ")
    pos_list = gloss_mapping[1]
    tagged_gloss = list()
    lowest_eddist = False
    # include '.i.' in pos-list so it can be tagged
    for token in gloss_list:
        if token == ".i.":
            pos_list.append([".i.", "<SYM>"])
    # for each analysed word
    for pos_tag in pos_list:
        tagged_word = pos_tag[0]
        tag = pos_tag[1]
        # if the word is not an unused word-type
        if tag not in ["<PVP>", "<IFP>", "<PFX>", "<UNR>", "<UNK>"]:
            # check every token in the gloss-list for lowest edit distance from the analysed word
            for token in gloss_list:
                eddist = ed(tagged_word, token)
                # assign the word the pos-tag of the analysed word with the smallest edit distance from it
                if not lowest_eddist:
                    lowest_eddist = [eddist, token, tag, tagged_word]
                    if eddist == 0:
                        break
                else:
                    if eddist < lowest_eddist[0]:
                        lowest_eddist = [eddist, token, tag, tagged_word]
                        if eddist == 0:
                            break
            tagged_gloss.append([lowest_eddist[1], lowest_eddist[2]])
            lowest_eddist = False
    # rearrange gloss to the same order as Hofman's
    arranged_tagged_gloss = list()
    for i in gloss_list:
        found = False
        for j in tagged_gloss:
            if i == j[0]:
                found = True
                arranged_tagged_gloss.append(j)
                # delete all guesses before the last perfectly matched word to remove junk.
                if i != ".i.":
                    jpos = tagged_gloss.index(j)
                    tagged_gloss = tagged_gloss[jpos + 1:]
                else:
                    tagged_gloss.remove(j)
                break
        # if no word pos found for word, tag as <X>
        if not found:
            arranged_tagged_gloss.append([i, "<X>"])
    return arranged_tagged_gloss


# Takes a mapping of POS to gloss from the map_glosswords function,
# POS tags the Hofman gloss by comparing each tagged word in the Bauer gloss to each word in the Hofman gloss.
# SECOND VERSION
def matchword_levdist(gloss_mapping):
    gloss_string = gloss_mapping[0]
    gloss_list = gloss_string.split(" ")
    pos_list = gloss_mapping[1]
    tagged_gloss = list()
    lowest_eddist = False
    # include '.i.' in pos-list so it can be tagged
    for token in gloss_list:
        if token == ".i.":
            pos_list.append([".i.", "<SYM>"])
    # for each analysed word
    for pos_tag in pos_list:
        tagged_word = pos_tag[0]
        tag = pos_tag[1]
        # if the word is not an unused word-type
        if tag not in ["<PVP>", "<IFP>", "<PFX>", "<UNR>", "<UNK>"]:
            # check every token in the gloss-list for lowest edit distance from the analysed word
            for token in gloss_list:
                # split or conjoin hyphenated words in Hofman's corpus to get edit distance of units
                if "-" in token:
                    deconstruct = token.split("-")
                    splitpat = re.compile(r'\b[hn]-|-[sn].*\b')
                    splitpatitir = splitpat.finditer(token)
                    partlist = list()
                    for j in splitpatitir:
                        partlist.append(j.group())
                    for part in partlist:
                        if part[-1] == "-":
                            partplace = deconstruct.index(part[:-1])
                            deconstruct = deconstruct[:partplace] + deconstruct[partplace + 1:]
                            deconstruct[partplace] = part[:-1] + deconstruct[partplace]
                    for subtoken in deconstruct:
                        eddist = ed(tagged_word, subtoken)
                        if not lowest_eddist:
                            lowest_eddist = [eddist, subtoken, tag, tagged_word]
                            if eddist == 0:
                                break
                        else:
                            if eddist < lowest_eddist[0]:
                                lowest_eddist = [eddist, subtoken, tag, tagged_word]
                                if eddist == 0:
                                    break
                eddist = ed(tagged_word, token)
                # assign the word the pos-tag of the analysed word with the smallest edit distance from it
                if not lowest_eddist:
                    lowest_eddist = [eddist, token, tag, tagged_word]
                    if eddist == 0:
                        break
                else:
                    if eddist < lowest_eddist[0]:
                        lowest_eddist = [eddist, token, tag, tagged_word]
                        if eddist == 0:
                            break
            # print(lowest_eddist)
            tagged_gloss.append([lowest_eddist[1], lowest_eddist[2], lowest_eddist[0]])
            lowest_eddist = False
    # rearrange gloss to the same order as Hofman's
    arranged_tagged_gloss = list()
    for i in gloss_list:
        candidates = list()
        for j in tagged_gloss:
            if i == j[0]:
                candidates.append(j)
        if candidates:
            candidates = sorted(candidates, key=lambda x: x[-1])
            candidate = candidates[0]
            arranged_tagged_gloss.append(candidate[:-1])
            tagged_gloss.remove(candidate)
        # split or join hyphenated words in Hofman's corpus to compare candidates with new units
        elif "-" in i:
            deconstruct = i.split("-")
            splitpat = re.compile(r'\b[hn]-|-[sn].*\b')
            splitpatitir = splitpat.finditer(i)
            partlist = list()
            for j in splitpatitir:
                partlist.append(j.group())
            for part in partlist:
                if part[-1] == "-":
                    partplace = deconstruct.index(part[:-1])
                    deconstruct = deconstruct[:partplace] + deconstruct[partplace + 1:]
                    deconstruct[partplace] = part[:-1] + deconstruct[partplace]
            for k in deconstruct:
                subcandidates = list()
                for l in tagged_gloss:
                    if k == l[0]:
                        subcandidates.append(l)
                if subcandidates:
                    subcandidates = sorted(subcandidates, key=lambda x: x[-1])
                    subcandidate = subcandidates[0]
                    arranged_tagged_gloss.append(subcandidate[:-1])
                    tagged_gloss.remove(subcandidate)
        # if no candidate with an edit distance can be found, tag the word with X
        else:
            arranged_tagged_gloss.append([i, "<X>"])
    return arranged_tagged_gloss


# #                                               TEST FUNCTIONS


# # Test Function: standardise_glosschars()

# print(standardise_glosschars(clean_gloss(" ".join(glosslist))))
# print(standardise_glosschars('áéíóúḟṁṅṡ⁊'))


# # Test Function: standardise_wordchars()

# justwordslist = list()
# for i in wordslist:
#     for j in i:
#         justwordslist.append(clean_word(j[0]))
# print(standardise_wordchars(" ".join(justwordslist)))
# print(standardise_wordchars('Íáæǽéíóúċḟṁṅṡ⁊ɫ'))


# # Test Function: remove_glosshyphens()

# # Print one gloss from Hofman's corpus both before and after hyphenation is removed
# testgloss = glosslist[1576]
# # testgloss = "issí tra in dias-sa rosechestar-som"
# # testgloss = ".i. a n-dliged n-ísin neph-accomoil inna teora liter i-noen-sillaib"
# print(clean_gloss(testgloss))
# print(remove_glosshyphens(clean_gloss(testgloss)))

# # Print all glosses from Hofman's corpus with hyphenation removed
# for gl in glosslist:
#     clean = remove_glosshyphens(clean_gloss(gl))
#     print(clean)


# # Test Function: matchword_levdist()

# # Choose whether to test on amended or original Hofman glosses
# amendedglosses = [".i. libardaib",
#                ".i. attá di ṡeirc la laitnori inna grec coseichetar ci d a comroicniu",
#                "in méit so",
#                "is sí tra in dias sa rosechestar som",
#                ".i. i ndead inna ní sin",
#                ".i. is huas neurt dom ara doidṅgi",
#                ".i. ci insamlar",
#                "aite",
#                "inna flaithemnachtae"]
# # test_on = amendedglosses
# test_on = glosslist[:9]

# #                                            Original Function: V1

# # Test edit distance function on one gloss
# which_gloss = 1
# print(matchword_levdist_original(map_glosswords(test_on[which_gloss], wordslist[which_gloss])))
# print(test_on[which_gloss])
# for i in wordslist[which_gloss]:
#     print(i[0])

# # Test edit distance function on a range of glosses
# start_gloss = 0
# stop_gloss = 9
# for glossnum in range(start_gloss, stop_gloss):
#     print(matchword_levdist_original(map_glosswords(test_on[glossnum], wordslist[glossnum])))

# #                                              New Function: V2

# # Test edit distance function on one gloss
# which_gloss = 1
# print(matchword_levdist(map_glosswords(test_on[which_gloss], wordslist[which_gloss])))
# # print(test_on[which_gloss])
# # for i in wordslist[which_gloss]:
# #     print(i[0])

# # Test edit distance function on a range of glosses
# start_gloss = 0
# stop_gloss = 9
# for glossnum in range(start_gloss, stop_gloss):
#     print(matchword_levdist(map_glosswords(test_on[glossnum], wordslist[glossnum])))

