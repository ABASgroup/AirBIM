import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import api from "../api/index";

import { LandingHeader } from "@landing/LandingHeader";
import { Modal } from "@ui/Modal";
import { FilledButton } from "@ui/FilledButton";
import { Input } from "@ui/Input";

function RegistrationPage() {
  const { register, handleSubmit, watch } = useForm();
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const password = watch("password");

  const onSubmit = async (data) => {
    if (data.password !== data.confirm_password) {
      setError("Пароли не совпадают");
      return;
    }

    try {
      const response = await api.post("/auth/register", {
        username: data.username,
        email: data.email,
        password: data.password
      });

      localStorage.setItem("access_token", response.data.access_token);
      navigate("/app/dashboard");
    } catch (err) {
      if (err.response?.status === 409) {
        setError("Данная почта уже зарегистрирована");
      } else {
        setError("Ошибка регистрации");
      }
    }
  };

  return (
    <>
      <LandingHeader />
      <main className="flex items-center justify-center min-h-[80vh]">
        <form onSubmit={handleSubmit(onSubmit)}>
          <Modal title="Регистрация" className="z-10">
            <div>
              <p>Логин</p>
              <Input
                {...register("username", { required: true })}
                placeholder="Ваше имя"
              />
            </div>
            <div>
              <p>Почта</p>
              <Input {...register("email", { required: true })}
                type="email"
                placeholder="email@example.com"
              />
            </div>
            <div>
              <p>Пароль</p>
              <Input {...register("password", { required: true })}
                type="password"
                placeholder="Пароль"
              />
            </div>
            <div>
              <p>Подтверждение пароля</p>
              <Input {...register("confirm_password", { required: true })}
                type="password"
                placeholder="Повторите пароль"
              />
            </div>
            {error && <p className="text-warning">{error}</p>}
            <div className="flex justify-between mt-10">
              <FilledButton type="submit">
                Подтвердить
              </FilledButton>
            </div>
          </Modal>
        </form>
      </main>
    </>
  );
}

export default RegistrationPage;