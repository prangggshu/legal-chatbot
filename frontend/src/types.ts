export interface MessageType {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
    metadata?: {
        answer_source?: string;
        clause_reference?: string;
        confidence_score?: number;
        risk_level?: string;
        risk_reason?: string;
    };
}

export interface ChatSession {
    id: string;
    title: string;
    messages: MessageType[];
    updatedAt: Date;
}
