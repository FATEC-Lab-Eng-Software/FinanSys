"use client";

import { useState, type InputHTMLAttributes } from "react";

type PasswordInputProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & {
  visibilityLabel?: string;
};

export function PasswordInput({ visibilityLabel, ...inputProps }: PasswordInputProps) {
  const [visible, setVisible] = useState(false);
  const labelSuffix = visibilityLabel ? ` ${visibilityLabel}` : "";

  return (
    <>
      <input {...inputProps} type={visible ? "text" : "password"} />
      <button
        className="password-toggle"
        type="button"
        aria-label={`${visible ? "Ocultar" : "Mostrar"} senha${labelSuffix}`}
        aria-pressed={visible}
        onClick={() => setVisible((current) => !current)}
      >
        {visible ? (
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M3 3l18 18M10.6 10.6a2 2 0 002.8 2.8" />
            <path d="M9.9 5.2A10.8 10.8 0 0112 5c5.2 0 8.7 4.5 9.5 6-.4.8-1.5 2.3-3.3 3.7M6.2 6.2C3.9 7.5 2.7 9.4 2.5 11c.8 1.5 4.3 6 9.5 6 1.1 0 2.1-.2 3-.6" />
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6z" />
            <circle cx="12" cy="12" r="2.5" />
          </svg>
        )}
      </button>
    </>
  );
}
