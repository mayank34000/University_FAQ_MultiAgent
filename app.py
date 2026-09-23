from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    session,
    make_response,
)

from dotenv import load_dotenv

load_dotenv()

import os

from auth import auth_bp, login_required
from db import init_db

from agents.router import (
    handle_question,
    generate_follow_up_questions,
)


# =========================================================
# FLASK APP
# =========================================================

app = Flask(
    __name__,
    template_folder="frontend/templates",
    static_folder="frontend/static",
)


# =========================================================
# SECRET KEY
# =========================================================

secret = os.environ.get("SECRET_KEY")

if not secret:
    raise RuntimeError(
        "SECRET_KEY environment variable is not set!"
    )

app.secret_key = secret


# =========================================================
# SESSION CONFIGURATION
# =========================================================

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)


# =========================================================
# DATABASE
# =========================================================

init_db()


# =========================================================
# AUTH BLUEPRINT
# =========================================================

app.register_blueprint(auth_bp)


# =========================================================
# MAIN ASSISTANT PAGE
# =========================================================

@app.route("/")
@login_required
def index():

    response = make_response(
        render_template("index.html")
    )

    # Prevent browser from restoring the authenticated
    # assistant page after logout.
    response.headers["Cache-Control"] = (
        "no-store, no-cache, must-revalidate, max-age=0"
    )

    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


# =========================================================
# ASK API
# =========================================================

@app.route("/api/ask", methods=["POST"])
@login_required
def ask():

    try:

        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "error": "No request data received."
            }), 400

        question = data.get(
            "question",
            ""
        ).strip()

        if not question:
            return jsonify({
                "error": "Please enter a question."
            }), 400

        # -----------------------------------------
        # Get answer from multi-agent system
        # -----------------------------------------

        result = handle_question(question)

        # Make sure result is always a dictionary
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
        # Follow-up questions
        # -----------------------------------------

        follow_ups = (
            result.get("follow_up_questions")
            or result.get("follow_ups")
            or result.get("followups")
            or []
        )

        # Generate follow-ups if they were not
        # returned by handle_question()
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
        if not isinstance(
            follow_ups,
            list
        ):

            follow_ups = []

        # -----------------------------------------
        # Sources / References
        # -----------------------------------------

        sources = (
            result.get("sources")
            or result.get("references")
            or []
        )

        if not isinstance(
            sources,
            list
        ):

            sources = []

        # -----------------------------------------
        # Final response
        # -----------------------------------------

        response_data = {
            "answer": answer,
            "agent": agent,
            "follow_up_questions": follow_ups,
            "sources": sources,
        }

        print(
            "\n========== API RESPONSE =========="
        )

        print(
            "Question:",
            question
        )

        print(
            "Agent:",
            agent
        )

        print(
            "Answer:",
            answer
        )

        print(
            "Follow-ups:",
            follow_ups
        )

        print(
            "Sources:",
            sources
        )

        print(
            "==================================\n"
        )

        return jsonify(
            response_data
        )

    except Exception as e:

        print(
            "\n========== API ERROR =========="
        )

        print(e)

        print(
            "===============================\n"
        )

        return jsonify({
            "error": str(e)
        }), 500


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )
