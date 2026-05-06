import { createContext, useEffect, useState, useRef, ReactNode, useContext } from 'react';
import Router from 'next/router';
import { api } from '../services/api';
import toast from 'react-hot-toast';

function formatApiDetail(error: unknown, fallback: string): string {
    const detail = (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
        const parts = detail.map((entry: unknown) => {
            if (entry && typeof entry === 'object' && 'msg' in entry) {
                return String((entry as { msg: string }).msg);
            }
            return typeof entry === 'string' ? entry : JSON.stringify(entry);
        });
        return parts.filter(Boolean).join('; ') || fallback;
    }
    return fallback;
}

interface User {
    id: number;
    email: string;
    provider: string;
    is_admin?: boolean;
}

interface AuthCredentials {
    email?: string;
    password?: string;
}

interface AuthContextData {
    user: User | null;
    isAuthenticated: boolean;
    loading: boolean;
    signIn: (credentials: AuthCredentials) => Promise<void>;
    signUp: (credentials: AuthCredentials) => Promise<void>;
    signOut: () => void;
}

export const AuthContext = createContext({} as AuthContextData);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const initialized = useRef(false);

    const isAuthenticated = !!user;

    useEffect(() => {
        if (initialized.current) return;
        initialized.current = true;

        async function restoreSession() {
            try {
                const res = await api.get('/auth/me');
                setUser(res.data);
            } catch (firstErr: unknown) {
                const status = (firstErr as { response?: { status?: number } })?.response?.status;

                if (status !== 401) {
                    setUser(null);
                    setLoading(false);
                    return;
                }

                try {
                    const refreshRes = await api.post('/auth/refresh');
                    const { access_token } = refreshRes.data;
                    window.sessionStorage.setItem('access_token', access_token);

                    const meRes = await api.get('/auth/me');
                    setUser(meRes.data);
                } catch {
                    window.sessionStorage.removeItem('access_token');
                    setUser(null);
                }
            } finally {
                setLoading(false);
            }
        }

        restoreSession();
    }, []);

    async function signIn({ email, password }: AuthCredentials) {
        try {
            const formData = new FormData();
            formData.append('username', email || '');
            formData.append('password', password || '');

            const response = await api.post('/auth/login', formData);
            const { access_token } = response.data;

            window.sessionStorage.setItem('access_token', access_token);

            const userResponse = await api.get('/auth/me');
            setUser(userResponse.data);

            toast.success('Bem-vindo de volta!');
            Router.push('/dashboard');
        } catch (error: unknown) {
            toast.error(formatApiDetail(error, 'Falha no login. Verifique suas credenciais.'));
        }
    }

    async function signUp({ email, password }: AuthCredentials) {
        try {
            await api.post('/auth/register', { email, password });
            toast.success('Conta criada! Faça login para continuar.');
            Router.push('/login');
        } catch (error: unknown) {
            toast.error(formatApiDetail(error, 'Erro ao criar conta.'));
        }
    }

    async function signOut() {
        try {
            await api.post('/auth/logout');
        } catch {
            // Logout no servidor é best-effort.
        } finally {
            window.sessionStorage.removeItem('access_token');
            setUser(null);
            Router.push('/login');
        }
    }

    return (
        <AuthContext.Provider value={{ user, isAuthenticated, loading, signIn, signUp, signOut }}>
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => useContext(AuthContext);
