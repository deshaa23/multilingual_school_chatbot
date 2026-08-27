import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
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