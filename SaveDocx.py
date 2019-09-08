"""Level 1"""

from docx import Document
import os


def save_docx(content, docname="New Doc"):
    """Saves content as text in a .docx document file. If a file already exists in the directory with the selected
       filename, the name is edited by adding a number to the end of it before saving. This prevents files with the same
       name from being overwritten"""
    newdocname = docname
    docnamelen = len(docname)
    doc = Document()
    curdir = os.getcwd()
    exists = os.path.isfile(curdir + "/" + docname + ".docx")
    doc.add_paragraph(content)
    if exists:
        doccount = 0
        while exists:
            newdocname = docname[:docnamelen] + str(doccount)
            exists = os.path.isfile(curdir + "/" + newdocname + ".docx")
            doccount += 1
    docname = newdocname
    doc.save(docname + ".docx")


# testdoc = """This is the title
#
# This is the secondary title
#
# Para 1 Line 1
# Para 1 Line 2
#
# Para 2 Line 1
# Para 2 Line 2"""
# save_docx(testdoc, "mydoc")
