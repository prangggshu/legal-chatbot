import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, X, FileText, Upload, ShieldAlert, ScrollText } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface ChatInputProps {
    onSendMessage: (message: string) => void;
    onUploadFile: (file: File) => void;
    onAnalyzeFile: (file?: File) => void;
    onSummarizeFile: (file?: File) => void;
    hasUploadedDocument?: boolean;
    disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, onUploadFile, onAnalyzeFile, onSummarizeFile, hasUploadedDocument = false, disabled }) => {
    const [input, setInput] = useState('');
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleSend = () => {
        if (input.trim() && !disabled) {
            onSendMessage(input.trim());
            setInput('');
        }
    };

    const handleUpload = () => {
        if (selectedFile && !disabled) {
            onUploadFile(selectedFile);
            setSelectedFile(null);
        }
    };

    const handleAnalyze = () => {
        if (!disabled && (selectedFile || hasUploadedDocument)) {
            onAnalyzeFile(selectedFile ?? undefined);
            setSelectedFile(null);
        }
    };

    const handleSummarize = () => {
        if (!disabled && (selectedFile || hasUploadedDocument)) {
            onSummarizeFile(selectedFile ?? undefined);
            setSelectedFile(null);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setSelectedFile(e.target.files[0]);
        }
    };

    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
        }
    }, [input]);

    return (
        <div className="mx-auto w-full max-w-4xl p-6">
            <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-2 shadow-[var(--shadow)]">
                <AnimatePresence>
                    {selectedFile && (
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: 10 }}
                            className="m-2 border-b border-[var(--border)] pb-2"
                        >
                            <div className="flex w-fit items-center gap-2 rounded-lg bg-[var(--glass-bg)] px-3 py-2">
                                <FileText size={16} />
                                <span className="max-w-60 truncate text-sm text-[var(--text-primary)]">{selectedFile.name}</span>
                                <button onClick={() => setSelectedFile(null)} className="p-1 text-[var(--text-secondary)] hover:text-red-500">
                                    <X size={14} />
                                </button>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                <div className="flex items-end gap-2 p-1">
                    <button
                        onClick={() => fileInputRef.current?.click()}
                        className="rounded-lg p-3 text-[var(--text-secondary)] hover:bg-[var(--glass-bg)] hover:text-[var(--text-primary)]"
                        disabled={disabled}
                    >
                        <Paperclip size={20} />
                    </button>

                    <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleFileChange}
                        className="hidden"
                        accept=".pdf,.txt,.doc,.docx"
                    />

                    <textarea
                        ref={textareaRef}
                        rows={1}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Ask a legal question..."
                        disabled={disabled}
                        className="min-h-10 max-h-48 flex-1 resize-none border-none bg-transparent py-3 text-base text-[var(--text-primary)] outline-none"
                    />

                    <button
                        onClick={handleSend}
                        disabled={disabled || !input.trim()}
                        className="rounded-lg bg-[var(--accent)] p-3 text-white transition hover:bg-[var(--accent-hover)] disabled:cursor-not-allowed disabled:opacity-30"
                    >
                        <Send size={20} />
                    </button>
                </div>

                <div className="flex gap-2 px-1 pt-1">
                    <button
                        onClick={handleUpload}
                        disabled={disabled || !selectedFile}
                        className="inline-flex items-center gap-1.5 rounded-md border border-[var(--border)] bg-[var(--glass-bg)] px-3 py-2 text-xs font-semibold text-[var(--text-primary)] hover:border-[var(--accent)] disabled:cursor-not-allowed disabled:opacity-50"
                    >
                        <Upload size={16} />
                        <span>Upload</span>
                    </button>
                    <button
                        onClick={handleAnalyze}
                        disabled={disabled || (!selectedFile && !hasUploadedDocument)}
                        className="inline-flex items-center gap-1.5 rounded-md border border-[var(--border)] bg-[var(--glass-bg)] px-3 py-2 text-xs font-semibold text-[var(--text-primary)] hover:border-[var(--accent)] disabled:cursor-not-allowed disabled:opacity-50"
                    >
                        <ShieldAlert size={16} />
                        <span>Document Analyse</span>
                    </button>
                    <button
                        onClick={handleSummarize}
                        disabled={disabled || (!selectedFile && !hasUploadedDocument)}
                        className="inline-flex items-center gap-1.5 rounded-md border border-[var(--border)] bg-[var(--glass-bg)] px-3 py-2 text-xs font-semibold text-[var(--text-primary)] hover:border-[var(--accent)] disabled:cursor-not-allowed disabled:opacity-50"
                    >
                        <ScrollText size={16} />
                        <span>Summarize</span>
                    </button>
                </div>
                <div className="px-1 pb-1 pt-2 text-center text-[11px] text-[var(--text-secondary)]">
                    Legal AI may provide inaccurate information. Verify important legal matters.
                </div>
            </div>
        </div>
    );
};
