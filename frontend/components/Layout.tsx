import { ReactNode } from 'react';
import { useAuth } from '../context/AuthContext';
import Link from 'next/link';

interface LayoutProps {
    children: ReactNode;
    showNav?: boolean;
}

export default function Layout({ children, showNav = true }: LayoutProps) {
    const { user, signOut, isAuthenticated } = useAuth();

    return (
        <div style={{ minHeight: '100vh', backgroundColor: 'var(--bg)', color: 'var(--text)' }}>
            {showNav && isAuthenticated && (
                <nav style={{
                    borderBottom: '1px solid var(--border)',
                    padding: '0 1.5rem',
                    height: '52px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    position: 'sticky',
                    top: 0,
                    backgroundColor: 'var(--surface)',
                    zIndex: 50,
                }}>
                    <Link
                        href="/dashboard"
                        style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text)', textDecoration: 'none', letterSpacing: '0.02em' }}
                    >
                        SecureAltAPIPC
                    </Link>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
                        <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', display: 'none' }} className="md-show">
                            {user?.email}
                        </span>
                        <button
                            id="nav-signout"
                            onClick={signOut}
                            style={{
                                fontSize: '0.82rem',
                                color: 'var(--text-muted)',
                                background: 'none',
                                border: '1px solid var(--border)',
                                borderRadius: '6px',
                                padding: '0.35rem 0.75rem',
                                cursor: 'pointer',
                                transition: 'color 0.15s ease, border-color 0.15s ease',
                            }}
                            onMouseEnter={e => {
                                (e.currentTarget as HTMLButtonElement).style.color = 'var(--danger)';
                                (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--danger)';
                            }}
                            onMouseLeave={e => {
                                (e.currentTarget as HTMLButtonElement).style.color = 'var(--text-muted)';
                                (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--border)';
                            }}
                        >
                            Sair
                        </button>
                    </div>
                </nav>
            )}

            <main>
                {children}
            </main>
        </div>
    );
}
