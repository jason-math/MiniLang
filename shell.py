import lang

while True:
    text = input('> ')
    if text.strip() == "":
        continue
    result, error = lang.run('<st_din>', text)
    if error:
        print(error.to_string())
    elif result:
        if len(result.elements) == 1:
            print(repr(result.elements[0]))
        else:
            print(repr(result))
