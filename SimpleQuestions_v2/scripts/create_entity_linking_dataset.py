#!/usr/bin/python

import os
import sys
import argparse

from subprocess import call

def execute_shell_command(command):
  print(command)
  try:
    call(command, shell=True)
  except Exception as e:
    print("ERROR: executing shell command:\n{}".format(command))
    print(e)
    sys.exit()

def combine_datasets(dirpath, allpath):
    print("combining datasets...")
    files = [("annotated_fb_data_train", "train"), ("annotated_fb_data_valid", "val"), ("annotated_fb_data_test", "test")]
    for f_tuple in files:
        f = f_tuple[0]
        fname = f_tuple[1]
        fpath = os.path.join(dirpath, f + ".txt")
        fpath_numbered = os.path.join(dirpath, f + "_numbered.txt")
        numbered_command = "awk '{{printf(\"{}-%d\\t%s\\n\", NR, $0)}}' {} > {}".format(fname, fpath, fpath_numbered)
        execute_shell_command(numbered_command)
        append_command = "cat {} >> {}".format(fpath_numbered, allpath)
        execute_shell_command(append_command)

def www2fb(in_str):
    if in_str.startswith("www.freebase.com"):
        return 'fb:%s' % (in_str.split('www.freebase.com/')[-1].replace('/', '.'))
    return in_str

def clean_uri(uri):
    if uri.startswith("<") and uri.endswith(">"):
        return clean_uri(uri[1:-1])
    elif uri.startswith("\"") and uri.endswith("\""):
        return clean_uri(uri[1:-1])
    return uri

def get_names_for_entities(namespath):
    print("getting names map...")
    names = {}
    with open(namespath, 'r') as f:
        for i, line in enumerate(f):
            if i % 1000000 == 0:
                print("line: {}".format(i))

            items = line.strip().split("\t")
            if len(items) != 4:
                print("ERROR: line - {}".format(line))
            entity = clean_uri(items[0])
            type = clean_uri(items[1])
            literal = clean_uri(items[2])
            if entity not in names.keys():
                names[entity] = [literal]
            else:
                names[entity].append(literal)
    return names

def create_entity_linking_dataset(datapath, namespath, outpath):
    names_map = get_names_for_entities(namespath)
    notfound = 0
    total = 0
    outfile = open(outpath, 'w')
    with open(datapath, 'r') as f:
        for i, line in enumerate(f):
            total += 1
            if i % 1000000 == 0:
                print("line: {}".format(i))

            items = line.strip().split("\t")
            if len(items) != 4:
                print("ERROR: line - {}".format(line))
            lineid = items[0]
            subject = www2fb(items[1])
            predicate = www2fb(items[2])
            object = www2fb(items[3])
            question = items[4]
            if subject not in names_map.keys():
                print("WARNING: name not found in map. line - {}".format(line))
                notfound += 1
                names_map[subject] = []

            line_to_write = "{} %%%% {} %%%% {} %%%% {} %%%% {} %%%% {}\n".format(lineid, subject, predicate, object, question,
                                                                                    " &&&& ".join(names_map[subject]))
            # print(line_to_write)
            outfile.write(line_to_write)

    print("notfound: {}".format(notfound))
    print("found: {}".format(total-notfound))
    outfile.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Augment Freebase subset to include additional fields')
    parser.add_argument('-d', '--dataset', dest='dataset', action='store', required = True,
                        help='path to the dataset directory - contains train, valid, test files')
    parser.add_argument('-n', '--names', dest='names', action='store', required=True,
                        help='path to the names file (from CFO)')
    parser.add_argument('-o', '--output', dest='output', action='store', required=True,
                        help='output file')

    args = parser.parse_args()
    print("Dataset: {}".format(args.dataset))
    print("Names: {}".format(args.names))
    print("Output: {}".format(args.output))
    allpath = os.path.join(args.dataset, "all-data-numbered.txt")
    if not os.path.isfile(allpath):
        combine_datasets(args.dataset, allpath)
    create_entity_linking_dataset(allpath, args.names, args.output)
    print("Created the dataset for entity linking.")
