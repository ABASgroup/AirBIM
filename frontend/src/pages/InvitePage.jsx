import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { LandingHeader } from "@landing";
import { Modal, FilledButton, UnfilledButton } from "@ui";
import { validateInviteLink, acceptInviteLink } from "@/api/invites";
import { ROLES } from "@/utils/roles";

function InvitePage() {
  const { token } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const isAuthorized = !!localStorage.getItem("access_token");

  useEffect(() => {
    validateInviteLink(token)
      .then(res => {
        setData(res.data);
        setLoading(false);
      })
      .catch(() => {
        setError("Ссылка недействительна или срок её действия истек");
        setLoading(false);
      });
  }, [token]);
  const handleAccept = async () => {
    if (!isAuthorized) {
      sessionStorage.setItem("pendingInvite", token);
      navigate("/login");
      return;
    }
    try {
      await acceptInviteLink(token);
      navigate("/app/dashboard");
    } catch (err) {
      setError("Не удалось принять приглашение. Возможно, вы уже являетесь участником.");
    }
  };
  return (
    <Modal title="Приглашение в команду" isOpen={true} showBackdrop>
      {loading ? (
        <p className="text-mute-text-color text-center animate-pulse">Проверка ссылки...</p>
      ) : error ? (
        <div className="flex flex-col gap-4 text-center">
          <p className="text-warning font-medium">{error}</p>
          <FilledButton onClick={() => navigate("/")} className="w-full">
            На главную
          </FilledButton>
        </div>
      ) : (
        <div className="flex flex-col gap-5 text-center">
          <p className="text-lg">
            Пользователь
            <span className="text-primary-color"> {data?.created_by?.username} </span>
            приглашает вас присоединиться к воркспейсу
            <span className="text-primary-color"> {data?.workspace?.name} </span>
          </p>
          <div className="bg-background-color p-3 rounded-[5px]">
            <label>Ваша роль</label>
            <span className="font-bold text-primary-color text-xl tracking-wide">
              {ROLES.find(r => r.value === data?.role)?.label || data?.role}
            </span>
          </div>
          <div className="flex justify-between w-full">
            <UnfilledButton onClick={() => navigate("/app")}>
              Отмена
            </UnfilledButton>
            <FilledButton onClick={handleAccept}>
              {isAuthorized ? "Принять приглашение" : "Войти и присоединиться"}
            </FilledButton>
          </div>
        </div>
      )}
    </Modal>
  );
}
export default InvitePage;