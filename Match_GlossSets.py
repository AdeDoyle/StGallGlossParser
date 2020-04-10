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
                raise RuntimeError("Expected reconstruction of word could not be determined.")
            elif reconstruct:
                words[word_index] = reconstruct
            if word_ending:
                del words[word_index + 1]
                word_ending = False
    return " ".join(words)


# Takes a mapping of POS to gloss from the map_glosswords function,
# POS tags the Hofman gloss by comparing each tagged word in the Bauer gloss to each word in the Hofman gloss.
# ORIGINAL VERSION (this function has been improved)
def matchword_levdist_first(gloss_mapping):
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
def matchword_levdist_second(gloss_mapping):
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


# Takes a mapping of POS to gloss from the map_glosswords function,
# POS tags the Hofman gloss by comparing each tagged word in the Bauer gloss to each word in the Hofman gloss.
# Gives a score for reliability of the cross tagging:
#     0 - perfect
#     1 - different number of words between standardised Bauer gloss and standardised Hofman gloss
#    10 - different number of tagged words before and after Latin content reintroduced
#   100 - hyphenated word in Hofman's gloss replaced by alternative(s) from Bauer's analysis
#  1000 - some spelling variation between matched words
# THIRD VERSION
def matchword_levdist(gloss_mapping):
    gloss_string = gloss_mapping[0]
    gloss_list = gloss_string.split(" ")
    standard_string = remove_glosshyphens(standardise_glosschars(gloss_string))
    standard_list = standard_string.split(" ")
    standard_mapping = False
    pos_list = gloss_mapping[1]
    possible_match_list = list()
    tags_rating = 0
    tagged_gloss = list()

    #                                                 PART 1:
    #
    # Create a list of standardised word forms from Hofman's gloss, and the original word they match.

    # if there are more words in Hofman's gloss before standardisation, combine disjointed words
    if len(gloss_list) > len(standard_list):
        replace_list = list()
        for i, original_word in enumerate(gloss_list):
            # if the word ends in a suspension stroke, the following word will be the expanded contraction
            # remove the hyphen and combine the two words to make one
            if original_word[-1] == "-":
                replacement = original_word[:-1] + gloss_list[i + 1]
                replacement_place = [i, i + 1]
                replace_list.append([replacement, replacement_place])
        # replace the two, originally split tokens of the word with the new combined form
        for replacement in replace_list:
            rep_word = replacement[0]
            rep_place = replacement[1]
            gloss_list = gloss_list[:rep_place[0]] + [rep_word] + gloss_list[rep_place[1] + 1:]
            standard_list = remove_glosshyphens(standardise_glosschars(" ".join(standard_list))).split(" ")
    if len(gloss_list) > len(standard_list):
        raise RuntimeError("Fewer words in Hofman's gloss after standardisation.")
    # if there are more words in Hofman's gloss after standardisation
    if len(standard_list) > len(gloss_list):
        standlist_copy = standard_list
        standard_mapping = list()
        # try to match each standardised word to its counterpart
        for i, split_word in enumerate(gloss_list):
            for j, standard_form in enumerate(standlist_copy):
                # if a standardised word form can be matched perfectly to a counterpart
                if standard_form == remove_glosshyphens(standardise_glosschars(split_word)):
                    # add the two matched words to 'word-to-standardised-word mapping' list as a tuple with indices
                    standard_mapping.append((split_word, standard_form, i))
                    standlist_copy = standlist_copy[1:]
                    break
                # if a standardised word form can't be matched perfectly to one counterpart
                else:
                    # assume that standardisation has split a word into two or more standardised words
                    i_sublist = remove_glosshyphens(standardise_glosschars(split_word)).split(" ")
                    for sub_i, sub_split_word in enumerate(i_sublist):
                        for sub_standard_form in standlist_copy:
                            # standardise the one word
                            # match each standard word to the full non-standard form if it matches a part of it
                            # add the two semi-matched words to 'word-to-standardised-word mapping' list as a tuple
                            # with their indices
                            if sub_standard_form == remove_glosshyphens(standardise_glosschars(sub_split_word)):
                                standard_mapping.append((split_word, sub_standard_form, [i, sub_i]))
                                standlist_copy = standlist_copy[1:]
                                break
                            # if a standardised word does not seem to match a part of the full non-standard word
                            else:
                                raise RuntimeError("Standard word form could not be matched to original word form from "
                                                   "Hofman.")
                    break
    # if there are the same number of words in Hofman's gloss before and after standardisation
    elif len(gloss_list) == len(standard_list):
        # assume a one-to-one match between the same indices in original and standardised word lists
        # match each as a tuple and add all to a 'word-to-standardised-word mapping' list
        gloss_indices = [i for i, _ in enumerate(gloss_list)]
        standard_mapping = list(zip(gloss_list, standard_list, gloss_indices))
        # if a matched pair in the 'word-to-standardised-word mapping' list do not match
        for matched_word in standard_mapping:
            if matched_word[1] != remove_glosshyphens(standardise_glosschars(matched_word[0])):
                print(matched_word[1], remove_glosshyphens(standardise_glosschars(matched_word[0])))
                raise RuntimeError("A word from Hofman's gloss has been paired with a standardised word form which it "
                                   "does not match.")
    # if no 'word-to-standardised-word mapping' list has been created yet
    if not standard_mapping:
        raise RuntimeError("No mapping of words to their standard forms has been created for Hofman's gloss.")

    #                                                 PART 2:
    #
    # Add a standardised form of each word to the original word and POS tag in Bauer's tagged-gloss list.

    for i, tagged_word in enumerate(pos_list):
        pos_list[i] = tagged_word + [standardise_wordchars(tagged_word[0])]

    #                                                 PART 3:
    #
    # Connect tagged words from Bauer's analysis with their counterparts from Hofman's gloss,
    # Apply reliability rating for the match between words in the gloss as a whole.

    # include '.i.' in pos-list so it can be tagged
    if ".i." in standard_list:
        if [".i.", "<SYM>", ".i."] not in pos_list:
            for token in standard_list:
                if token == ".i.":
                    pos_list.append([".i.", "<SYM>", ".i."])
    # remove '-' from pos_list where Bauer has used it to represent a word reduced to zero
    pos_list = [i for i in pos_list if i[0] != "-"]
    # check reliability of cross-tagging and apply score to output
    # measure length of POS list against token list after accounting for ".i." symbols and hyphens
    # increase one digit if no. of tokens don't match
    if len(pos_list) != len(standard_list):
        tags_rating += 1
    # for each valid (POS tag in use) tagged word, if a perfect match can be found:
    #     1. align its position in the POS-list with the position of its counterpart in the Gloss-list
    #     2. add Bauer's original word, the pos tag, and the edit distance, to the tagged-gloss list
    alignment_list = list()
    # for each word in Bauer's analysis, in order
    sorted_list = list()
    for pos_place, pos_tag in enumerate(pos_list):
        original_word = pos_tag[0]
        standard_word = pos_tag[-1]
        tag = pos_tag[1]
        # if the word is valid (has a usable POS tag)
        if tag not in ["<PVP>", "<IFP>", "<PFX>", "<UNR>", "<UNK>"]:
            # check the edit distance between its standard and the standard form of every token in Hofman's gloss,
            # in order
            for token_list in standard_mapping:
                original_token = token_list[0]
                standard_token = token_list[1]
                token_place = token_list[2]
                if token_place not in sorted_list:
                    eddist = ed(standard_word, standard_token)
                    # if an edit distance of zero occurs, the first time it occurs, assume the two are a match
                    # add Bauer's word, its POS tag, Hofman's word, the edit distance, and indices for the match to a
                    # matching-words list
                    if eddist == 0:
                        sorted_list.append(token_place)
                        lowest_eddist = [original_word, tag, original_token, eddist, [token_place, pos_place]]
                        alignment_list.append((pos_place, token_place))
                        tagged_gloss.append(lowest_eddist)
                        break
    # if any words have not been aligned yet
    if alignment_list:
        # separate the list of words which have been perfectly aligned into separate lists for each used word and tag
        used_pos = list(list(zip(*alignment_list))[0])
        used_toks = list(list(zip(*alignment_list))[1])
    else:
        used_pos = list()
        used_toks = list()
    # for the remaining words in Bauer's analysis which cannot be mapped perfectly to a word in Hofman's gloss
    # find the word in Hofman's gloss with the lowest edit distance from the each analysed word and match these
    lowest_eddist = False
    # for each remaining word in Bauer's analysis, in order
    for pos_place, pos_tag in enumerate(pos_list):
        if pos_place not in used_pos:
            original_word = pos_tag[0]
            standard_word = pos_tag[-1]
            tag = pos_tag[1]
            # if the word is valid (has a usable POS tag)
            if tag not in ["<PVP>", "<IFP>", "<PFX>", "<UNR>", "<UNK>"]:
                # check its edit distance against every remaining token in Hofman's gloss, in order
                for token_list in standard_mapping:
                    original_token = token_list[0]
                    standard_token = token_list[1]
                    token_place = token_list[2]
                    if token_place not in used_toks:
                        eddist = ed(standard_word, standard_token)
                        # find the lowest edit distance between the standard Bauer word and a standard Hofman token,
                        # assume the two are a match and identify the pair as the lowest-edit-distance candidates
                        if not lowest_eddist:
                            lowest_eddist = [original_word, tag, original_token, eddist, [token_place, pos_place]]
                        elif eddist < lowest_eddist[3]:
                            lowest_eddist = [original_word, tag, original_token, eddist, [token_place, pos_place]]
                # if the lowest non-zero edit distance has been found between the Bauer word and a Hofman token
                # assume the two are a match
                # add Bauer's word, its POS tag, the Hofman word, the edit distance, and indices for the match to a
                # matching-words list
                if lowest_eddist:
                    alignment_list.append((lowest_eddist[-1][-1], lowest_eddist[-1][0]))
                    tagged_gloss.append(lowest_eddist)
                    lowest_eddist = False
    # if any POS tagged words remain unmatched, but all tokens from Hofman's gloss have been matched
    if alignment_list:
        # separate the list of words which have already been aligned with their best possible candidates
        used_pos = list(list(zip(*alignment_list))[0])
    else:
        used_pos = list()
    # for any leftover words in Bauer's analysis, in order
    for pos_place, pos_tag in enumerate(pos_list):
        if pos_place not in used_pos:
            original_word = pos_tag[0]
            standard_word = pos_tag[-1]
            tag = pos_tag[1]
            # if the word is valid (has a usable POS tag)
            if tag not in ["<PVP>", "<IFP>", "<PFX>", "<UNR>", "<UNK>"]:
                placement = False
                # check that the standard form of the word is in the standard token
                for token_list in standard_mapping:
                    original_token = token_list[0]
                    standard_token = token_list[1]
                    token_place = token_list[2]
                    if standard_word in standard_token:
                        # check where in the standard token the standard word is (start/end/middle/unknown)
                        if standard_token[:len(standard_word)] == standard_word:
                            placement = "S"
                        elif standard_token[-len(standard_word):] == standard_word:
                            placement = "E"
                        else:
                            placement = "M"
                        possible_match_list.append([original_word, tag, original_token, token_place, placement])
                if not placement:
                    raise RuntimeError("Unused POS tagged word ({}) could not be matched".format(original_word))

    #                                                 PART 4:
    #
    # Rearange the gloss so that tagged words occur in the correct position.

    # because Bauer never analyses the '.i.' symbol, rely only on its index from Hofman's gloss
    for tagged_place, word in enumerate(tagged_gloss):
        if word[0] == ".i.":
            old_tag = word[-1]
            word_place = old_tag[0]
            new_tag = [word_place, word_place]
            word = word[:-1] + [new_tag]
            tagged_gloss[tagged_place] = word
    # sort the tagged tokens based primarily on their index in Hofman's gloss,
    # if necessary, sort tagged tokens secondarily based on their index Bauer's analysis
    try:
        tagged_gloss = sorted(tagged_gloss, key=lambda x: (x[-1][1], x[-1][0]))
    except TypeError:
        updated_tagged_gloss = list()
        for data in tagged_gloss:
            if isinstance(data[-1][0], list):
                updated_tagged_gloss.append(data)
            elif isinstance(data[-1][0], int):
                new_list = [data[-1][0], data[-1][0]]
                new_data = data[:-1] + [[new_list, data[-1][1]]]
                updated_tagged_gloss.append(new_data)
        tagged_gloss = sorted(updated_tagged_gloss, key=lambda x: (x[-1][1], x[-1][0]))
    before_length = len(tagged_gloss)
    # reintroduce latin words which could not be matched with anything in Bauer's analysis,
    # and order tokens in accordance with Hofman's gloss
    recombine_list = list()
    hyphenation = False
    for i in standard_mapping:
        standard_check_tok = i[1]
        found = False
        for j, pos_data in enumerate(tagged_gloss):
            pos_check_word = remove_glosshyphens(standardise_glosschars(pos_data[2])).split(" ")
            if len(pos_check_word) > 1:
                hyphenation = True
            if standard_check_tok in pos_check_word:
                recombine_list.append(pos_data)
                found = True
                del tagged_gloss[j]
                break

            # else:
            #     print([i[1] for i in standard_mapping])
            #     print([j[2] for j in tagged_gloss])
            #     raise RuntimeError("Words not matched as expected here.")

        if not found:
            recombine_list.append([i[0], "<X>", i[1], [i[2], i[2]]])
    tagged_gloss = recombine_list
    # check reliability of cross-tagging and update score before output
    # measure length of the tagged gloss before and after Latin content is reintroduced
    # increase ten digit if no. of tokens don't match
    # increase hundred digit if hyphenated word has been replaced
    after_length = len(tagged_gloss)
    if before_length != after_length:
        tags_rating += 10
    if hyphenation:
        tags_rating += 100
    # if indices of potential-matches already assigned
    # remove suggested match from potential-matches list OR include suggested match and adjust relevant word
    match_indices = [x[-1][-1] for x in tagged_gloss]
    possible_match_list = [x for x in possible_match_list if x[-1][-1] not in match_indices]
    if possible_match_list:
        remove_indices = list()
        for pos_index, possible_match in enumerate(possible_match_list):
            check_matched = False
            check_token = possible_match[2]
            token_place = possible_match[3]
            placement = possible_match[4]
            for tagged_data in tagged_gloss:
                match_token = tagged_data[2]
                tagged_tok_place = tagged_data[-1]
                if tagged_tok_place[0] == token_place and match_token == check_token:
                    check_matched = True
                    if placement == 'S':
                        remove_indices.append(pos_index)
                    elif placement == 'E':
                        remove_indices.append(pos_index)
                    elif placement == 'M':
                        remove_indices.append(pos_index)
            if not check_matched:
                raise RuntimeError("Mismatched potential match with gloss-word or gloss-word's index in gloss.")
        if remove_indices:
            for index in sorted(remove_indices, reverse=True):
                del possible_match_list[index]
    if possible_match_list:
        raise RuntimeError("Possible matches remain which have not been used.")
    # remove all indeces from tagged-gloss list for output
    for i, word in enumerate(tagged_gloss):
        tagged_gloss[i] = word[:4]
    # check reliability of cross-tagging and update score before output
    # increase thousand digit if edit distance not 0 for all tokens
    dist_list = [i[-1] for i in tagged_gloss]
    for i in dist_list:
        if i != 0:
            tags_rating += 1000
            break
    # remove edit distances and original Hofman token from token data before output
    # then add reliability score for gloss and any possible word matches to the tagged-gloss list before output
    tagged_gloss = [tags_rating, [i[:-2] for i in tagged_gloss], possible_match_list]
    return tagged_gloss


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

