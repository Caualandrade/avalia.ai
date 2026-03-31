import React from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import './index.css';

const AppContent = () => {
  const { user, loading } = useAuth();
  const [showRegister, setShowRegister] = React.useState(false);

  React.useEffect(() => {
    const handleSwitch = () => setShowRegister(true);
    window.addEventListener('switch-to-register', handleSwitch);
    return () => window.removeEventListener('switch-to-register', handleSwitch);
  }, []);

  if (loading) return (
    <div style={{ display: 'flex', height: '100vh', justifyContent: 'center', alignItems: 'center' }}>
      <div className="glass-card" style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>Carregando Portal...</div>
    </div>
  );

  if (user) return <Dashboard />;
  
  return showRegister ? (
    <Register onBackToLogin={() => setShowRegister(false)} />
  ) : (
    <Login />
  );
};

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
