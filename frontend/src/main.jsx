import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./styles/theme.css";
import { LanguageProvider } from "./context/LanguageContext";


ReactDOM.createRoot(document.getElementById("root")).render(
  <LanguageProvider>
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
  </LanguageProvider>
);