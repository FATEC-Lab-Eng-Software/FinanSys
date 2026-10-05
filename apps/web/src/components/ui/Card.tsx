import type { ReactNode } from "react";

type SectionProps = {
    children: ReactNode;
    className?: string;
};

function Card({ children, className = "" }: SectionProps) {
    return (
        <div className={`flex flex-col gap-4 rounded-xl bg-primary p-5 shadow-sm ${className}`}>
            {children}
        </div>
    );
}

function CardHeader({ children, className = "" }: SectionProps) {
    return <div className={`flex items-center justify-between gap-2 ${className}`}>{children}</div>;
}

function CardBody({ children, className = "" }: SectionProps) {
    return <div className={`flex flex-col gap-2 ${className}`}>{children}</div>;
}

function CardFooter({ children, className = "" }: SectionProps) {
    return (
        <div className={`flex items-center justify-between gap-2 border-t border-gray-200 pt-4 ${className}`}>
            {children}
        </div>
    );
}

Card.Header = CardHeader;
Card.Body = CardBody;
Card.Footer = CardFooter;

export default Card;