
from Clean_ExcelLists import create_data_combo
from Clean_Glosses import create_clean_glossdict, create_clean_worddict
from OpenXlsx import list_xlsx
from Reassign_POS import save_sorted_tags, sort_tag_levels, list_tag_levels,\
    save_all_pos_combos_list, create_pos_taglist
from Map_GlossWords import create_glosslist, create_wordlist


# #                                             CREATE RESOURCES

# # Create SG. 'Combined Data.xlsx'
# print(create_data_combo())
#
# # Set analyses variable for creation of further resources
# analyses = list_xlsx("SG. Combined Data", "Sheet 1")
#
# # Create 'Clean_GlossDict.pkl' and 'Clean_WordDict.pkl'
# print(create_clean_glossdict())
# print(create_clean_worddict())
#
# # Create 'A1 List.pkl', 'A2 List.pkl', 'A3 List.pkl', 'Active_Passive List.pkl',
# # 'Relative Options List.pkl', and 'Translations List.pkl'
# print(save_sorted_tags(sort_tag_levels(list_tag_levels(analyses))))
#
# # Create 'All POS Combos Used.pkl' and 'POS_taglist.pkl'
# print(save_all_pos_combos_list(analyses))
# print(create_pos_taglist())
#
# # Create 'Gloss_List.pkl' and 'Words_List.pkl'
# print(create_glosslist(analyses))
# print(create_wordlist(analyses))