# #                                              Function: V1

# # Test edit distance function on one gloss
# which_gloss = 1
# print(matchword_levdist_first(map_glosswords(test_on[which_gloss], wordslist[which_gloss])))
# print(test_on[which_gloss])
# for i in wordslist[which_gloss]:
#     print(i[0])

# # Test edit distance function on a range of glosses
# start_gloss = 0
# stop_gloss = 9
# for glossnum in range(start_gloss, stop_gloss):
#     print(matchword_levdist_first(map_glosswords(test_on[glossnum], wordslist[glossnum])))

# #                                              Function: V2

# # Test edit distance function on one gloss
# which_gloss = 1
# print(matchword_levdist_second(map_glosswords(test_on[which_gloss], wordslist[which_gloss])))
# # print(test_on[which_gloss])
# # for i in wordslist[which_gloss]:
# #     print(i[0])

# # Test edit distance function on a range of glosses
# start_gloss = 0
# stop_gloss = 9
# for glossnum in range(start_gloss, stop_gloss):
#     print(matchword_levdist_second(map_glosswords(test_on[glossnum], wordslist[glossnum])))

# #                                              Function: V3

# # Test edit distance function on individual glosses
# tglos = 1
# test_on = glosslist[tglos:tglos + 1]
# print(matchword_levdist(map_glosswords(test_on[0], wordslist[tglos])))

