import type {
    FormHTMLAttributes,
    InputHTMLAttributes,
    LabelHTMLAttributes,
    ReactNode,
    SelectHTMLAttributes,
} from "react";

type SectionProps = {
    children: ReactNode;
    className?: string;
};

const fieldStyle =
    "w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-700 focus:ring-2 focus:ring-blue-700/20";

function Form({ className = "", ...props }: FormHTMLAttributes<HTMLFormElement>) {
    return <form className={`flex flex-col gap-4 ${className}`} {...props} />;
}

function FormField({ children, className = "" }: SectionProps) {
    return <div className={`flex flex-col gap-1 ${className}`}>{children}</div>;
}

function FormLabel({ className = "", ...props }: LabelHTMLAttributes<HTMLLabelElement>) {
    return <label className={`text-sm font-medium ${className}`} {...props} />;
}

function FormInput({ className = "", ...props }: InputHTMLAttributes<HTMLInputElement>) {
    return <input className={`${fieldStyle} ${className}`} {...props} />;
}

function FormSelect({ className = "", ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
    return <select className={`${fieldStyle} ${className}`} {...props} />;
}

function FormError({ children }: { children?: ReactNode }) {
    if (!children) return null;
    return <p className="text-sm text-red-600">{children}</p>;
}

function FormActions({ children, className = "" }: SectionProps) {
    return <div className={`flex justify-end gap-2 ${className}`}>{children}</div>;
}

Form.Field = FormField;
Form.Label = FormLabel;
Form.Input = FormInput;
Form.Select = FormSelect;
Form.Error = FormError;
Form.Actions = FormActions;

export default Form;