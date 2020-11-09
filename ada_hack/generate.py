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


def get_reg_width(prog, reg):
    reg_type = prog['locals'][reg]
    return width[reg_type]


def generate_const(gname, reg, prog, value):
    reg_type = prog['locals'][reg]
    w = width[reg_type]
    v = value['value']

    port = f"{w}'d{v}"
    lines = []
    cells = []

    return port, lines, cells


def generate_indentifier(gname, reg, prog, value):
    name = value['name']
    if name in prog['locals']:
        port = f"{name}.out"
    else:
        port = f"{name}.read_data"

    lines = []
    cells = []

    return port, lines, cells


def generate_binary(gname, reg, prog, value):
    op = value['op']
    left = value['left']
    right = value['right']

    lport, llines, lcells = generate_value(gname, reg, prog, left)
    rport, rlines, rcells = generate_value(gname, reg, prog, right)

    cells = lcells + rcells
    lines = llines + rlines
    regw = get_reg_width(prog, reg)

    aname = f"{gname}_add"

    if op == 'plus':
        cells += [f"{aname} = prim std_add({regw});"]

    lines += [f"{aname}.left = {lport};"]
    lines += [f"{aname}.right = {rport};"]

    port = f"{aname}.out"
    return port, lines, cells


def generate_value(gname, reg, prog, value):
    if value['type'] == 'const':
        return generate_const(gname, reg, prog, value)
    elif value['type'] == 'binary':
        return generate_binary(gname, reg, prog, value)
    elif value['type'] == 'identifier':
        return generate_indentifier(gname, reg, prog, value)
    else:
        print(value)
        return None, None, None


def assign_reg(gname, prog, statement):
    reg = statement['name']
    value = statement['value']
    lines = []

    lines += [f"{gname}[done] = {reg}.done;"]
    lines += [f"{reg}.write_en = 1'd1;"]

    port, sublines, cells = generate_value(gname, reg, prog, value)

    lines += sublines
    lines += [f"{reg}.in = {port};"]

    return {
        'name': gname,
        'lines': lines,
        'control': {"operator": 'enable', "group": gname}
    }, cells


def generate_while(gname, prog, statement):
    return {
        'name': gname,
        'lines': [],
        'control': {"operator": 'while', "body": []}
    }, None


def gen_group(gname, prog, statement):
    typ = statement['type']
    if typ == 'assignment':
        name = statement['name']
        if name in prog['locals']:
            # We know it's a register
            return assign_reg(gname, prog, statement)
    elif typ == 'while':
        return generate_while(gname, prog, statement)
    return None, None


def generate_groups(prog):
    groups = []
    cells = []
    for group_num, statement in enumerate(prog['statements']):
        name = f'group_{group_num}'
        group, gcells = gen_group(name, prog, statement)
        if group is not None:
            groups += [group]
            cells += gcells

    return groups, cells


def make_control(groups):
    seq = []
    for g in groups:
        control = g['control']
        if control['operator'] == 'enable':
            seq += [f"{control['group']};"]
        elif control['operator'] == 'while':
            body = [make_control(x) for x in control['body']]
            seq += [f""" while {control['port']} with {control['group']} {{
{body}
}}"""]
        else:
            pass
    return seq


def generate(prog):
    tmpl_file = sys.argv[1]

    groups, cells = generate_groups(prog)
    control = make_control(groups)

    futil = None
    with open(tmpl_file) as f:
        tmpl = Template(f.read())
        futil = tmpl.render(
            prog=prog,
            width=width,
            size=size,
            index_width=index_width,
            groups=groups,
            cells=cells,
            control=control
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
