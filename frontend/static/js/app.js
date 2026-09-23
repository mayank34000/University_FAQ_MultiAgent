/* =========================================================
   UNIVERSITY FAQ ASSISTANT
   Frontend only
   Uses the existing Flask POST /api/ask endpoint.
   ========================================================= */

const chatMessages = document.getElementById("chatMessages");
const questionInput = document.getElementById("questionInput");
const sendButton = document.getElementById("sendButton");
const themeToggle = document.getElementById("themeToggle");
const themeIcon = document.getElementById("themeIcon");
const characterCount = document.getElementById("characterCount");
const quickQuestions = document.getElementById("quickQuestions");

let isLoading = false;

/* -------------------------
   Theme
   ------------------------- */

function applyTheme(theme) {
    const dark = theme === "dark";

    document.body.classList.toggle("dark", dark);
    themeIcon.textContent = dark ? "☀" : "☾";
}

function loadTheme() {
    applyTheme(localStorage.getItem("university-faq-theme") || "light");
}

themeToggle.addEventListener("click", () => {
    const nextTheme = document.body.classList.contains("dark")
        ? "light"
        : "dark";

    localStorage.setItem("university-faq-theme", nextTheme);
    applyTheme(nextTheme);
});

/* -------------------------
   Quick questions
   ------------------------- */

document.querySelectorAll(".question-card").forEach((button) => {
    button.addEventListener("click", () => {
        const question = button.dataset.question;
        if (question) askQuestion(question);
    });
});

/* -------------------------
   Input
   ------------------------- */

function updateCounter() {
    characterCount.textContent = `${questionInput.value.length}/500`;
}

function resizeInput() {
    questionInput.style.height = "auto";
    questionInput.style.height =
        `${Math.min(questionInput.scrollHeight, 105)}px`;
}

questionInput.addEventListener("input", () => {
    updateCounter();
    resizeInput();
});

questionInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        askQuestion(questionInput.value);
    }
});

sendButton.addEventListener("click", () => {
    askQuestion(questionInput.value);
});

/* -------------------------
   API
   ------------------------- */

async function askQuestion(rawQuestion) {
    if (isLoading) return;

    const question = String(rawQuestion || "").trim();

    if (!question) {
        questionInput.focus();
        return;
    }

    if (question.length > 500) {
        addSystemMessage("Please keep your question under 500 characters.");
        return;
    }

    isLoading = true;
    sendButton.disabled = true;

    if (quickQuestions) {
        quickQuestions.style.display = "none";
    }

    addUserMessage(question);

    questionInput.value = "";
    questionInput.style.height = "auto";
    updateCounter();

    const typing = addTypingIndicator();
    scrollToBottom();

    try {
        const response = await fetch("/api/ask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: question
            })
        });

        let data = {};

        try {
            data = await response.json();
        } catch {
            throw new Error("The server returned an invalid response.");
        }

        removeElement(typing);

        if (response.status === 401) {
            window.location.href = '/login';
            return;
        }

        if (!response.ok) {
            throw new Error(
                data.error ||
                data.details ||
                "Unable to get an answer."
            );
        }

        const answer = normalizeText(
            data.answer ||
            data.response ||
            data.message ||
            "I couldn't find an answer."
        );

        const followUps = normalizeFollowUps(
            data.follow_up_questions ||
            data.follow_ups ||
            data.followups ||
            []
        );

        const sources = normalizeSources(
            data.sources ||
            data.references ||
            []
        );

        addAssistantMessage(
            answer,
            followUps,
            sources,
            data.agent || ""
        );

    } catch (error) {
        removeElement(typing);

        console.error("API ERROR:", error);

        addSystemMessage(
            error.message ||
            "Something went wrong. Please try again."
        );
    } finally {
        isLoading = false;
        sendButton.disabled = false;
        questionInput.focus();
        scrollToBottom();
    }
}

/* -------------------------
   Normalization
   ------------------------- */

