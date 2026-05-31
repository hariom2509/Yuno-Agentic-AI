import axios from "axios";

const getBaseURL = () => {
  if (process.env.REACT_APP_BACKEND_URL) {
    return process.env.REACT_APP_BACKEND_URL;
  }
  const protocol = window.location.protocol;
  const hostname = window.location.hostname;
  const port = window.location.port;

  // If in production (single container serving both frontend & backend),
  // make request relative to the serving host and port
  if (port && port !== "3000" && port !== "3001") {
    return "";
  }
  return `${protocol}//${hostname}:8001`;
};

const api = axios.create({
  baseURL: getBaseURL(),
  timeout: 60000, // 60s
});

export default api;