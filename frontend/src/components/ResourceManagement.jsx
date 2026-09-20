import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';

export default function ResourceManagement() {
  const { token } = useAuth();
  const [resources, setResources] = useState([]);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const loadResources = useCallback(() => {
    fetch('http://127.0.0.1:8000/api/resources', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.json())
      .then(setResources)
      .catch(() => setError('Could not load resources'));
  }, [token]);

  useEffect(() => {
    loadResources();
  }, [loadResources]);

  const handleCreate = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    try {
      const response = await fetch('http://127.0.0.1:8000/api/resources', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ name, description }),
      });
      const data = await response.json();
      if (!response.ok) {
        setError(data.detail || 'Failed to create resource');
        return;
      }
      setSuccess('Resource created successfully');
      setName('');
      setDescription('');
      loadResources();
    } catch {
      setError('Could not reach the server');
    }
  };

  const handleDeactivate = async (resourceId) => {
    setError('');
    setSuccess('');
    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/resources/${resourceId}/deactivate`,
        {
          method: 'PATCH',
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      const data = await response.json();
      if (!response.ok) {
        setError(data.detail || 'Failed to deactivate resource');
        return;
      }
      setSuccess('Resource deactivated successfully');
      loadResources();
    } catch {
      setError('Could not reach the server');
    }
  };

  return (
    <div className="bg-slate-800 rounded-lg p-6 mt-6">
      <h2 className="text-lg font-semibold text-white mb-4">Resource Management</h2>

      {error && (
        <div className="bg-red-900 text-red-200 text-sm p-2 rounded mb-3">{error}</div>
      )}
      {success && (
        <div className="bg-green-900 text-green-200 text-sm p-2 rounded mb-3">{success}</div>
      )}

      <form onSubmit={handleCreate} className="flex gap-2 mb-4">
        <input
          type="text"
          placeholder="Resource name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          className="bg-slate-700 text-white p-2 rounded text-sm flex-1"
        />
        <input
          type="text"
          placeholder="Description (optional)"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="bg-slate-700 text-white p-2 rounded text-sm flex-1"
        />
        <button
          type="submit"
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm"
        >
          Add
        </button>
      </form>

      <table className="w-full text-sm text-left text-slate-300">
        <thead>
          <tr className="border-b border-slate-700">
            <th className="py-2">Name</th>
            <th className="py-2">Description</th>
            <th className="py-2">Status</th>
            <th className="py-2">Actions</th>
          </tr>
        </thead>
        <tbody>
          {resources.map((r) => (
            <tr key={r.id} className="border-b border-slate-700">
              <td className="py-2">{r.name}</td>
              <td className="py-2">{r.description || '-'}</td>
              <td className="py-2">{r.is_active ? 'Active' : 'Inactive'}</td>
              <td className="py-2">
                {r.is_active && (
                  <button
                    onClick={() => handleDeactivate(r.id)}
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