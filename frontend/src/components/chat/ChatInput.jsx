import { useState } from "react";

import { useLanguage } from "../../context/LanguageContext";
import { uiText } from "../../constants/uiText";

function ChatInput({ onSend, loading }) {

    const [question, setQuestion] = useState("");

    const { language } = useLanguage();

    const text = uiText[language];

    const handleSubmit = (e) => {

        e.preventDefault();

        if (!question.trim()) return;

        onSend(question);

        setQuestion("");

    };

    return (

        <form
            className="chat-input-container"
            onSubmit={handleSubmit}
        >

            <input

                type="text"

                value={question}

                placeholder={text.askPlaceholder}

                onChange={(e) =>
                    setQuestion(e.target.value)
                }

                disabled={loading}

            />

            <button
                disabled={loading}
            >

                {loading
                    ? "..."
                    : text.send}

            </button>

        </form>

    );

}

export default ChatInput;