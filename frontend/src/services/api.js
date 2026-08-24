import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8001",
});

console.log("API BASE URL =", api.defaults.baseURL);

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");

  console.log("Sending token:", token);

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

export default api;