# tglos = 2
# test_on = glosslist[tglos:tglos + 1]
# print(matchword_levdist(map_glosswords(test_on[0], wordslist[tglos])))

# tglos = 14
# test_on = glosslist[tglos:tglos + 1]
# print(matchword_levdist(map_glosswords(test_on[0], wordslist[tglos])))

# tglos = 17
# test_on = glosslist[tglos:tglos + 1]
# print(matchword_levdist(map_glosswords(test_on[0], wordslist[tglos])))

# tglos = 26
# test_on = glosslist[tglos:tglos + 1]
# print(matchword_levdist(map_glosswords(test_on[0], wordslist[tglos])))

# tglos = 33
# test_on = glosslist[tglos:tglos + 1]
# print(matchword_levdist(map_glosswords(test_on[0], wordslist[tglos])))

# tglos = 54
# test_on = glosslist[tglos:tglos + 1]
# print(matchword_levdist(map_glosswords(test_on[0], wordslist[tglos])))

# tglos = 2760
# test_on = glosslist[tglos:tglos + 1]
# print(map_glosswords(test_on[0], wordslist[tglos]))
# print(matchword_levdist(map_glosswords(test_on[0], wordslist[tglos])))

# # Test edit distance function on a range of glosses
# test_on = glosslist
# start_gloss = 0
# stop_gloss = 27
# for glossnum in range(start_gloss, stop_gloss):
#     print(glossnum, matchword_levdist(map_glosswords(test_on[glossnum], wordslist[glossnum])))

