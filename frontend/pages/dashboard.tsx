import { useAuth } from '../context/AuthContext';
import Layout from '../components/Layout';
import ProtectedRoute from '../components/ProtectedRoute';

export default function Dashboard() {
    const { user } = useAuth();

    return (
        <ProtectedRoute>
            <Layout>
                <div style={{ padding: '2rem 1.5rem', maxWidth: '680px', margin: '0 auto' }}>
                    <div className="card" style={{ marginBottom: '1.25rem' }}>
                        <div style={{ marginBottom: '1.5rem' }}>
                            <p style={{ fontSize: '0.75rem', fontWeight: 500, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', margin: '0 0 0.3rem 0' }}>
                                Conta
                            </p>
                            <h1 style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text)', margin: 0 }}>
                                {user?.email}
                            </h1>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                            <div className="info-card">
                                <p style={{ fontSize: '0.7rem', color: 'var(--text-subtle)', textTransform: 'uppercase', letterSpacing: '0.06em', margin: '0 0 0.35rem 0' }}>
                                    Email
                                </p>
                                <p style={{ color: 'var(--text)', fontSize: '0.9rem', margin: 0, wordBreak: 'break-all' }}>
                                    {user?.email}
                                </p>
                            </div>

                            <div className="info-card">
                                <p style={{ fontSize: '0.7rem', color: 'var(--text-subtle)', textTransform: 'uppercase', letterSpacing: '0.06em', margin: '0 0 0.35rem 0' }}>
                                    Provedor
                                </p>
                                <p style={{ color: 'var(--text)', fontSize: '0.9rem', margin: 0, textTransform: 'capitalize' }}>
                                    {user?.provider}
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="info-card">
                        <p style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', margin: '0 0 0.4rem 0' }}>
                            Sessão segura
                        </p>
                        <p style={{ color: 'var(--text-subtle)', fontSize: '0.85rem', margin: 0, lineHeight: 1.6 }}>
                            O sistema utiliza <strong style={{ color: 'var(--text-muted)' }}>Refresh Token Rotation</strong> com armazenamento em Cookies HTTPOnly,
                            mitigando riscos de ataques XSS e garantindo persistência transparente entre sessões.
                        </p>
                    </div>
                </div>
            </Layout>
        </ProtectedRoute>
    );
}
