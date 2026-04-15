// Страница логина
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { Modal, FilledButton, UnfilledButton, Input } from "@ui";
import api from "@/api/index";

function LoginPage() {
  const { register, handleSubmit } = useForm();
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const onSubmit = async (data) => {
    setError("");
    try {
      const formData = new FormData();
      formData.append("username", data.login);
      formData.append("password", data.password);
      const response = await api.post("/auth/login", formData);
      localStorage.setItem("access_token", response.data.access_token);
      navigate("/app/dashboard");
    } catch (err) {
      if (err.response?.status === 401) {
        setError("Неверная почта или пароль");
      } else {
        setError("Ошибка соединения");
      }
    }
  };

  return (
    <>
      <form onSubmit={handleSubmit(onSubmit)}>
        <Modal title="Вход">
          <div>
            <label>Почта</label>
            <Input
              {...register("login", { required: true })}
              placeholder="email@example.com"
            />
          </div>
          <div>
            <label>Пароль</label>
            <Input
              {...register("password", { required: true })}
              type="password"
              placeholder="Пароль"
            />
          </div>
          {error && <p className="text-warning">{error}</p>}
          <div className="flex justify-between mt-5">
            <UnfilledButton type="button">
              Забыл пароль
            </UnfilledButton>
            <FilledButton type="submit">
              Подтвердить
            </FilledButton>
          </div>
        </Modal>
      </form>
    </>
  );
};

export default LoginPage;