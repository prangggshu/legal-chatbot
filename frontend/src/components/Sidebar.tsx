import React from 'react';
import { Plus, MessageSquare, Menu, ChevronLeft, User, Settings } from 'lucide-react';
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
}

export const Sidebar: React.FC<SidebarProps> = ({
    isOpen,
    setIsOpen,
    sessions,
    currentSessionId,
    onNewChat,
    onSelectSession
}) => {
    return (
        <div className={cn(
            "sidebar-container",
            isOpen ? "w-64" : "w-0 overflow-hidden"
        )}>
            <div className="sidebar-content">
                <div className="sidebar-header">
                    <button onClick={onNewChat} className="new-chat-btn">
                        <Plus size={18} />
                        <span>New Chat</span>
                    </button>
                    <button onClick={() => setIsOpen(false)} className="close-sidebar-btn">
                        <ChevronLeft size={18} />
                    </button>
                </div>

                <div className="sidebar-history">
                    <div className="history-label">Recent Chats</div>
                    {sessions.map(session => (
                        <button
                            key={session.id}
                            onClick={() => onSelectSession(session.id)}
                            className={cn(
                                "session-item",
                                currentSessionId === session.id && "active"
                            )}
                        >
                            <MessageSquare size={16} />
                            <span className="truncate">{session.title}</span>
                        </button>
                    ))}
                </div>

                <div className="sidebar-footer">
                    <div className="user-profile">
                        <div className="user-avatar">
                            <User size={20} />
                        </div>
                        <span>Legal Professional</span>
                    </div>
                    <button className="settings-btn">
                        <Settings size={18} />
                    </button>
                </div>
            </div>
        </div>
    );
};
