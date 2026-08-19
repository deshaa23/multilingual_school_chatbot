import { createContext, useContext, useState } from "react";

const LanguageContext = createContext();

export function LanguageProvider({ children }) {

    const [language, setLanguage] = useState(
        localStorage.getItem("uiLanguage") || "ENGLISH"
    );

    const changeLanguage = (lang) => {

        localStorage.setItem("uiLanguage", lang);

        setLanguage(lang);

    };

    return (

        <LanguageContext.Provider
            value={{
                language,
                changeLanguage
            }}
        >
            {children}
        </LanguageContext.Provider>

    );

}

export function useLanguage() {

    return useContext(LanguageContext);

}