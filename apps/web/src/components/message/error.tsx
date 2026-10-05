import { CircleX } from "lucide-react"

interface ErrorProps {
    title : string
}

export default function Error({ title } : ErrorProps) {
    return (
        <div className="flex flex-row bg-red-50 border-2 border-red-400 rounded-md p-4 gap-2">
            <CircleX/>
            <h4>{title}</h4>
        </div>
    )
}