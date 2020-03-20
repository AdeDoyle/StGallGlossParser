"""1. Change all chars [CHECK]
   2. Remove accents [CHECK]
   3. Remove hyphens [CHECK]
   4. Match all tokens in B to equivolent in A [CHECK]
   5. Output matchlist [CHECK]
   """

"""
   1.0. Find each word from Bauer in Hoffman [CHECK]
       1.1. Split Hoffman words if necessary to match with Bauer's [CHECK]
       1.2. Replace words in Hoffman in all cases with Bauer's [CHECK]
   2.0. Anything in Hoffman not replaced with Bauer, tag as Latin
       2.1. Tag Latin words with X(?)
   3.0. Give reliability score for match [CHECK]
   """

from Match_GlossSets import standardise_glosschars, standardise_wordchars, remove_glosshyphens
from Map_GlossWords import map_glosswords
from OpenXlsx import list_xlsx
from Pickle import open_obj
import re
from nltk import edit_distance as ed


analyses = list_xlsx("SG. Combined Data", "Sheet 1")
glosslist = open_obj("Gloss_List.pkl")
wordslist = open_obj("Words_List.pkl")


# Takes a mapping of POS to gloss from the map_glosswords function,
# POS tags the Hofman gloss by comparing each tagged word in the Bauer gloss to each word in the Hofman gloss.
# Gives a score for reliability of the cross tagging:
#     0 - perfect
#     1 - different number of words, all Bauer words matched with no spelling variation
#     2 - same number of words, some spelling variation
#     3 - different number of words, some spelling variation between matched words
# THIRD VERSION
def matchword_levdist_test(gloss_mapping):
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


# # TESTS


# # Choose whether to test on amended or original Hofman glosses
# amendedglosses = [".i. libardaib",
#                   ".i. attá di ṡeirc la laitnori inna grec coseichetar ci d a comroicniu",
#                   "in méit so",
#                   "is sí tra in dias sa rosechestar som",
#                   ".i. i ndead inna ní sin",
#                   ".i. is huas neurt dom ara doidṅgi",
#                   ".i. ci insamlar",
#                   "aite",
#                   "inna flaithemnachtae"]
# test_on = amendedglosses

# # Test edit distance function on one gloss
# tglos = 2620
# test_on = glosslist[tglos:tglos + 1]
# print(matchword_levdist_test(map_glosswords(test_on[0], wordslist[tglos])))

# # Test edit distance function on a range of glosses
# test_on = glosslist
# start_gloss = 0
# stop_gloss = 27
# for glossnum in range(start_gloss, stop_gloss):
#     print(glossnum, matchword_levdist_test(map_glosswords(test_on[glossnum], wordslist[glossnum])))

# # Test edit distance function on all glosses
# test_on = glosslist
# for glossnum, gloss in enumerate(test_on):
#     check = matchword_levdist_test(map_glosswords(gloss, wordslist[glossnum]))
#     if check:
#         print(glossnum, check)

