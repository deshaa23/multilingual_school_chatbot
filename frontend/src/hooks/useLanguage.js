import { useState } from "react";

export default function useLanguage() {

    const [language, setLanguage] = useState(

        localStorage.getItem("uiLanguage") || "ENGLISH"

    );

    const changeLanguage = (lang) => {

        localStorage.setItem("uiLanguage", lang);

        setLanguage(lang);

    };

    return {

        language,

        changeLanguage

    };

}