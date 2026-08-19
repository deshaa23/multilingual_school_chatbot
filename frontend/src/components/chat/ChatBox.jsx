import { useEffect, useRef } from "react";
import ChatMessage from "./ChatMessage";

function ChatBox({ messages, loading }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  return (
    <div className="chat-box">
      {messages.map((message, index) => (
        <ChatMessage
          key={index}
          message={message}
        />
      ))}

      {loading && (
        <div className="bot-message thinking">
          Thinking...
        </div>
      )}

      <div ref={bottomRef}></div>
    </div>
  );
}

export default ChatBox;