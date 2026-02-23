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
                "w-full py-6",
                isBot ? "bg-[var(--glass-bg)]" : ""
            )}
        >
            <div className="mx-auto flex w-full max-w-4xl gap-6 px-6">
                <div className="shrink-0">
                    {isBot ? (
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--accent)] text-white">
                            <Bot size={20} />
                        </div>
                    ) : (
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-zinc-700 text-zinc-300">
                            <User size={20} />
                        </div>
                    )}
                </div>

                <div className="flex flex-1 flex-col gap-2">
                    <div className="text-xs font-bold uppercase text-[var(--text-secondary)]">
                        {isBot ? "Legal AI Advisor" : "You"}
                    </div>
                    <div className="break-words whitespace-pre-wrap text-base text-[var(--text-primary)]">
                        {message.content}
                    </div>

                    {isBot && message.metadata && (
                        <div className="mt-4 flex flex-wrap gap-2">
                            {message.metadata.risk_level && (
                                <div className={cn(
                                    "flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold",
                                    message.metadata.risk_level.toLowerCase() === 'high' && 'border-red-500/20 bg-red-500/10 text-red-500',
                                    message.metadata.risk_level.toLowerCase() === 'medium' && 'border-amber-500/20 bg-amber-500/10 text-amber-500',
                                    message.metadata.risk_level.toLowerCase() === 'low' && 'border-emerald-500/20 bg-emerald-500/10 text-emerald-500'
                                )}>
                                    <AlertTriangle size={14} />
                                    <span>Risk: {message.metadata.risk_level}</span>
                                </div>
                            )}
                            {message.metadata.clause_reference && (
                                <div className="flex items-center gap-1.5 rounded-full border border-blue-500/20 bg-blue-500/10 px-2.5 py-1 text-xs font-semibold text-blue-500">
                                    <Shield size={14} />
                                    <span>Ref: {message.metadata.clause_reference}</span>
                                </div>
                            )}
                            {message.metadata.confidence_score !== undefined && (
                                <div className="flex items-center gap-1.5 rounded-full border border-zinc-500/20 bg-zinc-500/10 px-2.5 py-1 text-xs font-semibold text-zinc-400">
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
