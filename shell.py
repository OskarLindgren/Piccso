import piccso

while True:
    text = input("Piccso > ")
    result, error = piccso.run("<stdin>", text)

    if error:
        print(error.as_string())
    else:
        print(result)