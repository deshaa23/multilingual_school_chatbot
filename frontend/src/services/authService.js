import api from "./api";

// --------------------
// Login
// --------------------

export const login = async (email, password) => {
  const formData = new URLSearchParams();

  formData.append("username", email);
  formData.append("password", password);

  const response = await api.post(
    "/auth/login",
    formData,
    {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    }
  );

  return response.data;
};

// --------------------
// Student Registration
// --------------------

export const registerStudent = async (studentData) => {
  const response = await api.post(
    "/auth/register",
    studentData
  );

  return response.data;
};

// --------------------
// Parent Registration
// --------------------

export const registerParent = async (parentData) => {
  const response = await api.post(
    "/auth/register/parent",
    parentData
  );

  return response.data;
};

// --------------------
// Get Classes
// --------------------

export const getClasses = async () => {
  const response = await api.get("/classes");
  return response.data;
};

// --------------------
// Current User
// --------------------

export const getCurrentUser = async () => {
  const response = await api.get("/auth/me");
  return response.data;
};