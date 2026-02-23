import React from 'react';
import { Plus, MessageSquare, ChevronLeft, User, LogOut } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface SidebarProps {
    isOpen: boolean;
    setIsOpen: (open: boolean) => void;
    sessions: any[];
    currentSessionId: string;
    onNewChat: () => void;
    onSelectSession: (id: string) => void;
    onLogout: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
    isOpen,
    setIsOpen,
    sessions,
    currentSessionId,
    onNewChat,
    onSelectSession,
    onLogout
}) => {
    return (
        <div className={cn(
            "z-[100] h-full border-r border-[var(--border)] bg-[var(--bg-sidebar)] transition-[width] duration-300 ease-in-out",
            isOpen ? "w-64" : "w-0 overflow-hidden"
        )}>
            <div className="flex h-full w-64 flex-col p-3">
                <div className="mb-6 flex gap-2">
                    <button onClick={onNewChat} className="flex flex-1 items-center gap-3 rounded-lg border border-[var(--border)] px-4 py-3 text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--glass-bg)]">
                        <Plus size={18} />
                        <span>New Chat</span>
                    </button>
                    <button onClick={() => setIsOpen(false)} className="p-3 text-[var(--text-secondary)] hover:text-[var(--text-primary)]">
                        <ChevronLeft size={18} />
                    </button>
                </div>

                <div className="flex flex-1 flex-col gap-1 overflow-y-auto">
                    <div className="p-2 text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)]">Recent Chats</div>
                    {sessions.map(session => (
                        <button
                            key={session.id}
                            onClick={() => onSelectSession(session.id)}
                            className={cn(
                                "flex items-center gap-3 rounded-md px-3 py-3 text-left text-sm text-[var(--text-primary)] hover:bg-[var(--glass-bg)]",
                                currentSessionId === session.id && "bg-[var(--glass-bg)]"
                            )}
                        >
                            <MessageSquare size={16} />
                            <span className="truncate">{session.title}</span>
                        </button>
                    ))}
                </div>

                <div className="mt-auto flex items-center justify-between border-t border-[var(--border)] pt-4">
                    <div className="flex items-center gap-3">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--accent)]">
                            <User size={20} />
                        </div>
                        <span>Legal Professional</span>
                    </div>
                    <button className="text-[var(--text-secondary)] hover:text-red-500" onClick={onLogout}>
                        <LogOut size={18} />
                    </button>
                </div>
            </div>
        </div>
    );
};
