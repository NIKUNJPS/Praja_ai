import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Shield, Lock, AlertCircle, CheckCircle } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card } from '../components/ui/card';

const ResetPassword = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { resetPassword } = useAuth();
  const [otp, setOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  // Get email from location state (passed from VerifyOTP)
  const email = location.state?.email;

  if (!email) {
    // If no email, redirect to forgot password
    navigate('/forgot-password');
    return null;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    setLoading(true);
    try {
      await resetPassword(email, otp, newPassword);
      setSuccess(true);
      setTimeout(() => navigate('/login'), 2000);
    } catch (err) {
      const detail = err.response?.data?.detail || 'Failed to reset password';
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0B1120] via-[#0F172A] to-[#1E293B] flex items-center justify-center px-6">
      <Card className="w-full max-w-md p-8 bg-gradient-to-br from-blue-950/40 to-purple-950/30 border border-blue-500/30 backdrop-blur-xl">
        <div className="flex items-center justify-center mb-8">
          <Shield className="h-12 w-12 text-blue-500 mr-3" />
          <div>
            <h1 className="text-2xl font-bold text-white">ICIOS</h1>
            <p className="text-sm text-blue-400">Civic Intelligence OS</p>
          </div>
        </div>

        <h2 className="text-3xl font-bold text-white mb-2 text-center">Reset Password</h2>
        <p className="text-gray-400 text-center mb-8">
          Enter the OTP sent to your email and your new password.
        </p>

        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start">
            <AlertCircle className="h-5 w-5 text-red-400 mr-3 flex-shrink-0 mt-0.5" />
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}

        {success && (
          <div className="mb-6 p-4 bg-green-500/10 border border-green-500/30 rounded-lg flex items-start">
            <CheckCircle className="h-5 w-5 text-green-400 mr-3 flex-shrink-0 mt-0.5" />
            <p className="text-green-400 text-sm">Password reset! Redirecting to login...</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">OTP Code</label>
            <Input
              type="text"
              placeholder="123456"
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
              required
              maxLength={6}
              className="bg-[#0B1120] border-blue-500/30 text-white placeholder:text-gray-500 focus:border-blue-500 text-center text-2xl tracking-widest"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              <Lock className="inline h-4 w-4 mr-2" />
              New Password
            </label>
            <Input
              type="password"
              placeholder="••••••••"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              minLength={6}
              className="bg-[#0B1120] border-blue-500/30 text-white placeholder:text-gray-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              <Lock className="inline h-4 w-4 mr-2" />
              Confirm Password
            </label>
            <Input
              type="password"
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              minLength={6}
              className="bg-[#0B1120] border-blue-500/30 text-white placeholder:text-gray-500 focus:border-blue-500"
            />
          </div>

          <Button
            type="submit"
            disabled={loading || success}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white py-6 rounded-xl font-medium shadow-lg shadow-blue-500/30"
          >
            {loading ? 'Resetting...' : 'Reset Password'}
          </Button>
        </form>

        <div className="mt-6 text-center">
          <Link to="/login" className="text-blue-400 hover:text-blue-300 text-sm">
            ← Back to Login
          </Link>
        </div>
      </Card>
    </div>
  );
};

export default ResetPassword;