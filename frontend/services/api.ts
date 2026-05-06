import axios from 'axios';

interface FailedRequest {
    resolve: (token: string | null) => void;
    reject: (error: Error | null) => void;
}

let isRefreshing = false;
let failedQueue: FailedRequest[] = [];

const processQueue = (error: Error | null, token: string | null = null) => {
    failedQueue.forEach(prom => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve(token);
        }
    });
    failedQueue = [];
};

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
    baseURL: API_BASE_URL,
    withCredentials: true,
});

api.interceptors.request.use(config => {
    const token = typeof window !== 'undefined' ? window.sessionStorage.getItem('access_token') : null;
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

api.interceptors.response.use(
    response => response,
    error => {
        const originalRequest = error.config;
        const requestUrl = String(originalRequest?.url || '');
        const isAuthEndpoint = requestUrl.includes('/auth/login')
            || requestUrl.includes('/auth/register')
            || requestUrl.includes('/auth/me')
            || requestUrl.includes('/auth/refresh')
            || requestUrl.includes('/auth/logout')
            || requestUrl.includes('/auth/admin');
        const hasAccessToken = typeof window !== 'undefined' && !!window.sessionStorage.getItem('access_token');

        if (
            error.response?.status === 401
            && !originalRequest._retry
            && !requestUrl.includes('/auth/refresh')
            && !isAuthEndpoint
            && hasAccessToken
        ) {
            if (isRefreshing) {
                return new Promise((resolve, reject) => {
                    failedQueue.push({ resolve, reject });
                })
                .then(token => {
                    originalRequest.headers.Authorization = `Bearer ${token}`;
                    return api(originalRequest);
                })
                .catch(err => Promise.reject(err));
            }

            originalRequest._retry = true;
            isRefreshing = true;

            return new Promise((resolve, reject) => {
                api.post('/auth/refresh')
                    .then(({ data }) => {
                        const { access_token } = data;

                        window.sessionStorage.setItem('access_token', access_token);

                        api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
                        originalRequest.headers.Authorization = `Bearer ${access_token}`;

                        processQueue(null, access_token);
                        resolve(api(originalRequest));
                    })
                    .catch(err => {
                        processQueue(err, null);
                        window.sessionStorage.removeItem('access_token');
                        if (typeof window !== 'undefined') {
                            window.location.href = '/login';
                        }
                        reject(err);
                    })
                    .finally(() => {
                        isRefreshing = false;
                    });
            });
        }

        return Promise.reject(error);
    }
);
