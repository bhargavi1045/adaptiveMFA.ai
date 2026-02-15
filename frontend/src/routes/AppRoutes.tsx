import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { PrivateRoute } from './PrivateRoute';
import { PublicRoute } from './PublicRoute';
import { ROUTES } from '@/utils/constants';

// Pages
import Login from '@/pages/Login';
import Register from '@/pages/Register';
import PasswordReset from '@/pages/PasswordReset';
import Dashboard from '@/pages/Dashboard';
import MFAVerification from '@/pages/MFAVerification';
import MFASetup from '@/pages/MFASetup';
import Settings from '@/pages/Settings';
import NotFound from '@/pages/NotFound';

export const AppRoutes: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route element={<PublicRoute />}>
          <Route path={ROUTES.LOGIN} element={<Login />} />
          <Route path={ROUTES.REGISTER} element={<Register />} />
          <Route
            path={ROUTES.PASSWORD_RESET}
            element={<PasswordReset />}
          />
        </Route>

        {/* MFA routes (semi-public) */}
        <Route path={ROUTES.MFA_SETUP} element={<MFASetup />} />
        <Route
          path={ROUTES.MFA_VERIFICATION}
          element={<MFAVerification />}
        />

        {/* Private routes */}
        <Route element={<PrivateRoute />}>
          <Route path={ROUTES.DASHBOARD} element={<Dashboard />} />
          <Route path={ROUTES.SETTINGS} element={<Settings />} />
        </Route>

        {/* Root redirect */}
        <Route
          path={ROUTES.HOME}
          element={<Navigate to={ROUTES.DASHBOARD} replace />}
        />

        {/* 404 */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
};
