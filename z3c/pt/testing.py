import expressions

def value(string):
    translator = expressions.PythonTranslation()
    return translator.value(string)
