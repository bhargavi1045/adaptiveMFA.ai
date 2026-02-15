import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { mfaCodeSchema } from '@/utils/validators';
import { Button } from '@/components/common/Button';
import { Input } from '@/components/common/Input';
import { Alert } from '@/components/common/Alert';
import { ROUTES } from '@/utils/constants';
import { Shield, ArrowLeft } from 'lucide-react';
import api from '@/services/axios/axiosConfig';
import { useAuth } from '@/contexts/AuthContext';

type MFACodeFormData = {
  code: string;
};

const MFAVerification: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { updateUser } = useAuth();

  const [error, setError] = useState<string>('');
  const [isVerifying, setIsVerifying] = useState(false);

  // Get mfa_token from location state
  const mfaToken = location.state?.mfa_token;
  const email = location.state?.email;

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<MFACodeFormData>({
    resolver: zodResolver(mfaCodeSchema),
  });

  useEffect(() => {
    if (!mfaToken) {
      console.error('No MFA token found, redirecting to login');
      navigate(ROUTES.LOGIN);
    }
  }, [mfaToken, navigate]);

  if (!mfaToken) return null;

  const onSubmit = async (data: MFACodeFormData) => {
    if (!mfaToken) {
      setError('No MFA token. Please login again.');
      return;
    }

    setIsVerifying(true);
    setError('');

    try {
      // Send MFA code verification
      const response = await api.post('/auth/verify-mfa', {
        email: email,
        code: data.code,
      });

      // Store tokens and redirect
      if (response.data.user) {
        updateUser(
          response.data.user
        );
        navigate(ROUTES.DASHBOARD);
      } else {
        setError('Invalid response from server');
      }
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail ||
        'Invalid verification code. Please try again.';
      setError(errorMessage);
      reset();
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-950 px-4 py-12">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-blue-600">
            <Shield className="h-8 w-8 text-white" />
          </div>
          <h2 className="mt-6 text-3xl font-bold text-white">
            Two-Factor Authentication
          </h2>
          <p className="mt-2 text-sm text-gray-400">
            Enter the 6-digit code from your authenticator app
          </p>
        </div>

        <div className="mt-8 rounded-lg bg-gray-900 px-8 py-8 shadow-md border border-gray-800">
          {error && (
            <Alert
              type="error"
              message={error}
              onClose={() => setError('')}
              className="mb-6"
            />
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <Input
              label="Verification Code"
              type="text"
              placeholder="000000"
              maxLength={6}
              error={errors.code?.message}
              {...register('code')}
              autoComplete="one-time-code"
              disabled={isVerifying}
              className="text-center text-2xl tracking-widest"
            />

            <Button
              type="submit"
              variant="primary"
              className="w-full"
              isLoading={isVerifying}
            >
              Verify
            </Button>
          </form>

          <div className="mt-6 space-y-3 text-center text-sm">
            <div className="border-t border-gray-800 pt-4">
              <button
                onClick={() => navigate(ROUTES.LOGIN)}
                className="inline-flex items-center text-gray-400 hover:text-gray-300"
              >
                <ArrowLeft className="mr-1 h-4 w-4" />
                Back to login
              </button>
            </div>
          </div>
        </div>

        <p className="mt-6 text-center text-xs text-gray-600">
          This extra step shows it's really you trying to sign in
        </p>
      </div>
    </div>
  );
};

export default MFAVerification;