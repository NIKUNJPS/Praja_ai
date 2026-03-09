import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../services/api'; // our configured axios instance with interceptors

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // ---------- Logout ----------
  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  }, []);

  // ---------- Fetch current user (using stored token) ----------
  const fetchCurrentUser = useCallback(async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const response = await api.get('/auth/me');
      setUser(response.data);
    } catch (error) {
      console.error('[Auth] Failed to fetch user:', error.response?.data || error.message);
      // If token is invalid, clear storage
      if (error.response?.status === 401) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCurrentUser();
  }, [fetchCurrentUser]);

  // ---------- Login ----------
  const login = async (email, password) => {
    try {
      const response = await api.post('/auth/login', { email, password });
      const { access_token, refresh_token } = response.data;
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      // Immediately fetch user data
      const userResponse = await api.get('/auth/me');
      setUser(userResponse.data);
      
      return response.data;
    } catch (error) {
      console.error('[Auth] Login failed:', error.response?.data || error.message);
      throw error;
    }
  };

  // ---------- Register ----------
  const register = async (email, password, name, role = 'PublicViewer') => {
    try {
      const response = await api.post('/auth/register', { email, password, name, role });
      return response.data; // returns user object (unverified)
    } catch (error) {
      console.error('[Auth] Registration failed:', error.response?.data || error.message);
      throw error;
    }
  };

  // ---------- Verify OTP ----------
  const verifyOTP = async (email, otp, purpose) => {
    try {
      const response = await api.post('/auth/verify-otp', { email, otp, purpose });
      return response.data; // { message: ... } or { reset_token: ... }
    } catch (error) {
      console.error('[Auth] OTP verification failed:', error.response?.data || error.message);
      throw error;
    }
  };

  // ---------- Resend OTP ----------
  const resendOTP = async (email, purpose) => {
    try {
      const response = await api.post('/auth/resend-otp', { email, purpose });
      return response.data; // { message: "OTP sent" }
    } catch (error) {
      console.error('[Auth] Resend OTP failed:', error.response?.data || error.message);
      throw error;
    }
  };

  // ---------- Forgot Password (request OTP) ----------
  const forgotPassword = async (email) => {
    try {
      const response = await api.post('/auth/forgot-password', { email });
      return response.data; // { message: "If the email exists, an OTP has been sent" }
    } catch (error) {
      console.error('[Auth] Forgot password failed:', error.response?.data || error.message);
      throw error;
    }
  };

  // ---------- Reset Password (with OTP) ----------
  const resetPassword = async (email, otp, newPassword) => {
    try {
      const response = await api.post('/auth/reset-password', {
        email,
        otp,
        new_password: newPassword,
      });
      return response.data; // { message: "Password updated successfully" }
    } catch (error) {
      console.error('[Auth] Reset password failed:', error.response?.data || error.message);
      throw error;
    }
  };

  // ---------- Refresh Token (optional, if you need manual refresh) ----------
  const refreshToken = async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) throw new Error('No refresh token');
    try {
      const response = await api.post('/auth/refresh', { refresh_token: refreshToken });
      const { access_token, refresh_token: new_refresh_token } = response.data;
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', new_refresh_token);
      return access_token;
    } catch (error) {
      console.error('[Auth] Token refresh failed:', error);
      logout();
      throw error;
    }
  };

  const value = {
    user,
    loading,
    login,
    register,
    verifyOTP,
    resendOTP,
    forgotPassword,
    resetPassword,
    logout,
    refreshToken, // optional, can be used manually
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;