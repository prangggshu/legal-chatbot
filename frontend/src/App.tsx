import { useState, useEffect } from 'react';
import { Menu } from 'lucide-react';
import { Sidebar } from './components/Sidebar';
import { ChatArea } from './components/ChatArea';
import { ChatInput } from './components/ChatInput';
import { MessageType, ChatSession } from './types';
import { askQuestion, uploadDocument } from './services/api';
import './components/Sidebar.css';
import './components/ChatArea.css';
import './components/Message.css';
import './components/ChatInput.css';

function App() {
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [currentSessionId, setCurrentSessionId] = useState<string>('');
    const [isLoading, setIsLoading] = useState(false);

    // Initialize first session
    useEffect(() => {
        if (sessions.length === 0) {
            const newSession: ChatSession = {
                id: Date.now().toString(),
                title: 'New Chat',
                messages: [],
                updatedAt: new Date()
            };
            setSessions([newSession]);
            setCurrentSessionId(newSession.id);
        }
    }, []);

    const currentSession = sessions.find(s => s.id === currentSessionId);

    const handleSendMessage = async (content: string) => {
        if (!currentSessionId) return;

        const userMessage: MessageType = {
            id: Date.now().toString(),
            role: 'user',
            content,
            timestamp: new Date()
        };

        // Update session with user message
        setSessions(prev => prev.map(s => {
            if (s.id === currentSessionId) {
                return {
                    ...s,
                    messages: [...s.messages, userMessage],
                    updatedAt: new Date(),
                    title: s.messages.length === 0 ? content.slice(0, 30) + (content.length > 30 ? '...' : '') : s.title
                };
            }
            return s;
        }));

        setIsLoading(true);

        try {
            const botResponse = await askQuestion(content);

            const botMessage: MessageType = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: botResponse.content || 'Sorry, I couldn\'t generate an answer.',
                timestamp: new Date(),
                metadata: botResponse.metadata
            };

            setSessions(prev => prev.map(s => {
                if (s.id === currentSessionId) {
                    return {
                        ...s,
                        messages: [...s.messages, botMessage],
                        updatedAt: new Date()
                    };
                }
                return s;
            }));
        } catch (error) {
            console.error(error);
            const errorMessage: MessageType = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: 'There was an error connecting to the legal engine. Please try again.',
                timestamp: new Date()
            };
            setSessions(prev => prev.map(s => {
                if (s.id === currentSessionId) {
                    return { ...s, messages: [...s.messages, errorMessage] };
                }
                return s;
            }));
        } finally {
            setIsLoading(false);
        }
    };

    const handleUploadFile = async (file: File) => {
        setIsLoading(true);
        try {
            const result = await uploadDocument(file);
            const systemMessage: MessageType = {
                id: Date.now().toString(),
                role: 'assistant',
                content: `Document "${file.name}" uploaded successfully. ${result.chunks_created} clauses analyzed and indexed. How can I help you with this document?`,
                timestamp: new Date()
            };

            setSessions(prev => prev.map(s => {
                if (s.id === currentSessionId) {
                    return {
                        ...s,
                        messages: [...s.messages, systemMessage],
                        updatedAt: new Date()
                    };
                }
                return s;
            }));
        } catch (error) {
            alert("Failed to upload document");
        } finally {
            setIsLoading(false);
        }
    };

    const handleNewChat = () => {
        const newSession: ChatSession = {
            id: Date.now().toString(),
            title: 'New Chat',
            messages: [],
            updatedAt: new Date()
        };
        setSessions([newSession, ...sessions]);
        setCurrentSessionId(newSession.id);
    };

    return (
        <div className="app-container">
            <Sidebar
                isOpen={isSidebarOpen}
                setIsOpen={setIsSidebarOpen}
                sessions={sessions}
                currentSessionId={currentSessionId}
                onNewChat={handleNewChat}
                onSelectSession={setCurrentSessionId}
            />

            <main className="main-content">
                {!isSidebarOpen && (
                    <button
                        onClick={() => setIsSidebarOpen(true)}
                        className="open-sidebar-btn"
                    >
                        <Menu size={18} />
                    </button>
                )}

                <ChatArea
                    messages={currentSession?.messages || []}
                    isLoading={isLoading}
                />

                <ChatInput
                    onSendMessage={handleSendMessage}
                    onUploadFile={handleUploadFile}
                    disabled={isLoading}
                />
            </main>
        </div>
    );
}

export default App;
