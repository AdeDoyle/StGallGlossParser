from conllu import parse, TokenList
from collections import OrderedDict
import re


def get_pos(sent):
    pospat = re.compile(r'<[A-Z]+[ >]')
    pospatitir = pospat.finditer(sent)
    for posfind in pospatitir:
        pos = posfind.group()[1:-1]
        return pos


def get_feats(sent):
    featspat = re.compile(r' [\w\d =|]+>')
    featspatitir = featspat.finditer(sent)
    feats = None
    for featsfind in featspatitir:
        feats = featsfind.group()[1:-1]
        feats = feats.split(" | ")
    if feats:
        feats = OrderedDict({i.split("=")[0]: i.split("=")[1] for i in feats})
    return feats


def compile_sent(sent):
    sent_list = list()
    for i, tok_data in enumerate(sent):
        tok_id = i + 1
        tok = tok_data[0]
        pos = get_pos(tok_data[1])
        feats = get_feats(tok_data[1])
        compiled_tok = OrderedDict({'id': tok_id, 'form': tok, 'lemma': tok, 'upostag': pos, 'xpostag': None,
                                    'feats': feats, 'head': None, 'deprel': None, 'deps': None, 'misc': None})
        sent_list.append(compiled_tok)
    sent_list = TokenList(sent_list).serialize()
    return sent_list


# #                                                  Test Functions

# s1 = [['.i.', '<SYM Abbr=Yes>'], ['cid', '<AUX Polarity=Pos | VerbType=Cop>'], ['bec', '<ADJ>'],
#       ['cid', '<AUX Polarity=Pos | VerbType=Cop>'], ['mar', '<ADJ>'],
#       ['ind', '<DET Case=Nom | Gender=Fem | Number=Sing>'], ['inducbál', '<NOUN>'],
#       ['ó', '<ADP AdpType=Prep | Definite=Ind>'], ['dia', '<NOUN>'], ['tar', '<ADP AdpType=Prep | Definite=Ind>'],
#       ['hési', '<NOUN>'], ['denmo', '<NOUN>'], ['ind', '<DET Case=Gen | Gender=Masc | Number=Sing>'],
#       ['libuir', '<NOUN>'], ['bith', '<AUX Polarity=Pos | VerbType=Cop>'], ['má', '<ADJ>'], ['de', '<PRON>'],
#       ['do', '<ADP AdpType=Prep | Definite=Ind>'], ['buith', '<NOUN>'], ['dait', '<PRON>'], ['siu', '<PRON>'],
#       ['hi', '<ADP AdpType=Prep | Definite=Ind>'], ['coimthecht', '<NOUN>'], ['oco', '<PRON>']]
# s2 = [['buaid', '<NOUN>'], ['lie', '<NOUN>'], ['vel', '<X>'], ['lapis', '<X>'], ['victorie', '<X>']]

# # test get_pos() and get_feats() functions
# test_tok = 0
# print(s1[test_tok][0])
# print(get_pos(s1[test_tok][1]))
# print(get_feats(s1[test_tok][1]))

# # test compile_sent() function
# print(compile_sent(s1))

# sent1 = [[i[0] for i in s1], [i[1] for i in s1]]
# for i in sent1:
#     fullpos = i[1]
#
# sent2 = [[i[0] for i in s2], [i[1] for i in s2]]

# #                                                  Test conllu Library

# data = """
# # id = 15b11
# # text = buaid lie ɫ lapis victorie
# 1   buaid      búaid   NOUN   _   _   _   _   _   _
# 2   lie        lía     NOUN   _   _   _   _   _   _
# 3   vel        _       X      _   _   _   _   _   _
# 4   lapis      _       X      _   _   _   _   _   _
# 5   victorie   _       X      _   _   _   _   _   _
#
# # id = 2a7
# # text = .i. cid bec cid mar indinducbál ó dia tarhési denmo ind libuir bith má de do buith daitsiu hi coimthecht oco ·'
# 1   .            .            PUNCT   _    PunctSide=Ini                          _   _       _   SpaceAfter=No
# 2   i            i            ADV     _    Abbr=Yes                               _   _       _   SpaceAfter=No
# 3   .            .            PUNCT   _    PunctSide=Fin                          _   _       _   _
# 4   cid          cid          AUX     _    Polarity=Pos | VerbType=Cop            _   _       _   _
# 5   bec          bec          ADJ     _    _                                      _   _       _   _
# 6   cid          cid          AUX     _    Polarity=Pos | VerbType=Cop            _   _       _   _
# 7   mar          mór          ADJ     _    _                                      _   _       _   _
# 8   ind          in           DET     _    Case=Nom | Gender=Fem | Number=Sing    _   _       _   SpaceAfter=No
# 9   inducbál     inducbál     NOUN    _    _                                      _   _       _   _
# 10  ó            ó            ADP     _    AdpType=Prep | Definite=Ind            _   _       _   _
# 11  dia          día          NOUN    _    _                                      _   _       _   _
# 12  tar          tar          ADP     _    AdpType=Prep | Definite=Ind            _   _       _   SpaceAfter=No
# 13  hési         éis          NOUN    _    _                                      _   _       _   _
# 14  denmo        dénum        NOUN    _    _                                      _   _       _   _
# 15  ind          in           DET     _    Case=Gen | Gender=Masc | Number=Sing   _   _       _   _
# 16  libuir       lebor        NOUN    _    _                                      _   _       _   _
# 17  bith         is           AUX     _    Polarity=Pos | VerbType=Cop            _   _       _   _
# 18  má           mór          ADJ     _    _                                      _   _       _   _
# 19  de           de           PRON    _    _                                      _   _       _   _
# 20  do           do           ADP     _    AdpType=Prep | Definite=Ind            _   _       _   _
# 21  buith        both         NOUN    _    _                                      _   _       _   _
# 22  dait         dait         PRON    _    _                                      _   _       _   SpaceAfter=No
# 23  siu          so           PRON    _    _                                      _   _       _   _
# 24  hi           i            ADP     _    AdpType=Prep | Definite=Ind            _   _       _   _
# 25  coimthecht   coimitecht   NOUN    _    _                                      _   _       _   _
# 26  oco          oc           PRON    _    _                                      _   _       _   _
#
# """

# sentences = parse(data)
# sentence_1 = sentences[0]
# sentence_2 = sentences[1]
# print(sentence_1)
# print(sentence_2)
# token = sentence_1[0]
# print(token)
# print(sentence_1.serialize())
# print(sentence_2.serialize())

# file_test = sentence_1.serialize() + sentence_2.serialize()
# with open("Test.conllu", "w") as text_file:
#     print(f"{file_test}", file=text_file)

