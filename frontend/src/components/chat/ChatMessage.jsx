function ChatMessage({ message }) {

    return (

        <div
            className={
                message.sender === "user"
                    ? "user-message"
                    : "bot-message"
            }
        >

            {message.text}

        </div>

    );
}

export default ChatMessage;