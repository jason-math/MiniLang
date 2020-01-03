import lang

while True:
    text = input('> ')
    result, error = lang.run('<std_in>', text)

    if error:
        print(error.to_string())
    elif result:
        print(result)
