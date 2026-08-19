import { Link } from "react-router-dom";

function Home() {

    return (

        <div className="home-page">

            <div className="hero-card">

                <h1>
                    🎓 School AI Assistant
                </h1>

                <p>
                    AI-Powered Multilingual School Chatbot
                </p>

                <div className="hero-buttons">

                    <Link to="/login">
                        <button>
                            Login
                        </button>
                    </Link>

                    <Link to="/register">
                        <button className="secondary-btn">
                            Create Account
                        </button>
                    </Link>

                </div>

            </div>

        </div>

    );

}

export default Home;