import RegisterForm from "../components/auth/RegisterForm";

function Register() {
  return (
    <div className="register-page">
    <div className="register-card">
        <h1>AI Assistant</h1>
        <p>AI-Powered Multilingual School Chatbot</p>
        <RegisterForm />
    </div>
</div>
  );
}

export default Register;