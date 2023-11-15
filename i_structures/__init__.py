
def html_formula(given_string):

    sub, formula = False, ''

    for token in given_string:
        if token.isdigit() or token == '.' or token == '-':
            if not sub:
                formula += '<sub>'
                sub = True
        else:
            if sub and token != 'd':
                formula += '</sub>'
                sub = False
        formula += token

    if sub:
        formula += '</sub>'

    return formula


def latex_formula(given_string):

    sub, formula = False, ''

    for token in given_string:
        if token.isdigit() or token == '.' or token == '-':
            if not sub:
                formula += '_{'
                sub = True
        else:
            if sub and token != 'd':
                formula += '}'
                sub = False
        formula += token

    if sub:
        formula += '}'

    return '$' + formula + '$'


def html_to_latex(given_string):

    return '$' + given_string.replace('<sub>', '_{').replace('</sub>', '}') + '$'
