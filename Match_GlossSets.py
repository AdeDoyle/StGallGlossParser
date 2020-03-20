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


# Takes a mapping of POS to gloss from the map_glosswords function,
# POS tags the Hofman gloss by comparing each tagged word in the Bauer gloss to each word in the Hofman gloss.
# Gives a score for reliability of the cross tagging:
#     0 - perfect
#     1 - different number of words, all Bauer words matched with no spelling variation
#     2 - same number of words, some spelling variation
#     3 - different number of words, some spelling variation between matched words
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
            if original_word[-1] == "-":
                replacement = original_word[:-1] + gloss_list[i + 1]
                replacement_place = [i, i + 1]
                replace_list.append([replacement, replacement_place])
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
        for i in gloss_list:
            for j in standlist_copy:
                # if a standardised word form can be matched perfectly to a counterpart
                if j == remove_glosshyphens(standardise_glosschars(i)):
                    # add the two matched words to 'word-to-standardised-word mapping' list as a tuple
                    standard_mapping.append((i, j))
                    standlist_copy = standlist_copy[1:]
                    break
                # if a standardised word form can't be matched perfectly to one counterpart
                else:
                    # assume that standardisation has split a word into two or more standardised words
                    i_sublist = remove_glosshyphens(standardise_glosschars(i)).split(" ")
                    for sub_i in i_sublist:
                        for sub_j in standlist_copy:
                            # standardise the one word
                            # match each standard word to the full non-standard form if it matches a part of it
                            # add the two semi-matched words to 'word-to-standardised-word mapping' list as a tuple
                            if sub_j == remove_glosshyphens(standardise_glosschars(sub_i)):
                                standard_mapping.append((i, sub_j))
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
        standard_mapping = list(zip(gloss_list, standard_list))
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
    # check reliability of cross-tagging and apply score to output (increase score if no. of tokens don't match)
    if len(pos_list) != len(standard_list):
        tags_rating += 1
    # for each valid (POS tag in use) tagged word, if a perfect match can be found:
    #     1. align its position in the POS-list with the position of its counterpart in the Gloss-list
    #     2. add Bauer's original word, the pos tag, and the edit distance, to the tagged-gloss list
    alignment_list = list()
    # for each word in Bauer's analysis, in order
    for pos_place, pos_tag in enumerate(pos_list):
        original_word = pos_tag[0]
        standard_word = pos_tag[-1]
        tag = pos_tag[1]
        # if the word is valid (has a usable POS tag)
        if tag not in ["<PVP>", "<IFP>", "<PFX>", "<UNR>", "<UNK>"]:
            # check its edit distance against every token in Hofman's gloss, in order
            for word_place, token in enumerate(standard_list):
                eddist = ed(standard_word, token)
                # if it occurs, the first time an edit distance is zero between the Bauer word the Hofman token,
                # assume the two are a match
                # add Bauer's word, its POS tag, the edit distance, and indices for the match to an alignment list
                if eddist == 0:
                    lowest_eddist = [original_word, tag, eddist, [word_place, pos_place]]
                    alignment_list.append((pos_place, word_place))
                    tagged_gloss.append(lowest_eddist)
                    break
    # if any words have been aligned yet
    if alignment_list:
        # separate the list of words which have been perfectly aligned into separate lists for each used word and tag
        used_pos = list(list(zip(*alignment_list))[0])
        used_words = list(list(zip(*alignment_list))[1])
    else:
        used_pos = list()
        used_words = list()
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
                for token_place, token in enumerate(standard_list):
                    if token_place not in used_words:
                        eddist = ed(standard_word, token)
                        # find the lowest edit distance between the Bauer word a Hofman token,
                        # assume the two are a match identify the pair as the lowest-edit-distance candidates
                        if not lowest_eddist:
                            lowest_eddist = [original_word, tag, eddist, [token_place, pos_place]]
                        elif eddist < lowest_eddist[2]:
                            lowest_eddist = [original_word, tag, eddist, [token_place, pos_place]]
                    # if this token has already been matched with another, better candidate word from Bauer's analysis
                    else:
                        # but this word analysed by Bauer has not been matched with any of Hofman's tokens yet
                        if not lowest_eddist:
                            # if the unused word analysed by Bauer makes up a part of the used Hofman token
                            if standard_word in token:
                                # add the match as a "possibly-contained-in" match to a separate list
                                original_token = False
                                for mapped_token in standard_mapping:
                                    if token == mapped_token[1]:
                                        original_token = mapped_token[0]
                                if original_token:
                                    possible_match_list.append([original_word, tag, original_token])
                                # if the original form of the standardised token from Hofman cannot be found
                                else:
                                    raise RuntimeError("No original token could be found for the standard form which "
                                                       "potentially matches this word analysed by Bauer.")
                            # if the unused word analysed by Bauer does not make up a part of the used Hofman token
                            # assume no relation and pass
                            else:
                                pass
                        # if this word analysed by Bauer has been matched to at least one of Hofman's tokens already
                        # pass (there's no need to do anything here, this will happen unless the loop is broken once an
                        # edit distance is found to be the lowest so far)
                        else:
                            pass
                # if the lowest non-zero edit distance has been found between the Bauer word and a Hofman token
                # assume the two are a match
                # add Bauer's word, its POS tag, the edit distance, and indices for the match to an alignment list
                if lowest_eddist:
                    tagged_gloss.append(lowest_eddist)
                # if no non-zero edit distance has been found between the Bauer word and a Hofman token which is lower
                # than other, more likely combinations
                # assume the Bauer word was duplicated in a longer word
                # add nothing to the alignment list
                elif possible_match_list:
                    if possible_match_list[-1][0] == original_word:
                        pass
                else:
                    raise RuntimeError("No match found for word analysed by Bauer, and no partial match found to "
                                       "suggest the word has been duplicated within longer word.")
                lowest_eddist = False

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
    tagged_gloss = sorted(tagged_gloss, key=lambda x: (x[-1][1], x[-1][0]))
    # remove all indeces from tagged-gloss list for output
    for i, word in enumerate(tagged_gloss):
        tagged_gloss[i] = word[:3]
    # check reliability of cross-tagging and update score before output (increase score if edit distance not 0 for all)
    dist_list = [i[-1] for i in tagged_gloss]
    for i in dist_list:
        if i != 0:
            tags_rating += 2
            break
    # remove edit distances from tokens
    # then add reliability score for gloss and any possible word matches to the tagged-gloss list before output
    tagged_gloss = [tags_rating, [i[:-1] for i in tagged_gloss], possible_match_list]
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

# # Test edit distance function on one gloss
# tglos = 2760
# test_on = glosslist[tglos:tglos + 1]
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

