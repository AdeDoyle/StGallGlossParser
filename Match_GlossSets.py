"""Level 1"""


from OpenXlsx import list_xlsx
from Pickle import open_obj
from Map_GlossWords import map_glosswords
from Clean_Glosses import clean_gloss

from nltk import edit_distance as ed


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


# #                                               TEST FUNCTIONS


testglosses = [".i. libardaib",
               ".i. attá di ṡeirc la laitnori inna grec coseichetar ci d a comroicniu",
               "in méit so",
               "is sí tra in dias sa rosechestar som",
               ".i. i ndead inna ní sin",
               ".i. is huas neurt dom ara doidṅgi",
               ".i. ci insamlar",
               "aite",
               "inna flaithemnachtae"]


# # Test on amended or original Hofman glosses
# test_on = testglosses
# # test_on = glosslist[:9]

# # Test edit distance function on one gloss
# which_gloss = 1
# print(matchword_levdist(map_glosswords(test_on[which_gloss], wordslist[which_gloss])))
# print(test_on[which_gloss])
# for i in wordslist[which_gloss]:
#     print(i[0])

# # Test edit distance function on a range of glosses
# start_gloss = 0
# stop_gloss = 9
# for glossnum in range(start_gloss, stop_gloss):
#     print(matchword_levdist(map_glosswords(test_on[glossnum], wordslist[glossnum])))


# for i, gloss in enumerate(glosslist[:9]):
#     wordlist = wordslist[i]
#     pos_data = map_glosswords(gloss, wordlist)
#     print(pos_data[0], "\n", pos_data[1])

