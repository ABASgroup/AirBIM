import { UnfilledButton } from "@ui/UnfilledButton";
import { useNavigate } from 'react-router-dom';

function Settings() {

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

export default Settings;