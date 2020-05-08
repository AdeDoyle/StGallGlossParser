"""Level 1"""


from OpenXlsx import list_xlsx
from Pickle import open_obj
import re
from nltk import edit_distance as ed
from Match_GlossSets import remove_glosshyphens, standardise_glosschars, standardise_wordchars
from Map_GlossWords import map_glosswords
from Clean_Glosses import clean_gloss, clean_word


analyses = list_xlsx("SG. Combined Data", "Sheet 1")
glosslist = open_obj("Gloss_List.pkl")
wordslist = open_obj("Words_List.pkl")


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

    #                                                 PART 3.1.0:
    #
    # for each valid (POS tag in use) tagged word, if a perfect match can be found:
    #     1. align its position in the POS-list with the position of its counterpart in the Gloss-list
    #     2. add Bauer's original word, the pos tag, and the edit distance, to the tagged-gloss list
    alignment_list = list()
    sorted_list = list()
    # for each word in Bauer's analysis, in order
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
    # if any words have been aligned yet
    if alignment_list:
        # isolate a list of used words (without used tags)
        used_pos = list(list(zip(*alignment_list))[0])
    else:
        used_pos = list()

    #                                                 PART 3.1.1:
    #
    # for each valid (POS tag in use) tagged word remaining, combine it with the following word where one exists,
    # if any of these combinations has a perfect match in the remaining tokens:
    #     1. align their positions in the POS-list with the position of the single counterpart in the Gloss-list
    #     2. add Bauer's original words, their pos tags, and their edit distances, to the tagged-gloss list in order
    # for each remaining word in Bauer's analysis which is followed by another remaining word
    for pos_place, pos_tag in enumerate(pos_list[:-1]):
        if pos_place not in used_pos and pos_place + 1 not in used_pos:
            tag = pos_tag[1]
            next_pos_tag = pos_list[pos_place + 1]
            next_tag = next_pos_tag[1]
            # if both words are valid (have usable POS tags) combine the two into one
            invalid_list = ["<PVP>", "<IFP>", "<PFX>", "<UNR>", "<UNK>"]
            if tag not in invalid_list and next_tag not in invalid_list:
                original_word = pos_tag[0]
                next_word = next_pos_tag[0]
                original_combo = original_word + next_word
                standard_combo = standardise_wordchars(original_combo)
                # check the edit distance between the combined tokens' standard form and
                # the standard form of every token in Hofman's gloss, in order
                for token_list in standard_mapping:
                    original_token = token_list[0]
                    standard_token = token_list[1]
                    token_place = token_list[2]
                    if token_place not in sorted_list:
                        eddist = ed(standard_combo, standard_token)
                        # if an edit distance of zero occurs, the first time it occurs, assume the two are a match
                        # add Bauer's word, its POS tag, Hofman's word, the edit distance, and indices for the match to
                        # a matching-words list
                        if eddist == 0:
                            sorted_list.append(token_place)
                            lowest_eddists = [[original_word, tag, original_token, eddist, [token_place, pos_place]],
                                              [next_word, next_tag, original_token, eddist, [token_place,
                                                                                             pos_place + 1]]]
                            alignment_list.extend([(pos_place, token_place)] + [(pos_place + 1, token_place)])
                            tagged_gloss.extend(lowest_eddists)
                            break
    # if any words or word-combos have been aligned yet
    if alignment_list:
        # separate the list of words and word-combos which have been perfectly aligned into
        # separate lists for each used word/word-combo and tag
        used_pos = list(list(zip(*alignment_list))[0])
        used_toks = list(list(zip(*alignment_list))[1])
    else:
        used_pos = list()
        used_toks = list()

    #                                                 PART 3.2.0:
    #
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

    #                                                 PART 3.3:
    #
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
                if not placement and original_word != 'mífogur':
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
    # for each token in Hofman's gloss, in order
    for i, tok_data in enumerate(standard_mapping):
        standard_check_tok = tok_data[1]
        found = False
        # find its first matching pos-tagged word where one exists, add it to a new, ordered, tagged gloss list
        for j, pos_data in enumerate(tagged_gloss):
            pos_check_word = remove_glosshyphens(standardise_glosschars(pos_data[2])).split(" ")
            if len(pos_check_word) > 1:
                hyphenation = True
            if standard_check_tok in pos_check_word:
                recombine_list.append(pos_data)
                found = True
                del tagged_gloss[j]
                # if the next tagged word is part of this same token in Hofman's gloss, add it to the tagged gloss too
                try:
                    next_standard_tok = standard_mapping[i + 1][1]
                except IndexError:
                    next_standard_tok = False
                if not next_standard_tok or next_standard_tok != standard_check_tok:
                    try:
                        next_pos_check_word = remove_glosshyphens(standardise_glosschars(tagged_gloss[0][2])).split(" ")
                    except IndexError:
                        next_pos_check_word = False
                    if next_pos_check_word and len(next_pos_check_word) == 1:
                        if standard_check_tok in next_pos_check_word:
                            recombine_list.append(tagged_gloss[0])
                            del tagged_gloss[0]
                break
        # if no tagged match was found, assume the word is Latin
        if not found:
            recombine_list.append([tok_data[0], "<X>", tok_data[1], [tok_data[2], tok_data[2]]])
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
                    if pos_index not in remove_indices:
                        check_matched = True
                        if placement == 'S':
                            remove_indices.append(pos_index)
                        elif placement == 'E':
                            remove_indices.append(pos_index)
                        elif placement == 'M':
                            remove_indices.append(pos_index)
            if not check_matched:
                remove_indices.append(pos_index)
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

# tglos = 953
# test_on = glosslist[tglos:tglos + 1]
# print(matchword_levdist(map_glosswords(test_on[0], wordslist[tglos])))

# tglos = 1542
# test_on = glosslist[tglos:tglos + 1]
# print(matchword_levdist(map_glosswords(test_on[0], wordslist[tglos])))

# tglos = 1878
# test_on = glosslist[tglos:tglos + 1]
# print(matchword_levdist(map_glosswords(test_on[0], wordslist[tglos])))

# tglos = 2425
# test_on = glosslist[tglos:tglos + 1]
# print(matchword_levdist(map_glosswords(test_on[0], wordslist[tglos])))

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
# error_codes = [0, 1, 11, 100, 101, 111, 1000, 1001, 1010, 1011, 1100, 1101, 1110, 1111]

# # Print the number of glosses containing each error code
# for ercode in error_codes:
#     codecount = 0
#     for outgloss in output_glosslist:
#         if outgloss[0] == ercode:
#             codecount += 1
#     print("{}: {}".format(ercode, codecount))

# # Print each gloss containing a specified error code
# for ercode in error_codes:
#     codecount = 0
#     for outgloss in output_glosslist:
#         if outgloss[0] == ercode:
#             codecount += 1
#             if ercode == 11:
#                 print(outgloss)
#                 print(" ".join([i[0] for i in outgloss[1]]) + "\n")

