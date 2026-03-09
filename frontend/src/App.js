import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

// --- Existing Pages ---
import Landing from './pages/Landing';
import Login from './pages/Login';
import Register from './pages/Register';
import VerifyOTP from './pages/VerifyOTP';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import Dashboard from './pages/Dashboard';
import Analytics from './pages/Analytics';
import NetworkGraph from './pages/NetworkGraph';
import PublicPortal from './pages/PublicPortal';

// --- New Pages for Praja.AI Landing ---
import Platform from './pages/Platform';
import Solutions from './pages/Solutions';
import Mission from './pages/Mission';
import Resources from './pages/Resources';

import './App.css';

// --- Scroll To Top Helper ---
// This ensures that when you navigate to a new page, it starts at the top
const ScrollToTop = () => {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <ScrollToTop /> {/* Activates scroll behavior */}
        <div className="App">
          <Routes>
            {/* --- Public routes --- */}
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/verify-otp" element={<VerifyOTP />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            <Route path="/public" element={<PublicPortal />} />

            {/* --- New Landing Page Routes --- */}
            <Route path="/platform" element={<Platform />} />
            <Route path="/solutions" element={<Solutions />} />
            <Route path="/mission" element={<Mission />} />
            <Route path="/resources" element={<Resources />} />

            {/* --- Protected routes --- */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/analytics"
              element={
                <ProtectedRoute>
                  <Analytics />
                </ProtectedRoute>
              }
            />
            <Route
              path="/network"
              element={
                <ProtectedRoute>
                  <NetworkGraph />
                </ProtectedRoute>
              }
            />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;