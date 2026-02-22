import React, { useRef, useEffect } from 'react';
import { MessageType } from '../types';
import { Message } from './Message';

interface ChatAreaProps {
    messages: MessageType[];
    isLoading: boolean;
}

export const ChatArea: React.FC<ChatAreaProps> = ({ messages, isLoading }) => {
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isLoading]);

    return (
        <div className="chat-area-container">
            {messages.length === 0 ? (
                <div className="empty-state">
                    <div className="empty-content">
                        <h1>Legal AI Advisor</h1>
                        <p>Upload a legal document or ask any legal question to get started.</p>
                        <div className="suggestion-grid">
                            <div className="suggestion-card">"Explain the termination clause in this contract."</div>
                            <div className="suggestion-card">"What are the liability limits specified?"</div>
                            <div className="suggestion-card">"Is there a non-compete clause?"</div>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="messages-list">
                    {messages.map((msg) => (
                        <Message key={msg.id} message={msg} />
                    ))}
                    {isLoading && (
                        <div className="loading-indicator">
                            <div className="typing-dot"></div>
                            <div className="typing-dot"></div>
                            <div className="typing-dot"></div>
                        </div>
                    )}
                    <div ref={bottomRef} />
                </div>
            )}
        </div>
    );
};
