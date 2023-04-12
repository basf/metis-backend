def html_formula(string):
    sub, formula = False, ""
    for symb in string:
        if symb.isdigit() or symb == "." or symb == "-":
            if not sub:
                formula += "<sub>"
                sub = True
        else:
            if sub and symb != "d":
                formula += "</sub>"
                sub = False
        formula += symb
    if sub:
        formula += "</sub>"
    return formula
