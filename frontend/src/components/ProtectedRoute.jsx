import { useAuth } from "../context/AuthContext.jsx";

// Wrap any component that requires login.
// If not logged in, shows the auth screen instead.
function ProtectedRoute({ children, fallback }) {
  const { user } = useAuth();
  return user ? children : fallback;
}

export default ProtectedRoute;