"use client";

import { useState } from "react";
import "./user.scss";
import { useRouter } from "next/navigation";
import HeaderMenu from "../component/Header/HeaderMenu/HeaderMenu";

export default function AuthPage() {
  const router = useRouter();
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [message, setMessage] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    const endpoint = isLogin ? "/api/login" : "/api/register";

    // Исправленная проверка полей
    if (isLogin) {
      if (!email || !password) {
        setMessage("Пожалуйста, заполните email и пароль");
        return;
      }
    } else {
      if (!email || !password || !name) {
        setMessage("Пожалуйста, заполните все поля");
        return;
      }
    }

    try {
      const response = await fetch(`http://localhost:8030${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(
          isLogin 
            ? { email: email.trim(), password: password }
            : { email: email.trim(), password: password, name: name.trim() }
        ),
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem("userName", isLogin ? data.name : name);
        localStorage.setItem("userEmail", email);
        localStorage.setItem("isAuthenticated", "true");
        setMessage("Успешно! Перенаправление...");
        
        router.push("/");
      } else {
        setMessage(data.error || "Ошибка при обработке запроса");
      }
    } catch (error) {
      console.error("Error:", error);
      setMessage("Ошибка соединения с сервером");
    }
  };

  return (
    <main className="main">
      <header className="header">
        <HeaderMenu />
      </header>
      <section className="section__auth">
        <div className="container">
          <h1 className="h1">{isLogin ? "Вход" : "Регистрация"}</h1>
          <form className="form" onSubmit={handleSubmit}>
            {!isLogin && (
              <input
                className="question__form"
                type="text"
                placeholder="Имя"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            )}
            <input
              className="email__form"
              type="email"
              placeholder="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <input
              className="passwd__form"
              type="password"
              placeholder="Пароль"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <button className="btn__form" type="submit">
              {isLogin ? "Войти" : "Зарегистрироваться"}
            </button>
            
          </form>

          <button className="btn__transition" onClick={() => setIsLogin(!isLogin)}>
            {isLogin ? "Перейти к регистрации" : "Перейти ко входу"}
          </button>

          {message && <p className="user__auth">{message}</p>}
        </div>
      </section>
    </main>
  );
}
