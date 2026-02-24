import { MessageType } from '../types';

const API_BASE = '/api';

export interface AuthResponse {
    status: 'success' | 'error';
    detail?: string;
    access_token?: string;
    token_type?: string;
    username?: string;
    expires_at?: number;
}

export interface UploadResponse {
    status: string;
    chunks_created: number;
    chunks_added: number;
}

export interface RiskAnalysisResponse {
    status: string;
    summary: {
        total_chunks: number;
        risk_sections: number;
        high_risk: number;
        medium_risk: number;
    };
    risk_sections: Array<{
        section_index: number;
        risk_level: string;
        risk_reason: string;
        section_text: string;
    }>;
}

export interface SummarizeResponse {
    status: 'success' | 'error';
    summary?: string;
    detail?: string;
}

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

export const uploadDocument = async (file: File): Promise<UploadResponse> => {
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

export const analyzeDocument = async (): Promise<RiskAnalysisResponse> => {
    const response = await fetch(`${API_BASE}/analyze`, {
        method: 'GET',
    });

    if (!response.ok) {
        throw new Error('Failed to analyze document');
    }

    return await response.json();
};

export const summarizeDocument = async (): Promise<SummarizeResponse> => {
    const response = await fetch(`${API_BASE}/summarize`, {
        method: 'GET',
    });

    if (!response.ok) {
        throw new Error('Failed to summarize document');
    }

    return await response.json();
};

export const loginUser = async (username: string, password: string): Promise<AuthResponse> => {
    const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
        throw new Error('Failed to login');
    }

    return await response.json();
};

export const registerUser = async (username: string, password: string): Promise<AuthResponse> => {
    const response = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
        throw new Error('Failed to register');
    }

    return await response.json();
};

export const verifyAuthToken = async (token: string): Promise<AuthResponse> => {
    const response = await fetch(`${API_BASE}/auth/verify?token=${encodeURIComponent(token)}`, {
        method: 'GET',
    });

    if (!response.ok) {
        throw new Error('Failed to verify token');
    }

    return await response.json();
};

export const logoutUser = async (token: string): Promise<AuthResponse> => {
    const response = await fetch(`${API_BASE}/auth/logout`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token }),
    });

    if (!response.ok) {
        throw new Error('Failed to logout');
    }

    return await response.json();
};
