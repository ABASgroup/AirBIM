// Страница настроек
import { UnfilledButton } from "@ui";
import { useNavigate } from 'react-router-dom';

function SettingsPage() {
    // Временный выход из аккаунта
    const navigate = useNavigate();
    const handleLogout = () => {
        localStorage.removeItem("access_token");
        navigate("/");
    };

    return (
        <>
            <h1>Настройки</h1>
            <UnfilledButton onClick={handleLogout}>Выйти</UnfilledButton>
        </>
    )
}

export default SettingsPage;