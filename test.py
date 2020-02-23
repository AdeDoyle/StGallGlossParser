"""Level 1"""


from OpenXlsx import list_xlsx
from Pickle import open_obj
from Map_GlossWords import map_glosswords
from Clean_Glosses import clean_gloss, clean_word
from nltk import edit_distance as ed
import re


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


"""1. Change all chars [CHECK]
   2. Remove accents [CHECK]
   3. Remove hyphens [CHECK]
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

