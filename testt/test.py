from rag.intent_classifier import detect_intent

while True:
    question = input("Question: ")

    if question.lower() == "exit":
        break

    print("Intent:", detect_intent(question))