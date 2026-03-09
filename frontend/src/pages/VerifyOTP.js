import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Shield, Mail, AlertCircle, CheckCircle } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card } from '../components/ui/card';

const VerifyOTP = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { verifyOTP, resendOTP } = useAuth();
  const [otp, setOtp] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);

  const queryParams = new URLSearchParams(location.search);
  const email = queryParams.get('email');
  const purpose = queryParams.get('purpose') || 'registration';

  useEffect(() => {
    if (!email) {
      setError('No email provided. Please go back to registration.');
    }
  }, [email]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await verifyOTP(email, otp, purpose);
      setSuccess(true);
      if (purpose === 'registration') {
        setTimeout(() => navigate('/login'), 2000);
      } else if (purpose === 'password_reset') {
        // If backend returns a reset_token, you could store it and go to reset password page
        // Here we assume the flow is: after OTP verification, go to reset password page
        // If the backend sends a reset_token, you could pass it in state.
        // For now, we go to reset password with email.
        setTimeout(() => navigate('/reset-password', { state: { email } }), 2000);
      }
    } catch (err) {
      console.error('OTP verification error:', err.response?.data || err.message);
      let errorMsg = 'Invalid or expired OTP';
      if (err.response?.data?.detail) {
        errorMsg = err.response.data.detail;
      } else if (err.response?.data?.message) {
        errorMsg = err.response.data.message;
      }
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setError('');
    setResendLoading(true);
    try {
      await resendOTP(email, purpose);
      alert('A new OTP has been sent to your email.');
    } catch (err) {
      setError('Failed to resend OTP. Please try again.');
    } finally {
      setResendLoading(false);
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

        <h2 className="text-3xl font-bold text-white mb-2 text-center">Verify Your Email</h2>
        <p className="text-gray-400 text-center mb-8">
          {purpose === 'registration'
            ? 'We sent a 6‑digit code to your email. Enter it below to complete registration.'
            : 'Enter the OTP sent to your email to reset your password.'}
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
            <p className="text-green-400 text-sm">
              {purpose === 'registration'
                ? 'Email verified! Redirecting to login...'
                : 'OTP verified! Redirecting...'}
            </p>
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
              value={email || ''}
              disabled
              className="bg-[#0B1120] border-blue-500/30 text-white opacity-75 cursor-not-allowed"
            />
          </div>

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

          <Button
            type="submit"
            disabled={loading || success || !email}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white py-6 rounded-xl font-medium shadow-lg shadow-blue-500/30"
          >
            {loading ? 'Verifying...' : 'Verify OTP'}
          </Button>
        </form>

        <div className="mt-4 text-center">
          <button
            onClick={handleResend}
            disabled={resendLoading || !email}
            className="text-blue-400 hover:text-blue-300 text-sm disabled:opacity-50"
          >
            {resendLoading ? 'Sending...' : 'Resend OTP'}
          </button>
        </div>

        <div className="mt-6 text-center">
          <Link
            to={purpose === 'registration' ? '/register' : '/forgot-password'}
            className="text-gray-500 hover:text-gray-400 text-sm"
          >
            ← Back
          </Link>
        </div>
      </Card>
    </div>
  );
};

export default VerifyOTP;