"""Level 1"""


from OpenXlsx import list_xlsx
from Pickle import open_obj
from Map_GlossWords import map_glosswords
from Clean_Glosses import clean_gloss
from nltk import edit_distance as ed
import re


analyses = list_xlsx("SG. Combined Data", "Sheet 1")
glosslist = open_obj("Gloss_List.pkl")
wordslist = open_obj("Words_List.pkl")


# Takes a mapping of POS to gloss from the map_glosswords function,
# POS tags the Hofman gloss by comparing each tagged word in the Bauer gloss to each word in the Hofman gloss.
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


testglosses = [".i. libardaib",
               ".i. attá di ṡeirc la laitnori inna grec coseichetar ci d a comroicniu",
               "in méit so",
               "is sí tra in dias sa rosechestar som",
               ".i. i ndead inna ní sin",
               ".i. is huas neurt dom ar a doidṅgi",
               ".i. ci insamlar",
               "aite",
               "inna flaithemnachtae"]


# # Test on amended or original Hofman glosses
# # test_on = testglosses
# test_on = glosslist[:9]

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


testlist = list()
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
                pass
            # If there's only one hyphen in a word
            elif word.count("-") == 1:
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
                    splitpat = re.compile(r'\b(niro|nádn)-')
                    splitpatitir = splitpat.finditer(word)
                    if splitpatitir:
                        for patfind in splitpatitir:
                            wrong_prefix = patfind.group()
                            wrong_remainder = "".join(word.split(wrong_prefix))
                            if wrong_prefix == "niro-":
                                word = "ni-ro" + wrong_remainder
                            elif wrong_prefix == "nádn-":
                                word = "nád-n" + wrong_remainder
                            reconstruct = " ".join(word.split("-"))
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
                # If the hyphen marks a prefix, remove the hyphen and insert a space
                if not reconstruct:
                    splitpat = re.compile(r'\b(ar|bith|cach|derb|etar|il|lán|llán|leth|mi|mí|neph|ní|nue|'
                                          r'oen|óen|oin|óin|oín|sen)-\w.*\b')
                    splitpatitir = splitpat.finditer(word)
                    if splitpatitir:
                        for _ in splitpatitir:
                            reconstruct = " ".join(deconstruct)
                # If the hyphen marks a suffix, remove the hyphen and insert a space
                if not reconstruct:
                    splitpat = re.compile(r'\b.*\w-(ni|sa|se|sem|si|sí|sidi|sin|siu|síu|so|som|son)\b')
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
                    testlist.append(word)
            if not reconstruct:
                # testlist.append(word)
                pass
            elif reconstruct:
                words[word_index] = reconstruct
            if word_ending:
                del words[word_index + 1]
                word_ending = False
    # return " ".join(words)
    return testlist


# \b[\wḟṡáéíóú]*-[^ḟṡa-záéíóú]
# for gl in glosslist:
#     clean = remove_glosshyphens(clean_gloss(gl))
#     if "-" in clean:
#         # print(clean)
#         # print()
#         pass

for gl in glosslist:
    remove_glosshyphens(clean_gloss(gl))
typecount = 0
for testitem in sorted(set(testlist)):
    typecount += 1
    print(str(typecount) + ". " + testitem)

# testgloss = "issí tra in dias-sa rosechestar-som"
# # testgloss = ".i. a n-dliged n-ísin neph-accomoil inna teora liter i-noen-sillaib"
# print(remove_glosshyphens(clean_gloss(testgloss)))

# for i in glosslist:
#     clean = clean_gloss(i)
#     if clean.count("-") >= 2:
#         print(clean)


"""1. Change all chars
   2. Remove accents
   3. Remove hyphens (hyphens at word ends?)
   4. Match all tokens in B to equivolent in A
   5. Output matchlist"""

# all_words = list()
# for gloss in glosslist:
#     gloss = clean_gloss(gloss)
#     words = gloss.split(" ")
#     for word in words:
#         if "-" in word:
#             if word not in all_words:
#                 all_words.append(word)
# print(len(all_words))
# for word in sorted(all_words):
#     # print(word)
#     if word.count("-") > 1:
#         print(word)

