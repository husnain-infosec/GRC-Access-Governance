import { useState } from 'react';
import { jwtDecode } from 'jwt-decode';
import { useAuth } from '../context/AuthContext';

export default function Login() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const { login } = useAuth();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        try {
            const response = await fetch('http://127.0.0.1:8000/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            });

            if (!response.ok) {
                const data = await response.json();
                setError(data.detail || 'Login failed');
                return;
            }

            const data = await response.json();
            const decoded = jwtDecode(data.access_token);
            login(data.access_token, decoded);
        } catch (err) {
            setError('Could not reach the server');
        }
    };

    return (
        <div className="min-h-screen bg-slate-900 flex items-center justify-center">
            <form
                onSubmit={handleSubmit}
                className="bg-slate-800 p-8 rounded-lg shadow-lg w-full max-w-sm"
            >
                <h1 className="text-2xl font-bold text-white mb-6">Sign In</h1>

                {error && (
                    <div className="bg-red-900 text-red-200 text-sm p-3 rounded mb-4">
                        {error}
                    </div>
                )}

                <label className="block text-slate-300 text-sm mb-1">Email</label>
                <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full p-2 rounded bg-slate-700 text-white mb-4 outline-none focus:ring-2 focus:ring-blue-500"
                />

                <label className="block text-slate-300 text-sm mb-1">Password</label>
                <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="w-full p-2 rounded bg-slate-700 text-white mb-6 outline-none focus:ring-2 focus:ring-blue-500"
                />

                <button
                    type="submit"
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded font-medium"
                >
                    Sign In
                </button>
            </form>
        </div>
    );
}