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

from Match_GlossSets import matchword_levdist
from Map_GlossWords import map_glosswords
from OpenXlsx import list_xlsx
from Pickle import open_obj


analyses = list_xlsx("SG. Combined Data", "Sheet 1")
glosslist = open_obj("Gloss_List.pkl")
wordslist = open_obj("Words_List.pkl")


# # Test edit distance function on one gloss
# tglos = 2620
# test_on = glosslist[tglos:tglos + 1]
# print(matchword_levdist(map_glosswords(test_on[0], wordslist[tglos])))

# Test edit distance function on all glosses
test_on = glosslist
count = 0
for glossnum, gloss in enumerate(test_on):
    check = matchword_levdist(map_glosswords(gloss, wordslist[glossnum]))
    if check[-1]:
        for pos_word in check[-1]:
            word_part = pos_word[0]
            tag_part = pos_word[1]
            check_in = pos_word[2]
            for word_tag in check[1]:
                word = word_tag[0]
                tag = word_tag[1]
                if tag == "<VERB>":
                    if check_in == word:
                        count += 1
                        print(count, glossnum, matchword_levdist(map_glosswords(gloss, wordslist[glossnum])))
                        break

