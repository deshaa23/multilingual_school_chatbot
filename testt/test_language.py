from ai.language_detector import get_language

while True:
    question = input("Question: ")

    if question.lower() == "exit":
        break

    print("Language:", get_language(question))