import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, X, FileText } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface ChatInputProps {
    onSendMessage: (message: string) => void;
    onUploadFile: (file: File) => void;
    disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, onUploadFile, disabled }) => {
    const [input, setInput] = useState('');
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleSend = () => {
        if ((input.trim() || selectedFile) && !disabled) {
            if (selectedFile) {
                onUploadFile(selectedFile);
                setSelectedFile(null);
            }
            if (input.trim()) {
                onSendMessage(input.trim());
                setInput('');
            }
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
        <div className="chat-input-container">
            <div className="chat-input-wrapper">
                <AnimatePresence>
                    {selectedFile && (
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: 10 }}
                            className="file-preview"
                        >
                            <div className="file-info">
                                <FileText size={16} />
                                <span className="file-name">{selectedFile.name}</span>
                                <button onClick={() => setSelectedFile(null)} className="remove-file-btn">
                                    <X size={14} />
                                </button>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                <div className="input-row">
                    <button
                        onClick={() => fileInputRef.current?.click()}
                        className="attach-btn"
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
                        className="chat-textarea"
                    />

                    <button
                        onClick={handleSend}
                        disabled={disabled || (!input.trim() && !selectedFile)}
                        className="send-btn"
                    >
                        <Send size={20} />
                    </button>
                </div>
                <div className="input-footer">
                    Legal AI may provide inaccurate information. Verify important legal matters.
                </div>
            </div>
        </div>
    );
};
