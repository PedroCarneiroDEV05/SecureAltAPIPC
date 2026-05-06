import { useEffect } from 'react';
import Router from 'next/router';
import { api } from '../services/api';
import toast from 'react-hot-toast';

export default function AuthCallback() {
    useEffect(() => {
        const hash = window.location.hash;
        if (!hash) {
            Router.push('/login');
            return;
        }

        const params = new URLSearchParams(hash.substring(1));
        const accessToken = params.get('access_token');

        if (!accessToken) {
            toast.error('Token não encontrado no retorno do Google.');
            Router.push('/login');
            return;
        }

        window.sessionStorage.setItem('access_token', accessToken);

        api.get('/auth/me')
            .then(() => {
                toast.success('Login via Google realizado!');
                Router.push('/dashboard');
            })
            .catch(() => {
                window.sessionStorage.removeItem('access_token');
                toast.error('Falha na autenticação via Google.');
                Router.push('/login');
            });
    }, []);

    return (
        <div style={{
            minHeight: '100vh',
            backgroundColor: 'var(--bg)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '1rem',
        }}>
            <span className="spinner" style={{ width: '28px', height: '28px', borderTopColor: 'var(--text-muted)', borderColor: 'var(--border)' }} />
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: 0 }}>Finalizando autenticação…</p>
        </div>
    );
}
