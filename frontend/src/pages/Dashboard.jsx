import { useState, useEffect } from "react";

import Navbar from "../components/layout/Navbar";
import QuickActions from "../components/chat/QuickActions";
import ChatBox from "../components/chat/ChatBox";
import ChatInput from "../components/chat/ChatInput";

import { sendMessage } from "../services/chatService";
import { getCurrentUser } from "../services/authService";

import { useLanguage } from "../context/LanguageContext";
import { uiText } from "../constants/uiText";

function Dashboard() {

    const { language } = useLanguage();

    const text = uiText[language];

    const [messages, setMessages] = useState([]);

    const [loading, setLoading] = useState(false);

    const [pendingQuestion, setPendingQuestion] = useState(null);

    const [user, setUser] = useState(null);

    useEffect(() => {

        loadUser();

    }, []);

    useEffect(() => {

        setMessages((previous) => {

            const otherMessages = previous.filter(
                (message) => message.type !== "welcome"
            );

            return [

                {
                    type: "welcome",
                    sender: "bot",
                    text: text.welcomeMessage
                },

                ...otherMessages

            ];

        });

    }, [text.welcomeMessage]);

    const loadUser = async () => {

        try {

            const data = await getCurrentUser();

            setUser(data);

        }

        catch (error) {

            console.log(error);

        }

    };

    const handleSend = async (question) => {

        let questionToSend = question;

        if (pendingQuestion) {

            questionToSend = `${pendingQuestion} of ${question}`;

        }else{
            setPendingQuestion(null);
        }

        setMessages((prev) => [

            ...prev,

            {

                sender: "user",

                text: question

            }

        ]);

        setLoading(true);

        try {
            console.log("Pending Question:", pendingQuestion);
            console.log("Question:", question);
            console.log("Question to send:", questionToSend);

            const response = await sendMessage(questionToSend);

            if (response.answer.includes("multiple children linked")) {

                setPendingQuestion(question);

            }else{
                setPendingQuestion(null);
            }

            setMessages((prev) => [

                ...prev,

                {

                    sender: "bot",

                    text: response.answer

                }

            ]);

        }

        catch (error) {

            setMessages((prev) => [

                ...prev,

                {

                    sender: "bot",

                    text:

                        error.response?.data?.detail ||

                        "Sorry, I couldn't process your request."

                }

            ]);

        }

        setLoading(false);

    };

    return (

        <div className="dashboard">

            <Navbar />

            <div className="user-card">

                <h2>{text.welcome}</h2>

                <p>

                    <strong>{text.email}:</strong> {user?.email}

                </p>

                <p>

                    <strong>Role:</strong> {user?.role}

                </p>

            </div>

            <main className="dashboard-main">

                <QuickActions
                onAsk={handleSend}
                />

                <div className="chat-section">

                    <ChatBox

                        messages={messages}

                        loading={loading}

                    />

                    <ChatInput

                        onSend={handleSend}

                        loading={loading}

                    />

                </div>

            </main>

        </div>

    );

}

export default Dashboard;