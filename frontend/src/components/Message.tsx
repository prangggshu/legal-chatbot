import React from 'react';
import { Bot, User, Shield, AlertTriangle, Info } from 'lucide-react';
import { MessageType } from '../types';
import { motion } from 'framer-motion';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface MessageProps {
    message: MessageType;
}

export const Message: React.FC<MessageProps> = ({ message }) => {
    const isBot = message.role === 'assistant';

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn(
                "message-wrapper",
                isBot ? "bot-message" : "user-message"
            )}
        >
            <div className="message-container">
                <div className="avatar-wrapper">
                    {isBot ? (
                        <div className="avatar bot-avatar">
                            <Bot size={20} />
                        </div>
                    ) : (
                        <div className="avatar user-avatar-icon">
                            <User size={20} />
                        </div>
                    )}
                </div>

                <div className="content-wrapper">
                    <div className="sender-name">
                        {isBot ? "Legal AI Advisor" : "You"}
                    </div>
                    <div className="message-content">
                        {message.content}
                    </div>

                    {isBot && message.metadata && (
                        <div className="metadata-container">
                            {message.metadata.risk_level && (
                                <div className={cn("risk-badge", message.metadata.risk_level.toLowerCase())}>
                                    <AlertTriangle size={14} />
                                    <span>Risk: {message.metadata.risk_level}</span>
                                </div>
                            )}
                            {message.metadata.clause_reference && (
                                <div className="ref-badge">
                                    <Shield size={14} />
                                    <span>Ref: {message.metadata.clause_reference}</span>
                                </div>
                            )}
                            {message.metadata.confidence_score !== undefined && (
                                <div className="conf-badge">
                                    <Info size={14} />
                                    <span>Conf: {(message.metadata.confidence_score * 100).toFixed(0)}%</span>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </motion.div>
    );
};
