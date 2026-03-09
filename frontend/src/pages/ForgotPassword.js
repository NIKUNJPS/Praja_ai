import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Shield, Mail, AlertCircle, CheckCircle } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card } from '../components/ui/card';

const ForgotPassword = () => {
  const navigate = useNavigate();
  const { forgotPassword } = useAuth();
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await forgotPassword(email);
      setSuccess(true);
      // After request, redirect to OTP verification with purpose=password_reset
      setTimeout(() => navigate(`/verify-otp?email=${encodeURIComponent(email)}&purpose=password_reset`), 2000);
    } catch (err) {
      const detail = err.response?.data?.detail || 'Failed to send OTP';
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

        <h2 className="text-3xl font-bold text-white mb-2 text-center">Forgot Password</h2>
        <p className="text-gray-400 text-center mb-8">
          Enter your email and we'll send you an OTP to reset your password.
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
            <p className="text-green-400 text-sm">OTP sent! Redirecting to verification...</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              <Mail className="inline h-4 w-4 mr-2" />
              Email
            </label>
            <Input
              type="email"
              placeholder="admin@icios.in"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="bg-[#0B1120] border-blue-500/30 text-white placeholder:text-gray-500 focus:border-blue-500"
            />
          </div>

          <Button
            type="submit"
            disabled={loading || success}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white py-6 rounded-xl font-medium shadow-lg shadow-blue-500/30"
          >
            {loading ? 'Sending...' : 'Send OTP'}
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

export default ForgotPassword;