"""Level 1."""

from functools import lru_cache
import docx


@lru_cache(maxsize=250)
def open_docx(filename):
    """Opens the document containing the glosses and returns the full text"""
    file = docx.Document(filename + ".docx")
    lines = []
    for para in file.paragraphs:
        lines.append(para.text)
    return '\n'.join(lines)


# print(open_docx("Wurzburg Glosses"))
