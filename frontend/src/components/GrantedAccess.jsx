import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';

export default function GrantedAccess() {
    const { token } = useAuth();
    const [grants, setGrants] = useState([]);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const loadGrants = useCallback(() => {
        fetch('http://127.0.0.1:8000/api/access-requests/granted', {
            headers: { Authorization: `Bearer ${token}` },
        })
            .then((res) => res.json())
            .then(setGrants)
            .catch(() => setError('Could not load granted access'));
    }, [token]);

    useEffect(() => {
        loadGrants();
    }, [loadGrants]);

    const handleRevoke = async (userId, resourceId) => {
        setError('');
        setSuccess('');
        try {
            const response = await fetch('http://127.0.0.1:8000/api/access-requests/revoke', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({ user_id: userId, resource_id: resourceId }),
            });
            const data = await response.json();
            if (!response.ok) {
                setError(data.detail || 'Failed to revoke access');
                return;
            }
            setSuccess('Access revoked successfully');
            loadGrants();
        } catch {
            setError('Could not reach the server');
        }
    };

    return (
        <div className="bg-slate-800 rounded-lg p-6 mt-6">
            <h2 className="text-lg font-semibold text-white mb-4">Granted Access</h2>

            {error && (
                <div className="bg-red-900 text-red-200 text-sm p-2 rounded mb-3">{error}</div>
            )}
            {success && (
                <div className="bg-green-900 text-green-200 text-sm p-2 rounded mb-3">{success}</div>
            )}

            {grants.length === 0 ? (
                <p className="text-slate-400 text-sm">No active access grants.</p>
            ) : (
                <table className="w-full text-sm text-left text-slate-300">
                    <thead>
                        <tr className="border-b border-slate-700">
                            <th className="py-2">User</th>
                            <th className="py-2">Resource</th>
                            <th className="py-2">Granted</th>
                            <th className="py-2">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {grants.map((g, i) => (
                            <tr key={i} className="border-b border-slate-700">
                                <td className="py-2">{g.user_id.slice(0, 8)}...</td>
                                <td className="py-2">{g.resource_id.slice(0, 8)}...</td>
                                <td className="py-2">{new Date(g.granted_at).toLocaleDateString()}</td>
                                <td className="py-2">
                                    <button
                                        onClick={() => handleRevoke(g.user_id, g.resource_id)}
                                        className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-xs"
                                    >
                                        Revoke
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    );
}