import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';

export default function UserManagement() {
    const { token } = useAuth();
    const [users, setUsers] = useState([]);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const loadUsers = useCallback(() => {
        fetch('http://127.0.0.1:8000/api/users', {
            headers: { Authorization: `Bearer ${token}` },
        })
            .then((res) => res.json())
            .then(setUsers)
            .catch(() => setError('Could not load users'));
    }, [token]);

    useEffect(() => {
        loadUsers();
    }, [loadUsers]);

    const handleRoleChange = async (userId, newRoleId) => {
        setError('');
        setSuccess('');
        try {
            const response = await fetch(`http://127.0.0.1:8000/api/users/${userId}/role`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({ role_id: Number(newRoleId) }),
            });
            const data = await response.json();
            if (!response.ok) {
                setError(data.detail || 'Failed to change role');
                return;
            }
            setSuccess('Role updated successfully');
            loadUsers();
        } catch {
            setError('Could not reach the server');
        }
    };

    const handleDeactivate = async (userId) => {
        setError('');
        setSuccess('');
        try {
            const response = await fetch(`http://127.0.0.1:8000/api/users/${userId}/deactivate`, {
                method: 'PATCH',
                headers: { Authorization: `Bearer ${token}` },
            });
            const data = await response.json();
            if (!response.ok) {
                setError(data.detail || 'Failed to deactivate user');
                return;
            }
            setSuccess('User deactivated successfully');
            loadUsers();
        } catch {
            setError('Could not reach the server');
        }
    };

    return (
        <div className="bg-slate-800 rounded-lg p-6 mt-6">
            <h2 className="text-lg font-semibold text-white mb-4">User Management</h2>

            {error && (
                <div className="bg-red-900 text-red-200 text-sm p-2 rounded mb-3">{error}</div>
            )}
            {success && (
                <div className="bg-green-900 text-green-200 text-sm p-2 rounded mb-3">{success}</div>
            )}

            <table className="w-full text-sm text-left text-slate-300">
                <thead>
                    <tr className="border-b border-slate-700">
                        <th className="py-2">Email</th>
                        <th className="py-2">Role</th>
                        <th className="py-2">Status</th>
                        <th className="py-2">Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {users.map((u) => (
                        <tr key={u.id} className="border-b border-slate-700">
                            <td className="py-2">{u.email}</td>
                            <td className="py-2">
                                <select
                                    value={u.role_id}
                                    onChange={(e) => handleRoleChange(u.id, e.target.value)}
                                    className="bg-slate-700 text-white text-xs rounded p-1"
                                >
                                    <option value={1}>Admin</option>
                                    <option value={2}>Manager</option>
                                    <option value={3}>Employee</option>
                                </select>
                            </td>
                            <td className="py-2">{u.is_active ? 'Active' : 'Inactive'}</td>
                            <td className="py-2">
                                {u.is_active && (
                                    <button
                                        onClick={() => handleDeactivate(u.id)}
                                        className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-xs"
                                    >
                                        Deactivate
                                    </button>
                                )}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}