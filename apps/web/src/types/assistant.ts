export type AssistantRole = "user" | "assistant";

export type AssistantMessage = {
    role: AssistantRole;
    content: string;
};

export type AssistantChatResponse = {
    message: string;
};
