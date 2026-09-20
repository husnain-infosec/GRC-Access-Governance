import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

export default function CreateRequest({ onCreated }) {
    const { token } = useAuth();
    const [resources, setResources] = useState([]);
    const [resourceId, setResourceId] = useState('');
    const [reason, setReason] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    useEffect(() => {
        fetch('http://127.0.0.1:8000/api/resources', {
            headers: { Authorization: `Bearer ${token}` },
        })
            .then((res) => res.json())
            .then(setResources)
            .catch(() => setError('Could not load resources'));
    }, [token]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');

        try {
            const response = await fetch('http://127.0.0.1:8000/api/access-requests', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({ resource_id: resourceId, reason }),
            });

            const data = await response.json();

            if (!response.ok) {
                setError(data.detail || 'Failed to create request');
                return;
            }

            setSuccess('Request submitted successfully');
            setReason('');
            setResourceId('');
            if (onCreated) onCreated();
        } catch {
            setError('Could not reach the server');
        }
    };

    return (
        <form onSubmit={handleSubmit} className="bg-slate-800 p-6 rounded-lg mb-6">
            <h2 className="text-lg font-semibold text-white mb-4">Request Access</h2>

            {error && (
                <div className="bg-red-900 text-red-200 text-sm p-2 rounded mb-3">{error}</div>
            )}
            {success && (
                <div className="bg-green-900 text-green-200 text-sm p-2 rounded mb-3">{success}</div>
            )}

            <label className="block text-slate-300 text-sm mb-1">Resource</label>
            <select
                value={resourceId}
                onChange={(e) => setResourceId(e.target.value)}
                required
                className="w-full p-2 rounded bg-slate-700 text-white mb-3"
            >
                <option value="">Select a resource</option>
                {resources.map((r) => (
                    <option key={r.id} value={r.id}>
                        {r.name}
                    </option>
                ))}
            </select>

            <label className="block text-slate-300 text-sm mb-1">Reason (optional)</label>
            <textarea
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                className="w-full p-2 rounded bg-slate-700 text-white mb-4"
                rows={2}
            />

            <button
                type="submit"
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded font-medium"
            >
                Submit Request
            </button>
        </form>
    );
}