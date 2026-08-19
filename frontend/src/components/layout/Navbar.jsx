import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { getCurrentUser } from "../../services/authService";

import { useLanguage } from "../../context/LanguageContext";
import { uiText } from "../../constants/uiText";

function Navbar() {

    const navigate = useNavigate();

    const [user, setUser] = useState(null);

    const { language, changeLanguage } = useLanguage();

    const text = uiText[language];

    
    useEffect(() => {

    let ignore = false;

    async function fetchUser() {

        try {

            const data = await getCurrentUser();

            if (!ignore) {
                setUser(data);
            }

        } catch (error) {

            console.log(error);

        }

    }

    fetchUser();

    return () => {
        ignore = true;
    };

}, []);


    const logout = () => {

        localStorage.clear();

        navigate("/", {
            replace: true
        });

    };

    return (

        <nav className="navbar">

            <div className="navbar-title">

                {text.assistantTitle}

            </div>

            <div className="navbar-user">

                {user && (

                    <>
                        <strong>{user.email}</strong>

                        {" "}({user.role})

                    </>

                )}

            </div>

            <div className="navbar-actions">

                <select
                    className="language-select"
                    value={language}
                    onChange={(e) =>
                        changeLanguage(e.target.value)
                    }
                >

                    <option value="ENGLISH">
                        English
                    </option>

                    <option value="HINDI">
                        हिन्दी
                    </option>

                    <option value="HINGLISH">
                        Hinglish
                    </option>

                </select>

                <button
                    className="logout-btn"
                    onClick={logout}
                >

                    {text.logout}

                </button>

            </div>

        </nav>

    );

}

export default Navbar;