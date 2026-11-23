export type AssistantRole = "user" | "assistant";

export type AssistantMessage = {
    role: AssistantRole;
    content: string;
    artifacts?: AssistantArtifact[];
    books?: AssistantBook[];
};

export type AssistantArtifact = {
    filename: string;
    content_type: string;
    content_base64: string;
};

export type AssistantBook = {
    title: string;
    authors: string[];
    description: string;
    published_date?: string | null;
    info_link: string;
};

export type AssistantChatResponse = {
    message: string;
    artifacts?: AssistantArtifact[];
    books?: AssistantBook[];
};
