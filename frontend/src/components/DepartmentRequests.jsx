import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';

export default function DepartmentRequests() {
    const { token } = useAuth();
    const [requests, setRequests] = useState([]);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const loadRequests = useCallback(() => {
        fetch('http://127.0.0.1:8000/api/access-requests/pending', {
            headers: { Authorization: `Bearer ${token}` },
        })
            .then((res) => res.json())
            .then(setRequests)
            .catch(() => setError('Could not load requests'));
    }, [token]);

    useEffect(() => {
        loadRequests();
    }, [loadRequests]);

    const handleDecision = async (requestId, action) => {
        setError('');
        setSuccess('');
        try {
            const response = await fetch(
                `http://127.0.0.1:8000/api/access-requests/${requestId}/${action}`,
                {
                    method: 'POST',
                    headers: { Authorization: `Bearer ${token}` },
                }
            );
            const data = await response.json();
            if (!response.ok) {
                setError(data.detail || `Failed to ${action} request`);
                return;
            }
            setSuccess(`Request ${action}d successfully`);
            loadRequests();
        } catch {
            setError('Could not reach the server');
        }
    };

    return (
        <div className="bg-slate-800 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Pending Requests</h2>

            {error && (
                <div className="bg-red-900 text-red-200 text-sm p-2 rounded mb-3">{error}</div>
            )}
            {success && (
                <div className="bg-green-900 text-green-200 text-sm p-2 rounded mb-3">{success}</div>
            )}

            {requests.length === 0 ? (
                <p className="text-slate-400 text-sm">No pending requests.</p>
            ) : (
                <table className="w-full text-sm text-left text-slate-300">
                    <thead>
                        <tr className="border-b border-slate-700">
                            <th className="py-2">Resource</th>
                            <th className="py-2">Reason</th>
                            <th className="py-2">Created</th>
                            <th className="py-2">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {requests.map((r) => (
                            <tr key={r.id} className="border-b border-slate-700">
                                <td className="py-2">{r.resource_id.slice(0, 8)}...</td>
                                <td className="py-2">{r.reason || '-'}</td>
                                <td className="py-2">{new Date(r.created_at).toLocaleDateString()}</td>
                                <td className="py-2 space-x-2">
                                    <button
                                        onClick={() => handleDecision(r.id, 'approve')}
                                        className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-xs"
                                    >
                                        Approve
                                    </button>
                                    <button
                                        onClick={() => handleDecision(r.id, 'reject')}
                                        className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-xs"
                                    >
                                        Reject
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