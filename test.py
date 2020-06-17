"""Level 1"""


from OpenXlsx import list_xlsx
from Pickle import open_obj
import re
from nltk import edit_distance as ed
from Match_GlossSets import remove_glosshyphens, standardise_glosschars, standardise_wordchars
from Map_GlossWords import map_glosswords
from CoNLL_U import split_pos_feats, add_features, update_feature, update_tag
from Clean_Glosses import clean_gloss, clean_word


analyses = list_xlsx("SG. Combined Data", "Sheet 1")
glosslist = open_obj("Gloss_List.pkl")
wordslist = open_obj("Words_List.pkl")


# Takes a mapping of POS to gloss from the map_glosswords function,
# POS tags the Hofman gloss by comparing each tagged word in the Bauer gloss to each word in the Hofman gloss.
# Gives a score for reliability of the cross tagging:
#     0 - perfect
#     1 - duplicated parts-of-speech removed from Bauer's analysis before combining
#    10 - different number of words between standardised Bauer gloss and standardised Hofman gloss
#   100 - different number of tagged words before and after Latin content reintroduced
#  1000 - hyphenated word in Hofman's gloss replaced by alternative(s) from Bauer's analysis
# 10000 - some spelling variation between matched words
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
    # Create a list of standardised token forms from Hofman's gloss, and the original token they match.

    # if there are more tokens in Hofman's gloss before standardisation, combine disjointed tokens
    if len(gloss_list) > len(standard_list):
        replace_list = list()
        for i, original_token in enumerate(gloss_list):
            # if the token ends in a suspension stroke, the following token will be the expanded contraction
            # remove the hyphen and combine the two tokens to make one
            if original_token[-1] == "-":
                replacement = original_token[:-1] + gloss_list[i + 1]
                replacement_place = [i, i + 1]
                replace_list.append([replacement, replacement_place])
        # replace the two, originally split tokens of the token with the new combined form
        for replacement in replace_list:
            rep_token = replacement[0]
            rep_place = replacement[1]
            gloss_list = gloss_list[:rep_place[0]] + [rep_token] + gloss_list[rep_place[1] + 1:]
            standard_list = remove_glosshyphens(standardise_glosschars(" ".join(standard_list))).split(" ")
    if len(gloss_list) > len(standard_list):
        raise RuntimeError("Fewer tokens in Hofman's gloss after standardisation.")
    # if there are more tokens in Hofman's gloss after standardisation
    if len(standard_list) > len(gloss_list):
        standlist_copy = standard_list
        standard_mapping = list()
        # try to match each standardised token to its counterpart
        for i, split_token in enumerate(gloss_list):
            for j, standard_form in enumerate(standlist_copy):
                # if a standardised token form can be matched perfectly to a counterpart
                if standard_form == remove_glosshyphens(standardise_glosschars(split_token)):
                    # add the two matched tokens to 'token-to-standardised-token mapping' list as a tuple with indices
                    standard_mapping.append((split_token, standard_form, i))
                    standlist_copy = standlist_copy[1:]
                    break
                # if a standardised token form can't be matched perfectly to one counterpart
                else:
                    # assume that standardisation has split a token into two or more standardised tokens
                    i_sublist = remove_glosshyphens(standardise_glosschars(split_token)).split(" ")
                    for sub_i, sub_split_token in enumerate(i_sublist):
                        for sub_standard_form in standlist_copy:
                            # standardise the one token
                            # match each standard token to the full non-standard form if it matches a part of it
                            # add the two semi-matched tokens to 'token-to-standardised-token mapping' list as a tuple
                            # with their indices
                            if sub_standard_form == remove_glosshyphens(standardise_glosschars(sub_split_token)):
                                standard_mapping.append((split_token, sub_standard_form, [i, sub_i]))
                                standlist_copy = standlist_copy[1:]
                                break
                            # if a standardised token does not seem to match a part of the full non-standard token
                            else:
                                raise RuntimeError("Standard token form could not be matched to original token form"
                                                   " from Hofman.")
                    break
    # if there are the same number of tokens in Hofman's gloss before and after standardisation
    elif len(gloss_list) == len(standard_list):
        # assume a one-to-one match between the same indices in original and standardised token lists
        # match each as a tuple and add all to a 'token-to-standardised-token mapping' list
        gloss_indices = [i for i, _ in enumerate(gloss_list)]
        standard_mapping = list(zip(gloss_list, standard_list, gloss_indices))
        # if a matched pair in the 'token-to-standardised-token mapping' list do not match
        for matched_token in standard_mapping:
            if matched_token[1] != remove_glosshyphens(standardise_glosschars(matched_token[0])):
                raise RuntimeError("A token from Hofman's gloss has been paired with a standardised token form which"
                                   " it does not match.")
    # if no 'token-to-standardised-token mapping' list has been created yet
    if not standard_mapping:
        raise RuntimeError("No mapping of tokens to their standard forms has been created for Hofman's gloss.")
    # if any token in the 'token-to-standardised-token mapping' list is a known triple combination
    # which is not accounted for by Bauer's analysis, split it into parts
    trip_toks = ["airindi", "airindí", "arindi", "arindí", "anisin", "anísin", "anisiu", "anísiu",
                 "dindí", "dindhí", "dondí", "donaib-hí",
                 "Manidecamar", "manubed"]
    mapping_copy = list()
    trips_found = False
    for i, token_match in enumerate(standard_mapping):
        if token_match[0] in trip_toks:
            trips_found = True
            match_original = token_match[0]
            match_standard = token_match[1]
            match_place = token_match[2]
            new_split = False
            if match_standard in ["airindi", "arindi"]:
                new_split = [(match_original[:-4], match_standard[:-4], match_place),
                             (match_original[-4:-1], match_standard[-4:-1], match_place),
                             (match_original[-1:], match_standard[-1:], match_place)]
            elif match_standard in ["anisin", "anisiu"]:
                new_split = [(match_original[:1], match_standard[:1], match_place),
                             (match_original[1:3], match_standard[1:3], match_place),
                             (match_original[3:], match_standard[3:], match_place)]
            elif match_standard in ["dindi", "dondi"]:
                new_split = [(match_original[:2], match_standard[:2], match_place),
                             (match_original[2:4], match_standard[2:4], match_place),
                             (match_original[4:], match_standard[4:], match_place)]
            elif match_original[-3:] == "-hí":
                new_split = [(match_original[:-3], match_standard[:-2], match_place),
                             (match_original[-2:], match_standard[-2:], match_place)]
            elif match_original[-2:] == "hí":
                new_split = [(match_original[:-2], match_standard[:-2], match_place),
                             (match_original[-2:], match_standard[-2:], match_place)]
            elif match_original[-1] == "í":
                new_split = [(match_original[:-1], match_standard[:-1], match_place),
                             (match_original[-1:], match_standard[-1:], match_place)]
            elif match_original[:4] in ["Mani"]:
                new_split = [(match_original[:4], match_standard[:4], match_place),
                             (match_original[4:], match_standard[4:], match_place)]
            elif match_original[:4] in ["manu"]:
                new_split = [(match_original[:2], match_standard[:2], match_place),
                             (match_original[2:], match_standard[2:], match_place)]
            for j in new_split:
                mapping_copy.append(j)
        else:
            mapping_copy.append(token_match)
    if trips_found:
        for i, token_match in enumerate(mapping_copy):
            mapping_copy[i] = (token_match[0], token_match[1], i)
    standard_mapping = mapping_copy

    #                                                 PART 2:
    #
    # Add a standardised form of each word to the original word and POS tag in Bauer's tagged-gloss list.
    # Also remove any hyphens used by Bauer unless they are used as stand-alone zero tokens.
    # Remove any doubled parts-of-speech which can be easily identified.
    for i, tagged_word_data in enumerate(pos_list):
        tagged_word = tagged_word_data[0]
        if "-" in tagged_word and len(tagged_word) > 1:
            tagged_word_data[0] = "".join(tagged_word.split("-"))
        pos_list[i] = tagged_word_data + [standardise_wordchars(tagged_word_data[0])]

    #                                                PART 2.1:
    #
    # check standardised pos-tagged words against a list of known duplicates and problem words, remove as necessary
    combine_subtract = False

    #                                               PART 2.1.0:
    #
    #                                                 COPULA
    #
    # remove doubled dependent conjunctions/particles before the copula, or add to the copula if not doubled
    # cf. Thurn 503, 546-563 Stifter 247-249, 386
    # list all enclitic forms of the copula
    enclitic_cops = [['th', '<AUX Polarity=Pos | VerbType=Cop>', 'th'],  # Present (Indic.)
                     ['id', '<AUX Polarity=Pos | VerbType=Cop>', 'id'],
                     ['so', '<AUX Polarity=Pos | VerbType=Cop>', 'so'],
                     ['su', '<AUX Polarity=Pos | VerbType=Cop>', 'su'],
                     ['tu', '<AUX Polarity=Pos | VerbType=Cop>', 'tu'],
                     ['ndid', '<AUX Polarity=Pos | VerbType=Cop>', 'ndid'],
                     ['ndat', '<AUX Polarity=Pos | VerbType=Cop>', 'ndat'],
                     ['d', '<AUX Polarity=Pos | VerbType=Cop>', 'd'],  # (Subj.)
                     ['b', '<AUX Polarity=Pos | VerbType=Cop>', 'b'],
                     ['bo', '<AUX Polarity=Pos | VerbType=Cop>', 'bo'],
                     ['p', '<AUX Polarity=Pos | VerbType=Cop>', 'p'],
                     ['m', '<AUX Polarity=Pos | VerbType=Cop>', 'm'],
                     ['mbé', '<AUX Polarity=Pos | VerbType=Cop>', 'mbe'],
                     ['t', '<AUX Polarity=Pos | VerbType=Cop>', 't'],
                     ['bí', '<AUX Polarity=Pos | VerbType=Cop>', 'bi'],  # Consutudinal Present
                     ['mbí', '<AUX Polarity=Pos | VerbType=Cop>', 'mbi'],
                     ['mtar', '<AUX Polarity=Pos | VerbType=Cop>', 'mtar'],  # Pret.
                     ['bbad', '<AUX Polarity=Pos | VerbType=Cop>', 'bbad'],  # Past (Subj.)
                     ['mbad', '<AUX Polarity=Pos | VerbType=Cop>', 'mbad'],
                     ['bat', '<AUX Polarity=Pos | VerbType=Cop>', 'bat'],  # Future
                     ['-', '<AUX Polarity=Pos | VerbType=Cop>', '-']]
    # list all full forms of the copula (forms which cannot be combined with preceding conjunctions/particles)
    full_cops = [['am', '<AUX Polarity=Pos | VerbType=Cop>', 'am'],  # Present (Indic.)
                 ['is', '<AUX Polarity=Pos | VerbType=Cop>', 'is'],
                 ['iss', '<AUX Polarity=Pos | VerbType=Cop>', 'iss'],
                 ['it', '<AUX Polarity=Pos | VerbType=Cop>', 'it'],
                 ['hit', '<AUX Polarity=Pos | VerbType=Cop>', 'hit'],
                 ['Hít', '<AUX Polarity=Pos | VerbType=Cop>', 'hit'],
                 ['as', '<AUX Polarity=Pos | VerbType=Cop>', 'as'],  # (Rel.)
                 ['nas', '<AUX Polarity=Pos | VerbType=Cop>', 'nas'],
                 ['ata', '<AUX Polarity=Pos | VerbType=Cop>', 'ata'],
                 ['atá', '<AUX Polarity=Pos | VerbType=Cop>', 'ata'],
                 ['rop', '<AUX Polarity=Pos | VerbType=Cop>', 'rop'],  # (Subj.)
                 ['beit', '<AUX Polarity=Pos | VerbType=Cop>', 'beit'],
                 ['beith', '<AUX Polarity=Pos | VerbType=Cop>', 'beith'],
                 ['bes', '<AUX Polarity=Pos | VerbType=Cop>', 'bes'],  # (Subj. Rel.)
                 ['ṁbes', '<AUX Polarity=Pos | VerbType=Cop>', 'mbes'],
                 ['beta', '<AUX Polarity=Pos | VerbType=Cop>', 'beta'],
                 ['bete', '<AUX Polarity=Pos | VerbType=Cop>', 'bete'],
                 ['rubat', '<AUX Polarity=Pos | VerbType=Cop>', 'rubat'],  # (Cond.)
                 ['ropat', '<AUX Polarity=Pos | VerbType=Cop>', 'ropat'],
                 ['ropad', '<AUX Polarity=Pos | VerbType=Cop>', 'ropad'],
                 ['bad', '<AUX Polarity=Pos | VerbType=Cop>', 'bad'],  # (Impv.)
                 ['ba', '<AUX Polarity=Pos | VerbType=Cop>', 'ba'],  # Pret.
                 ['bá', '<AUX Polarity=Pos | VerbType=Cop>', 'ba'],  # Perf.
                 ['bid', '<AUX Polarity=Pos | VerbType=Cop>', 'bid'],  # Past (Subj.)
                 ['bed', '<AUX Polarity=Pos | VerbType=Cop>', 'bed'],
                 ['mbed', '<AUX Polarity=Pos | VerbType=Cop>', 'mbed'],
                 ['beth', '<AUX Polarity=Pos | VerbType=Cop>', 'beth'],
                 ['betis', '<AUX Polarity=Pos | VerbType=Cop>', 'betis'],
                 ['ṁbad', '<AUX Polarity=Pos | VerbType=Cop>', 'mbad'],  # (Subj. Rel.)
                 ['mbetis', '<AUX Polarity=Pos | VerbType=Cop>', 'mbetis'],
                 ['bith', '<AUX Polarity=Pos | VerbType=Cop>', 'bith'],  # Future
                 ['bit', '<AUX Polarity=Pos | VerbType=Cop>', 'bit'],
                 ['bas', '<AUX Polarity=Pos | VerbType=Cop>', 'bas']]  # (Rel.)
    # list all verbal particles which can be used in conjunction with a copula
    verbal_particles = [['no', '<PART PartType=Vb>', 'no'],
                        ['nu', '<PART PartType=Vb>', 'nu']]
    # list forms of the copula which have been combined with too many preceding parts of speech ((2<=) + copula)
    over_full_cops = [['cenid', '<AUX Polarity=Pos | VerbType=Cop>', 'cenid'],
                      ['cenobed', '<AUX Polarity=Pos | VerbType=Cop>', 'cenobed'],
                      ['corop', '<AUX Polarity=Pos | VerbType=Cop>', 'corop'],
                      ['corob', '<AUX Polarity=Pos | VerbType=Cop>', 'corob'],
                      ['manubed', '<AUX Polarity=Pos | VerbType=Cop>', 'manubed'],
                      ['nobed', '<AUX Polarity=Pos | VerbType=Cop>', 'nobed'],
                      ['nombed', '<AUX Polarity=Pos | VerbType=Cop>', 'nombed'],
                      ['nombetis', '<AUX Polarity=Pos | VerbType=Cop>', 'nombetis']]
    # list forms of the copula pre-combined with conjunctions/pronouns/particles by Bauer
    combined_cop_forms = [['arṅdid', '<AUX Polarity=Pos | VerbType=Cop>', 'arndid'],
                          ['ceto', '<AUX Polarity=Pos | VerbType=Cop>', 'ceto'],
                          ['cheso', '<AUX Polarity=Pos | VerbType=Cop>', 'cheso'],
                          ['ciaso', '<AUX Polarity=Pos | VerbType=Cop>', 'ciaso'],
                          ['cit', '<AUX Polarity=Pos | VerbType=Cop>', 'cit'],
                          ['cith', '<AUX Polarity=Pos | VerbType=Cop>', 'cith'],
                          ['combed', '<AUX Polarity=Pos | VerbType=Cop>', 'combed'],
                          ['conid', '<AUX Polarity=Pos | VerbType=Cop>', 'conid'],
                          ['comtis', '<AUX Polarity=Pos | VerbType=Cop>', 'comtis'],
                          ['condib', '<AUX Polarity=Pos | VerbType=Cop>', 'condib'],
                          ['combad', '<AUX Polarity=Pos | VerbType=Cop>', 'combad'],
                          ['mad', '<AUX Polarity=Pos | VerbType=Cop>', 'mad'],
                          ['robu', '<AUX Polarity=Pos | VerbType=Cop>', 'robu'],
                          ['robbu', '<AUX Polarity=Pos | VerbType=Cop>', 'robbu'],
                          ['rombu', '<AUX Polarity=Pos | VerbType=Cop>', 'rombu'],
                          ['rop', '<AUX Polarity=Pos | VerbType=Cop>', 'rop'],
                          ['roppad', '<AUX Polarity=Pos | VerbType=Cop>', 'roppad']]
    # list forms of the copula pre-combined with negative particles by Bauer but tagged as positive
    neg_cops = [['níbad', '<AUX Polarity=Pos | VerbType=Cop>', 'nibad'],
                ['nirubi', '<AUX Polarity=Pos | VerbType=Cop>', 'nirubi'],
                ['nad', '<AUX Polarity=Pos | VerbType=Cop>', 'nad'],
                ['nadṁbed', '<AUX Polarity=Pos | VerbType=Cop>', 'nadmbed'],
                ['nírbu', '<AUX Polarity=Pos | VerbType=Cop>', 'nirbu'],
                ['níbbad', '<AUX Polarity=Pos | VerbType=Cop>', 'nibbad'],
                ['nitat', '<AUX Polarity=Pos | VerbType=Cop>', 'nitat'],
                ['níbbu', '<AUX Polarity=Pos | VerbType=Cop>', 'nibbu'],
                ['nand', '<AUX Polarity=Pos | VerbType=Cop>', 'nand'],
                ['ní', '<AUX Polarity=Pos | VerbType=Cop>', 'ni'],
                ['nibad', '<AUX Polarity=Pos | VerbType=Cop>', 'nibad']]
    # list enclitic forms of the copula preceded by negative particles but tagged as positive
    neg_cop_enclitics = [['nd', '<AUX Polarity=Pos | VerbType=Cop>', 'nd']]
    # list forms of the copula combined as a result of the processes below (where they cause trouble)
    new_combined_cops = [['cid', '<AUX Polarity=Pos | VerbType=Cop>', 'cid'],
                         ['mad', '<AUX Polarity=Pos | VerbType=Cop>', 'mad'],
                         ['cesu', '<AUX Polarity=Pos | VerbType=Cop>', 'cesu']]
    # list independent conjunctions (p.247-249) which cannot be combined with enclitic forms of the copula
    indie_conj = [['amal', '<SCONJ>', 'amal'],
                  ['ar', '<SCONJ>', 'ar'],
                  ['arindí', '<SCONJ>', 'arindi'],
                  ['acht', '<SCONJ>', 'acht'],
                  ['dég', '<SCONJ>', 'deg'],
                  ['ore', '<SCONJ>', 'ore']]
    # list conjunctions which can combine with enclitic forms of the copula (not necessarily dependent conjunctions)
    conj_combo_forms = [['a', '<SCONJ>', 'a'],  # Temporal (independent)
                        ['ara', '<SCONJ>', 'ara'],  # Consecutive & Final
                        ['ce', '<SCONJ>', 'ce'],  # Adversative (independent)
                        ['che', '<SCONJ>', 'che'],
                        ['ci', '<SCONJ>', 'ci'],
                        ['cia', '<SCONJ>', 'cia'],
                        ['co', '<SCONJ>', 'co'],  # Consecutive & Final
                        ['con', '<SCONJ>', 'con'],
                        ['ma', '<SCONJ>', 'ma']]  # Conditional (independent)
    # list negative conjunctions which can combine with forms of the copula (enclitic or reduced to zero)
    neg_conj_combo_forms = [['na', '<SCONJ Polarity=Neg>', 'na'],
                            ['nach', '<SCONJ Polarity=Neg>', 'nach'],
                            ['nách', '<SCONJ Polarity=Neg>', 'nach'],
                            ['naich', '<SCONJ Polarity=Neg>', 'naich']]
    # list particles which can combine with enclitic forms of the copula
    particle_combo_forms = [['i', '<PART PronType=Int>', 'i'],
                            ['im', '<PART PronType=Int>', 'im'],
                            ['in', '<PART PronType=Int>', 'in'],
                            ['a', '<PART PartType=Vb | PronType=Rel>', 'a']]
    # list pronouns which can combine with enclitic forms of the copula
    combo_pron_forms = [['c', '<PRON PronType=Int>', 'c'],
                        ['ce', '<PRON PronType=Int>', 'ce'],
                        ['ced', '<PRON PronType=Int>', 'ced'],
                        ['ci', '<PRON PronType=Int>', 'ci'],
                        ['cia', '<PRON PronType=Int>', 'cia'],
                        ['Cia', '<PRON PronType=Int>', 'cia'],
                        ['cid', '<PRON PronType=Int>', 'cid'],
                        ['sechi', '<PRON PronType=Ind>', 'sechi']]
    # count the instances of the compounded copula form(s) in the gloss
    cop_count = 0
    for tagged_word_data in pos_list:
        split_tagged_pos = split_pos_feats(tagged_word_data[1])
        tagged_short_pos = split_tagged_pos[0]
        tagged_feats = split_tagged_pos[1]
        if tagged_short_pos == "AUX" and all(feat in tagged_feats for feat in ["Polarity=Pos", "VerbType=Cop"]):
            tagged_check_word = [tagged_word_data[0], '<AUX Polarity=Pos | VerbType=Cop>', tagged_word_data[2]]
            # identify forms of the copula which have not been accounted for yet
            if tagged_check_word not in full_cops and tagged_check_word not in enclitic_cops and \
                    tagged_check_word not in combined_cop_forms and tagged_check_word not in neg_cops and \
                    tagged_check_word not in neg_cop_enclitics and tagged_check_word not in over_full_cops:
                print(tagged_word_data)
                print([i[0] for i in standard_mapping])
                print([i for i in pos_list])
                raise RuntimeError("Unknown copula form")
            # identify forms of the copula which may require changing
            if tagged_check_word not in full_cops:
                if tagged_check_word in enclitic_cops or tagged_check_word in neg_cops or \
                        tagged_check_word in neg_cop_enclitics or tagged_check_word in combined_cop_forms or \
                        tagged_check_word in over_full_cops:
                    cop_count += 1
                else:
                    print(tagged_word_data)
                    print([i[0] for i in standard_mapping])
                    print([i[0] for i in pos_list])
                    raise RuntimeError("new form of copula found")
    for i in range(cop_count):
        # for each word in the POS list
        for j, tagged_word_data in enumerate(pos_list):
            tagged_original, tagged_pos, tagged_standard = tagged_word_data[0], tagged_word_data[1], tagged_word_data[2]
            split_tagged_pos = split_pos_feats(tagged_pos)
            tagged_short_pos = split_tagged_pos[0]
            tagged_feats = split_tagged_pos[1]
            # if the POS is a positive form of the copula
            if tagged_short_pos == "AUX" and all(feat in tagged_feats for feat in ["Polarity=Pos", "VerbType=Cop"]):
                tagged_check_word = [tagged_original, '<AUX Polarity=Pos | VerbType=Cop>', tagged_standard]
                # if the copula form has been reduced to zero in this position
                if tagged_original == "-":
                    last_pos_place = 1
                    try:
                        if j != 0:
                            last_pos_data = pos_list[j-last_pos_place]
                            # find any preverbal particles used within the copula form
                            split_last_pos = split_pos_feats(last_pos_data[1])
                            if split_last_pos[0] == "PVP":
                                print(tagged_word_data)
                                print([k[0] for k in standard_mapping])
                                print([k[0] for k in pos_list])
                                raise RuntimeError("PVP found before copula form reduced to zero")
                        else:
                            last_pos_data = False
                    except IndexError:
                        last_pos_data = False
                    # there needs to be a preceding POS to attach the zero copula form to
                    if last_pos_data:
                        last_original, last_pos, last_standard = last_pos_data[0], last_pos_data[1], last_pos_data[2]
                        split_last_pos = split_pos_feats(last_pos)
                        last_feats = split_last_pos[1]
                        # if the last POS is an interrogative particle
                        # delete the empty copula as it does not change the form of the preceding POS
                        if last_pos_data in particle_combo_forms:
                            del pos_list[j]
                            combine_subtract = True
                            break
                        # if the last POS is an interrogative pronoun
                        # delete the empty copula as it does not change the form of the preceding POS
                        elif last_pos_data in combo_pron_forms and 'PronType=Int' in last_feats:
                            del pos_list[j]
                            combine_subtract = True
                            break
                        # fix polarity of negative copula forms reduced to zero which are listed as positive by Bauer
                        elif last_pos_data in neg_conj_combo_forms:
                            neg_pos = update_feature(tagged_pos, "Polarity=Neg")
                            tagged_word_data = [tagged_original, neg_pos, tagged_standard]
                            pos_list[j] = tagged_word_data
                            combine_subtract = True
                            break
                        else:
                            print(tagged_word_data)
                            print(last_pos_data)
                            print([k[0] for k in standard_mapping])
                            print([k[0] for k in pos_list])
                            raise RuntimeError("Copula reduced to zero, last POS not a known POS")
                    else:
                        print(tagged_word_data)
                        print([k[0] for k in standard_mapping])
                        print([k[0] for k in pos_list])
                        raise RuntimeError("Copula reduced to zero, but no word precedes the copula form")
                # fix polarity of negative copula forms which are listed as positive by Bauer
                if tagged_check_word in neg_cops or tagged_check_word in neg_cop_enclitics:
                    neg_pos = update_feature(tagged_pos, "Polarity=Neg")
                    tagged_word_data = [tagged_original, neg_pos, tagged_standard]
                    pos_list[j] = tagged_word_data
                    combine_subtract = True
                    break
                # if an enclitic or precombined form of the copula is used
                if tagged_check_word not in full_cops:
                    if tagged_check_word in enclitic_cops or tagged_check_word in combined_cop_forms:
                        last_pos_place = 1
                        copula_preverbs = list()
                        try:
                            if j != 0:
                                last_pos_data = pos_list[j-last_pos_place]
                                # find any preverbal particles used within the copula form
                                split_last_pos = split_pos_feats(last_pos_data[1])
                                if split_last_pos[0] == "PVP":
                                    while split_last_pos[0] == "PVP":
                                        copula_preverbs.append(last_pos_data)
                                        last_pos_place += 1
                                        last_pos_data = pos_list[j-last_pos_place]
                                        split_last_pos = split_pos_feats(last_pos_data[1])
                                        if j-last_pos_place == 0 and split_last_pos[0] == "PVP":
                                            print(last_pos_data)
                                            print(tagged_word_data)
                                            print([k[0] for k in standard_mapping])
                                            print([k[0] for k in pos_list])
                                            raise RuntimeError("Copula preverb is the first POS in the gloss")
                            else:
                                last_pos_data = False
                        except IndexError:
                            last_pos_data = False
                        # there should be a POS preceding an enclitic form of the copula but perhaps not if precombined
                        if last_pos_data:
                            last_original, last_pos, last_standard = last_pos_data[0], last_pos_data[1], \
                                                                     last_pos_data[2]
                            split_last_pos = split_pos_feats(last_pos)
                            last_short_pos = split_last_pos[0]
                            last_feats = split_last_pos[1]
                            # if an enclitic or precombined copula form is preceded by a preverb
                            if copula_preverbs:
                                if len(copula_preverbs) > 1:
                                    print(last_pos_data)
                                    print(copula_preverbs)
                                    print(tagged_word_data)
                                    print([k[0] for k in standard_mapping])
                                    print([k[0] for k in pos_list])
                                    raise RuntimeError("More preverbs preceding copula than expected")
                                elif len(copula_preverbs) == 1:
                                    pvp_pos_data = copula_preverbs[0]
                                    pvp_original = pvp_pos_data[0]
                                    pvp_pos = pvp_pos_data[1]
                                    pvp_standard = pvp_pos_data[2]
                                    split_pvp_pos = split_pos_feats(pvp_pos)
                                    pvp_feats = split_pvp_pos[1]
                                    # if the preverb is not already at the beginning of the copula form
                                    # add the two together, and add the perverb's features to the copula's
                                    if pvp_original not in tagged_original and pvp_standard not in tagged_standard:
                                        cop_combo = [pvp_original + tagged_original,
                                                     add_features(tagged_pos, pvp_feats),
                                                     pvp_standard + tagged_standard]
                                        print(pos_list)
                                        pos_list = pos_list[:j-last_pos_place+1] + [cop_combo] + pos_list[j+1:]
                                        print(pos_list)
                                        combine_subtract = True
                                        # break
                                        raise RuntimeError("Preverb not present in copula form")
                                    # if the preverb is doubled at the begining of the copula form
                                    # add the preverb's features to the copula's and remove the doubled preverb
                                    elif pvp_original == tagged_original[:len(pvp_original)] \
                                            and pvp_standard == tagged_standard[:len(pvp_standard)]:
                                        cop_combo = [tagged_original,
                                                     add_features(tagged_pos, pvp_feats),
                                                     tagged_standard]
                                        pos_list = pos_list[:j-last_pos_place+1] + [cop_combo] + pos_list[j+1:]
                                        combine_subtract = True
                                        break
                                    else:
                                        print(last_pos_data)
                                        print(copula_preverbs)
                                        print(tagged_word_data)
                                        print([k[0] for k in standard_mapping])
                                        print([k[0] for k in pos_list])
                                        raise RuntimeError("Preverb present in copula form")
                            # if an enclitic or precombined copula form is preceded by verbal particles
                            elif last_pos_data in verbal_particles:
                                # if the verbal particle is not already at the beginning of the copula form
                                if last_original not in tagged_original and last_standard not in tagged_standard:
                                    cop_combo = [last_original + tagged_original,
                                                 tagged_pos,
                                                 last_standard + tagged_standard]
                                    pos_list = pos_list[:j-last_pos_place] + [cop_combo] + pos_list[j+1:]
                                    combine_subtract = True
                                    break
                                elif last_original == tagged_original[:len(last_original)] \
                                        and last_standard == tagged_standard[:len(last_standard)]:
                                    print(last_pos_data)
                                    print(tagged_word_data)
                                    print([k[0] for k in standard_mapping])
                                    print([k[0] for k in pos_list])
                                    raise RuntimeError("Preverb present at beginning of copula form")
                                else:
                                    print(last_pos_data)
                                    print(tagged_word_data)
                                    print([k[0] for k in standard_mapping])
                                    print([k[0] for k in pos_list])
                                    raise RuntimeError("Preverb present in copula form")
                            # if an enclitic or precombined copula form is preceded by something other than a preverb
                            # which is capable of combining with it, and not negative
                            elif last_pos_data not in indie_conj \
                                    and (last_pos_data in particle_combo_forms or last_pos_data in combo_pron_forms
                                         or (last_short_pos == 'SCONJ' and 'Polarity=Neg' not in last_feats)
                                         or last_short_pos == 'ADP'):
                                # if the preceding POS is a dependent conjunction or a particle
                                if last_pos_data in conj_combo_forms or last_pos_data in particle_combo_forms:
                                    # if the conjunction/particle is repeated in the copula form
                                    # combine the copula's features with those of the conjunction/particle
                                    # keep the full copula form, but use the preceding POS tag
                                    if last_original == tagged_original[:len(last_original)]:
                                        combined_pos = add_features(last_pos, tagged_feats)
                                        cop_combo = [tagged_original, combined_pos, tagged_standard]
                                        pos_list = pos_list[:j-last_pos_place] + [cop_combo] + pos_list[j+1:]
                                        combine_subtract = True
                                        break
                                    # if the conjunction/particle needs to be combined with an enclitic copula form
                                    # combine the copula's features with those of the conjunction
                                    # combine the conjunction with the copula form and use the conjunction's POS tag
                                    elif tagged_check_word in enclitic_cops:
                                        combined_pos = add_features(last_pos, tagged_feats)
                                        cop_combo = [last_original + tagged_original,
                                                     combined_pos,
                                                     last_standard + tagged_standard]
                                        pos_list = pos_list[:j-last_pos_place] + [cop_combo] + pos_list[j+1:]
                                        combine_subtract = True
                                        break
                                    # if the copula form is not enclitic, or otherwise cannot be combined
                                    else:
                                        print(last_pos_data)
                                        print(tagged_word_data)
                                        raise RuntimeError("Unknown form of copula, cannot combine if not enclitic")
                                # if the preceding POS is a pronoun
                                elif last_pos_data in combo_pron_forms:
                                    combined_pos = add_features(last_pos, tagged_feats)
                                    cop_combo = [last_original + tagged_original,
                                                 combined_pos,
                                                 last_standard + tagged_standard]
                                    pos_list = pos_list[:j-last_pos_place] + [cop_combo] + pos_list[j+1:]
                                    combine_subtract = True
                                    break
                                # if the preceding POS is a preposition
                                elif last_short_pos == "ADP" and tagged_check_word in combined_cop_forms:
                                    combined_pos = add_features(last_pos, tagged_feats)
                                    cop_combo = [tagged_original, combined_pos, tagged_standard]
                                    pos_list = pos_list[:j-last_pos_place] + [cop_combo] + pos_list[j+1:]
                                    combine_subtract = True
                                    break
                                # if there is an unexpected POS preceding the enclitic copula form
                                else:
                                    print(last_pos_data)
                                    print(tagged_word_data)
                                    print([k[0] for k in standard_mapping])
                                    print([k[0] for k in pos_list])
                                    raise RuntimeError("Unknown conjunction/particle preceding copula\n"
                                                       "              OR independent conjunction not in indie_conj "
                                                       "list")
                            # if an independent conjunction precedes a pre-combined copula form:
                            elif last_short_pos == "SCONJ" and last_pos_data in indie_conj:
                                if tagged_check_word in combined_cop_forms:
                                    continue
                            # if any other POS precedes a pre-combined copula form:
                            elif tagged_check_word in combined_cop_forms:
                                # if the preceding POS is not repeated in the copula form
                                # it is unrelated to the copula, which is already whole, and can be ignored
                                if last_original not in tagged_original and last_standard not in tagged_standard:
                                    continue
                                # if the preceding POS is repeated in the copula form
                                else:
                                    print(last_pos_data)
                                    print(tagged_word_data)
                                    print([k[0] for k in standard_mapping])
                                    print([k for k in pos_list])
                                    raise RuntimeError("Word preceding pre-combined copula contained in copula form")
                            # fix polarity of enclitic copula forms which follow negative particles or conjunctions
                            elif 'Polarity=Neg' in last_feats:
                                tagged_pos = update_feature(tagged_pos, "Polarity=Neg")
                                pos_list[j] = [tagged_original, tagged_pos, tagged_standard]
                                break
                            # if any other unaccounted-for POS precedes the enclitic copula form
                            else:
                                print(last_pos_data)
                                print(tagged_word_data)
                                print([k[0] for k in standard_mapping])
                                print([k for k in pos_list])
                                raise RuntimeError("New POS type preceding copula form")
                        # if preverbs precede an enclitic copula form but there is no preceding POS
                        elif copula_preverbs:
                            print(tagged_word_data)
                            print([k[0] for k in standard_mapping])
                            print([k[0] for k in pos_list])
                            raise RuntimeError("No data for last POS, but preverbs preceding copula form.")
                        # if there is no POS preceding the enclitic form of the copula
                        elif tagged_check_word not in new_combined_cops:
                            print(tagged_word_data)
                            print(pos_list)
                            raise RuntimeError("No POS preceding enclitic or precombined copula form")
                    # if Bauer combined too many conjunctions/preverbs etc. with a copula and some must be removed
                    # from the over-full copula form to meet the word-separation standard
                    elif tagged_check_word in over_full_cops:
                        last_pos_place = 1
                        copula_preverbs = list()
                        try:
                            if j != 0:
                                last_pos_data = pos_list[j-last_pos_place]
                                # find any preverbal particles used within the copula form
                                split_last_pos = split_pos_feats(last_pos_data[1])
                                if split_last_pos[0] == "PVP":
                                    while split_last_pos[0] == "PVP":
                                        copula_preverbs.append(last_pos_data)
                                        last_pos_place += 1
                                        last_pos_data = pos_list[j-last_pos_place]
                                        split_last_pos = split_pos_feats(last_pos_data[1])
                                        if j - last_pos_place == 0 and split_last_pos[0] == "PVP":
                                            print(last_pos_data)
                                            print(tagged_word_data)
                                            print([k[0] for k in standard_mapping])
                                            print([k[0] for k in pos_list])
                                            raise RuntimeError("Copula preverb is the first POS in the gloss")
                            else:
                                last_pos_data = False
                        except IndexError:
                            last_pos_data = False
                        if last_pos_data:
                            last_original, last_pos, last_standard = last_pos_data[0], last_pos_data[1], \
                                                                     last_pos_data[2]
                            split_last_pos = split_pos_feats(last_pos)
                            last_short_pos = split_last_pos[0]
                            last_feats = split_last_pos[1]
                            # if there are preverb(s) preceding an overfull copula form
                            # they should remain part of the copula, but any preceding POS should be removed
                            if copula_preverbs:
                                print(last_pos_data)
                                print(copula_preverbs)
                                print(tagged_word_data)
                                raise RuntimeError()
                                # # if the last POS is a combinable conjunction and it is repeated in the copula form
                                # # it should be separated from the copula form leaving only the preverb(s) attached
                                # if last_pos_data in conj_combo_forms and \
                                #         last_original == tagged_original[:len(last_original)]:
                                #     reduced_copform = [tagged_original[len(last_original):],
                                #                        tagged_pos,
                                #                        tagged_standard[len(last_standard):]]
                                #     reduced_original = reduced_copform[0]
                                #     reduced_standard = reduced_copform[2]
                                #     # as the preverb now potentially makes up part of the copula form, treat it as the
                                #     # last POS, change the POS tag from PVP to PART, and add the PartType=Vb feature
                                #     # there should be only one preverb attached to any copula in the St. Gall corpus
                                #     if len(copula_preverbs) == 1:
                                #         last_preverb_data = copula_preverbs[0]
                                #         last_original, last_pos, last_standard = last_preverb_data[0], \
                                #                                                  last_preverb_data[1], \
                                #                                                  last_preverb_data[2]
                                #         last_feats = split_pos_feats(last_pos)[1]
                                #         last_pos = update_tag(last_pos, 'PART')
                                #         last_pos = add_features(last_pos, ['PartType=Vb'])
                                #         copula_preverb = [last_original, last_pos, last_standard]
                                #         # if the preverb is a full (not reduced) variant spelling of 'ro' or 'no'
                                #         if copula_preverb in verbal_particles:
                                #             # if the preverb is already at the beginning of the reduced copula form
                                #             # remove it to isolate the remaining, pure copula form
                                #             if last_original == reduced_original[:len(last_original)]:
                                #                 reduced_copform = [reduced_original[len(last_original):],
                                #                                    tagged_pos,
                                #                                    reduced_standard[len(last_standard):]]
                                #                 reduced_check_cop = [reduced_copform[0],
                                #                                      '<AUX Polarity=Pos | VerbType=Cop>',
                                #                                      reduced_copform[2]]
                                #                 # if the copula form remaining after removing the preverb is an enclitic
                                #                 # recombine it with the preverb and keep the copula's POS information
                                #                 if reduced_check_cop in enclitic_cops:
                                #                     tagged_pos = add_features(tagged_pos, last_feats)
                                #                     final_cop = [[last_original + reduced_copform[0],
                                #                                  tagged_pos,
                                #                                  last_standard + reduced_copform[2]]]
                                #                 # if the copula form remaining after removing the preverb is a full form
                                #                 # separate the preverb from the copula
                                #                 elif reduced_check_cop in full_cops:
                                #                     final_cop = [copula_preverb] + [reduced_copform]
                                #                 # if the copula form is neither a known enclitic nor full form
                                #                 else:
                                #                     print(tagged_word_data)
                                #                     print(copula_preverbs)
                                #                     print(last_pos_data)
                                #                     print(reduced_copform)
                                #                     raise RuntimeError("Undetermined copula form, cannot combine")
                                #                 pos_list = pos_list[:j-last_pos_place+1] + final_cop + pos_list[j+1:]
                                #                 combine_subtract = True
                                #                 break
                                #             else:
                                #                 print(tagged_word_data)
                                #                 print(copula_preverbs)
                                #                 print(last_pos_data)
                                #                 raise RuntimeError("Could not separate over-full copula form")
                                #         else:
                                #             print(tagged_word_data)
                                #             print(copula_preverb)
                                #             print(last_pos_data)
                                #             raise RuntimeError("Copula preceded unexpected preverb")
                                #     else:
                                #         print(tagged_word_data)
                                #         print(copula_preverbs)
                                #         print(last_pos_data)
                                #         raise RuntimeError("Multiple preverbs between copula form and last POS")
                                # # if the last POS is not a combining conjunction, or the last POS is a combinable
                                # # conjunction but is not repeated in the copula form along with preverb(s)
                                # # as the preverb now potentially makes up part of the copula form, treat it as the
                                # # last POS, change the POS tag from PVP to PART, and add the PartType=Vb feature
                                # # there should be only one preverb attached to any copula in the St. Gall corpus
                                # elif len(copula_preverbs) == 1:
                                #     last_preverb_data = copula_preverbs[0]
                                #     last_original, last_pos, last_standard = last_preverb_data[0], \
                                #                                              last_preverb_data[1], last_preverb_data[2]
                                #     last_pos = update_tag(last_pos, 'PART')
                                #     last_pos = add_features(last_pos, ['PartType=Vb'])
                                #     copula_preverb = [last_original, last_pos, last_standard]
                                #     # if the preverb is a full (not reduced) variant spelling of 'ro' or 'no'
                                #     if copula_preverb in verbal_particles:
                                #         # if the preverb is already at the beginning of the reduced copula form
                                #         # remove it to isolate the remaining, pure copula form
                                #         if last_original == tagged_original[:len(last_original)]:
                                #             reduced_copform = [tagged_original[len(last_original):],
                                #                                tagged_pos,
                                #                                tagged_standard[len(last_standard):]]
                                #             reduced_check_cop = [reduced_copform[0],
                                #                                  '<AUX Polarity=Pos | VerbType=Cop>',
                                #                                  reduced_copform[2]]
                                #             # if the copula form remaining after removing the preverb is a full form
                                #             # separate the preverb from the copula form from the preverb
                                #             if reduced_check_cop in full_cops:
                                #                 final_cop = [copula_preverb] + [reduced_copform]
                                #             # if the copula form remaining after removing the preverb is an enclitic
                                #             # recombine it with the preverb and keep the copula's POS information
                                #             elif reduced_check_cop in enclitic_cops:
                                #                 print(tagged_word_data)
                                #                 print(reduced_copform)
                                #                 print(copula_preverb)
                                #                 print(last_pos_data)
                                #                 raise RuntimeError("Enclitic copula form following verbal particle")
                                #             # if the copula form is neither a known enclitic nor full form
                                #             else:
                                #                 print(tagged_word_data)
                                #                 print(reduced_copform)
                                #                 print(copula_preverb)
                                #                 print(last_pos_data)
                                #                 raise RuntimeError("Undknown copula form, cannot split/combine")
                                #             pos_list = pos_list[:j-last_pos_place+1] + final_cop + pos_list[j+1:]
                                #             combine_subtract = True
                                #             break
                                #         # if the preverb is not present in the copula form
                                #         else:
                                #             print(tagged_word_data)
                                #             print(copula_preverbs)
                                #             print(last_pos_data)
                                #             raise RuntimeError("Could not separate over-full copula form")
                                #     # if the preverb is not one of the expected verbal particles ('ro' or 'no')
                                #     else:
                                #         print(tagged_word_data)
                                #         print(copula_preverb)
                                #         print(last_pos_data)
                                #         raise RuntimeError("Copula preceded by unexpected preverb")
                                # # if there were more than one preverb (not expected preceding a copula in St. Gall)
                                # else:
                                #     print(tagged_word_data)
                                #     print(copula_preverbs)
                                #     print(last_pos_data)
                                #     raise RuntimeError("More preverbs found preceding copula form than expected")
                            # if there are no preverbs preceding an overfull copula form but the last POS is a preverbal
                            # particle which has been attached to the beginning of the over-full copula
                            # remove everything from th copula from, leaving only the base form itself
                            elif last_pos_data in verbal_particles \
                                    and last_original == tagged_original[:len(last_original)]:
                                tagged_original = tagged_original[len(last_original):]
                                tagged_standard = tagged_standard[len(last_standard):]
                                tagged_word_data = [tagged_original, tagged_pos, tagged_standard]
                                pos_list[j] = tagged_word_data
                                combine_subtract = True
                                break
                            # if there are no preverbs preceding an overfull copula form but the last POS is a negative
                            # particle which has been attached to the beginning of the over-full copula
                            # remove everything from th copula from, leaving only the base form itself
                            # change the polarity of the copula to negative
                            elif last_short_pos == "PART" and "Polarity=Neg" in last_feats and \
                                    last_original in tagged_original:
                                tagged_pos = update_feature(tagged_pos, "Polarity=Neg")
                                tagged_original = tagged_original[tagged_original.find(last_original) +
                                                                  len(last_original):]
                                tagged_standard = tagged_standard[tagged_standard.find(last_standard) +
                                                                  len(last_standard):]
                                reduced_copform = [tagged_original, tagged_pos, tagged_standard]
                                pos_list[j] = reduced_copform
                                combine_subtract = True
                                break
                            # if there are any unaccounted for over-full copula forms remaining
                            else:
                                print(tagged_word_data)
                                print(last_pos_data)
                                print(pos_list)
                                raise RuntimeError("Could not separate over-full copula form")
                        # if there are preverbs but no preceding POS
                        elif copula_preverbs:
                            raise RuntimeError("Preverb(s) preceding over-full copula are first POS in gloss")
                        # if nothing precedes the over-full copula form
                        else:
                            raise RuntimeError("No POS preceding over-full copula form")
                    # if the copula form is not a known enclitic, combined, full, over-full or negative form
                    elif tagged_check_word not in new_combined_cops:
                        print(tagged_word_data)
                        print([k[0] for k in standard_mapping])
                        print([k for k in pos_list])
                        raise RuntimeError("Copula form not could not be found")
                # ensure absolute forms of the copula are not compounded with preceding conjunctions, etc.
                elif tagged_check_word in full_cops:
                    last_pos_place = 1
                    copula_preverbs = list()
                    try:
                        if j != 0:
                            last_pos_data = pos_list[j - last_pos_place]
                            # find any preverbal particles used within the copula form
                            split_last_pos = split_pos_feats(last_pos_data[1])
                            if split_last_pos[0] == "PVP":
                                while split_last_pos[0] == "PVP":
                                    copula_preverbs.append(last_pos_data)
                                    last_pos_place += 1
                                    last_pos_data = pos_list[j - last_pos_place]
                                    split_last_pos = split_pos_feats(last_pos_data[1])
                                    if j - last_pos_place == 0 and split_last_pos[0] == "PVP":
                                        print(last_pos_data)
                                        print(tagged_word_data)
                                        print([k[0] for k in standard_mapping])
                                        print([k[0] for k in pos_list])
                                        raise RuntimeError("Copula preverb is the first POS in the gloss")
                        else:
                            last_pos_data = False
                    except IndexError:
                        last_pos_data = False
                    # there should be no preverbs before an absolute or otherwise full form of the copula
                    if copula_preverbs:
                        print(tagged_word_data)
                        print(copula_preverbs)
                        print(last_pos_data)
                        raise RuntimeError("Preverbs found before absolute copula form")
                    # if there is a POS before the full copula form
                    elif last_pos_data:
                        last_original, last_pos, last_standard = last_pos_data[0], last_pos_data[1], last_pos_data[2]
                        split_last_pos = split_pos_feats(last_pos)
                        last_short_pos = split_last_pos[0]
                        # if the last POS before the full copula form is a conjunction
                        if last_short_pos == "SCONJ":
                            # if the last POS is not an independent conjunction (as would be expected)
                            if last_pos_data in conj_combo_forms or last_pos_data not in indie_conj:
                                print(tagged_word_data)
                                print(last_pos_data)
                                raise RuntimeError("Unexpected conjunction found before absolute copula form")
                        # if the last POS before the full copula form is any other combinable type
                        elif last_pos_data in particle_combo_forms or last_pos_data in combo_pron_forms:
                            print(tagged_word_data)
                            print(last_pos_data)
                            raise RuntimeError("Unexpected POS found before absolute copula form")
    # remove doubled 'ní' particle before negative form of the copula, also 'ní'
    # list all copula forms which are negative, or can be combined with negative particles
    full_neg_list = [['in', '<AUX Polarity=Neg | VerbType=Cop>', 'in'],  # Typo
                     ['nad', '<AUX Polarity=Neg | VerbType=Cop>', 'nad'],
                     ['nadṁbed', '<AUX Polarity=Neg | VerbType=Cop>', 'nadmbed'],
                     ['nand', '<AUX Polarity=Neg | VerbType=Cop>', 'nand'],
                     ['ni', '<AUX Polarity=Neg | VerbType=Cop>', 'ni'],
                     ['ní', '<AUX Polarity=Neg | VerbType=Cop>', 'ni'],
                     ['Ni', '<AUX Polarity=Neg | VerbType=Cop>', 'ni'],
                     ['Ní', '<AUX Polarity=Neg | VerbType=Cop>', 'ni'],
                     ['nibad', '<AUX Polarity=Neg | VerbType=Cop>', 'nibad'],
                     ['níbad', '<AUX Polarity=Neg | VerbType=Cop>', 'nibad'],
                     ['nibat', '<AUX Polarity=Neg | VerbType=Cop>', 'nibat'],
                     ['nibba', '<AUX Polarity=Neg | VerbType=Cop>', 'nibba'],
                     ['níbbad', '<AUX Polarity=Neg | VerbType=Cop>', 'nibbad'],
                     ['níbbu', '<AUX Polarity=Neg | VerbType=Cop>', 'nibbu'],
                     ['nibu', '<AUX Polarity=Neg | VerbType=Cop>', 'nibu'],
                     ['níbu', '<AUX Polarity=Neg | VerbType=Cop>', 'nibu'],
                     ['niptis', '<AUX Polarity=Neg | VerbType=Cop>', 'niptis'],
                     ['nírbu', '<AUX Polarity=Neg | VerbType=Cop>', 'nirbu'],
                     ['nirubi', '<AUX Polarity=Neg | VerbType=Cop>', 'nirubi'],
                     ['nitat', '<AUX Polarity=Neg | VerbType=Cop>', 'nitat'],
                     ['nítat', '<AUX Polarity=Neg | VerbType=Cop>', 'nitat']]
    enclitic_neg_list = [['-', '<AUX Polarity=Neg | VerbType=Cop>', '-'],
                         ['b', '<AUX Polarity=Neg | VerbType=Cop>', 'b'],
                         ['bba', '<AUX Polarity=Neg | VerbType=Cop>', 'bba'],
                         ['bbad', '<AUX Polarity=Neg | VerbType=Cop>', 'bbad'],
                         ['bed', '<AUX Polarity=Neg | VerbType=Cop>', 'bed'],
                         ['bi', '<AUX Polarity=Neg | VerbType=Cop>', 'bi'],
                         ['bí', '<AUX Polarity=Neg | VerbType=Cop>', 'bi'],
                         ['d', '<AUX Polarity=Neg | VerbType=Cop>', 'd'],
                         ['mba', '<AUX Polarity=Neg | VerbType=Cop>', 'mba'],
                         ['mtar', '<AUX Polarity=Neg | VerbType=Cop>', 'mtar'],
                         ['nd', '<AUX Polarity=Neg | VerbType=Cop>', 'nd'],
                         ['ndat', '<AUX Polarity=Neg | VerbType=Cop>', 'ndat'],
                         ['nip', '<AUX Polarity=Neg | VerbType=Cop>', 'nip'],
                         ['p', '<AUX Polarity=Neg | VerbType=Cop>', 'p'],
                         ['th', '<AUX Polarity=Neg | VerbType=Cop>', 'th']]
    # list all negative particles which can take enclitic copula forms
    neg_parts = [['na', '<PART Polarity=Neg | PronType=Rel>', 'na'],
                 ['ni', '<PART Polarity=Neg>', 'ni'],
                 ['ṅi', '<PART Polarity=Neg>', 'ni'],
                 ['ní', '<PART Polarity=Neg>', 'ni']]
    # list all preverbs which can come between a negative particle and a copula form
    neg_preverbs = [['r', '<PVP>', 'r'],
                    ['ru', '<PVP>', 'ru']]
    # list all parts of speech which are not negative particles and which combine with a following negative copula form
    # (generally a form reduced to zero)
    neg_conjunctions = [['nach', '<SCONJ Polarity=Neg>', 'nach'],
                        ['nách', '<SCONJ Polarity=Neg>', 'nach'],
                        ['naich', '<SCONJ Polarity=Neg>', 'naich']]
    neg_int_pronouns = [['Caní', '<PRON Polarity=Neg | PronType=Int>', 'cani']]
    # count the instances of the negative copula form(s) in the gloss
    neg_count = 0
    for tagged_word_data in pos_list:
        split_tagged_pos = split_pos_feats(tagged_word_data[1])
        tagged_short_pos = split_tagged_pos[0]
        tagged_feats = split_tagged_pos[1]
        if tagged_short_pos == "AUX" and all(feat in tagged_feats for feat in ["Polarity=Neg", "VerbType=Cop"]):
            tagged_check_word = [tagged_word_data[0], '<AUX Polarity=Neg | VerbType=Cop>', tagged_word_data[2]]
            if tagged_check_word not in full_neg_list and tagged_check_word not in enclitic_neg_list:
                print(tagged_word_data)
                print([i[0] for i in standard_mapping])
                print([i[0] for i in pos_list])
                print(pos_list)
                raise RuntimeError("New negative copula form")
            # identify forms of the copula which may require changing
            if tagged_check_word in full_neg_list or tagged_check_word in enclitic_neg_list:
                neg_count += 1
    for i in range(neg_count):
        for j, tagged_word_data in enumerate(pos_list):
            tagged_original, tagged_pos, tagged_standard = tagged_word_data[0], tagged_word_data[1], tagged_word_data[2]
            split_tagged_pos = split_pos_feats(tagged_pos)
            tagged_short_pos = split_tagged_pos[0]
            tagged_feats = split_tagged_pos[1]
            if tagged_short_pos == "AUX" and all(feat in tagged_feats for feat in ["Polarity=Neg", "VerbType=Cop"]):
                tagged_check_word = [tagged_original, '<AUX Polarity=Neg | VerbType=Cop>', tagged_standard]
                if tagged_check_word in full_neg_list or tagged_check_word in enclitic_neg_list:
                    last_pos_place = 1
                    copula_preverbs = list()
                    try:
                        if j != 0:
                            last_pos_data = pos_list[j-last_pos_place]
                            # find any preverbal particles used within the copula form
                            split_last_pos = split_pos_feats(last_pos_data[1])
                            if split_last_pos[0] == "PVP":
                                while split_last_pos[0] == "PVP":
                                    copula_preverbs.append(last_pos_data)
                                    last_pos_place += 1
                                    last_pos_data = pos_list[j-last_pos_place]
                                    split_last_pos = split_pos_feats(last_pos_data[1])
                                    if j-last_pos_place == 0 and split_last_pos[0] == "PVP":
                                        print(last_pos_data)
                                        print(tagged_word_data)
                                        print([k[0] for k in standard_mapping])
                                        print([k[0] for k in pos_list])
                                        raise RuntimeError("Copula preverb is the first POS in the gloss")
                        else:
                            last_pos_data = False
                    except IndexError:
                        last_pos_data = False
                    # if there are preverbs between the negative particle and the copula form
                    if copula_preverbs:
                        # if all preverbs found are in the list of preverbs which can occur within a copula form
                        # join them together into one conjoined preverb
                        check_preverbs = list()
                        for verbal_prefix_data in copula_preverbs:
                            check_preverb = [verbal_prefix_data[0], "<PVP>", verbal_prefix_data[2]]
                            check_preverbs.append(check_preverb)
                        if all(check_preverb in neg_preverbs for check_preverb in check_preverbs):
                            combined_preverbs = [''.join(pvp[0] for pvp in copula_preverbs),
                                                 ''.join(pvp[2] for pvp in copula_preverbs)]
                            combined_preverb_feats = list()
                            for verbal_prefix_data in copula_preverbs:
                                verbal_prefix_pos = verbal_prefix_data[1]
                                verbal_prefix_feats = split_pos_feats(verbal_prefix_pos)[1]
                                for verbal_prefix_feat in verbal_prefix_feats:
                                    if verbal_prefix_feat not in combined_preverb_feats:
                                        combined_preverb_feats.append(verbal_prefix_feat)
                            # if the combined preverbs occur within the copula form
                            # remove the preverbs from the POS list and leave only the copula form and negative particle
                            # add the features of the combined preverbs to the copula features
                            # do not break out of the loop, the negative particle still needs to be checked
                            if combined_preverbs[0] in tagged_original and combined_preverbs[1] in tagged_standard:
                                tagged_pos = add_features(tagged_pos, combined_preverb_feats)
                                tagged_word_data = [tagged_original, tagged_pos, tagged_standard]
                                pos_list = pos_list[:j-last_pos_place+1] + [tagged_word_data] + pos_list[j+1:]
                                pass
                            # if the combined preverbs cannot be found within the copula form
                            else:
                                raise RuntimeError("Known preverb(s) not contained in copula form")
                        # if a preverb is found which cannot occur within a copula form
                        else:
                            print(tagged_word_data)
                            print(copula_preverbs)
                            print(last_pos_data)
                            raise RuntimeError("Unknown preverb(s) between negative particle and copula form")
                    if last_pos_data:
                        last_original, last_pos, last_standard = last_pos_data[0], last_pos_data[1], last_pos_data[2]
                        split_last_pos = split_pos_feats(last_pos)
                        last_short_pos = split_last_pos[0]
                        last_feats = split_last_pos[1]
                        # if the last POS is a negative particle
                        if last_short_pos == "PART" and "Polarity=Neg" in last_feats:
                            # if the last POS (neg. part.) is the exact same as the following negative copula form
                            # delete the negative particle from the POS list
                            if tagged_original == last_original and tagged_standard == last_standard:
                                del pos_list[j-last_pos_place]
                                combine_subtract = True
                                break
                            # if the last POS is repeated at the beginning of the copula form
                            # delete the negative particle from the POS list
                            elif last_original == tagged_original[:len(last_original)]:
                                del pos_list[j-last_pos_place]
                                combine_subtract = True
                                break
                            # if the last POS (neg. part.) is not a t the beginning of the copula form as expected
                            elif last_original in tagged_original and last_standard in tagged_standard:
                                raise RuntimeError("Negative particle not at beginning of copula form")
                            # if the last POS (neg. part.) is not repeated in the following negative form of the copula
                            # join the two forms and update the features of the copula POS tag
                            elif last_pos_data in neg_parts:
                                tagged_pos = add_features(tagged_pos, last_feats)
                                new_neg_cop = [last_original + tagged_original,
                                               tagged_pos,
                                               last_standard + tagged_standard]
                                pos_list = pos_list[:j-last_pos_place] + [new_neg_cop] + pos_list[j+1:]
                                combine_subtract = True
                                break
                            # if the last POS is not a known negative particle
                            else:
                                print(last_pos_data)
                                print(tagged_word_data)
                                print([k[0] for k in standard_mapping])
                                print([k[0] for k in pos_list])
                                raise RuntimeError("New neg. particle or poss. doubling of particle preceeding copula")
                        # if the last POS is not a negative particle but the copula form is reduced to zero and negative
                        elif tagged_original == '-' and tagged_standard == '-' and tagged_short_pos == 'AUX' \
                                and all(feat in tagged_feats for feat in ["Polarity=Neg", "VerbType=Cop"]):
                            # if the last POS is a known negative conjunction delete the copula form
                            if last_pos_data in neg_conjunctions:
                                del pos_list[j]
                                combine_subtract = True
                                break
                            # if the last POS is a known negative interrogative pronoun delete the copula form
                            elif last_pos_data in neg_int_pronouns:
                                del pos_list[j]
                                combine_subtract = True
                                break
                            # if something other than the expected negative parts of speech precede the copula form
                            else:
                                print(last_pos_data)
                                print(tagged_word_data)
                                print([i[0] for i in standard_mapping])
                                raise RuntimeError("Negative form of copula reduced to zero preceded by unknown POS")
                        # if the last POS is not a negative particle but the copula form enclitic and negative
                        elif tagged_check_word in enclitic_neg_list:
                            # if the last POS is a known combining conjunction, other than the negative forms
                            if last_pos_data in conj_combo_forms:
                                print(last_pos_data)
                                print(tagged_word_data)
                                print([k[0] for k in standard_mapping])
                                print([k[0] for k in pos_list])
                                raise RuntimeError("Enclitic negative copula not preceded by negative POS")
                            # if the last POS is a known negative combining conjunction and the copula form is enclitic
                            # combine the copula's features with conjunction's, keeping the conjunction's POS tag
                            # combine the conjunction form with the copula form
                            elif last_pos_data in neg_conj_combo_forms:
                                combined_pos = add_features(last_pos, tagged_feats)
                                new_neg_cop = [last_original + tagged_original,
                                               combined_pos,
                                               last_standard + tagged_standard]
                                pos_list = pos_list[:j-last_pos_place] + [new_neg_cop] + pos_list[j+1:]
                                combine_subtract = True
                                break
                            # if any other type of POS precedes the enclitic negative copula form
                            else:
                                print(last_pos_data)
                                print(tagged_word_data)
                                print([k[0] for k in standard_mapping])
                                print([k[0] for k in pos_list])
                                raise RuntimeError("Enclitic negative copula not combined with previous POS")
                        # if the form of the copula is neither in the full nor enclitic negative copula lists
                        elif tagged_check_word not in full_neg_list:
                            print(last_pos_data)
                            print(tagged_word_data)
                            print([k[0] for k in standard_mapping])
                            print([k[0] for k in pos_list])
                            raise RuntimeError("Last POS not negative particle")

    #                                               PART 2.1.1:
    #
    #                                                 VERBS
    #
    # remove doubled particles, etc. before verbs, or add to the verb if not doubled
    # count instances of verbs in the gloss
    verb_independent_POS = ["ADJ", "ADV", "AUX", "NOUN", "NUM", "PRON", "VERB"]
    verb_dependent_POS = ["CCONJ", "PART", "SCONJ"]
    # list conjunct and verbal particles which take conjunct forms of the verb (cf. Stifter p.135, 27.7)
    conjunct_particles = [['a', '<PART PartType=Vb | PronType=Rel>', 'a'],
                          ['in', '<PART PronType=Int>', 'in'],
                          ['nád', '<PART Polarity=Neg | PronType=Rel>', 'nad'],
                          ['ni', '<PART Polarity=Neg>', 'ni'],
                          ['ní', '<PART Polarity=Neg>', 'ni'],
                          ['Ní', '<PART Polarity=Neg>', 'ni'],
                          ['no', '<PART PartType=Vb>', 'no']]
    # list preverbs which are sometimes described as verbal particles, but can be compounded within the verbal complex
    verbal_particles = [['ro', '<PVP Aspect=Perf>', 'ro']]
    # list conjunctions which take conjunct forms of the verb (cf. Stifter p.248-249, 49.6)
    dependent_conjunctions = [['co', '<SCONJ>', 'co'],
                              ['con', '<SCONJ>', 'con'],
                              ['na', '<SCONJ Polarity=Neg>', 'na']]
    # list conjunctions which do not take conjunct forms of the verb (cf. Stifter p.248-249, 49.6)
    independent_conjunctions = [['a', '<SCONJ>', 'a'],
                                ['air', '<SCONJ>', 'air'],
                                ['ar', '<SCONJ>', 'ar'],
                                ['amal', '<SCONJ>', 'amal'],
                                ['cenmitha', '<SCONJ>', 'cenmitha'],
                                ['ce', '<SCONJ>', 'ce'],
                                ['ci', '<SCONJ>', 'ci'],
                                ['cia', '<SCONJ>', 'cia'],
                                ['ma', '<SCONJ>', 'ma'],
                                ['ɫ', '<CCONJ>', 'no'],
                                ['⁊', '<CCONJ>', 'ocus'],
                                ['ol', '<SCONJ>', 'ol']]
    independent_particles = [['hí', '<PART>', 'hi'],
                             ['neph', '<PART Polarity=Neg | Prefix=Yes>', 'neph']]
    verbcount = 0
    for tagged_word_data in pos_list:
        split_tagged_pos = split_pos_feats(tagged_word_data[1])
        tagged_short_pos = split_tagged_pos[0]
        if tagged_short_pos == "VERB":
            verbcount += 1
    for i in range(verbcount):
        for j, tagged_word_data in enumerate(pos_list):
            tagged_original, tagged_pos, tagged_standard = tagged_word_data[0], tagged_word_data[1], tagged_word_data[2]
            split_tagged_pos = split_pos_feats(tagged_pos)
            tagged_short_pos = split_tagged_pos[0]
            tagged_feats = split_tagged_pos[1]
            # if the POS is a verb
            if tagged_short_pos == "VERB":
                # find the preceding POS or parts-of-speech
                last_pos_place = 1
                verbal_affixes = list()
                try:
                    if j != 0:
                        last_pos_data = pos_list[j-last_pos_place]
                        # find any preverbal particles used within the copula form
                        split_last_pos = split_pos_feats(last_pos_data[1])
                        if split_last_pos[0] in ["PVP", "IFP"] and j-last_pos_place > 0:
                            while split_last_pos[0] in ["PVP", "IFP"]:
                                verbal_affixes.append(last_pos_data)
                                last_pos_place += 1
                                last_pos_data = pos_list[j-last_pos_place]
                                split_last_pos = split_pos_feats(last_pos_data[1])
                                if j-last_pos_place == 0 and split_last_pos[0] == "PVP":
                                    verbal_affixes.append(last_pos_data)
                                    break
                        elif split_last_pos[0] in ["PVP", "IFP"] and j-last_pos_place == 0:
                            verbal_affixes.append(last_pos_data)
                    else:
                        last_pos_data = False
                except IndexError:
                    last_pos_data = False
                # put the list of POS which can be prefixed to a verb in order
                if verbal_affixes:
                    verbal_affixes.reverse()
                # if there is no POS preceding a verb, assume the verb is complete already and move on
                if not last_pos_data:
                    continue
                # if there is a POS preceding a verb form
                elif last_pos_data:
                    last_original, last_pos, last_standard = last_pos_data[0], last_pos_data[1], last_pos_data[2]
                    split_last_pos = split_pos_feats(last_pos)
                    last_short_pos = split_last_pos[0]
                    last_feats = split_last_pos[1]
                    # if there are only preverbal particles and infixed pronouns preceding a verb form
                    if last_short_pos == "PVP":
                        if not verbal_affixes:
                            raise RuntimeError("Expected verbal affixes preceding verb form, none found")
                        else:
                            # check if every preverbal particle and infixed pronoun is already in the full verb form
                            # collect any features and add them to the following verb
                            reduced_verbform = tagged_original
                            collected_preverb_feats = list()
                            for verb_prefix_data in verbal_affixes:
                                verb_prefix_original = verb_prefix_data[0]
                                verb_prefix_pos = verb_prefix_data[1]
                                verb_prefix_standard = verb_prefix_data[2]
                                split_verb_prefix = split_pos_feats(verb_prefix_pos)
                                verb_prefix_feats = split_verb_prefix[1]
                                # because the first POS is a PVP itself, if any infixed pronouns precede the verb form
                                # they can simply be treated as any other preverb here
                                # make sure any preverbal affix is in the verb form
                                if verb_prefix_original == reduced_verbform[:len(verb_prefix_original)]:
                                    reduced_verbform = reduced_verbform[len(verb_prefix_original):]
                                # if the last POS is a verbal particle like 'ro', and no other POS precedes it,
                                # and the verbal particle is not at the beginning of the following verb
                                # everything that follows has to be part of the verb form (break out of the loop)
                                # add the verbal particle to the following verb form
                                # combine its features, and features of all other preverbs, with the verb's features
                                elif verb_prefix_data in verbal_particles and last_pos_data == verb_prefix_data:
                                    tagged_original = verb_prefix_original + tagged_original
                                    tagged_standard = verb_prefix_standard + tagged_standard
                                    for sub_verb_prefix_data in verbal_affixes:
                                        sub_verb_prefix_feats = split_pos_feats(sub_verb_prefix_data[1])[1]
                                        tagged_pos = add_features(tagged_pos, sub_verb_prefix_feats)
                                    tagged_word_data = [tagged_original, tagged_pos, tagged_standard]
                                    break
                                # if the preverb is reduced to zero and has no features to be added to the verb,
                                # move past it without reducing the verb form
                                elif verb_prefix_original == "-":
                                    if verb_prefix_feats:
                                        print(verb_prefix_data)
                                        print(tagged_word_data)
                                        print([k[0] for k in standard_mapping])
                                        print([k[0] for k in pos_list])
                                        raise RuntimeError()
                                    else:
                                        continue
                                # if a preverb or infixed pronoun can't be found where expected in the verb form
                                else:
                                    if last_pos_data != verb_prefix_data:
                                        print(last_pos_data)
                                    print(verb_prefix_data)
                                    print(tagged_word_data)
                                    print([k[0] for k in standard_mapping])
                                    print([k[0] for k in pos_list])
                                    raise RuntimeError("Not all preverbs found in following verb form")
                                # for each prefix in this loop, add its features to a list to be added to the verb's
                                if verb_prefix_feats:
                                    for preverbal_feature in verb_prefix_feats:
                                        if preverbal_feature not in collected_preverb_feats:
                                            collected_preverb_feats.append(preverbal_feature)
                            # if features have been added to the verb form, add them to the POS list
                            if collected_preverb_feats:
                                tagged_pos = add_features(tagged_pos, collected_preverb_feats)
                                tagged_word_data = [tagged_original, tagged_pos, tagged_standard]
                            # remove the preverbs and infixed pronouns from the POS list
                            pos_list = pos_list[:j-last_pos_place] + [tagged_word_data] + pos_list[j+1:]
                            combine_subtract = True
                            break
                    # if the last POS is not a combinable type of POS
                    elif last_short_pos in verb_independent_POS:
                        # if there are no preverbal affixes between the last POS and the verb form
                        # assume the last POS and verbal complex cannot be combined and move on
                        if not verbal_affixes:
                            continue
                        # if there are preverbal affixes between the last POS (uncombinable) and the verb form
                        else:
                            first_preverb_data = verbal_affixes[0]
                            first_preverb_original = first_preverb_data[0]
                            split_first_preverb = split_pos_feats(first_preverb_data[1])
                            first_preverb_short_pos = split_first_preverb[0]
                            first_preverb_feats = split_first_preverb[1]
                            # if there is only one preverbal affix and it is a preverb, not an infixed pronoun
                            if len(verbal_affixes) == 1 and first_preverb_short_pos == "PVP":
                                # if the preverb is already present in the following verb form
                                if first_preverb_original == tagged_original[:len(first_preverb_original)]:
                                    if first_preverb_feats:
                                        tagged_pos = add_features(tagged_pos, first_preverb_feats)
                                        tagged_word_data = [tagged_original, tagged_pos, tagged_standard]
                                    pos_list = pos_list[:j-1] + [tagged_word_data] + pos_list[j+1:]
                                    combine_subtract = True
                                    break
                                # if the compounding preverb is not present in the following verb form
                                else:
                                    print(last_pos_data)
                                    print(first_preverb_data)
                                    print(tagged_word_data)
                                    print([k[0] for k in standard_mapping])
                                    print([k[0] for k in pos_list])
                                    raise RuntimeError("Conjoining preverb immediately preceding verb form but "
                                                       "preverb not part of verb already")
                            # if there is only one preverbal affix and it is not a preverbal particle, as expexted
                            elif len(verbal_affixes) == 1 and first_preverb_short_pos != "PVP":
                                print(last_pos_data)
                                print(first_preverb_short_pos)
                                print(first_preverb_data)
                                print(tagged_word_data)
                                print([k[0] for k in standard_mapping])
                                print([k[0] for k in pos_list])
                                raise RuntimeError("Unexpected POS found as only preverbal affix")
                            # if there are more than one preverbal affixes preceding a verb form
                            elif len(verbal_affixes) > 1:
                                # check if every preverbal particle and infixed pronoun is already in the full verb form
                                reduced_verbform = tagged_original
                                for verb_prefix_data in verbal_affixes:
                                    verb_prefix = verb_prefix_data[0]
                                    verb_prefix_pos = verb_prefix_data[1]
                                    split_verb_prefix = split_pos_feats(verb_prefix_pos)
                                    verb_prefix_short_pos = split_verb_prefix[0]
                                    verb_prefix_feats = split_verb_prefix[1]
                                    # check if any infixed pronouns precede the verb form
                                    # if so, add their features to the verb's
                                    if verb_prefix_short_pos == "IFP":
                                        tagged_pos = add_features(tagged_pos, verb_prefix_feats, ['PronType'])
                                        tagged_word_data = [tagged_original, tagged_pos, tagged_standard]
                                        pos_list[j] = tagged_word_data
                                    # add features from any preverb to the verb's features also
                                    elif verb_prefix_short_pos == "PVP":
                                        tagged_pos = add_features(tagged_pos, verb_prefix_feats)
                                        tagged_word_data = [tagged_original, tagged_pos, tagged_standard]
                                        pos_list[j] = tagged_word_data
                                    # check if the preverbal affix is in the verb form
                                    if verb_prefix == reduced_verbform[:len(verb_prefix)]:
                                        reduced_verbform = reduced_verbform[len(verb_prefix):]
                                    # if a preverb or infixed pronoun can't be found where expected in the verb form
                                    else:
                                        print(verb_prefix)
                                        print(reduced_verbform)
                                        print(tagged_word_data)
                                        print([k[0] for k in standard_mapping])
                                        print([k[0] for k in pos_list])
                                        raise RuntimeError("Not all preverbs found in following verb form")
                                # remove the preverbs and infixed pronouns from the POS list
                                pos_list = pos_list[:j-last_pos_place+1] + pos_list[j:]
                                combine_subtract = True
                                break
                            else:
                                print(last_pos_data)
                                print(first_preverb_data)
                                print(tagged_word_data)
                                print([k[0] for k in standard_mapping])
                                print([k[0] for k in pos_list])
                                raise RuntimeError("Unexpected number of preverbs/infixes preceding verb form")
                    # if the last POS is a combinable type of POS
                    elif last_short_pos in verb_dependent_POS:
                        # if the last POS is a conjunct particle separate it from the verbal cluster
                        # treat any infixed pronouns as suffixed pronouns to the conjunct particle
                        if last_pos_data in conjunct_particles or last_pos_data in dependent_conjunctions:
                            # if there are no preverbs or infixed pronouns between the conjunct particle and the verb
                            # ensure the conjunct particle is not represented in the verb form
                            if not verbal_affixes:
                                # if the conjunct particle is not in the verb form
                                if last_original != tagged_original[:len(last_original)]:
                                    continue
                                # if the conjunct particle is in the verb form, reduce the verb form
                                else:
                                    tagged_original = tagged_original[len(last_original):]
                                    tagged_standard = tagged_standard[len(last_standard):]
                                    tagged_word_data = [tagged_original, tagged_pos, tagged_standard]
                                    pos_list[j] = tagged_word_data
                                    combine_subtract = True
                                    break
                            # if preverbs and/or infixed pronouns follow the conjunct particle
                            elif verbal_affixes:
                                first_affix_data = verbal_affixes[0]
                                first_affix_original = first_affix_data[0]
                                first_affix_pos = first_affix_data[1]
                                first_affix_standard = first_affix_data[2]
                                split_first_affix = split_pos_feats(first_affix_pos)
                                first_affix_short_pos = split_first_affix[0]
                                first_affix_feats = split_first_affix[1]
                                # if the first POS following the conjunct particle is a preverbal particle
                                # separate the conjunct particle and let the verb begin with the preverbal particle
                                if first_affix_short_pos == "PVP":
                                    # check if every preverbal affix is already in the full verb form
                                    reduced_verbform = tagged_original
                                    for verb_prefix_data in verbal_affixes:
                                        verb_prefix = verb_prefix_data[0]
                                        verb_prefix_pos = verb_prefix_data[1]
                                        split_verb_prefix = split_pos_feats(verb_prefix_pos)
                                        verb_prefix_short_pos = split_verb_prefix[0]
                                        verb_prefix_feats = split_verb_prefix[1]
                                        if verb_prefix_short_pos == "IFP":
                                            raise RuntimeError("IFP found following initial preverb instead of conjunct"
                                                               " particle, unexpected in this position.")
                                        # if the preverb is at the beginning of the verb form, reduce the verb form
                                        if verb_prefix == reduced_verbform[:len(verb_prefix)]:
                                            reduced_verbform = reduced_verbform[len(verb_prefix):]
                                            if verb_prefix_feats:
                                                print(verb_prefix_data)
                                                raise RuntimeError("Prefix features must be added to verb")
                                        # if the preverb is reduced to zero, move past it without reducing the verb form
                                        elif verb_prefix == "-":
                                            if verb_prefix_feats:
                                                print(verb_prefix_data)
                                                raise RuntimeError("Prefix features must be added to verb")
                                            else:
                                                continue
                                        # if the first preverb following a conjunct particle is in the verb form
                                        # but not in the initial position
                                        # combine preceding particles to see if any combo is in initial position
                                        # if so, remove it from the verb original and standard forms before progressing
                                        elif verb_prefix in reduced_verbform and verb_prefix_data == first_affix_data:
                                            combined_prepos_orig = ""
                                            combined_prepos_std = ""
                                            for backstep in range(j-1):
                                                start_position = j-1-backstep-len(verbal_affixes)
                                                backword_data = pos_list[start_position]
                                                backstep_orig = backword_data[0]
                                                combined_prepos_orig = backstep_orig + combined_prepos_orig
                                                backstep_std = backword_data[2]
                                                combined_prepos_std = backstep_std + combined_prepos_std
                                                if combined_prepos_orig == tagged_original[:len(
                                                        combined_prepos_orig)] \
                                                        and combined_prepos_std == tagged_standard[:len(
                                                        combined_prepos_std)]:
                                                    tagged_original = tagged_original[len(combined_prepos_orig):]
                                                    reduced_verbform = tagged_original
                                                    tagged_standard = tagged_standard[len(combined_prepos_std):]
                                                    tagged_word_data = [tagged_original, tagged_pos, tagged_standard]
                                                    pos_list[j] = tagged_word_data
                                                    break
                                            if verb_prefix == reduced_verbform[:len(verb_prefix)]:
                                                reduced_verbform = reduced_verbform[len(verb_prefix):]
                                                if verb_prefix_feats:
                                                    tagged_pos = add_features(tagged_pos, verb_prefix_feats, ["Mood"])
                                                    tagged_word_data = [tagged_original, tagged_pos, tagged_standard]
                                                    pos_list[j] = tagged_word_data
                                            # if Bauer added the preverb to his analysis but not the nasalisation marker
                                            elif "ṅ" + verb_prefix == reduced_verbform[:len(verb_prefix) + 1] \
                                                    or "n" + verb_prefix == reduced_verbform[:len(verb_prefix) + 1]:
                                                reduced_verbform = reduced_verbform[len(verb_prefix) + 1:]
                                                if verb_prefix_feats:
                                                    tagged_pos = add_features(tagged_pos, verb_prefix_feats)
                                                    tagged_word_data = [tagged_original, tagged_pos, tagged_standard]
                                                    pos_list[j] = tagged_word_data
                                            else:
                                                print(last_pos_data)
                                                print(verb_prefix)
                                                print(reduced_verbform)
                                                print(tagged_word_data)
                                                print([k[0] for k in standard_mapping])
                                                print([k[0] for k in pos_list])
                                                raise RuntimeError("Not all preverbs found in following verb form")
                                        # if the first preverb following a conjunct particle is not in the verb form
                                        elif verb_prefix not in reduced_verbform:
                                            print(verb_prefix)
                                            print(reduced_verbform)
                                            print(tagged_word_data)
                                            print([k[0] for k in standard_mapping])
                                            print([k[0] for k in pos_list])
                                            raise RuntimeError("Not all preverbs found in following verb form")
                                        # if a preverb or infixed pronoun can't be found where expected in the verb form
                                        else:
                                            print(verb_prefix)
                                            print(reduced_verbform)
                                            print(tagged_word_data)
                                            print([k[0] for k in standard_mapping])
                                            print([k[0] for k in pos_list])
                                            raise RuntimeError("Not all preverbs found in following verb form")
                                    # remove the preverbs and infixed pronouns from the POS list
                                    pos_list = pos_list[:j-last_pos_place+1] + pos_list[j:]
                                    combine_subtract = True
                                    break
                                # if the first POS following the conjunct particle is an infixed pronoun
                                # suffix it to the conjunct particle and separate both from the verb
                                # then ensure any remaining preverbs aren't repeated in the verb form
                                elif first_affix_short_pos == "IFP":
                                    combined_last_original = last_original + first_affix_original
                                    combined_last_pos = add_features(last_pos, first_affix_feats)
                                    combined_last_standard = last_standard + first_affix_standard
                                    combined_last_data = [combined_last_original,
                                                          combined_last_pos,
                                                          combined_last_standard]
                                    # if the combined conjunct particle and now-suffixed pronoun are in the verb form
                                    # they should be doubled at the beginning of the verb form, remove them if so
                                    # only add the features of any following preverbs to the verb's
                                    if combined_last_original == tagged_original[:len(combined_last_original)] and \
                                            combined_last_standard == tagged_standard[:len(combined_last_standard)]:
                                        # delete the IFP from the verbal affixes
                                        del verbal_affixes[0]
                                        # check that any remaining preverbal affix is a preverb and add its features
                                        # to the verb
                                        for remaining_affix in verbal_affixes:
                                            remaining_affix_pos = remaining_affix[1]
                                            split_remaining_affix = split_pos_feats(remaining_affix_pos)
                                            remaining_affix_short_pos = split_remaining_affix[0]
                                            remaining_affix_feats = split_remaining_affix[1]
                                            if remaining_affix_short_pos != "PVP":
                                                raise RuntimeError("Unexpected POS among remaining verbal affixes")
                                            # if all remaining affixes are preverbs, assume all are in the verb form
                                            # add their features to the verb's
                                            if remaining_affix_feats:
                                                tagged_pos = add_features(tagged_pos, remaining_affix_feats)
                                        tagged_original = tagged_original[len(combined_last_original):]
                                        tagged_standard = tagged_standard[len(combined_last_standard):]
                                        tagged_word_data = [tagged_original, tagged_pos, tagged_standard]
                                        pos_list = pos_list[:j-last_pos_place] + [combined_last_data] + \
                                                   [tagged_word_data] + pos_list[j+1:]
                                        combine_subtract = True
                                        break
                                    # if the combined conjunct particle and now-suffixed pronoun are in the verb form
                                    # but not at its beginning, remove them and everything before them from its form
                                    # only add the features of any following preverbs to the verb's
                                    elif combined_last_original in tagged_original \
                                            and combined_last_standard in tagged_standard:
                                        # delete the IFP from the verbal affixes
                                        del verbal_affixes[0]
                                        # check that any remaining preverbal affix is a preverb and add its features
                                        # to the verb
                                        for remaining_affix in verbal_affixes:
                                            remaining_affix_pos = remaining_affix[1]
                                            split_remaining_affix = split_pos_feats(remaining_affix_pos)
                                            remaining_affix_short_pos = split_remaining_affix[0]
                                            remaining_affix_feats = split_remaining_affix[1]
                                            if remaining_affix_short_pos != "PVP":
                                                raise RuntimeError("Unexpected POS among remaining verbal affixes")
                                            # if all remaining affixes are preverbs, assume all are in the verb form
                                            # add their features to the verb's
                                            if remaining_affix_feats:
                                                tagged_pos = add_features(tagged_pos, remaining_affix_feats)
                                                raise RuntimeError("Unexpected preverb features found")
                                        tagged_original = tagged_original[tagged_original.find(combined_last_original)
                                                                          + len(combined_last_original):]
                                        tagged_standard = tagged_standard[tagged_standard.find(combined_last_standard)
                                                                          + len(combined_last_standard):]
                                        tagged_word_data = [tagged_original, tagged_pos, tagged_standard]
                                        pos_list = pos_list[:j-last_pos_place] + [combined_last_data] + \
                                                   [tagged_word_data] + pos_list[j+1:]
                                        combine_subtract = True
                                        break
                                    else:
                                        print(last_pos_data)
                                        print(combined_last_data)
                                        print(tagged_word_data)
                                        print([k[0] for k in standard_mapping])
                                        print([k[0] for k in pos_list])
                                        raise RuntimeError("Conjunct particle and pronoun not in verb form")
                                else:
                                    print(last_pos_data)
                                    print(first_affix_data)
                                    print(tagged_word_data)
                                    print([k[0] for k in standard_mapping])
                                    print([k[0] for k in pos_list])
                                    raise RuntimeError("Conjunct particle followed by unexpected POS")
                        # if the last POS preceding a verb form and any preverbal affixes is an independent conjunction
                        # a conjunction with a combined copula form, or a particle which cannot be combined with
                        # dependent verb forms
                        elif last_pos_data in independent_conjunctions or last_pos_data in independent_particles \
                                or last_short_pos == "SCONJ" and "VerbType=Cop" in last_feats:
                            # if there are no preverbs or infixed pronouns between the conjunction and the verb
                            # ensure the conjunction is not represented in the verb form
                            if not verbal_affixes:
                                if last_original != tagged_original[:len(last_original)]:
                                    continue
                                else:
                                    print(last_pos_data)
                                    print(tagged_word_data)
                                    print([k[0] for k in standard_mapping])
                                    print([k[0] for k in pos_list])
                                    raise RuntimeError("Conjunction repeated in verb form")
                            # if there are preverbs or infixed pronouns
                            else:
                                # check if every preverbal particle and infixed pronoun is already in the full verb form
                                reduced_verbform = tagged_original
                                for verb_prefix_data in verbal_affixes:
                                    verb_prefix = verb_prefix_data[0]
                                    verb_prefix_pos = verb_prefix_data[1]
                                    split_verb_prefix = split_pos_feats(verb_prefix_pos)
                                    verb_prefix_short_pos = split_verb_prefix[0]
                                    verb_prefix_feats = split_verb_prefix[1]
                                    # if an infixed pronoun is found not to be following an initial preverb
                                    if verb_prefix_short_pos == "IFP" and verb_prefix_data != verbal_affixes[1]:
                                        print(last_pos_data)
                                        print(verbal_affixes)
                                        print(tagged_word_data)
                                        print([k[0] for k in standard_mapping])
                                        print([k[0] for k in pos_list])
                                        raise RuntimeError("IFP found in unexpected position")
                                    # because the preceding POS is separate from the verbal complex any infixed pronouns
                                    # will occur after an initial preverb, so they can be treated like any other preverb
                                    # make sure any preverbal affix is in the verb form
                                    if verb_prefix == reduced_verbform[:len(verb_prefix)]:
                                        reduced_verbform = reduced_verbform[len(verb_prefix):]
                                        if verb_prefix_feats:
                                            tagged_pos = add_features(tagged_pos, verb_prefix_feats, ["PronType"])
                                            tagged_word_data = [tagged_original, tagged_pos, tagged_standard]
                                            pos_list[j] = tagged_word_data
                                    # if Bauer added the preverb to his analysis but not the nasalisation marker
                                    elif "n" + verb_prefix == reduced_verbform[:len(verb_prefix) + 1]:
                                        reduced_verbform = reduced_verbform[len(verb_prefix) + 1:]
                                        if verb_prefix_feats:
                                            tagged_pos = add_features(tagged_pos, verb_prefix_feats)
                                            tagged_word_data = [tagged_original, tagged_pos, tagged_standard]
                                            pos_list[j] = tagged_word_data
                                    # if a preverb or infixed pronoun can't be found where expected in the verb form
                                    else:
                                        print(verb_prefix)
                                        print(reduced_verbform)
                                        print(tagged_word_data)
                                        print([k[0] for k in standard_mapping])
                                        print([k[0] for k in pos_list])
                                        raise RuntimeError("Not all preverbs found in following verb form")
                                # remove the preverbs and infixed pronouns from the POS list
                                pos_list = pos_list[:j-last_pos_place+1] + pos_list[j:]
                                combine_subtract = True
                                break
                        # if the last POS preceding the verb form is reduced to zero
                        elif last_original == "-" and last_standard == "-":
                            second_last_data = pos_list[j-last_pos_place-1]
                            # list all parts of speech that relative particles can fall into (cf. Thurn p.312)
                            blank_rel_combos = [['hi', '<ADP AdpType=Prep | Definite=Ind>', 'hi']]
                            if second_last_data in blank_rel_combos:
                                sl_original = second_last_data[0]
                                sl_pos = second_last_data[1]
                                sl_standard = second_last_data[2]
                                sl_pos = add_features(sl_pos, last_feats)
                                second_last_data = [sl_original, sl_pos, sl_standard]
                                pos_list = pos_list[:j-last_pos_place-1] + [second_last_data] + pos_list[j:]
                                combine_subtract = True
                                break
                            else:
                                print(second_last_data)
                                print(last_pos_data)
                                print(tagged_word_data)
                                print([k[0] for k in standard_mapping])
                                print([k[0] for k in pos_list])
                                raise RuntimeError("Empty relative particle preceded by unknown form")
                        # if the last POS's data can't be found in any list
                        else:
                            print(last_pos_data)
                            print(tagged_word_data)
                            print([k[0] for k in standard_mapping])
                            print([k[0] for k in pos_list])
                            raise RuntimeError("Unknown combinable POS preceding verbal complex, add to list")
                    # if an unknown POS type precedes a verb form and any preverbal affixes
                    else:
                        print(last_pos_data)
                        print(tagged_word_data)
                        print([k[0] for k in standard_mapping])
                        print([k[0] for k in pos_list])
                        raise RuntimeError("Unknown POS type preceding verbal complex, identify POS")

    #                                               PART 2.1.2:
    #
    #                                                ARTICLE
    #
    # combine compounded articles with preceding prepositions

    #                                               PART 2.1.3:
    #
    #                                                  MISC
    #
    # remove doubled compounds of prefixed particles and nouns/adjectives following the two individually
    prepart_list = [['áer', '<PART Prefix=Yes>', 'aer'],
                    ['am', '<PART Prefix=Yes>', 'am'],
                    ['an', '<PART Prefix=Yes>', 'an'],
                    ['co', '<PART Prefix=Yes>', 'co'],
                    ['com', '<PART Prefix=Yes>', 'com'],
                    ['chom', '<PART Prefix=Yes>', 'chom'],
                    ['déden', '<PART Prefix=Yes>', 'deden'],
                    ['dí', '<PART Prefix=Yes>', 'di'],
                    ['im', '<PART Prefix=Yes>', 'im'],
                    ['mi', '<PART Prefix=Yes>', 'mi'],
                    ['mí', '<PART Prefix=Yes>', 'mi'],
                    ['neph', '<PART Polarity=Neg | Prefix=Yes>', 'neph']]
    # count the instances of prefixed particles in the gloss
    prepart_count = 0
    for tagged_word_data in pos_list:
        split_tagged_pos = split_pos_feats(tagged_word_data[1])
        tagged_short_pos = split_tagged_pos[0]
        tagged_feats = split_tagged_pos[1]
        if tagged_short_pos == "PART" and 'Prefix=Yes' in tagged_feats:
            if tagged_word_data not in prepart_list:
                print(tagged_word_data)
                print([i[0] for i in standard_mapping])
                print([i[0] for i in pos_list])
                raise RuntimeError("Prefixed particle not in full list")
            elif tagged_word_data in prepart_list:
                prepart_count += 1
    for i in range(prepart_count):
        for j, tagged_word_data in enumerate(pos_list):
            tagged_original, tagged_pos, tagged_standard = tagged_word_data[0], tagged_word_data[1], tagged_word_data[2]
            # if a prefixed particle is found in the gloss look for the following POS, with which it combines
            if tagged_word_data in prepart_list:
                try:
                    next_pos_data = pos_list[j+1]
                # if the prefixed particle is the last POS in the gloss
                except IndexError:
                    next_pos_data = False
                # if a combining POS is found, look ahead one more place to find the compounded form of the two POS
                if next_pos_data:
                    next_original, next_pos, next_standard = next_pos_data[0], next_pos_data[1], next_pos_data[2]
                    try:
                        third_pos_data = pos_list[j+2]
                    # if no POS follows the two combining POS, combine the two to create the compounded form
                    except IndexError:
                        third_pos_data = False
                        compounded_form = [tagged_original + next_original, next_pos, tagged_standard + next_standard]
                        # if the compound form of the two POS is found elsewhere in the gloss
                        if compounded_form in pos_list:
                            print(tagged_word_data)
                            print(next_pos_data)
                            print(compounded_form)
                            print([i[0] for i in standard_mapping])
                            print([i[0] for i in pos_list])
                            raise RuntimeError("Compound word form in gloss, but not following separate parts")
                        # if there is no compounded form of the two POS in the gloss, the gloss is already in order
                        else:
                            pass
                    # if there is a POS following the two combining POS
                    if third_pos_data:
                        third_original, third_pos, third_standard = third_pos_data[0], \
                                                                    third_pos_data[1], third_pos_data[2]
                        split_third_pos = split_pos_feats(third_pos)
                        compounded_form = [tagged_original + next_original, next_pos, tagged_standard + next_standard]
                        # if the prefixed particle and following POS are duplicated in the third POS
                        if third_pos_data == compounded_form:
                            del pos_list[j+2]
                        # if the prefixed particle and following POS are duplicated somewhere else in the gloss
                        elif compounded_form in pos_list:
                            print(tagged_word_data)
                            print(next_pos_data)
                            print(compounded_form)
                            print([i[0] for i in standard_mapping])
                            print([i[0] for i in pos_list])
                            raise RuntimeError("Compound word form in gloss, but not following separate parts")
    # remove combined conjunction, 'arindí', where it doubles the breakdown, 'ar', 'ind', and 'í'
    arindi_list = [['airindi', '<SCONJ>', 'airindi'],
                   ['airindí', '<SCONJ>', 'airindi'],
                   ['arindi', '<SCONJ>', 'arindi'],
                   ['arindí', '<SCONJ>', 'arindi']]
    arindi_count = 0
    for tagged_word_data in pos_list:
        if tagged_word_data in arindi_list:
            arindi_count += 1
    for i in range(arindi_count):
        for j, tagged_word_data in enumerate(pos_list):
            if tagged_word_data in arindi_list:
                try:
                    last_pos_data = pos_list[j-1]
                except IndexError:
                    raise RuntimeError("Could not find breakdown of combined conjunction, 'airindí'")
                if last_pos_data:
                    last_three_pos = pos_list[j-3:j]
                    if last_three_pos in [[['ar', '<ADP AdpType=Prep | Definite=Def | Prefix=Yes>', 'ar'],
                                           ['ind', '<DET AdpType=Prep | Case=Dat | Gender=Neut | Number=Sing>', 'ind'],
                                           ['í', '<PART>', 'i']],
                                          [['ar', '<ADP AdpType=Prep | Definite=Def | Prefix=Yes>', 'ar'],
                                           ['ind', '<DET AdpType=Prep | Case=Dat | Gender=Neut | Number=Sing>', 'ind'],
                                           ['i', '<PART>', 'i']],
                                          [['air', '<ADP AdpType=Prep | Definite=Def | Prefix=Yes>', 'air'],
                                           ['ind', '<DET AdpType=Prep | Case=Dat | Gender=Neut | Number=Sing>', 'ind'],
                                           ['í', '<PART>', 'i']],
                                          [['air', '<ADP AdpType=Prep | Definite=Def | Prefix=Yes>', 'air'],
                                           ['ind', '<DET AdpType=Prep | Case=Dat | Gender=Neut | Number=Sing>', 'ind'],
                                           ['i', '<PART>', 'i']]]:
                        del pos_list[j]
                        combine_subtract = True
                    else:
                        print(last_three_pos)
                        print([i[0] for i in pos_list])
                        print([i[0] for i in standard_mapping])
                        raise RuntimeError("Could not find breakdown of combined conjunction, 'airindí'")
    # remove doubled 'ol', and 'chenae' breakdown of adverb 'olchenae'
    # cf. eDIL entries for 'olchena' and '1 ol, (al)' vs. entries for 'arindí' and '1 ar'
    olchena_list = [['olchene', '<ADV>', 'olchene'],
                    ['olchenae', '<ADV>', 'olchenae'],
                    ['olchenæ', '<ADV>', 'olchenae'],
                    ['olchaenae', '<ADV>', 'olchaenae'],
                    ['olchænae', '<ADV>', 'olchaenae']]
    # count the instances of the word in the gloss
    olchena_count = 0
    for tagged_word_data in pos_list:
        if tagged_word_data in olchena_list:
            olchena_count += 1
    for i in range(olchena_count):
        for j, tagged_word_data in enumerate(pos_list):
            if tagged_word_data in olchena_list:
                try:
                    last_pos_data = pos_list[j-1]
                    last_two_pos = pos_list[j-2:j]
                except IndexError:
                    last_pos_data = False
                try:
                    next_pos_data = pos_list[j+1]
                    next_two_pos = pos_list[j+1:j+3]
                except IndexError:
                    next_pos_data = False
                olchena_parts = [[['ol', '<ADP AdpType=Prep | Definite=Ind>', 'ol'],
                                  ['chenae', '<PRON PronType=Prs>', 'chenae']],
                                 [['ol', '<ADP AdpType=Prep | Definite=Ind>', 'ol'],
                                  ['chænae', '<PRON PronType=Prs>', 'chaenae']],
                                 [['ol', '<ADP AdpType=Prep | Definite=Ind>', 'ol'],
                                  ['chaenae', '<PRON PronType=Prs>', 'chaenae']]]
                # find the two POS preceding and following the combined form, if there are two
                if last_pos_data:
                    # check if the preceding two POS make up the combined form and delete them if so
                    if last_two_pos in olchena_parts:
                        pos_list = pos_list[:j-2] + pos_list[j:]
                        combine_subtract = True
                        break
                    # if the preceding two POS did not make up the combined form, check the following two instead
                    elif next_pos_data:
                        if next_two_pos in olchena_parts:
                            pos_list = pos_list[:j+1] + pos_list[j+3:]
                            combine_subtract = True
                            break
                else:
                    raise RuntimeError("Could not find doubled parts of word to remove")

    #                                             PART 2.1 (reprise):
    #
    # update rating to show gloss has had content combined or removed
    if combine_subtract:
        tags_rating += 1

    #                                                PART 2.2:
    #
    # if Bauer has analysed an instance of 'ɫ' but Hofman has expanded it as latin 'vel', revert it to 'ɫ' and tag
    i_count = False
    # if there's any instance of 'ɫ' in Bauer's analysis, count how many there are in the analysis
    for i in pos_list:
        if i == ['ɫ', '<CCONJ>', 'no']:
            i_count = pos_list.count(i)
            break
    # then count how many instances of 'no' or 'nó' Hofman has in his gloss
    if i_count:
        j_count = 0
        for j in standard_mapping:
            if j[:2] in [('no', 'no'), ('nó', 'no')]:
                j_count += 1
        # if the two counts do not match, find the difference
        if j_count != i_count:
            missing_count = i_count - j_count
            # if there are more instances in Bauer's analysis than Hofman's gloss
            if missing_count > 0:
                # check for instances of 'vel' in Hofman's gloss used instead, and change them to 'ɫ'
                for k in range(missing_count):
                    for l, tok_maping in enumerate(standard_mapping):
                        if tok_maping[:2] == ('vel', 'vel'):
                            standard_mapping[l] = ('ɫ', 'no', tok_maping[2])
            # if there are more instances in Hofman's gloss than Bauer's analysis
            elif missing_count < 0:
                # look for instances of nó written in full in Bauer's gloss
                alts_found = 0
                for k in range(abs(missing_count)):
                    for word_an in pos_list:
                        if word_an in [['nó', '<CCONJ>', 'no']]:
                            alts_found += 1
                if missing_count + alts_found != 0:
                    pvp_no_count = pos_list.count(['no', '<PART PartType=Vb>', 'no'])
                    if missing_count + alts_found + pvp_no_count != 0:
                        print(missing_count, alts_found, pvp_no_count)
                        print([i[0] for i in standard_mapping])
                        print([i[0] for i in pos_list])
                        print(pos_list)
                        raise RuntimeError("Missing 'ɫ' in Bauer's analysis, or 'no/nó' repeated by Hofman")

    #                                                 PART 3:
    #
    # Connect tagged words from Bauer's analysis with their counterparts from Hofman's gloss,
    # Apply reliability rating for the match between words in the gloss as a whole.

    # include '.i.' in pos-list so it can be tagged
    if ".i." in standard_list:
        if pos_list.count([".i.", "<ADV Abbr=Yes>", ".i."]) + pos_list.count(["<ADV Abbr=Yes | Typo=Yes>"]) !=\
                standard_list.count(".i."):
            for token in standard_list:
                if token == ".i.":
                    pos_list.append([".i.", "<ADV Abbr=Yes>", ".i."])
    # remove '-' from pos_list where Bauer has used it to represent a word reduced to zero
    for i in pos_list:
        if i == "-":
            raise RuntimeError("Word reduced to zero")
    pos_list = [i for i in pos_list if i[0] != "-"]
    # check if there are duplicate parts-of-speech, if so flag this for later
    duplicate_pos = False
    for i in pos_list:
        if pos_list.count(i) > 1:
            duplicate_pos = True
            break
    # check reliability of cross-tagging and apply score to output
    # measure length of POS list against token list after accounting for ".i." symbols and hyphens
    # increase one digit if no. of tokens don't match
    if len(pos_list) != len(standard_list):
        tags_rating += 10
    # list known mismatches *fix in matching section later*
    known_mismatches = [['asanarbaram', '<VERB>', 'asanarbaram']]
    # list known edit-distance errors and do not allow them to be used as lowest edit distances
    eddist_errors = [['ní', '<PART Polarity=Neg>', 'niro-graigther', 0, [[7, 0], 2]],
                     ['ní', '<PART Polarity=Neg>', 'niro-graigther', 11, [[7, 1], 2]],
                     ['con', '<SCONJ>', 'hoc', 4, [1, 0]]]

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
        if tag not in ["<PVP>", "<IFP>", "<UNR>", "<UNK>"]:
            # check the edit distance between its standard and the standard form of every token in Hofman's gloss,
            # in order
            for token_list in standard_mapping:
                original_token = token_list[0]
                standard_token = token_list[1]
                token_place = token_list[2]
                if token_place not in sorted_list:
                    eddist = ed(standard_word, standard_token, substitution_cost=2)
                    # if an edit distance of zero occurs, the first time it occurs, assume the two are a match
                    # add Bauer's word, its POS tag, Hofman's word, the edit distance, and indices for the match to a
                    # matching-words list
                    if eddist == 0:
                        l_ed_check = [original_word, tag, original_token, eddist, [token_place, pos_place]]
                        if l_ed_check not in eddist_errors:
                            sorted_list.append(token_place)
                            lowest_eddist = l_ed_check
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
            invalid_list = ["<PVP>", "<IFP>", "<UNR>", "<UNK>"]
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
                        eddist = ed(standard_combo, standard_token, substitution_cost=2)
                        # if an edit distance of zero occurs, the first time it occurs, assume the two are a match
                        # add Bauer's word, its POS tag, Hofman's word, the edit distance, and indices for the match to
                        # a matching-words list
                        if eddist == 0:
                            l_ed_check = [[original_word, tag, original_token, eddist, [token_place, pos_place]],
                                          [next_word, next_tag, original_token, eddist, [token_place, pos_place + 1]]]
                            if l_ed_check[0] not in eddist_errors and l_ed_check[1] not in eddist_errors:
                                sorted_list.append(token_place)
                                lowest_eddists = l_ed_check
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

    #                                                 PART 3.2:
    #
    # for the remaining words in Bauer's analysis which cannot be mapped perfectly to a word in Hofman's gloss
    # find the word in Hofman's gloss with the lowest edit distance from the each analysed word and match these

    lowest_eddist = False
    last_match = [0, 0]
    dupos_list = list()
    conjunct_particles = [['ní', '<PART Polarity=Neg>', 'ni']]
    # for each remaining word in Bauer's analysis, in order, excluding some problematic conjunct particles
    for pos_place, pos_tag in enumerate(pos_list):
        if pos_place not in used_pos and pos_tag not in conjunct_particles:
            original_word = pos_tag[0]
            standard_word = pos_tag[-1]
            tag = pos_tag[1]
            # if the word is valid (has a usable POS tag)
            if tag not in ["<PVP>", "<IFP>", "<UNR>", "<UNK>"]:
                # if this POS is not related to the last token which matched to a POS in this section
                # (i.e. if this POS's index more than one degree higher than the next last match's POS index
                # check if there is an already matched POS index in the alignment list from an earlier section)
                if pos_place > last_match[1] + 1:
                    search_for = False
                    # reverse through the sorted list of assigned POS indices
                    for i in list(reversed(sorted([i[0] for i in alignment_list]))):
                        # find the first index which is lower than the current POS's index (pos_place)
                        if i < pos_place:
                            search_for = i
                            break
                    # if the next lowest POS index can be found in the list of aligned POS
                    if search_for:
                        for j in list(reversed(alignment_list)):
                            # find the index of that POS in the unsorted alignment list
                            if j[0] == search_for:
                                # update the last matched-index to the one found in the alignment list
                                last_match = list(reversed(j))
                                break
                # check its edit distance against every remaining token in Hofman's gloss, in order
                for token_list in standard_mapping:
                    original_token = token_list[0]
                    standard_token = token_list[1]
                    token_place = token_list[2]
                    eddist = False
                    # exclude tokens from comparison which come before the last matched token in the gloss
                    try:
                        if token_place not in used_toks and token_place >= last_match[0]:
                            eddist = ed(standard_word, standard_token, substitution_cost=2)
                            # find the lowest edit distance between the standard Bauer word and a standard Hofman token,
                            # if the edit dist. is lower than the maximum possible edit dist. between the two strings,
                            # assume the two are a match and identify the pair as the lowest-edit-distance candidates
                            if not lowest_eddist:
                                max_poss_ed = len(standard_word) + len(standard_token)
                                if max_poss_ed > eddist and [pos_tag, token_place] not in dupos_list:
                                    l_ed_check = [original_word, tag, original_token, eddist, [token_place, pos_place]]
                                    if l_ed_check not in eddist_errors:
                                        lowest_eddist = l_ed_check
                            elif eddist < lowest_eddist[3]:
                                max_poss_ed = len(standard_word) + len(standard_token)
                                if max_poss_ed > eddist and [pos_tag, token_place] not in dupos_list:
                                    l_ed_check = [original_word, tag, original_token, eddist, [token_place, pos_place]]
                                    if l_ed_check not in eddist_errors:
                                        lowest_eddist = l_ed_check
                    # if the token is part of a split token
                    except TypeError:
                        try:
                            token_firstplace = token_place[0]
                            if token_place not in used_toks and token_firstplace >= last_match[0]:
                                eddist = ed(standard_word, standard_token, substitution_cost=2)
                                # find the lowest edit distance between the standard Bauer word and a standard Hofman
                                # token, if the edit dist. is lower than the maximum possible edit dist. between the
                                # two strings, assume the two are a match and identify the pair as the
                                # lowest-edit-distance candidates
                                if not lowest_eddist:
                                    max_poss_ed = len(standard_word) + len(standard_token)
                                    if max_poss_ed > eddist and [pos_tag, token_place] not in dupos_list:
                                        l_ed_check = [original_word, tag, original_token, eddist,
                                                      [token_place, pos_place]]
                                        if l_ed_check not in eddist_errors:
                                            lowest_eddist = l_ed_check
                                elif eddist < lowest_eddist[3]:
                                    max_poss_ed = len(standard_word) + len(standard_token)
                                    if max_poss_ed > eddist and [pos_tag, token_place] not in dupos_list:
                                        l_ed_check = [original_word, tag, original_token, eddist,
                                                      [token_place, pos_place]]
                                        if l_ed_check not in eddist_errors:
                                            lowest_eddist = l_ed_check
                        # if the token is not part of a split token, but the last matched token was
                        except TypeError:
                            last_match_firstplace = last_match[0]
                            if token_place not in used_toks and token_place >= last_match_firstplace[0]:
                                eddist = ed(standard_word, standard_token, substitution_cost=2)
                                # find the lowest edit distance between the standard Bauer word and a standard Hofman
                                # token, if the edit dist. is lower than the maximum possible edit dist. between the
                                # two strings, assume the two are a match and identify the pair as the
                                # lowest-edit-distance candidates
                                if not lowest_eddist:
                                    max_poss_ed = len(standard_word) + len(standard_token)
                                    if max_poss_ed > eddist and [pos_tag, token_place] not in dupos_list:
                                        l_ed_check = [original_word, tag, original_token, eddist,
                                                      [token_place, pos_place]]
                                        if l_ed_check not in eddist_errors:
                                            lowest_eddist = l_ed_check
                                elif eddist < lowest_eddist[3]:
                                    max_poss_ed = len(standard_word) + len(standard_token)
                                    if max_poss_ed > eddist and [pos_tag, token_place] not in dupos_list:
                                        l_ed_check = [original_word, tag, original_token, eddist,
                                                      [token_place, pos_place]]
                                        if l_ed_check not in eddist_errors:
                                            lowest_eddist = l_ed_check
                # if the lowest non-zero edit distance has been found between the Bauer word and a Hofman token
                # assume the two are a match
                # add Bauer's word, its POS tag, the Hofman word, the edit distance, and indices for the match to a
                # matching-words list
                if lowest_eddist:
                    alignment_list.append((lowest_eddist[-1][-1], lowest_eddist[-1][0]))
                    tagged_gloss.append(lowest_eddist)
                    last_match = lowest_eddist[-1]
                    # if there are duplicates of the one POS, ensure that they are not matched with the same token
                    if duplicate_pos and pos_list.count(pos_tag) > 1:
                        used_dup_match = [pos_tag, lowest_eddist[-1][0]]
                        if used_dup_match not in dupos_list:
                            dupos_list.append(used_dup_match)
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
    # create a list of doubled-compounds to be removed from the pos_list if they cannot be matched
    compounds_found = list()
    mismatches_found = list()
    # if they're not removable compounded words, add them to a list of potential sub-word matches
    for pos_place, pos_tag in enumerate(pos_list):
        if pos_place not in used_pos:
            original_word = pos_tag[0]
            standard_word = pos_tag[-1]
            tag = pos_tag[1]
            # if the word is valid (has a usable POS tag)
            if tag not in ["<PVP>", "<IFP>", "<UNR>", "<UNK>"]:
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
                    if pos_tag in known_mismatches:
                        mismatches_found.append([pos_place, pos_tag])
                    else:
                        print(pos_tag)
                        print([i[0] for i in standard_mapping])
                        print([i[0] for i in pos_list])
                        print([i for i in tagged_gloss])
                        raise RuntimeError(f"Unused POS tagged word ({original_word}) could not be matched")
    pos_list = [j for i, j in enumerate(pos_list) if [i, j] not in compounds_found]
    pos_list = [j for i, j in enumerate(pos_list) if [i, j] not in mismatches_found]

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
    tagged_gloss_copy = tagged_gloss[:]
    for i, tok_data in enumerate(standard_mapping):
        standard_check_tok = tok_data[1]
        found = False
        # find its first matching pos-tagged word where one exists, add it to a new, ordered, tagged gloss list
        for j, pos_data in enumerate(tagged_gloss_copy):
            pos_check_word = remove_glosshyphens(standardise_glosschars(pos_data[2])).split(" ")
            if len(pos_check_word) > 1:
                hyphenation = True
            # if the standardised token is in a list containing the standardised POS
            # (i.e. if there's a perfect one-to-one match between Bauer and Hofmann's spelling and word-spacing)
            if standard_check_tok in pos_check_word:
                recombine_list.append(pos_data)
                found = True
                del tagged_gloss_copy[j]
                # if the next tagged word is part of this same token in Hofman's gloss, add it to the tagged gloss too
                try:
                    next_standard_tok = standard_mapping[i + 1][1]
                except IndexError:
                    next_standard_tok = False
                if not next_standard_tok or next_standard_tok != standard_check_tok:
                    # if this is the last token, or the next token's standard form is different to this token's
                    # check if there's another part for this token(?)
                    try:
                        next_standard_check_token = remove_glosshyphens(standardise_glosschars
                                                                        (tagged_gloss_copy[0][2])).split(" ")
                    except IndexError:
                        next_standard_check_token = False
                    if next_standard_check_token and len(next_standard_check_token) == 1:
                        if standard_check_tok in next_standard_check_token:
                            recombine_list.append(tagged_gloss_copy[0])
                            del tagged_gloss_copy[0]
                    elif next_standard_check_token and len(next_standard_check_token) > 1:
                        if standard_check_tok in next_standard_check_token:
                            recombine_list.append(tagged_gloss_copy[0])
                            del tagged_gloss_copy[0]
                break
        # if no tagged match was found, assume the word is Latin
        if not found and recombine_list:
            if tok_data[0] != recombine_list[-1][2]:
                recombine_list.append([tok_data[0], "<X>", tok_data[1], [tok_data[2], tok_data[2]]])
    # if there were words which were part of a matched pos set where only the first was carried forward above
    if tagged_gloss_copy:
        # find the second word which was not carried forward and the paired word which preceded it
        for remaining_pos in tagged_gloss_copy:
            for j, pos_search in enumerate(tagged_gloss):
                if pos_search == remaining_pos:
                    match_found = False
                    pos_tok = pos_search[2]
                    pos_pos = pos_search[1]
                    pos_position = pos_search[4]
                    # check if the word right before the remaining word forms a pair with it
                    # if not, check each preceeding word in reverse order
                    try:
                        pair_index = 0
                        while not match_found:
                            pair_index += 1
                            poss_pair_pos = tagged_gloss[j-pair_index]
                            pair_tok = poss_pair_pos[2]
                            pair_pos = poss_pair_pos[1]
                            pair_position = poss_pair_pos[4]
                            # ensure the two words are parts of a split pair by comparing their shared full token
                            # then compairing their positions in the gloss with respect to each other
                            if isinstance(pos_position[0], int):
                                if pair_tok == pos_tok and pair_position[0] == pos_position[0]:
                                    # if the correct word is found to make a pair with the remaining word
                                    if pair_position[1] == pos_position[1] - 1:
                                        match_found = True
                                        word_pair = poss_pair_pos
                                        # add the second word to the output list after its counterpart
                                        if word_pair in recombine_list:
                                            insert_after = recombine_list.index(word_pair) + 1
                                            recombine_list = recombine_list[:insert_after] + [remaining_pos] +\
                                                             recombine_list[insert_after:]
                                        else:
                                            raise RuntimeError("Test This")
                            # if the first place in the position of the POS is represented by a list
                            # (i.e. if the word makes up part of a split token)
                            # ensure the two words are parts of a split pair by comparing their shared full token
                            # then compairing their positions in the gloss with respect to each other
                            elif isinstance(pos_position[0], list):
                                if pair_tok == pos_tok and pair_position[0][0] == pos_position[0][0]:
                                    # if the correct word is found to make a pair with the remaining word
                                    if pair_position[0][1] == pos_position[0][1] - 1 and \
                                            pair_position[1] == pos_position[1] - 1:
                                        match_found = True
                                        word_pair = poss_pair_pos
                                        # add the second word to the output list after its counterpart
                                        if word_pair in recombine_list:
                                            insert_after = recombine_list.index(word_pair) + 1
                                            recombine_list = recombine_list[:insert_after] + [remaining_pos] + \
                                                             recombine_list[insert_after:]
                                        # if the counterpart cannot be found in the output list
                                        else:
                                            raise RuntimeError("Test This")
                                    # if a part of a word precedes a word and certain omitted morphemes
                                    # (e.g. <SCONJ Polarity=Neg> --> <PVP> --> <VERB>) position one will be a list
                                    # and position 2 will have a gap in number because of the omission
                                    elif pair_position[0] == pos_position[0]:
                                        if pos_pos == "<VERB>" and pair_pos == "<SCONJ>":
                                            match_found = True
                                            word_pair = poss_pair_pos
                                            # add the second word to the output list after its counterpart
                                            if word_pair in recombine_list:
                                                insert_after = recombine_list.index(word_pair) + 1
                                                recombine_list = recombine_list[:insert_after] + [remaining_pos] + \
                                                                 recombine_list[insert_after:]
                    # if the whole list is exhausted but no matched pair has been found
                    # as before, check if the word right before the remaining word forms a pair with it
                    # if not, check each preceeding word(s) in reverse order
                    except IndexError:
                        if isinstance(pos_position[0], int):
                            # if the remaining word has a duplicate that has already been assigned
                            # assume the two were accidentally switched in section 3.1
                            # swap their POS positions and re-attempt to add the remaining word to output list
                            if len([i for i in tagged_gloss if i[:2] == remaining_pos[:2]]) == 2:
                                duplicates = [i for i in tagged_gloss if i[:2] == remaining_pos[:2]]
                                duplicates.remove(remaining_pos)
                                duplicate = duplicates[0]
                                dup_position = duplicate[-1]
                                rempos_position = remaining_pos[-1]
                                new_dup_position = [dup_position[:1] + rempos_position[1:]]
                                new_rempos_position = [rempos_position[:1] + dup_position[1:]]
                                new_dup = duplicate[:-1] + new_dup_position
                                new_rempos = remaining_pos[:-1] + new_rempos_position
                                recombine_list[recombine_list.index(duplicate)] = new_dup
                                # add the word to the beginning of the string if it should be there
                                if new_rempos_position == [[0, 0]]:
                                    recombine_list = [new_rempos] + recombine_list
                                    raise RuntimeError("Test This")
                                else:
                                    print(remaining_pos)
                                    print([i[0] for i in standard_mapping])
                                    print([i for i in pos_list])
                                    print([i for i in recombine_list])
                                    raise RuntimeError("Test This")
                            else:
                                # # solved once with trip_toks
                                # # solved once with eddist_errors
                                print(remaining_pos)
                                # print(tagged_gloss_copy)
                                print([i[0] for i in standard_mapping])
                                print([i for i in pos_list])
                                # print([i for i in tagged_gloss])
                                print([i for i in recombine_list])
                                # print([i[0] for i in recombine_list])
                                raise RuntimeError("Ran through entire list of words but could not find pair")
                        # if the first place in the position of the POS is represented by a list
                        # (i.e. if the word makes up part of a split token)
                        elif isinstance(pos_position[0], list):
                            # if no match can be found but the remaining word has a duplicate that was assigned
                            # assume the two were accidentally switched in section 3.1
                            # swap their POS positions and re-attempt to add the remaining word to output list
                            if len([i for i in tagged_gloss if i[:2] == remaining_pos[:2]]) == 2:
                                duplicates = [i for i in tagged_gloss if i[:2] == remaining_pos[:2]]
                                duplicates.remove(remaining_pos)
                                duplicate = duplicates[0]
                                dup_position = duplicate[-1]
                                rempos_position = remaining_pos[-1]
                                new_dup_position = [dup_position[:1] + rempos_position[1:]]
                                new_rempos_position = [rempos_position[:1] + dup_position[1:]]
                                new_dup = duplicate[:-1] + new_dup_position
                                new_rempos = remaining_pos[:-1] + new_rempos_position
                                recombine_list[recombine_list.index(duplicate)] = new_dup
                                # add the word to the beginning of the string if it should be there
                                if new_rempos_position == [[[0, 0], 0]]:
                                    recombine_list = [new_rempos] + recombine_list
                                    raise RuntimeError("Test This")
                                else:
                                    raise RuntimeError("Test This")
                            else:
                                # # solved once with eddist_errors
                                # print([i[0] for i in tagged_gloss_copy])
                                # print(remaining_pos)
                                # print([i[0] for i in standard_mapping])
                                # print([i[0] for i in pos_list])
                                # print([i for i in recombine_list])
                                # print([i for i in tagged_gloss])
                                raise RuntimeError("Test This")
    tagged_gloss = recombine_list
    # check reliability of cross-tagging and update score before output
    # measure length of the tagged gloss before and after Latin content is reintroduced
    # increase ten digit if no. of tokens don't match
    # increase hundred digit if hyphenated word has been replaced
    after_length = len(tagged_gloss)
    if before_length != after_length:
        tags_rating += 100
    if hyphenation:
        tags_rating += 1000
    # if indices of potential-matches already assigned
    # remove suggested match from potential-matches list OR include suggested match and adjust relevant word
    # create a list of indices for tokens which have already been matched to words in the gloss
    match_indices = [x[-1][0] for x in tagged_gloss]
    # remove any possible matches which have the same token position as those in the matched-indices list
    possible_match_list = [x for x in possible_match_list if x[3] not in match_indices]
    # if anything remains in the list of possible matches
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
                # check if the type of index (list/int) matches between the potential match and the used POS,
                # if it matches, whether it be a list or an int, compare the two
                if type(tagged_tok_place[0]) == type(token_place):
                    if tagged_tok_place[0] == token_place and match_token == check_token:
                        if pos_index not in remove_indices:
                            check_matched = True
                        else:
                            raise RuntimeError("Position index doubled in list of indices for removal.\n"
                                               "Check if this can be fixed by fixing the potential-matches section.")
                # if the index type does not match, compare parts as necessary
                else:
                    try:
                        if tagged_tok_place[0][0] == token_place and match_token == check_token:
                            if pos_index not in remove_indices:
                                check_matched = True
                            else:
                                raise RuntimeError("Position index doubled in list of indices for removal.\n"
                                                   "Check if this can be fixed by fixing the potential-matches "
                                                   "section.")
                    except TypeError:
                        if tagged_tok_place == token_place and match_token == check_token:
                            if pos_index not in remove_indices:
                                check_matched = True
                            else:
                                raise RuntimeError("Position index doubled in list of indices for removal.\n"
                                                   "Check if this can be fixed by fixing the potential-matches "
                                                   "section.")
            # if the the match has been confirmed
            if check_matched:
                if placement == 'S':
                    remove_indices.append(pos_index)
                elif placement == 'E':
                    remove_indices.append(pos_index)
                elif placement == 'M':
                    remove_indices.append(pos_index)
            else:
                print(possible_match)
                print(possible_match_list)
                print([i[0] for i in standard_mapping])
                raise RuntimeError("Mismatched potential match with gloss-word or gloss-word's index in gloss.")
        # remove all matches as they are duplicates of morphemes already represented in larger words
        # NOTE: this could be changed if it's found to be useful to retain these tagged morphemes
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
            tags_rating += 10000
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

