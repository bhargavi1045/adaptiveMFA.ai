import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useAuth } from '@/contexts/AuthContext';
import { registerSchema } from '@/utils/validators';
import { Button } from '@/components/common/Button';
import { Input } from '@/components/common/Input';
import { Alert } from '@/components/common/Alert';
import { ROUTES, APP_NAME } from '@/utils/constants';
import { Lock } from 'lucide-react';

type RegisterFormData = {
  email: string;
  password: string;
  confirmPassword: string;
};

const Register: React.FC = () => {
  const navigate = useNavigate();
  const { register: registerUser } = useAuth();
  const [error, setError] = useState<string>('');

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterFormData) => {
    setError('');
    
    try {
      const response = await registerUser(data.email, data.password, data.confirmPassword);
      
      // Backend returns: { message, user, qr_code_uri, backup_codes, setup_token }
      if (response.qr_code_uri) {
        navigate('/mfa-setup', { 
          state: {
            qr_code_uri: response.qr_code_uri,
            backup_codes: response.backup_codes || [],
            setup_token: response.setup_token,
            user: response.user
          } 
        });
      } else {
        navigate(ROUTES.DASHBOARD, { replace: true });
      }
      
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail || err.message || 'Registration failed. Please try again.';
      setError(errorMessage);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-950 px-4 py-12">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-blue-600">
            <Lock className="h-8 w-8 text-white" />
          </div>
          <h2 className="mt-6 text-3xl font-bold text-white">{APP_NAME}</h2>
          <p className="mt-2 text-sm text-gray-400">
            Create your account to get started
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

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <Input
              label="Email Address"
              type="email"
              placeholder="you@example.com"
              error={errors.email?.message}
              {...register('email')}
              autoComplete="email"
              disabled={isSubmitting}
            />

            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
              error={errors.password?.message}
              {...register('password')}
              autoComplete="new-password"
              disabled={isSubmitting}
              helperText="Must be at least 8 characters with uppercase, lowercase, number, and special character"
            />

            <Input
              label="Confirm Password"
              type="password"
              placeholder="••••••••"
              error={errors.confirmPassword?.message}
              {...register('confirmPassword')}
              autoComplete="new-password"
              disabled={isSubmitting}
            />

            <div className="flex items-start">
              <input
                type="checkbox"
                required
                className="mt-1 h-4 w-4 rounded border-gray-600 bg-gray-800 text-blue-600 focus:ring-blue-500"
              />
              <label className="ml-2 text-sm text-gray-300">
                I agree to the{' '}
                <a href="#" className="text-blue-400 hover:text-blue-300">
                  Terms of Service
                </a>{' '}
                and{' '}
                <a href="#" className="text-blue-400 hover:text-blue-300">
                  Privacy Policy
                </a>
              </label>
            </div>

            <Button
              type="submit"
              variant="primary"
              className="w-full"
              isLoading={isSubmitting}
            >
              Create Account
            </Button>
          </form>

          <div className="mt-6 text-center text-sm">
            <span className="text-gray-400">Already have an account? </span>
            <Link
              to={ROUTES.LOGIN}
              className="font-medium text-blue-400 hover:text-blue-300"
            >
              Sign in
            </Link>
          </div>
        </div>

        <p className="mt-6 text-center text-xs text-gray-600">
          Protected by advanced adaptive multi-factor authentication
        </p>
      </div>
    </div>
  );
};

export default Register;