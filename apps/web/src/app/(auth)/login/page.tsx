"use client"

import { useActionState } from "react"
import { loginAction } from "../actions"

const initialState = {
  error: null as string | null,
}

export default function LoginPage() {
  const [state, formAction, isPending] = useActionState(loginAction, initialState)

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        * { box-sizing: border-box; margin: 0; padding: 0; }

        .login-root {
          min-height: 100vh;
          width: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          background-color: #030712;
          background-image:
            radial-gradient(ellipse 80% 60% at 50% -10%, rgba(99, 102, 241, 0.35) 0%, transparent 60%),
            radial-gradient(ellipse 40% 40% at 90% 90%, rgba(168, 85, 247, 0.2) 0%, transparent 50%);
          font-family: 'Inter', system-ui, sans-serif;
          padding: 24px;
        }

        .login-card {
          width: 100%;
          max-width: 440px;
          background: rgba(15, 23, 42, 0.8);
          border: 1px solid rgba(99, 102, 241, 0.2);
          border-radius: 24px;
          padding: 48px 40px;
          box-shadow:
            0 0 0 1px rgba(99, 102, 241, 0.05),
            0 24px 64px rgba(0, 0, 0, 0.6),
            0 0 80px rgba(99, 102, 241, 0.08);
          backdrop-filter: blur(24px);
        }

        .login-header {
          text-align: center;
          margin-bottom: 40px;
        }

        .login-logo {
          width: 56px;
          height: 56px;
          margin: 0 auto 20px;
          background: linear-gradient(135deg, #6366f1, #a855f7);
          border-radius: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 8px 32px rgba(99, 102, 241, 0.4);
        }

        .login-logo svg {
          width: 28px;
          height: 28px;
          color: white;
        }

        .login-title {
          font-size: 28px;
          font-weight: 800;
          color: #f8fafc;
          letter-spacing: -0.5px;
          line-height: 1.2;
        }

        .login-subtitle {
          margin-top: 8px;
          font-size: 14px;
          color: #64748b;
          font-weight: 400;
        }

        .login-form {
          display: flex;
          flex-direction: column;
          gap: 20px;
        }

        .error-box {
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.25);
          border-radius: 10px;
          padding: 12px 16px;
          font-size: 13px;
          color: #f87171;
          text-align: center;
        }

        .field {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .field label {
          font-size: 13px;
          font-weight: 600;
          color: #cbd5e1;
          letter-spacing: 0.02em;
        }

        .input-wrap {
          position: relative;
        }

        .input-icon {
          position: absolute;
          left: 14px;
          top: 50%;
          transform: translateY(-50%);
          width: 16px;
          height: 16px;
          color: #475569;
          pointer-events: none;
        }

        .field input {
          width: 100%;
          background: rgba(30, 41, 59, 0.6);
          border: 1px solid rgba(71, 85, 105, 0.5);
          border-radius: 10px;
          padding: 12px 14px 12px 42px;
          font-size: 14px;
          color: #f1f5f9;
          font-family: inherit;
          outline: none;
          transition: border-color 0.2s, box-shadow 0.2s;
        }

        .field input::placeholder {
          color: #334155;
        }

        .field input:focus {
          border-color: #6366f1;
          box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
        }

        .submit-btn {
          width: 100%;
          padding: 14px;
          background: linear-gradient(135deg, #6366f1, #a855f7);
          border: none;
          border-radius: 12px;
          font-size: 15px;
          font-weight: 700;
          color: white;
          font-family: inherit;
          cursor: pointer;
          letter-spacing: 0.01em;
          box-shadow: 0 4px 24px rgba(99, 102, 241, 0.35);
          transition: all 0.2s;
          margin-top: 4px;
        }

        .submit-btn:hover:not(:disabled) {
          transform: translateY(-1px);
          box-shadow: 0 8px 32px rgba(99, 102, 241, 0.5);
        }

        .submit-btn:active:not(:disabled) {
          transform: translateY(0px);
        }

        .submit-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .spinner {
          display: inline-block;
          width: 14px;
          height: 14px;
          border: 2px solid rgba(255,255,255,0.3);
          border-top-color: white;
          border-radius: 50%;
          animation: spin 0.7s linear infinite;
          margin-right: 8px;
          vertical-align: middle;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .login-footer {
          margin-top: 28px;
          text-align: center;
          font-size: 13px;
          color: #475569;
        }

        .login-footer a {
          color: #818cf8;
          text-decoration: none;
          font-weight: 600;
        }

        .login-footer a:hover {
          color: #a5b4fc;
          text-decoration: underline;
        }

        .login-copy {
          margin-top: 16px;
          text-align: center;
          font-size: 11px;
          color: #334155;
        }

        .divider {
          display: flex;
          align-items: center;
          gap: 12px;
          margin: 4px 0;
        }

        .divider-line {
          flex: 1;
          height: 1px;
          background: rgba(51, 65, 85, 0.6);
        }

        .divider-text {
          font-size: 11px;
          color: #475569;
          font-weight: 500;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }
      `}</style>

      <div className="login-root">
        <div className="login-card">
          <div className="login-header">
            <div className="login-logo">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M13 10V3L4 14h7v7l9-11h-7z" fill="currentColor" stroke="none"/>
              </svg>
            </div>
            <h1 className="login-title">KS FoodOps</h1>
            <p className="login-subtitle">Entre na sua conta para continuar</p>
          </div>

          <form action={formAction} className="login-form">
            {state?.error && (
              <div className="error-box">{state.error}</div>
            )}

            <div className="field">
              <label htmlFor="email">Email</label>
              <div className="input-wrap">
                <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                <input
                  id="email"
                  type="email"
                  name="email"
                  required
                  placeholder="seu@email.com"
                  autoComplete="email"
                />
              </div>
            </div>

            <div className="field">
              <label htmlFor="password">Senha</label>
              <div className="input-wrap">
                <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                <input
                  id="password"
                  type="password"
                  name="password"
                  required
                  placeholder="••••••••"
                  autoComplete="current-password"
                />
              </div>
            </div>

            <button type="submit" disabled={isPending} className="submit-btn">
              {isPending ? (
                <><span className="spinner" />Entrando...</>
              ) : (
                "Entrar"
              )}
            </button>
          </form>

          <div className="login-footer">
            Não tem uma conta?{" "}
            <a href="/register">Cadastre-se agora</a>
          </div>

          <div className="login-copy">
            © 2026 KS FoodOps · Todos os direitos reservados
          </div>
        </div>
      </div>
    </>
  )
}
