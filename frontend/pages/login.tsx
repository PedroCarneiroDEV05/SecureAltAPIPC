import { useState, useEffect } from 'react';
import Link from 'next/link';
import Router from 'next/router';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL } from '../services/api';

export default function Login() {
    const { signIn, isAuthenticated, loading } = useAuth();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        if (!loading && isAuthenticated) {
            Router.push('/dashboard');
        }
    }, [isAuthenticated, loading]);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setIsLoading(true);
        await signIn({ email, password });
        setIsLoading(false);
    }

    const handleGoogleLogin = () => {
        window.location.href = `${API_BASE_URL}/auth/google/login`;
    };

    if (loading || isAuthenticated) return null;

    return (
        <div style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '1.5rem',
        }}>
            <div className="card" style={{ width: '100%', maxWidth: '420px' }}>
                <div style={{ marginBottom: '2rem' }}>
                    <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text)', margin: '0 0 0.4rem 0' }}>
                        Entrar
                    </h1>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: 0 }}>
                        Acesse sua conta para continuar
                    </p>
                </div>

                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                    <div>
                        <label className="field-label" htmlFor="login-email">Email</label>
                        <input
                            id="login-email"
                            type="email"
                            required
                            className="input-field"
                            placeholder="exemplo@email.com"
                            value={email}
                            onChange={e => setEmail(e.target.value)}
                        />
                    </div>

                    <div>
                        <label className="field-label" htmlFor="login-password">Senha</label>
                        <input
                            id="login-password"
                            type="password"
                            required
                            className="input-field"
                            placeholder="Sua senha"
                            value={password}
                            onChange={e => setPassword(e.target.value)}
                        />
                    </div>

                    <button
                        id="login-submit"
                        type="submit"
                        disabled={isLoading}
                        className="btn-primary"
                        style={{ marginTop: '0.5rem' }}
                    >
                        {isLoading ? <span className="spinner" /> : 'Entrar'}
                    </button>
                </form>

                <div className="divider">ou</div>

                <button
                    id="login-google"
                    className="btn-secondary"
                    onClick={handleGoogleLogin}
                >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                        <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#555"/>
                        <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#555"/>
                        <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#555"/>
                        <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#555"/>
                    </svg>
                        Entrar com Google
                    </button>

                <p style={{ marginTop: '1.75rem', textAlign: 'center', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                    Não tem uma conta?{' '}
                    <Link href="/register" style={{ color: 'var(--text)', fontWeight: 500 }}>
                        Criar conta
                    </Link>
                </p>
            </div>
        </div>
    );
}
