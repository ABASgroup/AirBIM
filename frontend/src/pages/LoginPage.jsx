// Страница логина
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { Modal, FilledButton, UnfilledButton, Input, Toast } from "@ui";
import { acceptInviteLink } from "@/api/invites";
import { useToast } from "@/context";
import api from "@/api/index";

function LoginPage() {
  const { register, handleSubmit } = useForm();
  const navigate = useNavigate();
  const { showToast } = useToast();

  const onSubmit = async (data) => {
    try {
      const formData = new FormData();
      formData.append("username", data.login);
      formData.append("password", data.password);
      const response = await api.post("/auth/login", formData);
      localStorage.setItem("access_token", response.data.access_token);
      const pendingInvite = sessionStorage.getItem("pendingInvite");
      if (pendingInvite) {
        await acceptInviteLink(pendingInvite);
        sessionStorage.removeItem("pendingInvite");
      }
      navigate("/app/dashboard");
    } catch (err) {
      if (err.response?.status === 401) {
        showToast({
          type: "warning",
          title: "Ошибка",
          message: "Неверная почта или пароль",
        });
      } else {
        showToast({
          type: "warning",
          title: "Ошибка",
          message: "Ошибка соединения",
        });
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