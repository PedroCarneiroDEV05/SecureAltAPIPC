import { useEffect } from 'react';
import Router from 'next/router';
import { useAuth } from '../context/AuthContext';

export default function Home() {
    const { isAuthenticated, loading } = useAuth();

    useEffect(() => {
        if (!loading) {
            if (isAuthenticated) {
                Router.push('/dashboard');
            } else {
                Router.push('/login');
            }
        }
    }, [isAuthenticated, loading]);

    return (
        <div className="min-height-screen flex items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
        </div>
    );
}
