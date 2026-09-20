import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './components/Login';
import MyRequests from './components/MyRequests';
import DepartmentRequests from './components/DepartmentRequests';
import GrantedAccess from './components/GrantedAccess';
import UserManagement from './components/UserManagement';
import ResourceManagement from './components/ResourceManagement';

function AppContent() {
  const { token, user, logout } = useAuth();

  if (!token) {
    return <Login />;
  }

  const roleLabel = user?.role_id === 1 ? 'Admin' : user?.role_id === 2 ? 'Manager' : 'Employee';

  return (
    <div className="min-h-screen bg-slate-900 text-white p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">GRC Access Governance System</h1>
          <p className="text-slate-400 text-sm">Logged in as {roleLabel}</p>
        </div>
        <button
          onClick={logout}
          className="bg-slate-700 hover:bg-slate-600 px-4 py-2 rounded text-sm"
        >
          Logout
        </button>
      </div>

      {user?.role_id === 3 ? (
        <MyRequests />
      ) : (
        <>
          <DepartmentRequests />
          <GrantedAccess />
          {user?.role_id === 1 && (
            <>
              <UserManagement />
              <ResourceManagement />
            </>
          )}
        </>
      )}
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;