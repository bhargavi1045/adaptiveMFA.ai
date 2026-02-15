import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useAuth } from '@/contexts/AuthContext';
import { loginSchema } from '@/utils/validators';
import { Button } from '@/components/common/Button';
import { Input } from '@/components/common/Input';
import { Alert } from '@/components/common/Alert';
import { ROUTES, APP_NAME } from '@/utils/constants';
import { Lock } from 'lucide-react';
import { generateDeviceId } from '@/utils/helpers';

type LoginFormData = {
  email: string;
  password: string;
};

const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [error, setError] = useState('');

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(loginSchema),
  });

  const getIpAddress = async (): Promise<string> => {
    try {
      const res = await fetch('https://api.ipify.org?format=json');
      const data = await res.json();
      return data.ip || '0.0.0.0';
    } catch {
      return '0.0.0.0';
    }
  };

  // ✅ Use sessionStorage instead of storageService
  const getStableDeviceFingerprint = (): string => {
    try {
      // Check if already stored in session
      const stored = sessionStorage.getItem('device_fp_session');
      if (stored && stored.trim() !== '') {
        return stored;
      }

      // First time: generate and store in session
      const newId = generateDeviceId();
      sessionStorage.setItem('device_fp_session', newId);
      return newId;
    } catch (error) {
      console.warn('sessionStorage not available, generating fresh fingerprint');
      return generateDeviceId();
    }
  };

  const onSubmit = async (data: LoginFormData) => {
    setError('');

    try {
      const ip_address = await getIpAddress();
      const deviceFingerprint = getStableDeviceFingerprint();

      console.log('Login with device fingerprint:', deviceFingerprint.substring(0, 16) + '...');

      const payload = {
        email: data.email,
        password: data.password,
        ip_address,
        user_agent: navigator.userAgent || 'unknown',
        device_fingerprint: deviceFingerprint,
        typing_speed: 0.0,
        key_interval: 0.0,
        key_hold: 0.0,
      };

      const response = await login(payload);
      console.log('Login response:', response);

      // ✅ Check for MFA requirement
      if (response.mfa_required || response.mfa_token) {
        navigate(ROUTES.MFA_VERIFICATION, {
          state: {
            mfa_token: response.mfa_token,
            email: data.email,
            login_event_id: response.login_event_id,
          },
        });
      }
      // ✅ Low-risk login (no MFA needed)
      else if (response.message === 'Login successful') {
        navigate(ROUTES.DASHBOARD);
      } else {
        setError('Unexpected login response. Please try again.');
      }
    } catch (err: any) {
      console.error('Login error:', err);
      const errorMessage =
        err.response?.data?.detail ||
        err.message ||
        'Login failed. Check credentials.';
      setError(errorMessage);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 px-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Lock className="w-10 h-10 text-blue-400" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">{APP_NAME}</h1>
          <p className="text-slate-400">
            Sign in to your account to continue
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <Alert
            type="error"
            message={error}
            onClose={() => setError('')}
            className="mb-6"
          />
        )}

        {/* Login Form */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            e.stopPropagation();
            handleSubmit(onSubmit)();
          }}
          noValidate
          className="space-y-6 bg-slate-800 rounded-lg p-8 border border-slate-700"
        >
          {/* Email */}
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
              Email Address
            </label>
            <Input
              id="email"
              type="email"
              placeholder="you@example.com"
              {...register('email')}
              error={errors.email?.message}
              disabled={isSubmitting}
            />
          </div>

          {/* Password */}
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-slate-300 mb-2">
              Password
            </label>
            <Input
              id="password"
              type="password"
              placeholder="••••••••"
              {...register('password')}
              error={errors.password?.message}
              disabled={isSubmitting}
            />
          </div>

          {/* Remember & Forgot */}
          <div className="flex items-center justify-between text-sm">
            <label className="flex items-center">
              <input
                type="checkbox"
                className="rounded border-slate-600 text-blue-500 focus:ring-blue-500"
                disabled={isSubmitting}
              />
              <span className="ml-2 text-slate-400">Remember me</span>
            </label>
            <Link
              to={ROUTES.PASSWORD_RESET}
              className="text-blue-400 hover:text-blue-300 transition"
            >
              Forgot password?
            </Link>
          </div>

          {/* Submit Button */}
          <Button
            type="submit"
            variant="primary"
            size="lg"
            disabled={isSubmitting}
            isLoading={isSubmitting}
          >
            {isSubmitting ? 'Signing in...' : 'Sign In'}
          </Button>

          {/* Sign Up Link */}
          <div className="text-center text-sm text-slate-400">
            Don't have an account?{' '}
            <Link
              to={ROUTES.REGISTER}
              className="text-blue-400 hover:text-blue-300 transition font-medium"
            >
              Sign up
            </Link>
          </div>
        </form>

        {/* Footer */}
        <div className="mt-6 text-center text-xs text-slate-500">
          Protected by advanced adaptive multi-factor authentication
        </div>
      </div>
    </div>
  );
};

export default Login;