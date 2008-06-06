import expressions

def pyexp(string):
    translator = expressions.PythonTranslation()
    return translator.expression(string)
