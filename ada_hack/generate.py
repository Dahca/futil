#! /usr/bin/python3
import sys
import json
import jinja2
from jinja2 import Template

width = {
    "int": 32,
}
size = {
    "int": 1,
}
index_width = {
    "int": 1,
}

def generate_const(reg, prog, statement):
    reg_type = prog['locals'][reg]
    w = width[reg_type]
    value = statement['value']['value']
    lines = []
    port = f"{w}'d{value}"

    return port, lines

def assign_reg(gname, prog, statement):
    reg = statement['name']
    value = statement['value']
    lines = []

    lines += [ f"{gname}[done] = {reg}.done;" ]
    lines += [ f"{reg}.write_en = 1'd1;"]

    port = None
    if value['type'] == 'const':
        port, sublines = generate_const(reg, prog, statement)

    lines += sublines
    lines += [ f"{reg}.in = {port};"]

    return {'name': gname, 'lines': lines}

def gen_group(gname, prog, statement):
    typ = statement['type']
    if typ == 'assignment':
        name = statement['name']
        if name in prog['locals']:
            # We know it's a register
            return assign_reg(gname, prog, statement)
    return None

def generate_groups(prog):
    groups = []
    for group_num, statement in enumerate(prog['statements']):
        name = f'group_{group_num}'
        group = gen_group(name, prog, statement)
        if group is not None:
            groups += [group]

    return groups

def generate(prog): 
    tmpl_file = sys.argv[1]

    groups = generate_groups(prog)

    futil = None
    with open(tmpl_file) as f:
        tmpl = Template(f.read())
        futil = tmpl.render(
            prog=prog,
            width=width,
            size=size,
            index_width=index_width,
            groups=groups
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