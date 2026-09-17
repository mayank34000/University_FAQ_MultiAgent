from flask import Flask, jsonify, render_template, request

from agents.router import (
    handle_question,
    generate_follow_up_questions,
)


app = Flask(
    __name__,
    template_folder="frontend/templates",
    static_folder="frontend/static",
)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "error": "No request data received."
            }), 400

        question = data.get("question", "").strip()

        if not question:
            return jsonify({
                "error": "Please enter a question."
            }), 400

        # -----------------------------------------
        # Get answer from the multi-agent system
        # -----------------------------------------

        result = handle_question(question)

        # Make sure we always have a dictionary
        if not isinstance(result, dict):
            result = {
                "answer": str(result)
            }

        answer = (
            result.get("answer")
            or result.get("response")
            or result.get("message")
            or ""
        )

        agent = (
            result.get("agent")
            or result.get("route")
            or result.get("domain")
            or ""
        )

        # -----------------------------------------
        # Get follow-up questions
        # -----------------------------------------

        follow_ups = (
            result.get("follow_up_questions")
            or result.get("follow_ups")
            or result.get("followups")
            or []
        )

        # If handle_question did not return follow-ups,
        # generate them here.
        if not follow_ups:
            try:
                follow_ups = generate_follow_up_questions(
                    question,
                    answer
                )
            except Exception as followup_error:
                print(
                    "FOLLOW-UP ERROR:",
                    followup_error
                )
                follow_ups = []

        # Make sure follow-ups are a list
        if not isinstance(follow_ups, list):
            follow_ups = []

        # -----------------------------------------
        # Sources / references
        # -----------------------------------------

        sources = (
            result.get("sources")
            or result.get("references")
            or []
        )

        if not isinstance(sources, list):
            sources = []

        # -----------------------------------------
        # Final response to frontend
        # -----------------------------------------

        response_data = {
            "answer": answer,
            "agent": agent,
            "follow_up_questions": follow_ups,
            "sources": sources,
        }

        print("\n========== API RESPONSE ==========")
        print("Question:", question)
        print("Agent:", agent)
        print("Answer:", answer)
        print("Follow-ups:", follow_ups)
        print("Sources:", sources)
        print("==================================\n")

        return jsonify(response_data)

    except Exception as e:
        print("\n========== API ERROR ==========")
        print(e)
        print("===============================\n")

        return jsonify({
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )