/* =========================================================
   UNIVERSITY FAQ ASSISTANT
   ========================================================= */


/* =========================================================
   ELEMENTS
   ========================================================= */

const form =
    document.getElementById("chatForm");

const input =
    document.getElementById("questionInput");

const sendBtn =
    document.getElementById("sendBtn");

const messages =
    document.getElementById("messages");

const emptyState =
    document.getElementById("emptyState");

const typingIndicator =
    document.getElementById("typingIndicator");

const clearChatBtn =
    document.getElementById("clearChatBtn");

const themeBtn =
    document.getElementById("themeBtn");

const heroAskBtn =
    document.getElementById("heroAskBtn");

const askQuestionBtn =
    document.getElementById("askQuestionBtn");

const contactAskBtn =
    document.getElementById("contactAskBtn");


/* =========================================================
   AGENT NAME
   ========================================================= */

function formatAgent(agent) {

    const names = {

        fees_academics:
            "Fees & Academics Agent",

        placements:
            "Placements Agent",

        campus_hostel:
            "Campus & Hostel Agent",

        unknown:
            "University FAQ Router"

    };

    return names[agent] ||
        agent ||
        "University FAQ Assistant";

}


/* =========================================================
   SCROLL TO CHAT
   ========================================================= */

function openChat() {

    document
        .getElementById("chat")
        .scrollIntoView({
            behavior: "smooth"
        });

    setTimeout(() => {

        input.focus();

    }, 500);

}


/* =========================================================
   ASK QUESTION FROM CATEGORY
   ========================================================= */

function askPresetQuestion(question) {

    document
        .getElementById("chat")
        .scrollIntoView({
            behavior: "smooth"
        });

    setTimeout(() => {

        input.value =
            question;

        resizeInput();

        sendQuestion();

    }, 500);

}


/* =========================================================
   REMOVE EMPTY STATE
   ========================================================= */

function removeEmptyState() {

    const state =
        document.getElementById("emptyState");

    if (state) {

        state.remove();

    }

}


/* =========================================================
   ADD USER MESSAGE
   ========================================================= */

function addUserMessage(question) {

    const row =
        document.createElement("div");

    row.className =
        "message-row user";


    const avatar =
        document.createElement("div");

    avatar.className =
        "user-avatar";

    avatar.innerHTML =
        '<i class="bi bi-person-fill"></i>';


    const content =
        document.createElement("div");

    content.className =
        "message-content";


    const bubble =
        document.createElement("div");

    bubble.className =
        "message-bubble";

    bubble.textContent =
        question;


    content.appendChild(
        bubble
    );

    row.appendChild(
        avatar
    );

    row.appendChild(
        content
    );

    messages.appendChild(
        row
    );


    scrollToBottom();

}


/* =========================================================
   ADD ASSISTANT MESSAGE
   ========================================================= */

function addAssistantMessage(
    answer,
    agent,
    followUps,
    sources
) {

    const row =
        document.createElement("div");

    row.className =
        "message-row assistant";


    /* ---------------------------------------------
       BOT AVATAR
       --------------------------------------------- */

    const avatar =
        document.createElement("div");

    avatar.className =
        "bot-avatar";

    avatar.innerHTML =
        '<i class="bi bi-robot"></i>';


    /* ---------------------------------------------
       CONTENT
       --------------------------------------------- */

    const content =
        document.createElement("div");

    content.className =
        "message-content";


    /* ---------------------------------------------
       ANSWER
       --------------------------------------------- */

    const bubble =
        document.createElement("div");

    bubble.className =
        "message-bubble";

    bubble.textContent =
        answer ||
        "I could not find an answer.";


    content.appendChild(
        bubble
    );


    /* ---------------------------------------------
       AGENT
       --------------------------------------------- */

    if (agent) {

        const agentLabel =
            document.createElement("div");

        agentLabel.className =
            "agent-label";

        const icon =
            document.createElement("i");

        icon.className =
            "bi bi-diagram-3";


        agentLabel.appendChild(
            icon
        );

        agentLabel.appendChild(
            document.createTextNode(
                " " +
                formatAgent(agent)
            )
        );


        content.appendChild(
            agentLabel
        );

    }


    /* ---------------------------------------------
       FOLLOW-UP QUESTIONS
       --------------------------------------------- */

    if (
        Array.isArray(followUps) &&
        followUps.length > 0
    ) {

        const followupBox =
            document.createElement("div");

        followupBox.className =
            "followups";


        const title =
            document.createElement("div");

        title.className =
            "followups-title";

        title.textContent =
            "You may also want to ask:";


        followupBox.appendChild(
            title
        );


        followUps
            .slice(0, 5)
            .forEach(question => {

                if (!question) {
                    return;
                }


                const button =
                    document.createElement("button");

                button.type =
                    "button";

                button.className =
                    "followup-btn";

                button.textContent =
                    question;


                button.addEventListener(
                    "click",
                    () => {

                        input.value =
                            question;

                        resizeInput();

                        sendQuestion();

                    }
                );


                followupBox.appendChild(
                    button
                );

            });


        content.appendChild(
            followupBox
        );

    }


    /* ---------------------------------------------
       SOURCES
       --------------------------------------------- */

    if (
        Array.isArray(sources) &&
        sources.length > 0
    ) {

        const sourceBox =
            document.createElement("div");

        sourceBox.className =
            "sources";


        const title =
            document.createElement("div");

        title.className =
            "sources-title";

        title.textContent =
            "Sources / References";


        sourceBox.appendChild(
            title
        );


        sources
            .slice(0, 5)
            .forEach(source => {

                const item =
                    document.createElement("span");

                item.className =
                    "source-item";


                let sourceName =
                    "Reference";


                if (
                    typeof source === "string"
                ) {

                    sourceName =
                        source;

                }

                else if (
                    source &&
                    typeof source === "object"
                ) {

                    sourceName =
                        source.title ||
                        source.name ||
                        source.id ||
                        "Reference";

                }


                item.innerHTML =
                    '<i class="bi bi-link-45deg"></i>';


                item.appendChild(
                    document.createTextNode(
                        " " + sourceName
                    )
                );


                sourceBox.appendChild(
                    item
                );

            });


        content.appendChild(
            sourceBox
        );

    }


    row.appendChild(
        avatar
    );

    row.appendChild(
        content
    );


    messages.appendChild(
        row
    );


    scrollToBottom();

}


