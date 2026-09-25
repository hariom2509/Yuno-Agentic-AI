import React from "react";
import ReactDOM from "react-dom/client";
import "./styles/global.css";
import App from "./App";

// Suppress unhandled errors originating from third-party Chrome extensions (e.g. Urban VPN)
if (typeof window !== "undefined") {
  window.addEventListener("error", (event) => {
    if (
      (event.filename && event.filename.includes("chrome-extension://")) ||
      (event.message && (event.message.includes("M_ID") || event.message.includes("extension")))
    ) {
      event.stopImmediatePropagation();
      event.preventDefault();
    }
  }, true);
}

const root = ReactDOM.createRoot(document.getElementById("root"));

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);