# tglos = 4
# test_on = glosslist[tglos:tglos + 1]
# print(matchword_levdist(map_glosswords(test_on[0], wordslist[tglos])))

# tglos = 14
# test_on = glosslist[tglos:tglos + 1]
# print(matchword_levdist(map_glosswords(test_on[0], wordslist[tglos])))

# tglos = 15
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

# tglos = 94
# test_on = glosslist[tglos:tglos + 1]
# print(matchword_levdist(map_glosswords(test_on[0], wordslist[tglos])))

# tglos = 156
# test_on = glosslist[tglos:tglos + 1]
# print(matchword_levdist(map_glosswords(test_on[0], wordslist[tglos])))

# tglos = 180
# test_on = glosslist[tglos:tglos + 1]
# print(matchword_levdist(map_glosswords(test_on[0], wordslist[tglos])))

# tglos = 226
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

# tglos = 2761
# test_on = glosslist[tglos:tglos + 1]
# print(matchword_levdist(map_glosswords(test_on[0], wordslist[tglos])))

# # Test edit distance function on a range of glosses
# test_on = glosslist
# start_gloss = 0
# stop_gloss = 27
# for glossnum in range(start_gloss, stop_gloss):
#     print(glossnum, matchword_levdist(map_glosswords(test_on[glossnum], wordslist[glossnum])))

# Test edit distance function on all glosses
test_on = glosslist
for glossnum, gloss in enumerate(test_on):
    check = matchword_levdist(map_glosswords(gloss, wordslist[glossnum]))
    if check:
        print(glossnum, check)
        # pass


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

