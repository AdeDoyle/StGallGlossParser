
import os
from conllu import parse


def test_conllu():
    """Tests Sg. files against those available in UD to ensure consistency"""

    # Navigate to a directory containing a JSON file of the Wb. Glosses and CoNLL_U files of the Sg. Glosses
    maindir = os.getcwd()
    files_dir = os.path.join(maindir, "check files")
    base_files = os.path.join(files_dir, "base files")
    comp_files = os.path.join(files_dir, "compare files")

    # Ensure that the correct folder structure is present. If not, create it.
    try:
        os.chdir(files_dir)
    except FileNotFoundError:
        os.mkdir("check files")
        os.chdir(files_dir)
    try:
        os.chdir(base_files)
    except FileNotFoundError:
        os.mkdir("base files")
        os.chdir(base_files)
    try:
        os.chdir(comp_files)
    except FileNotFoundError:
        os.chdir(files_dir)
        os.mkdir("compare files")
        os.chdir(comp_files)
    os.chdir(maindir)

    # Ensure files exist in both the base and comparison folders
    if len(os.listdir(base_files)) == 0:
        raise RuntimeError(f"No files in directory: {base_files}")
    if len(os.listdir(comp_files)) == 0:
        raise RuntimeError(f"No files in directory: {comp_files}")

    base_file_contents = dict()

    # For each current UD file (test and incomplete)
    for conllu_file in os.listdir(base_files):
        if conllu_file[-7:] == ".conllu" and "combined_POS" not in conllu_file:

            # Parse the .conllu file, and add its contents to a list of base-file contents
            with open(os.path.join(base_files, conllu_file), "r", encoding="utf-8") as conllu_file_import:
                base_data = conllu_file_import.read()
            file_data = parse(base_data)
            base_file_contents[conllu_file] = file_data

    comp_file_contents = dict()

    # For each potentially divergent conllu file in the comparison files folder
    for conllu_file in os.listdir(comp_files):
        if conllu_file[-7:] == ".conllu" and "combined_POS" not in conllu_file:

            # Parse the .conllu file, and add its contents to a list of base-file contents
            with open(os.path.join(comp_files, conllu_file), "r", encoding="utf-8") as conllu_file_import:
                comp_data = conllu_file_import.read()
            file_data = parse(comp_data)
            comp_file_contents[conllu_file] = file_data

    error_count = 0

    # For each parsed conllu file in the base-file contents list
    for base_file_name in base_file_contents:
        base_file = base_file_contents.get(base_file_name)
        # For each unique gloss ID
        for base_sent in base_file:
            base_toks = [token.get("form") for token in base_sent]
            base_heads = [token.get("lemma") for token in base_sent]
            base_pos = [token.get("upos") for token in base_sent]
            unique_id = base_sent.metadata.get("sent_id")
            # Look for the same unique gloss ID in the check files and compare the contents with the base file
            for check_file_name in comp_file_contents:
                check_file = comp_file_contents.get(check_file_name)
                for check_sent in check_file:
                    check_toks = [token.get("form") for token in check_sent]
                    check_heads = [token.get("lemma") for token in check_sent]
                    check_pos = [token.get("upos") for token in check_sent]
                    check_id = check_sent.metadata.get("sent_id")
                    if check_id == unique_id and base_sent != check_sent:

                        if base_toks != check_toks:
                            error_count += 1
                            print(f"Error (tokens): {error_count}"
                                  f"\nSentence (ID {unique_id}) does not match between files:"
                                  f"\n    {base_file_name}\n    {check_file_name}"
                                  f"\n        {base_toks}"
                                  f"\n        {check_toks}\n")

                        elif base_heads != check_heads:
                            error_count += 1
                            print(f"Error (heads): {error_count}"
                                  f"\nSentence (ID {unique_id}) does not match between files:"
                                  f"\n    {base_file_name}\n    {check_file_name}"
                                  f"\n        {base_heads}"
                                  f"\n        {check_heads}\n")

                        elif base_pos != check_pos:
                            error_count += 1
                            print(f"Error (POS): {error_count}"
                                  f"\nSentence (ID {unique_id}) does not match between files:"
                                  f"\n    {base_file_name}\n    {check_file_name}"
                                  f"\n        {base_pos}"
                                  f"\n        {check_pos}"
                                  f"\n        {base_toks}"
                                  f"\n        {check_toks}\n")

                        # elif base_sent.metadata.get("text") != check_sent.metadata.get("text"):
                        #     error_count += 1
                        #     print(f"Error (text): {error_count}"
                        #           f"\nSentence (ID {unique_id}) does not match between files:"
                        #           f"\n    {base_file_name}\n    {check_file_name}"
                        #           f"\n        {base_sent.metadata.get('text')}"
                        #           f"\n        {check_sent.metadata.get('text')}\n")

    return f"Found {error_count} errors when comparing files."


if __name__ == "__main__":

    print(test_conllu())
