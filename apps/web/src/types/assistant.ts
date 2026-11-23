export type AssistantRole = "user" | "assistant";

export type AssistantMessage = {
    role: AssistantRole;
    content: string;
    artifacts?: AssistantArtifact[];
};

export type AssistantArtifact = {
    filename: string;
    content_type: string;
    content_base64: string;
};

export type AssistantChatResponse = {
    message: string;
    artifacts?: AssistantArtifact[];
};
