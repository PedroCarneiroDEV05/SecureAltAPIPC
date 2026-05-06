import { ReactNode, useEffect } from 'react';
import Router from 'next/router';
import { useAuth } from '../context/AuthContext';

interface ProtectedRouteProps {
    children: ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
    const { isAuthenticated, loading } = useAuth();

    useEffect(() => {
        if (!loading && !isAuthenticated) {
            Router.push('/login');
        }
    }, [isAuthenticated, loading]);

    if (loading || !isAuthenticated) {
        return (
            <div style={{
                minHeight: '100vh',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '1rem',
                backgroundColor: 'var(--bg)',
            }}>
                <span className="spinner" style={{ width: '28px', height: '28px', borderTopColor: 'var(--text-muted)', borderColor: 'var(--border)' }} />
                <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: 0 }}>Verificando sessão…</p>
            </div>
        );
    }

    return <>{children}</>;
}
