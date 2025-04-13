
const messageForm = document.querySelector(".prompt__form");
const chatHistoryContainer = document.querySelector(".chats");
const suggestionItems = document.querySelectorAll(".suggests__item");

const themeToggleButton = document.getElementById("themeToggler");
const clearChatButton = document.getElementById("deleteButton");

// State
let currentUserMessage = null;
let isGeneratingResponse = false;

const API_REQUEST_URL = "http://localhost:8000/grimorio";

// Utilitários
const createChatMessageElement = (htmlContent, ...cssClasses) => {
    const messageElement = document.createElement("div");
    messageElement.classList.add("message", ...cssClasses);
    messageElement.innerHTML = htmlContent;
    return messageElement;
};

const showTypingEffect = (rawText, htmlText, messageElement, incomingMessageElement, skipEffect = false) => {
    const copyIconElement = incomingMessageElement.querySelector(".message__icon");
    copyIconElement.classList.add("hide");

    if (skipEffect) {
        messageElement.innerHTML = htmlText;
        hljs.highlightAll();
        addCopyButtonToCodeBlocks();
        copyIconElement.classList.remove("hide");
        isGeneratingResponse = false;
        return;
    }

    const wordsArray = rawText.split(' ');
    let wordIndex = 0;

    const typingInterval = setInterval(() => {
        messageElement.innerText += (wordIndex === 0 ? '' : ' ') + wordsArray[wordIndex++];
        if (wordIndex === wordsArray.length) {
            clearInterval(typingInterval);
            isGeneratingResponse = false;
            messageElement.innerHTML = htmlText;
            hljs.highlightAll();
            addCopyButtonToCodeBlocks();
            copyIconElement.classList.remove("hide");
        }
    }, 45);
};

const requestApiResponse = async (incomingMessageElement) => {
    const messageTextElement = incomingMessageElement.querySelector(".message__text");

    try {
        const response = await fetch(API_REQUEST_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pergunta: currentUserMessage })
        });

        const data = await response.json();
        if (!data.resposta) throw new Error("Resposta vazia.");

        const raw = data.resposta;
        const parsed = marked.parse(raw);
        showTypingEffect(raw, parsed, messageTextElement, incomingMessageElement);

    } catch (error) {
        messageTextElement.innerText = error.message || "Erro ao buscar resposta.";
        messageTextElement.closest(".message").classList.add("message--error");
    } finally {
        incomingMessageElement.classList.remove("message--loading");
    }
};

const displayLoadingAnimation = () => {
    const loadingHtml = `
        <div class="message__content">
            <img class="message__avatar" src="assets/gemini.svg" alt="Grimório avatar">
            <p class="message__text"></p>
            <div class="message__loading-indicator">
                <div class="message__loading-bar"></div>
                <div class="message__loading-bar"></div>
                <div class="message__loading-bar"></div>
            </div>
        </div>
        <span onClick="copyMessageToClipboard(this)" class="message__icon hide"><i class='bx bx-copy-alt'></i></span>
    `;

    const loadingMessageElement = createChatMessageElement(loadingHtml, "message--incoming", "message--loading");
    chatHistoryContainer.appendChild(loadingMessageElement);
    requestApiResponse(loadingMessageElement);
};

const handleOutgoingMessage = () => {
    currentUserMessage = messageForm.querySelector(".prompt__form-input").value.trim() || currentUserMessage;
    if (!currentUserMessage || isGeneratingResponse) return;

    isGeneratingResponse = true;

    const outgoingMessageHtml = `
        <div class="message__content">
            <img class="message__avatar" src="assets/profile.png" alt="Usuário">
            <p class="message__text"></p>
        </div>
    `;

    const outgoingMessageElement = createChatMessageElement(outgoingMessageHtml, "message--outgoing");
    outgoingMessageElement.querySelector(".message__text").innerText = currentUserMessage;
    chatHistoryContainer.appendChild(outgoingMessageElement);

    messageForm.reset();
    document.body.classList.add("hide-header");
    setTimeout(displayLoadingAnimation, 300);
};

const copyMessageToClipboard = (copyButton) => {
    const messageContent = copyButton.parentElement.querySelector(".message__text").innerText;
    navigator.clipboard.writeText(messageContent);
    copyButton.innerHTML = `<i class='bx bx-check'></i>`;
    setTimeout(() => copyButton.innerHTML = `<i class='bx bx-copy-alt'></i>`, 1000);
};

const addCopyButtonToCodeBlocks = () => {
    const codeBlocks = document.querySelectorAll('pre');
    codeBlocks.forEach(block => {
        const codeElement = block.querySelector('code');
        const language = [...codeElement.classList].find(cls => cls.startsWith('language-'))?.replace('language-', '') || 'Text';

        const label = document.createElement('div');
        label.innerText = language.charAt(0).toUpperCase() + language.slice(1);
        label.classList.add('code__language-label');
        block.appendChild(label);

        const copyBtn = document.createElement('button');
        copyBtn.innerHTML = `<i class='bx bx-copy'></i>`;
        copyBtn.classList.add('code__copy-btn');
        block.appendChild(copyBtn);

        copyBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(codeElement.innerText).then(() => {
                copyBtn.innerHTML = `<i class='bx bx-check'></i>`;
                setTimeout(() => copyBtn.innerHTML = `<i class='bx bx-copy'></i>`, 2000);
            }).catch(err => {
                console.error("Copy failed:", err);
                alert("Unable to copy text!");
            });
        });
    });
};

// Eventos
themeToggleButton.addEventListener('click', () => {
    const isLight = document.body.classList.toggle("light_mode");
    localStorage.setItem("themeColor", isLight ? "light_mode" : "dark_mode");
    themeToggleButton.querySelector("i").className = isLight ? "bx bx-moon" : "bx bx-sun";
});

clearChatButton.addEventListener('click', () => {
    if (confirm("Tem certeza que deseja apagar tudo?")) {
        chatHistoryContainer.innerHTML = "";
        currentUserMessage = null;
        isGeneratingResponse = false;
    }
});

suggestionItems.forEach(suggestion => {
    suggestion.addEventListener('click', () => {
        const text = suggestion.querySelector(".suggests__item-text").innerText;
        const input = document.querySelector(".prompt__form-input");
        input.value = text;
        input.dispatchEvent(new Event("input"));
        currentUserMessage = text;
        handleOutgoingMessage();
    });
});

messageForm.addEventListener('submit', e => {
    e.preventDefault();
    handleOutgoingMessage();
});