function normalizeText(value) {
    if (value === null || value === undefined) return "";

    if (typeof value === "string") {
        return value.trim();
    }

    if (typeof value === "object") {
        return String(
            value.answer ??
            value.content ??
            value.text ??
            value.response ??
            value.message ??
            ""
        ).trim();
    }

    return String(value).trim();
}

function normalizeFollowUps(value) {
    if (!Array.isArray(value)) return [];

    return value
        .map((item) => {
            if (typeof item === "string") {
                return item.trim();
            }

            if (item && typeof item === "object") {
                return String(
                    item.question ??
                    item.text ??
                    item.content ??
                    item.value ??
                    ""
                ).trim();
            }

            return String(item || "").trim();
        })
        .filter(Boolean)
        .slice(0, 3);
}

function normalizeSources(value) {
    if (!Array.isArray(value)) return [];

    return value
        .map((item) => {
            if (typeof item === "string") return item.trim();

            if (item && typeof item === "object") {
                return String(
                    item.name ??
                    item.title ??
                    item.source ??
                    ""
                ).trim();
            }

            return String(item || "").trim();
        })
        .filter(Boolean);
}

/* -------------------------
   User message
   ------------------------- */

function addUserMessage(question) {
    const row = document.createElement("div");
    row.className = "message-row user-row";

    const column = document.createElement("div");
    column.className = "message-column";

    const bubble = document.createElement("div");
    bubble.className = "bubble user-bubble";

    const paragraph = document.createElement("p");
    paragraph.textContent = question;

    bubble.appendChild(paragraph);

    const label = document.createElement("div");
    label.className = "message-label";
    label.textContent = "You";

    column.appendChild(bubble);
    column.appendChild(label);
    row.appendChild(column);

    chatMessages.appendChild(row);
}

/* -------------------------
   Assistant message
   ------------------------- */

function addAssistantMessage(answer, followUps, sources, agent) {
    const row = document.createElement("div");
    row.className = "message-row assistant-row";

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = "🤖";

    const column = document.createElement("div");
    column.className = "message-column";

    const bubble = document.createElement("div");
    bubble.className = "bubble assistant-bubble";

    renderAnswer(bubble, answer);

    const label = document.createElement("div");
    label.className = "message-label";
    label.textContent = formatAgent(agent);

    column.appendChild(bubble);
    column.appendChild(label);

    if (followUps.length === 3) {
        addFollowUps(column, followUps);
    } else if (followUps.length > 0) {
        addFollowUps(column, followUps);
    }

    if (sources.length > 0) {
        addSources(column, sources);
    }

    row.appendChild(avatar);
    row.appendChild(column);

    chatMessages.appendChild(row);
    scrollToBottom();
}

/* -------------------------
   Answer rendering
   Supports basic markdown:
   headings, bullets, bold.
   No raw HTML is injected.
   ------------------------- */

