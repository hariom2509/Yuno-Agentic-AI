import axios from "axios";

const getBaseURL = () => {
  if (process.env.REACT_APP_BACKEND_URL) {
    return process.env.REACT_APP_BACKEND_URL;
  }
  const protocol = window.location.protocol;
  const hostname = window.location.hostname;
  return `${protocol}//${hostname}:8001`;
};

const api = axios.create({
  baseURL: getBaseURL(),
  timeout: 60000, // 60s
});

export default api;