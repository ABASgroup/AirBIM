import { UnfilledButton } from "../../components/UnfilledButton";
import { useNavigate } from 'react-router-dom';

function Dashboard() {

    // Временный выход из аккаунта
    const navigate = useNavigate();
    const handleLogout = () => {
        localStorage.removeItem("access_token");
        navigate("/");
    };

    return (
        <>
            <h1>Дышборд</h1>
            <UnfilledButton onClick={handleLogout}>Выйти</UnfilledButton>
        </>
    )
}

export default Dashboard;