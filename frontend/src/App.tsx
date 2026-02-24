import { useState, useEffect } from 'react';
import { Menu, User, Mail, Lock, LogOut } from 'lucide-react';
import { Sidebar } from './components/Sidebar';
import { ChatArea } from './components/ChatArea';
import { ChatInput } from './components/ChatInput';
import { MessageType, ChatSession } from './types';
import {
    askQuestion,
    uploadDocument,
    analyzeDocument,
    summarizeDocument,
    loginUser,
    registerUser,
    verifyAuthToken,
    logoutUser,
} from './services/api';

function App() {
    const [authState, setAuthState] = useState<'login' | 'register'>('login');
    const [authToken, setAuthToken] = useState(() => localStorage.getItem('authToken') || '');
    const [authUsername, setAuthUsername] = useState(() => localStorage.getItem('authUsername') || '');
    const [isAuthenticated, setIsAuthenticated] = useState(() => !!localStorage.getItem('authToken'));
    const [authChecking, setAuthChecking] = useState(() => !!localStorage.getItem('authToken'));
    const [authLoading, setAuthLoading] = useState(false);
    const [authError, setAuthError] = useState('');
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        password: ''
    });
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [currentSessionId, setCurrentSessionId] = useState<string>('');
    const [isLoading, setIsLoading] = useState(false);

    const handleAuthChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const clearAuthState = () => {
        setIsAuthenticated(false);
        setAuthToken('');
        setAuthUsername('');
        localStorage.removeItem('authToken');
        localStorage.removeItem('authUsername');
    };

    const saveAuthState = (token: string, username: string) => {
        setAuthToken(token);
        setAuthUsername(username);
        setIsAuthenticated(true);
        localStorage.setItem('authToken', token);
        localStorage.setItem('authUsername', username);
    };

    const handleAuthSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setAuthError('');
        setAuthLoading(true);

        const username = formData.email.trim();
        const password = formData.password;

        try {
            if (authState === 'register') {
                const registerResponse = await registerUser(username, password);
                if (registerResponse.status !== 'success') {
                    setAuthError(registerResponse.detail || 'Registration failed.');
                    return;
                }
            }

            const loginResponse = await loginUser(username, password);
            if (loginResponse.status !== 'success' || !loginResponse.access_token) {
                setAuthError(loginResponse.detail || 'Login failed.');
                return;
            }

            saveAuthState(loginResponse.access_token, loginResponse.username || username);
        } catch (error) {
            setAuthError('Unable to connect to authentication service.');
        } finally {
            setAuthLoading(false);
        }
    };

    const handleLogout = async () => {
        try {
            if (authToken) {
                await logoutUser(authToken);
            }
        } catch (error) {
            console.error(error);
        } finally {
            clearAuthState();
        }
    };

    useEffect(() => {
        const verifyToken = async () => {
            if (!authToken) {
                setAuthChecking(false);
                return;
            }

            try {
                const response = await verifyAuthToken(authToken);
                if (response.status !== 'success') {
                    clearAuthState();
                    setAuthChecking(false);
                    return;
                }

                if (response.username) {
                    setAuthUsername(response.username);
                    localStorage.setItem('authUsername', response.username);
                }
            } catch (error) {
                clearAuthState();
            } finally {
                setAuthChecking(false);
            }
        };

        verifyToken();
    }, []);

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

    const handleAnalyzeFile = async (file: File) => {
        setIsLoading(true);
        try {
            await uploadDocument(file);
            const result = await analyzeDocument();
            const summary = result.summary;
            const sectionText = result.risk_sections.length > 0
                ? `\n\nRisk area details:\n${result.risk_sections
                    .map(section => [
                        `• Section ${section.section_index} (${section.risk_level})`,
                        `  Reason: ${section.risk_reason || 'Not provided'}`,
                        `  Text: ${section.section_text || 'Not provided'}`,
                    ].join('\n'))
                    .join('\n\n')}`
                : '\n\nRisk area details:\nNo high or medium risk areas detected.';

            const overallRisk = summary.high_risk > 0
                ? 'High'
                : summary.medium_risk > 0
                    ? 'Medium'
                    : 'Low';

            const systemMessage: MessageType = {
                id: Date.now().toString(),
                role: 'assistant',
                content: `Document "${file.name}" uploaded and risk analysis completed.\nTotal sections: ${summary.total_chunks}\nFlagged sections: ${summary.risk_sections}\nHigh risk: ${summary.high_risk}\nMedium risk: ${summary.medium_risk}${sectionText}`,
                timestamp: new Date(),
                metadata: {
                    risk_level: overallRisk,
                    risk_reason: result.risk_sections.length > 0
                        ? `${result.risk_sections.length} risk areas identified`
                        : 'No high or medium risk areas identified',
                    answer_source: 'document_risk_analysis',
                }
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
            alert('Failed to analyze document risks');
        } finally {
            setIsLoading(false);
        }
    };

    const handleSummarizeFile = async (file: File) => {
        setIsLoading(true);
        try {
            await uploadDocument(file);
            const result = await summarizeDocument();

            if (result.status !== 'success' || !result.summary) {
                throw new Error(result.detail || 'Failed to summarize document');
            }

            const summaryMessage: MessageType = {
                id: Date.now().toString(),
                role: 'assistant',
                content: `Summary for "${file.name}":\n\n${result.summary}`,
                timestamp: new Date(),
                metadata: {
                    answer_source: 'document_summary',
                }
            };

            setSessions(prev => prev.map(s => {
                if (s.id === currentSessionId) {
                    return {
                        ...s,
                        messages: [...s.messages, summaryMessage],
                        updatedAt: new Date()
                    };
                }
                return s;
            }));
        } catch (error) {
            alert('Failed to summarize document');
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

    if (authChecking) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-[#0a0a0c]">
                <div className="rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm text-gray-300">
                    Verifying session...
                </div>
            </div>
        );
    }

    if (!isAuthenticated) {
        return (
            <div className="relative min-h-screen overflow-hidden bg-[#0a0a0c] px-4 flex items-center justify-center">
                <div className="absolute right-4 top-4 z-20 inline-flex items-center gap-2 rounded-full border border-red-500/30 bg-red-500/10 px-3 py-1.5 text-sm text-red-400">
                    <User size={14} />
                    <span className="font-medium">Logged out</span>
                </div>

                <form
                    onSubmit={handleAuthSubmit}
                    className="z-10 w-full max-w-[28rem] rounded-2xl border border-white/10 bg-white/[0.06] px-8 py-9 text-center"
                >
                    <h1 className="text-3xl font-semibold text-white">{authState === 'login' ? 'Login' : 'Sign up'}</h1>
                    <p className="mt-2 text-sm text-gray-400">Please sign in to continue</p>

                    {authState !== 'login' && (
                        <div className="mt-4 flex h-12 w-full items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 focus-within:border-blue-500/70">
                            <User size={16} className="shrink-0 text-white/65" />
                            <input
                                type="text"
                                name="name"
                                placeholder="Name"
                                value={formData.name}
                                onChange={handleAuthChange}
                                required
                                className="w-full border-none bg-transparent text-white placeholder:text-white/55 outline-none"
                            />
                        </div>
                    )}

                    <div className="mt-4 flex h-12 w-full items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 focus-within:border-blue-500/70">
                        <Mail size={16} className="shrink-0 text-white/65" />
                        <input
                            type="email"
                            name="email"
                            placeholder="Email id"
                            value={formData.email}
                            onChange={handleAuthChange}
                            required
                            className="w-full border-none bg-transparent text-white placeholder:text-white/55 outline-none"
                        />
                    </div>

                    <div className="mt-4 flex h-12 w-full items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 focus-within:border-blue-500/70">
                        <Lock size={16} className="shrink-0 text-white/65" />
                        <input
                            type="password"
                            name="password"
                            placeholder="Password"
                            value={formData.password}
                            onChange={handleAuthChange}
                            required
                            className="w-full border-none bg-transparent text-white placeholder:text-white/55 outline-none"
                        />
                    </div>

                    <div className="mt-3 text-left">
                        <button type="button" className="text-sm text-indigo-400 hover:underline">Forget password?</button>
                    </div>

                    <button
                        type="submit"
                        disabled={authLoading}
                        className="mt-3 h-11 w-full rounded-full bg-indigo-600 font-semibold text-white transition hover:bg-indigo-500"
                    >
                        {authLoading
                            ? 'Please wait...'
                            : authState === 'login' ? 'Login' : 'Sign up'}
                    </button>

                    {authError && (
                        <p className="mt-3 text-sm text-red-400">{authError}</p>
                    )}

                    <p
                        onClick={() => setAuthState(prev => prev === 'login' ? 'register' : 'login')}
                        className="mt-4 cursor-pointer text-sm text-gray-400"
                    >
                        {authState === 'login' ? "Don't have an account?" : 'Already have an account?'}
                        <span className="ml-1 text-indigo-400 hover:underline">click here</span>
                    </p>
                </form>

                <div className="pointer-events-none absolute inset-0" aria-hidden="true">
                    <div className="absolute left-1/2 top-20 h-[24rem] w-[58rem] -translate-x-1/2 rounded-full bg-gradient-to-tr from-indigo-700/35 to-transparent blur-[56px]" />
                    <div className="absolute bottom-10 right-12 h-[14rem] w-[24rem] rounded-full bg-gradient-to-bl from-indigo-700/35 to-transparent blur-[48px]" />
                </div>
            </div>
        );
    }

    return (
        <div className="flex h-screen w-screen overflow-hidden bg-[var(--bg-primary)]">
            <Sidebar
                isOpen={isSidebarOpen}
                setIsOpen={setIsSidebarOpen}
                sessions={sessions}
                currentSessionId={currentSessionId}
                onNewChat={handleNewChat}
                onSelectSession={setCurrentSessionId}
                onLogout={handleLogout}
            />

            <main className="relative flex h-full flex-1 flex-col overflow-hidden">
                {!isSidebarOpen && (
                    <button
                        onClick={() => setIsSidebarOpen(true)}
                        className="absolute left-4 top-4 z-50 flex items-center justify-center rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)] p-2 text-[var(--text-secondary)] hover:bg-[var(--glass-bg)] hover:text-[var(--text-primary)]"
                    >
                        <Menu size={18} />
                    </button>
                )}

                <div className="absolute right-4 top-4 z-50 flex items-center gap-2">
                    <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-sm text-emerald-400">
                        <User size={14} />
                        <span className="font-medium">{authUsername ? `Logged in: ${authUsername}` : 'Logged in'}</span>
                    </div>
                    <button
                        onClick={handleLogout}
                        className="inline-flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-400 hover:bg-red-500/20"
                    >
                        <LogOut size={16} />
                        <span>Logout</span>
                    </button>
                </div>

                <ChatArea
                    messages={currentSession?.messages || []}
                    isLoading={isLoading}
                />

                <ChatInput
                    onSendMessage={handleSendMessage}
                    onUploadFile={handleUploadFile}
                    onAnalyzeFile={handleAnalyzeFile}
                    onSummarizeFile={handleSummarizeFile}
                    disabled={isLoading}
                />
            </main>
        </div>
    );
}

export default App;
