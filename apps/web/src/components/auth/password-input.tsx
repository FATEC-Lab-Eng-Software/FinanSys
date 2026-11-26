"use client";

import { useState, type InputHTMLAttributes } from "react";

type PasswordInputProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & {
  visibilityLabel?: string;
};

export function PasswordInput({ visibilityLabel, className, ...inputProps }: PasswordInputProps) {
  const [visible, setVisible] = useState(false);
  const labelSuffix = visibilityLabel ? ` ${visibilityLabel}` : "";

  return (
    <>
      <input {...inputProps} className={`h-11 w-full min-w-0 border-0 bg-transparent text-xs text-login-text outline-none placeholder:text-login-input-placeholder autofill:[-webkit-text-fill-color:var(--color-login-text)] autofill:[caret-color:var(--color-login-text)] autofill:[-webkit-box-shadow:inset_0_0_0_1000px_var(--color-login-surface)] ${className ?? ""}`} type={visible ? "text" : "password"} />
      <button
        className="grid size-7 flex-[0_0_28px] cursor-pointer place-items-center rounded-md border-0 bg-transparent p-0 text-login-icon hover:bg-login-password-toggle-hover hover:text-login-blue focus-visible:outline-2 focus-visible:outline-login-focus-ring focus-visible:outline-offset-2"
        type="button"
        aria-label={`${visible ? "Ocultar" : "Mostrar"} senha${labelSuffix}`}
        aria-pressed={visible}
        onClick={() => setVisible((current) => !current)}
      >
        {visible ? (
          <svg className="size-4 fill-none stroke-current stroke-[1.7] [stroke-linecap:round] [stroke-linejoin:round]" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M3 3l18 18M10.6 10.6a2 2 0 002.8 2.8" />
            <path d="M9.9 5.2A10.8 10.8 0 0112 5c5.2 0 8.7 4.5 9.5 6-.4.8-1.5 2.3-3.3 3.7M6.2 6.2C3.9 7.5 2.7 9.4 2.5 11c.8 1.5 4.3 6 9.5 6 1.1 0 2.1-.2 3-.6" />
          </svg>
        ) : (
          <svg className="size-4 fill-none stroke-current stroke-[1.7] [stroke-linecap:round] [stroke-linejoin:round]" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6z" />
            <circle cx="12" cy="12" r="2.5" />
          </svg>
        )}
      </button>
    </>
  );
}
