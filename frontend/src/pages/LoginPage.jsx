import { LandingHeader } from "../components/landing/LandingHeader";
import { Modal } from "../components/Modal";
import { FilledButton } from "../components/FilledButton";
import { UnfilledButton } from "../components/UnfilledButton";
import { Input } from "../components/Input";
import { useForm } from "react-hook-form";

const LoginPage = () => {
    const { register, handleSubmit } = useForm();
    const onSubmit = (data) => console.log("Данные формы:", data);
    return (
        <>
            <LandingHeader />
            <main className="flex items-center justify-center min-h-[80vh]">
                <form onSubmit={handleSubmit(onSubmit)}>
                    <Modal title="Вход">
                        <div>
                            <p>Логин</p>
                            <Input
                                {...register("login", { required: true })}
                                placeholder="Почта или логин"
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