#! /usr/bin/python3
import sys
import json
import jinja2
from jinja2 import Template

def generate(prog): 
    tmpl_file = sys.argv[1]
    width = {
        "int": 32,
    }
    size = {
        "int": 1,
    }
    index_width = {
        "int": 1,
    }

    futil = None
    with open(tmpl_file) as f:
        tmpl = Template(f.read())
        futil = tmpl.render(
            prog=prog,
            width=width,
            size=size,
            index_width=index_width
        )

    outfile = sys.argv[3]
    with open(outfile, 'w') as f:
        f.write(futil)


def main():
    fname = sys.argv[2]
    with open(fname) as f:
        prog = json.load(f)

    generate(prog)

if __name__ == '__main__':
    main()