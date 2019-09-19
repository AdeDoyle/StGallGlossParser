"""Level 1."""

import pickle
import os


def save_obj(filename, obj):
    """Creates a pickle file containing a given object.
       If the chosen filename already exists, instead of overwriting it, the new filename will be numbered."""
    newfilename = filename
    curdir = os.getcwd()
    exists = os.path.isfile(curdir + "/" + filename + ".pkl")
    filenamelen = len(filename)
    if exists:
        filecount = 0
        while exists:
            newfilename = filename[:filenamelen] + str(filecount)
            exists = os.path.isfile(curdir + "/" + newfilename + ".pkl")
            filecount += 1
    filename = newfilename
    outfile = open("{}.pkl".format(filename), 'wb')
    pickle.dump(obj, outfile)
    outfile.close()


def open_obj(filename):
    """Opens a previously saved pickle file as a python object."""
    infile = open(filename, 'rb')
    this_obj = pickle.load(infile)
    infile.close()
    return this_obj

