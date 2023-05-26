import axios from "axios";
import React, { useState, useRef, useEffect } from "react";
import "./App.css";
import { FaFile } from "react-icons/fa";
import { FaPaperPlane } from "react-icons/fa";
import paletteImage from "./img/palette.png"; // Import the image file
import robotImage from "./img/robot.png"; // Import the robot image
import userImage from "./img/user.png"; // Import the user image


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
      } else if (file.type === "text/plain") {
        response = await axios.post("http://localhost:8000/load_txt/", formData);
      } else if (file.type === "text/csv") {
        response = await axios.post("http://localhost:8000/load_csv/", formData);
      } else {
        throw new Error("Unsupported file type.");
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
      fileType: file.type === "application/pdf" ? "pdf" : (file.type === "text/plain" ? "txt" : "csv"), // Add file type flag
    };
    setMessages((messages) => [...messages, messageObject]);
    setInputValue("");
    try {
      let response;

      if(messageObject.fileType === "csv") {
         response = await axios.post(`http://localhost:8000/ask_csv?query=${messageObject.text}`);
      } else {
        response = await axios.post(`http://localhost:8000/ask_question?query=${messageObject.text}`);
      }
      
      const botMessageObject = {
        text: response.data.answer,
        sender: "bot",
        timestamp: new Date(),
      };

      // Check if the bot's response is empty or has a length of 0
      if (!botMessageObject.text || botMessageObject.text.length === 0) {
        // If the response is empty, ask the same question again
        response = await axios.post(`http://localhost:8000/ask_question?query=${messageObject.text}`);
        botMessageObject.text = response.data.answer || "죄송합니다. 해당 질문에 대해서 답변할 수 없습니다.";
      }

      setMessages((messages) => [...messages, botMessageObject]);
    } catch (error) {
      console.error("Error:", error);
      alert("Error with query");
    }
    setIsBotLoading(false);
  };
  
  return (
    <div className="app-container">
      <img src={paletteImage} alt="palette" style={{ width: "15%", height: "auto" }}/>
      <br />
      {/* <div className="attachment-input">
        <input type="file" onChange={(event) => setFile(event.target.files[0])} />
        <button onClick={handleFileUpload}>
          {isLoading ? <div className="loader"></div> : <FaFile />}
        </button>
      </div> */}
      <div className="attachment-input">
        <label htmlFor="file-upload" className="button-container">
          <span className="button-text"><FaFile /> 파일 선택</span>
          <input id="file-upload" type="file" onChange={(event) => setFile(event.target.files[0])} />
        </label>
        <span className="file-path">{file ? file.name : "선택된 파일 없음"}</span>
        <button onClick={handleFileUpload} className="button-container-white">
          {isLoading ? <div className="loader"></div> : "Upload"}
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
            {/* add profile pic */}
            {message.sender === "user" ? (
              <>
                <img src={userImage} alt="User Profile" className="profile-image" />
                <div className="message-text">
                  {message.text}
                </div>
              </>
            ) : (
              <>
                <img src={robotImage} alt="Robot Profile" className="profile-image" />
                <div className="message-text">
                  {message.text}
                </div>
              </>
            )}
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
             <img src={robotImage} alt="Robot Profile" className="profile-image" />
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
          {isBotLoading ? "Sending..." : <>Send {<FaPaperPlane />}</>}
        </button>
      </form>
    </div>
  );
}

export default App;
