import lang

while True:
    text = input('> ')
    result, error = lang.run('<st_din>', text)
    if error:
        print(error.to_string())
    elif result:
        print(result)
