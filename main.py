from agents.router import handle_question


def main():
    print("University FAQ Assistant")
    print("Type 'exit' to quit.\n")

    while True:
        question = input("Ask a question: ").strip()

        if question.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        if not question:
            continue

        try:
            result = handle_question(question)

            print("\nAnswer:")

            if isinstance(result, dict):
                answer = result.get("answer", "")
                follow_ups = result.get("follow_up_questions", [])

                print(answer)

                if follow_ups:
                    print("\nFollow-up questions:")

                    for i, follow_up in enumerate(follow_ups[:3], 1):
                        print(f"{i}. {follow_up}")

            else:
                print(result)

            print()

        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()