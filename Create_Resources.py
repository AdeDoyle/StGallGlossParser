
from Clean_ExcelLists import save_xlsx
from Clean_Glosses import save_obj
from Reassign_POS import save_sorted_tags, sort_tag_levels, list_tag_levels, save_all_pos_combos_list, loop_tags
from Map_GlossWords import create_glosslist, create_wordlist

# # Create SG. Combined Data.xlsx
# save_xlsx("SG. Combined Data", combolist, True)
#
# # Create Clean_GlossDict.pkl
# sgData = list_xlsx("SG. Combined Data", "Sheet 1")
# glosslist = list()
# lastgloss = ""
# for i in sgData:
#     thisgloss = i[8]
#     if thisgloss != lastgloss:
#         glosslist.append(thisgloss)
#         lastgloss = thisgloss
# glossdict = {}
# for i in glosslist:
#     glossdict[i] = clean_gloss(i)
# save_obj("Clean_GlossDict", glossdict)
#
# # Create Clean_WordDict.pkl
# sgData = list_xlsx("SG. Combined Data", "Sheet 1")
# wordlist = list()
# for i in sgData:
#     thisword = i[1]
#     if thisword:
#         if thisword not in wordlist:
#             wordlist.append(thisword)
# worddict = {}
# for i in wordlist:
#     worddict[i] = clean_word(i)
# save_obj("Clean_WordDict", worddict)
#
# # Create 'A1 List.pkl', 'A2 List.pkl', 'A3 List.pkl', 'Active_Passive List.pkl',
# # 'Relative Options List.pkl', and 'Translations List.pkl'
# print(save_sorted_tags(sort_tag_levels(list_tag_levels(analyses))))
#
# # Create 'All POS Combos Used.pkl'
# print(save_all_pos_combos_list(analyses))
#
# # Create 'POS_taglist.pkl'
# pos_list = list()
# for i in loop_tags(analyses, True):
#     tagged_i = i[1], i[-1]
#     pos_list.append(tagged_i)
# save_obj("POS_taglist", pos_list)
#
# # Create 'Gloss_List.pkl' and 'Words_List.pkl'
# create_glosslist(analyses)
# create_wordlist(analyses)
