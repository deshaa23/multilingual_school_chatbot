import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { login } from "../../services/authService";

function LoginForm() {

  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = async (e) => {

    e.preventDefault();

    try {

      const data = await login(email, password);

      localStorage.setItem("token", data.access_token);
      localStorage.setItem("token_type", data.token_type);

      alert("Login Successful!");

      navigate("/dashboard");

    } catch (error) {

      console.log(error);

      alert(
        error.response?.data?.detail ||
        "Invalid email or password."
      );

    }

  };

  return (

    <form
      className="login-form"
      onSubmit={handleSubmit}
    >

      <h2>Login</h2>

      <div className="input-group">

        <label>Email</label>

        <input
          type="email"
          placeholder="Enter your email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

      </div>

      <div className="input-group">

        <label>Password</label>

        <input
          type="password"
          placeholder="Enter your password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

      </div>

      <button type="submit">

        Login

      </button>

      <div className="register-link">

        <p>
          Don't have an account?
        </p>


      </div>

    </form>

  );

}

export default LoginForm;