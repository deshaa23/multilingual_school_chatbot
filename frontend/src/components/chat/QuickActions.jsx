import { useLanguage } from "../../context/LanguageContext";
import { uiText } from "../../constants/uiText";

function QuickActions({ onAsk }) {

  const { language } = useLanguage();

  const text = uiText[language];

  return (

    <div className="quick-actions">

      <h3>{text.quickActions}</h3>

      {text.suggestions.map((item) => (

        <button
          key={item}
          className="action-card"
          onClick={() => onAsk(item)}
        >
          {item}
        </button>

      ))}

    </div>

  );

}

export default QuickActions;