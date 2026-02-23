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
        <div className="flex flex-1 flex-col overflow-y-auto scroll-smooth">
            {messages.length === 0 ? (
                <div className="flex flex-1 items-center justify-center px-8 text-center">
                    <div className="max-w-3xl">
                        <h1 className="mb-4 bg-gradient-to-br from-white to-zinc-400 bg-clip-text text-4xl font-semibold text-transparent">Legal AI Advisor</h1>
                        <p className="mb-12 text-lg text-zinc-400">Upload a legal document or ask any legal question to get started.</p>
                        <div className="mb-8 grid grid-cols-1 gap-4 md:grid-cols-3">
                            <div className="rounded-xl border border-white/10 bg-white/5 p-4 text-sm text-white transition hover:-translate-y-0.5 hover:border-blue-500 hover:bg-white/10">"Explain the termination clause in this contract."</div>
                            <div className="rounded-xl border border-white/10 bg-white/5 p-4 text-sm text-white transition hover:-translate-y-0.5 hover:border-blue-500 hover:bg-white/10">"What are the liability limits specified?"</div>
                            <div className="rounded-xl border border-white/10 bg-white/5 p-4 text-sm text-white transition hover:-translate-y-0.5 hover:border-blue-500 hover:bg-white/10">"Is there a non-compete clause?"</div>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="mx-auto flex w-full max-w-4xl flex-col gap-4 py-8">
                    {messages.map((msg) => (
                        <Message key={msg.id} message={msg} />
                    ))}
                    {isLoading && (
                        <div className="mx-auto flex w-full max-w-4xl gap-1.5 py-6">
                            <div className="h-2 w-2 animate-bounce rounded-full bg-zinc-400"></div>
                            <div className="h-2 w-2 animate-bounce rounded-full bg-zinc-400 [animation-delay:120ms]"></div>
                            <div className="h-2 w-2 animate-bounce rounded-full bg-zinc-400 [animation-delay:240ms]"></div>
                        </div>
                    )}
                    <div ref={bottomRef} />
                </div>
            )}
        </div>
    );
};
