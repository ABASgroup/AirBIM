import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import api from "../api/index";

import { LandingHeader } from "../components/landing/LandingHeader";
import { Modal } from "../components/Modal";
import { FilledButton } from "../components/FilledButton";
import { UnfilledButton } from "../components/UnfilledButton";
import { Input } from "../components/Input";

const LoginPage = () => {
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
        setError("Неверная почта или пароль");
      }
    };
    return (
      <>
        <LandingHeader />
        <main className="flex items-center justify-center min-h-[80vh]">
          <form onSubmit={handleSubmit(onSubmit)}>
            <Modal title="Вход">
              <div>
                <p>Почта</p>
                <Input
                  {...register("login", { required: true })}
                  placeholder="email@example.com"
                />
              </div>
              <div>
                <p>Пароль</p>
                <Input
                  {...register("password", { required: true })}
                  type="password"
                  placeholder="Пароль"
                />
              </div>
              {error && <p className="text-warning">{error}</p>}
              <div className="flex justify-between mt-10">
                <UnfilledButton type="button">
                  Забыл пароль
                </UnfilledButton>
                <FilledButton type="submit">
                  Подтвердить
                </FilledButton>
              </div>
            </Modal>
          </form>
        </main>
      </>
    );
  };

  export default LoginPage;