"""Level 1"""

import xlsxwriter
import os


def save_xlsx(filename, datalists, headers=False):
    """Takes a list (datalists) of data-lists and creates a table where each data-list is a new row in the table. Saves
       the table as a .xlsx document. Each data-list must be the same length. If a file already exists in the directory
       with the selected filename, the name is edited by adding a number to the end of it before saving. This prevents
       files with the same name from being overwritten."""
    newfilename = filename
    curdir = os.getcwd()
    exists = os.path.isfile(curdir + "/" + filename + ".xlsx")
    filenamelen = len(filename)
    if exists:
        filecount = 0
        while exists:
            newfilename = filename[:filenamelen] + str(filecount)
            exists = os.path.isfile(curdir + "/" + newfilename + ".xlsx")
            filecount += 1
    filename = newfilename + ".xlsx"
    wb = xlsxwriter.Workbook(filename)
    ws = wb.add_worksheet("Sheet 1")
    header = wb.add_format({"bold": True})
    firstlen = len(datalists[0])
    for datalist in datalists:
        if len(datalist) != firstlen:
            raise RuntimeError("Error: Uneven Row Lengths in Table.")
    cols = firstlen
    rows = len(datalists)
    for row in range(rows):
        data = datalists[row]
        for col in range(cols):
            datum = data[col]
            if row == 0 and headers:
                ws.write(row, col, datum, header)
            else:
                ws.write(row, col, datum)
    wb.close()


# save_xlsx("test workbook", [["FirstNo", "SecondNo", "ThirdNo"], [1, 2, 3], [4, 5, 6], [7, 8, 9]], True)
# save_xlsx("test workbook", [["FirstNo", "SecondNo", "ThirdNo"], [9, 8, 7], [6, 5, 4], [3, 2, 1]])
