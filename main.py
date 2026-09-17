from agents.router import handle_question, generate_follow_up_questions


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

            # Get the answer
            if isinstance(result, dict):
                answer = result.get("answer", "")
                follow_ups = result.get("follow_up_questions", [])
            else:
                answer = result
                follow_ups = []

            print("\nAnswer:")
            print(answer)

            # Generate follow-up questions if they weren't returned
            if not follow_ups:
                follow_ups = generate_follow_up_questions(
                    question,
                    answer
                )

            if follow_ups:
                print("\nFollow-up questions:")
                for i, follow_up in enumerate(follow_ups, 1):
                    print(f"{i}. {follow_up}")

            print()

        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()