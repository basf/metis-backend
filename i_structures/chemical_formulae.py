# Copyright (c) Evgeny Blokhin, 2016-2019
# Distributed under MIT license, see LICENSE file.

from collections import defaultdict

from pyparsing import (
    Suppress, Regex, Forward, Group, Optional, OneOrMore, oneOf,
    ParseResults,
    ParseException as FormulaError
)
from ase.data import chemical_symbols


mpds_chem_elements = " ".join(chemical_symbols[1:-16] + [chemical_symbols[-8]] + ["D", "T"]) # H - No, Rg, D, T

def get_formula_parser(chemical_tokens):
    LPAR, RPAR = map(Suppress, "[]")
    index = Regex(r"\d+(\.\d*)?").setParseAction(lambda t: float(t[0]))
    element = oneOf(chemical_tokens)
    chemical_formula = Forward()
    term = Group((element | Group(LPAR + chemical_formula + RPAR)("subgroup")) + Optional(index, default=1)("mult"))
    chemical_formula << OneOrMore(term)

    def multiplyContents(tokens):
        t = tokens[0]
        if t.subgroup:
            mult = t.mult
            for term in t.subgroup:
                term[1] *= mult
            return t.subgroup
    term.setParseAction(multiplyContents)

    def sumByElement(tokens):
        elementsList = [t[0] for t in tokens]
        duplicates = len(elementsList) > len(set(elementsList))
        if duplicates:
            ctr = defaultdict(int)
            for t in tokens:
                ctr[t[0]] += t[1]
            return ParseResults([ParseResults([k, v]) for k, v in ctr.items()])
    chemical_formula.setParseAction(sumByElement)

    return chemical_formula


standard_parser = get_formula_parser(mpds_chem_elements)
lowercase_parser = get_formula_parser(mpds_chem_elements.lower())

def parse_formula(aux, lowercase=False, remove_isotopes=True):
    if '(' in aux:
        raise FormulaError('Round brackets are not supported')
    result = lowercase_parser.parseString(aux) if lowercase else standard_parser.parseString(aux)
    result = dict(result.asList())

    if remove_isotopes:
        # take care of D and T
        if 'D' in result or 'T' in result:
            result['H'] = result.get('H', 0.0) + result.get('D', 0.0) + result.get('T', 0.0)

            try: del result['D']
            except KeyError: pass

            try: del result['T']
            except KeyError: pass

    return result