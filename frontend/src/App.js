import axios from "axios";
import React, { useState, useRef, useEffect } from "react";
import "./App.css";
import { FaFile } from "react-icons/fa";
import { FaPaperPlane } from "react-icons/fa";

function App() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [file, setFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isBotLoading, setIsBotLoading] = useState(false);
  const chatContainerRef = useRef(null);

  useEffect(() => {
    // Scroll to bottom of chat container
    chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
  }, [messages]);

  const handleFileUpload = async () => {
    setIsLoading(true);
    const formData = new FormData();
    formData.append("file", file);
    try {
      let response;
      if (file.type === "application/pdf") {
        response = await axios.post("http://localhost:8000/load_document/", formData);
      } else {
        response = await axios.post("http://localhost:8000/load_txt/", formData);
      }
      alert("Documents added successfully!");
    } catch (error) {
      console.error("Error:", error);
      alert("Error adding documents");
    }
    setIsLoading(false);
  };
  
  const handleMessageSubmit = async (event) => {
    event.preventDefault();
    if (!inputValue.trim() || isBotLoading) {
      return;
    }
    setIsBotLoading(true);
    const messageObject = {
      text: inputValue.trim(),
      sender: "user",
      timestamp: new Date(),
      fileType: file.type === "application/pdf" ? "pdf" : "text", // Add file type flag
    };
    setMessages((messages) => [...messages, messageObject]);
    setInputValue("");
    try {
      let response;
      // if (messageObject.fileType === "pdf") {
      //   response = await axios.post(`http://localhost:8000/query/?query=${messageObject.text}`);
      // } else {
      //   response = await axios.post(`http://localhost:8000/query_txts/?query=${messageObject.text}`);
      // }
      response = await axios.post(`http://localhost:8000/ask_question?query=${messageObject.text}`);
      
      const botMessageObject = {
        text: response.data.answer,
        sender: "bot",
        timestamp: new Date(),
      };
      setMessages((messages) => [...messages, botMessageObject]);
    } catch (error) {
      console.error("Error:", error);
      alert("Error with query");
    }
    setIsBotLoading(false);
  };
  
  return (
    <div className="app-container">
      <h1>LangChain & ChatGPT</h1>
      <div className="attachment-input">
        <input type="file" onChange={(event) => setFile(event.target.files[0])} />
        <button onClick={handleFileUpload}>
          {isLoading ? <div className="loader"></div> : <FaFile />}
        </button>
      </div>
      <br />
      <div ref={chatContainerRef} className="chat-container">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`chat-message ${
              message.sender === "user" ? "user-message" : "bot-message"
            }`}
          >
            <div className="message-text">{message.text}</div>
            <div className="message-timestamp">
              {message.timestamp.toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </div>
          </div>
        ))}
        {isBotLoading && (
          <div className="chat-message bot-message">
             <div className="bot-typing-animation">
              <span></span>
              <span></span>
              <span></span>
             </div>
          </div>
        )}
      </div>
      <form onSubmit={handleMessageSubmit} className="input-form">
        <input
          type="text"
          placeholder="Enter your message..."
          value={inputValue}
          onChange={(event) => setInputValue(event.target.value)}
          disabled={isBotLoading}
        />
        <button type="submit" disabled={isBotLoading}>
          {isBotLoading ? "Sending..." : <FaPaperPlane />}
        </button>
      </form>
    </div>
  );
}

export default App;
