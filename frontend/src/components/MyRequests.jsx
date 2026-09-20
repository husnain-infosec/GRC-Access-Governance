import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import CreateRequest from './CreateRequest';

const statusColors = {
    PENDING: 'bg-yellow-900 text-yellow-200',
    APPROVED: 'bg-green-900 text-green-200',
    REJECTED: 'bg-red-900 text-red-200',
};

export default function MyRequests() {
    const { token } = useAuth();
    const [requests, setRequests] = useState([]);

    const loadRequests = useCallback(() => {
        fetch('http://127.0.0.1:8000/api/access-requests/me', {
            headers: { Authorization: `Bearer ${token}` },
        })
            .then((res) => res.json())
            .then(setRequests);
    }, [token]);

    useEffect(() => {
        loadRequests();
    }, [loadRequests]);

    return (
        <div>
            <CreateRequest onCreated={loadRequests} />

            <div className="bg-slate-800 rounded-lg p-6">
                <h2 className="text-lg font-semibold text-white mb-4">My Requests</h2>
                {requests.length === 0 ? (
                    <p className="text-slate-400 text-sm">No requests yet.</p>
                ) : (
                    <table className="w-full text-sm text-left text-slate-300">
                        <thead>
                            <tr className="border-b border-slate-700">
                                <th className="py-2">Resource</th>
                                <th className="py-2">Status</th>
                                <th className="py-2">Reason</th>
                                <th className="py-2">Created</th>
                            </tr>
                        </thead>
                        <tbody>
                            {requests.map((r) => (
                                <tr key={r.id} className="border-b border-slate-700">
                                    <td className="py-2">{r.resource_id.slice(0, 8)}...</td>
                                    <td className="py-2">
                                        <span className={`px-2 py-1 rounded text-xs ${statusColors[r.status]}`}>
                                            {r.status}
                                        </span>
                                    </td>
                                    <td className="py-2">{r.reason || '-'}</td>
                                    <td className="py-2">{new Date(r.created_at).toLocaleDateString()}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
}