/* =========================================================
   LOADING
   ========================================================= */

function setLoading(isLoading) {

    if (isLoading) {

        typingIndicator.classList.remove(
            "d-none"
        );

    }

    else {

        typingIndicator.classList.add(
            "d-none"
        );

    }


    sendBtn.disabled =
        isLoading;

}


/* =========================================================
   RESIZE TEXTAREA
   ========================================================= */

function resizeInput() {

    input.style.height =
        "auto";

    input.style.height =
        Math.min(
            input.scrollHeight,
            120
        ) + "px";

}


/* =========================================================
   SCROLL CHAT
   ========================================================= */

function scrollToBottom() {

    messages.scrollTo({

        top:
            messages.scrollHeight,

        behavior:
            "smooth"

    });

}


/* =========================================================
   SEND QUESTION
   ========================================================= */

async function sendQuestion() {

    const question =
        input.value.trim();


    if (
        !question ||
        sendBtn.disabled
    ) {

        return;

    }


    removeEmptyState();


    /* Show user question */

    addUserMessage(
        question
    );


    /* Clear input */

    input.value =
        "";

    resizeInput();


    /* Show loading */

    setLoading(
        true
    );


    try {

        const response =
            await fetch(
                "/api/ask",
                {
                    method:
                        "POST",

                    headers:
                        {
                            "Content-Type":
                                "application/json"
                        },

                    body:
                        JSON.stringify({
                            question:
                                question
                        })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Server error."
            );

        }


        /* -----------------------------------------
           Read backend response
           ----------------------------------------- */

        const answer =
            data.answer ||
            data.response ||
            data.message ||
            "No answer was returned.";


        const agent =
            data.agent ||
            data.route ||
            data.domain ||
            "";


        const followUps =
            data.follow_up_questions ||
            data.follow_ups ||
            data.followups ||
            [];


        const sources =
            data.sources ||
            data.references ||
            [];


        console.log(
            "Backend response:",
            data
        );

        console.log(
            "Follow-up questions:",
            followUps
        );


        addAssistantMessage(
            answer,
            agent,
            followUps,
            sources
        );

    }


    catch (error) {

        console.error(
            "Question error:",
            error
        );


        addAssistantMessage(

            "Sorry, I could not process your question.\n\n" +
            error.message,

            "unknown",

            [],

            []

        );

    }


    finally {

        setLoading(
            false
        );

        input.focus();

    }

}


/* =========================================================
   FORM SUBMIT
   ========================================================= */

form.addEventListener(
    "submit",
    event => {

        event.preventDefault();

        sendQuestion();

    }
);


/* =========================================================
   ENTER TO SEND
   ========================================================= */

input.addEventListener(
    "keydown",
    event => {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            sendQuestion();

        }

    }
);


/* =========================================================
   INPUT RESIZE
   ========================================================= */

input.addEventListener(
    "input",
    resizeInput
);


/* =========================================================
   EXAMPLE QUESTIONS
   ========================================================= */

document
    .querySelectorAll(
        ".example-question"
    )
    .forEach(button => {

        button.addEventListener(
            "click",
            () => {

                askPresetQuestion(
                    button.dataset.question
                );

            }
        );

    });


/* =========================================================
   CATEGORY QUESTIONS
   ========================================================= */

document
    .querySelectorAll(
        ".category-card"
    )
    .forEach(button => {

        button.addEventListener(
            "click",
            () => {

                askPresetQuestion(
                    button.dataset.question
                );

            }
        );

    });


/* =========================================================
   ASK BUTTONS
   ========================================================= */

if (heroAskBtn) {

    heroAskBtn.addEventListener(
        "click",
        openChat
    );

}


if (askQuestionBtn) {

    askQuestionBtn.addEventListener(
        "click",
        openChat
    );

}


if (contactAskBtn) {

    contactAskBtn.addEventListener(
        "click",
        openChat
    );

}


/* =========================================================
   CLEAR CHAT
   ========================================================= */

clearChatBtn.addEventListener(
    "click",
    () => {

        window.location.reload();

    }
);


/* =========================================================
   DARK MODE
   ========================================================= */

function updateThemeIcon() {

    const icon =
        themeBtn.querySelector("i");


    if (
        document.body.classList.contains(
            "dark"
        )
    ) {

        icon.className =
            "bi bi-sun";

    }

    else {

        icon.className =
            "bi bi-moon";

    }

}


themeBtn.addEventListener(
    "click",
    () => {

        document.body.classList.toggle(
            "dark"
        );


        const isDark =
            document.body.classList.contains(
                "dark"
            );


        localStorage.setItem(
            "universityFAQTheme",
            isDark
                ? "dark"
                : "light"
        );


        updateThemeIcon();

    }
);


/* =========================================================
   LOAD SAVED THEME
   ========================================================= */

const savedTheme =
    localStorage.getItem(
        "universityFAQTheme"
    );


if (
    savedTheme === "dark"
) {

    document.body.classList.add(
        "dark"
    );

}


updateThemeIcon();


/* =========================================================
   INITIALIZE
   ========================================================= */

resizeInput();