function renderAnswer(container, answer) {
    const lines = String(answer || "").split(/\r?\n/);

    let list = null;

    const closeList = () => {
        if (list) {
            container.appendChild(list);
            list = null;
        }
    };

    lines.forEach((rawLine) => {
        const line = rawLine.trim();

        if (!line) {
            closeList();
            return;
        }

        if (/^#{1,6}\s+/.test(line)) {
            closeList();

            const heading = document.createElement("p");
            heading.style.fontWeight = "700";
            heading.textContent = line.replace(/^#{1,6}\s+/, "");
            container.appendChild(heading);
            return;
        }

        if (/^[-*•]\s+/.test(line)) {
            if (!list) {
                list = document.createElement("ul");
                list.style.margin = "5px 0 0 18px";
            }

            const li = document.createElement("li");
            li.style.marginBottom = "3px";
            li.appendChild(formatInlineText(
                line.replace(/^[-*•]\s+/, "")
            ));

            list.appendChild(li);
            return;
        }

        closeList();

        const paragraph = document.createElement("p");
        paragraph.appendChild(formatInlineText(line));
        container.appendChild(paragraph);
    });

    closeList();
}

function formatInlineText(text) {
    const fragment = document.createDocumentFragment();
    let remaining = text;

    const regex = /\*\*(.*?)\*\*/g;
    let match;
    let lastIndex = 0;

    while ((match = regex.exec(text)) !== null) {
        if (match.index > lastIndex) {
            fragment.appendChild(
                document.createTextNode(
                    text.slice(lastIndex, match.index)
                )
            );
        }

        const strong = document.createElement("strong");
        strong.textContent = match[1];
        fragment.appendChild(strong);

        lastIndex = regex.lastIndex;
    }

    if (lastIndex < remaining.length) {
        fragment.appendChild(
            document.createTextNode(
                remaining.slice(lastIndex)
            )
        );
    }

    return fragment;
}

/* -------------------------
   Follow-up questions
   ------------------------- */

function addFollowUps(parent, questions) {
    const section = document.createElement("div");
    section.className = "followups";

    const title = document.createElement("div");
    title.className = "followup-title";
    title.textContent = "You may also ask";

    const list = document.createElement("div");
    list.className = "followup-list";

    questions.slice(0, 3).forEach((question) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "followup-button";
        button.textContent = question;

        button.addEventListener("click", () => {
            askQuestion(question);
        });

        list.appendChild(button);
    });

    section.appendChild(title);
    section.appendChild(list);
    parent.appendChild(section);
}

/* -------------------------
   Sources
   ------------------------- */

function addSources(parent, sources) {
    const wrapper = document.createElement("div");
    wrapper.className = "sources";

    sources.forEach((source) => {
        const tag = document.createElement("span");
        tag.className = "source-tag";
        tag.textContent = source;
        wrapper.appendChild(tag);
    });

    parent.appendChild(wrapper);
}

/* -------------------------
   Typing indicator
   ------------------------- */

function addTypingIndicator() {
    const row = document.createElement("div");
    row.className = "message-row assistant-row";

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = "🤖";

    const column = document.createElement("div");
    column.className = "message-column";

    const bubble = document.createElement("div");
    bubble.className = "bubble assistant-bubble";

    const typing = document.createElement("div");
    typing.className = "typing";

    for (let i = 0; i < 3; i++) {
        const dot = document.createElement("span");
        typing.appendChild(dot);
    }

    bubble.appendChild(typing);
    column.appendChild(bubble);
    row.appendChild(avatar);
    row.appendChild(column);

    chatMessages.appendChild(row);

    return row;
}

/* -------------------------
   Error/system message
   ------------------------- */

function addSystemMessage(text) {
    const row = document.createElement("div");
    row.className = "message-row assistant-row";

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = "⚠️";

    const column = document.createElement("div");
    column.className = "message-column";

    const bubble = document.createElement("div");
    bubble.className = "bubble assistant-bubble";

    const paragraph = document.createElement("p");
    paragraph.textContent = text;

    bubble.appendChild(paragraph);
    column.appendChild(bubble);
    row.appendChild(avatar);
    row.appendChild(column);

    chatMessages.appendChild(row);
    scrollToBottom();
}

/* -------------------------
   Agent label
   ------------------------- */

function formatAgent(agent) {
    const labels = {
        fees_academics: "Fees & Academics",
        placements: "Placements",
        campus_hostel: "Campus & Hostel",
        accounts_admin: "Accounts & Administration",
        router: "University Assistant"
    };

    return labels[agent] || "University Assistant";
}

/* -------------------------
   Helpers
   ------------------------- */

function removeElement(element) {
    if (element && element.parentNode) {
        element.parentNode.removeChild(element);
    }
}

function scrollToBottom() {
    requestAnimationFrame(() => {
        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: "smooth"
        });
    });
}

loadTheme();
updateCounter();

/* -------------------------
   Logout
   ------------------------- */

const logoutBtn = document.getElementById("logoutBtn");

if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
        window.location.href = "/logout";
    });
}
