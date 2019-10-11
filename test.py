"""Level ."""

"""   
   Find all consecutive cleaned words in each gloss
   
   Use above to isolate OI material
   
   Split glosses into gloss-lists on non-OI material
   
   Match tokenisation of OI material in gloss-lists to words
   
   Impliment appropriate spacing in gloss-lists based on tokenisation
   
   Sequence gloss-lists
"""

from functools import lru_cache
from Pickle import open_obj
from OpenXlsx import list_xlsx

glossdict = open_obj("Clean_GlossDict.pkl")
analyses = list_xlsx("SG. Combined Data", "Sheet 1")

for i in range(10):
    print(analyses[i])