# # Test edit distance function on all glosses
# test_on = glosslist
# for glossnum, gloss in enumerate(test_on):
#     check = matchword_levdist(map_glosswords(gloss, wordslist[glossnum]))
#     if check:
#         print(glossnum, check)


# # Print the number of glosses containing an error code of 0 (i.e. perfectly matched glosses)
# test_on = glosslist
# count = 0
# for glossnum, gloss in enumerate(test_on):
#     check = matchword_levdist(map_glosswords(gloss, wordslist[glossnum]))
#     if check[0] == 0:
#         count += 1
#         print(count, glossnum, check)

# # # Produce a list of all error codes which occur in output of matchword_levdist function
# output_glosslist = [matchword_levdist(map_glosswords(j, wordslist[i])) for i, j in enumerate(glosslist)]
# # error_codes = sorted(list(set([i[0] for i in output_glosslist])))
# error_codes = [0, 1, 100, 101, 1000, 1001, 1010, 1011, 1100, 1101, 1110, 1111]

# # Print the numbe of glosses containing each error code
# for ercode in error_codes:
#     codecount = 0
#     for outgloss in output_glosslist:
#         if outgloss[0] == ercode:
#             codecount += 1
#     if codecount < 100:
#         print("{}: {}".format(ercode, codecount))

