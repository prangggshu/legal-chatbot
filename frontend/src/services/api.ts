import { MessageType } from '../types';

const API_BASE = '/api';

export const askQuestion = async (query: string): Promise<Partial<MessageType>> => {
    const response = await fetch(`${API_BASE}/ask`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
    });

    if (!response.ok) {
        throw new Error('Failed to ask question');
    }

    const data = await response.json();

    return {
        content: data.answer,
        metadata: {
            answer_source: data.answer_source,
            clause_reference: data.clause_reference,
            confidence_score: data.confidence_score,
            risk_level: data.risk_level,
            risk_reason: data.risk_reason,
        }
    };
};

export const uploadDocument = async (file: File): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        throw new Error('Failed to upload document');
    }

    return await response.json();
};
