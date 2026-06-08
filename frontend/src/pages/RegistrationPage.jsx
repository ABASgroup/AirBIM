// Странциа регистрации
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { Modal, FilledButton, Input } from "@ui";
import { acceptInviteLink } from "@/api/invites";
import { useToast } from "@/context";
import api from "../api/index";

function RegistrationPage() {
  const { register, handleSubmit, watch } = useForm();
  const navigate = useNavigate();
  const { showToast } = useToast();

  const password = watch("password");

  const onSubmit = async (data) => {
    if (data.password !== data.confirm_password) {
      showToast({
        type: "warning",
        title: "Ошибка",
        message: "Пароли не совпадают",
      });
      return;
    }

    try {
      const response = await api.post("/auth/register", {
        username: data.username,
        email: data.email,
        password: data.password
      });

      localStorage.setItem("access_token", response.data.access_token);
      const pendingInvite = sessionStorage.getItem("pendingInvite");
      if (pendingInvite) {
        await acceptInviteLink(pendingInvite);
        sessionStorage.removeItem("pendingInvite");
      }
      navigate("/app/dashboard");
    } catch (err) {
      if (err.response?.status === 409) {
        showToast({
          type: "warning",
          title: "Ошибка",
          message: "Данная почта уже зарегистрирована",
        });
      } else {
        showToast({
          type: "warning",
          title: "Ошибка",
          message: "Ошибка регистрации",
        });
      }
    }
  };

  return (
    <>
      <form onSubmit={handleSubmit(onSubmit)}>
        <Modal title="Регистрация">
          <div>
            <label>Логин</label>
            <Input
              {...register("username", { required: true })}
              placeholder="Ваше имя"
            />
          </div>
          <div>
            <label>Почта</label>
            <Input {...register("email", { required: true })}
              type="email"
              placeholder="email@example.com"
            />
          </div>
          <div>
            <label>Пароль</label>
            <Input {...register("password", { required: true })}
              type="password"
              placeholder="Пароль"
            />
          </div>
          <div>
            <label>Подтверждение пароля</label>
            <Input {...register("confirm_password", { required: true })}
              type="password"
              placeholder="Повторите пароль"
            />
          </div>
          <div className="flex justify-end mt-5">
            <FilledButton type="submit">
              Подтвердить
            </FilledButton>
          </div>
        </Modal>
      </form>
    </>
  );
}

export default RegistrationPage;