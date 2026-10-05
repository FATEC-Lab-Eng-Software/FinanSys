"use client";

import { useEffect } from "react";
import type { ReactNode } from "react";

type ModalProps = {
    open: boolean;
    onClose: () => void;
    children: ReactNode;
    labelledBy?: string;
};

export default function Modal({ open, onClose, children, labelledBy }: ModalProps) {
    useEffect(() => {
        if (!open) return;

        function handleKeyDown(event: KeyboardEvent) {
            if (event.key === "Escape") onClose();
        }

        const previousOverflow = document.body.style.overflow;
        document.body.style.overflow = "hidden";
        document.addEventListener("keydown", handleKeyDown);

        return () => {
            document.body.style.overflow = previousOverflow;
            document.removeEventListener("keydown", handleKeyDown);
        };
    }, [open, onClose]);

    if (!open) return null;

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
            onClick={onClose}
        >
            <div
                role="dialog"
                aria-modal="true"
                aria-labelledby={labelledBy}
                className="w-full max-w-md"
                onClick={(event) => event.stopPropagation()}
            >
                {children}
            </div>
        </div>
    );
}