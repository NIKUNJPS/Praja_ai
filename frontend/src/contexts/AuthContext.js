import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

const API_URL = process.env.REACT_APP_BACKEND_URL;

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('access_token'));
  const [loading, setLoading] = useState(true);

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setToken(null);
    setUser(null);
  }, []);

  const fetchCurrentUser = useCallback(async () => {
    if (!token) {
      console.log('[Auth] No token found, skipping user fetch');
      setLoading(false);
      return;
    }

    try {
      console.log('[Auth] Fetching user with token:', token?.substring(0, 20) + '...');
      const response = await axios.get(`${API_URL}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      console.log('[Auth] User fetched successfully:', response.data);
      setUser(response.data);
    } catch (error) {
      console.error('[Auth] Failed to fetch user:', error.response?.data || error.message);
      logout();
    } finally {
      setLoading(false);
    }
  }, [token, logout]);

  useEffect(() => {
    fetchCurrentUser();
  }, [fetchCurrentUser]);

  const login = async (email, password) => {
    try {
      console.log('[Auth] Login attempt for:', email);
      const response = await axios.post(`${API_URL}/api/auth/login`, { email, password });
      const { access_token, refresh_token } = response.data;
      
      console.log('[Auth] Login successful, storing tokens');
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      setToken(access_token);
      
      // Fetch user data immediately after setting token
      console.log('[Auth] Fetching user data after login');
      const userResponse = await axios.get(`${API_URL}/api/auth/me`, {
        headers: { Authorization: `Bearer ${access_token}` }
      });
      console.log('[Auth] User data fetched:', userResponse.data);
      setUser(userResponse.data);
      
      return response.data;
    } catch (error) {
      console.error('[Auth] Login failed:', error.response?.data || error.message);
      throw error;
    }
  };

  const register = async (email, password, name, role = 'PublicViewer') => {
    const response = await axios.post(`${API_URL}/api/auth/register`, { 
      email, 
      password, 
      name, 
      role 
    });
    return response.data;
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export default AuthContext;