"""Level 1."""

from functools import lru_cache
import pandas as pd
import matplotlib.pyplot as plt


@lru_cache(maxsize=250)
def open_xlsx(filename, sheet=None, droplist=None):
    dataframe = pd.read_excel(filename + ".xlsx", sheet_name=sheet, index_col=None, na_values=['NA'])
    if droplist:
        dataframe = dataframe.drop(list(droplist), axis=1)
    return dataframe


@lru_cache(maxsize=250)
def list_xlsx(filename, sheet=None, droplist=None):
    dataframe = open_xlsx(filename, sheet, droplist)
    datalist = dataframe.values.tolist()
    return datalist


# glosses_df = open_xlsx("glosses_full", "glosses")
# words_df = open_xlsx("glosses_words", "words")
#
# print(glosses_df.head())
# print(glosses_df.info())
# print(glosses_df.drop(["recordID", "book", "subsection", "code", "ms_num", "keil_vol", "keil_page", "keil_line",
#                        "types", "keil_ref", "thesaurus_page"], axis=1).head())
# plt.show(pd.value_counts(glosses_df['has_analysis']).plot.bar())


# drop_tup = ("recordID", "book", "subsection", "code", "ms_num", "keil_vol", "keil_page", "keil_line", "types",
#             "keil_ref", "thesaurus_page")
#
# list_glosses = list_xlsx("glosses_full", "glosses", drop_tup)
# list_words = list_xlsx("glosses_words", "words")
#
# for dlist in list_glosses:
#     print(dlist)
#
# for dlist in list_words:
#     print(dlist)

