import { useEffect, useState } from "react";
import { Navigate, Link } from "react-router-dom";

import LoginForm from "../components/auth/LoginForm";
import { getCurrentUser } from "../services/authService";

import { uiText } from "../constants/uiText";
import { useLanguage } from "../context/LanguageContext";

function Login() {

  const [checkingAuth, setCheckingAuth] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);

  const { language } = useLanguage();

  console.log("Language =", language);

  const text = uiText[language];

  console.log("Title =", text.assistantTitle);

  useEffect(() => {

    const checkAuth = async () => {

      const token = localStorage.getItem("token");

      if (!token) {
        setCheckingAuth(false);
        return;
      }

      try {

        await getCurrentUser();

        setAuthenticated(true);

      } 
      catch {

        localStorage.removeItem("token");
        localStorage.removeItem("token_type");

        setAuthenticated(false);

      }

      setCheckingAuth(false);

    };

    checkAuth();

  }, []);

  if (checkingAuth) {

    return (

      <div className="login-page">

        <div className="login-card">

          <h2>Checking session...</h2>

        </div>

      </div>

    );

  }

  if (authenticated) {

    return <Navigate to="/dashboard" replace />;

  }

  return (

    <div className="login-page">

      <div className="login-card">

        <h1>{text.assistantTitle}</h1>

        <p>{text.assistantSubtitle}</p>

        <LoginForm />

        <hr />

        <div className="register-options">


  <div className="register-links">

    <Link to="/register">
      Student Registration
    </Link>

    <Link to="/parent-register">
      Parent Registration
    </Link>

  </div>

</div>

      </div>

    </div>

  );

}

export default Login;