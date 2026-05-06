import { useState, useEffect } from 'react';
import Link from 'next/link';
import Router from 'next/router';
import { useAuth } from '../context/AuthContext';

export default function Register() {
    const { signUp, isAuthenticated, loading } = useAuth();
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
        await signUp({ email, password });
        setIsLoading(false);
    }

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
                        Criar conta
                    </h1>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: 0 }}>
                        Preencha os dados abaixo para se registrar
                    </p>
                </div>

                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                    <div>
                        <label className="field-label" htmlFor="register-email">Email</label>
                        <input
                            id="register-email"
                            type="email"
                            required
                            className="input-field"
                            placeholder="exemplo@email.com"
                            value={email}
                            onChange={e => setEmail(e.target.value)}
                        />
                    </div>

                    <div>
                        <label className="field-label" htmlFor="register-password">Senha</label>
                        <input
                            id="register-password"
                            type="password"
                            required
                            minLength={8}
                            className="input-field"
                            placeholder="Mínimo 8 caracteres"
                            value={password}
                            onChange={e => setPassword(e.target.value)}
                        />
                    </div>

                    <button
                        id="register-submit"
                        type="submit"
                        disabled={isLoading}
                        className="btn-primary"
                        style={{ marginTop: '0.5rem' }}
                    >
                        {isLoading ? <span className="spinner" /> : 'Criar conta'}
                    </button>
                </form>

                <p style={{ marginTop: '1.75rem', textAlign: 'center', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                    Já tem uma conta?{' '}
                    <Link href="/login" style={{ color: 'var(--text)', fontWeight: 500 }}>
                        Entrar
                    </Link>
                </p>
            </div>
        </div>
    );
}
