import { useState } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import LoginPage from "./pages/Login";
import RegisterPage from "./pages/Register";
import Sidebar from "./pages/Sidebar";
import CollaborativeEditor from "./pages/Editor";
import "./App.css";

function AppContent() {
  const { user, logout, isInitialized } = useAuth();
  const [currentSlug, setCurrentSlug]   = useState(null);
  const [authScreen, setAuthScreen]     = useState("login"); // "login" | "register"

  // Wait for stored token to be validated before deciding what to render.
  // Without this, the login screen flashes for a moment on every refresh.
  if (!isInitialized) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", color: "#999" }}>
        Loading…
      </div>
    );
  }

  // Not logged in: show auth screens
  if (!user) {
    if (authScreen === "login") {
      return (
        <LoginPage
          onSwitch={() => setAuthScreen("register")}
          onSuccess={() => {}}
        />
      );
    }
    return (
      <RegisterPage
        onSwitch={() => setAuthScreen("login")}
        onSuccess={() => {}}
      />
    );
  }

  // Logged in: show main app
  return (
    <div className="app-layout">
      <Sidebar onPageClick={setCurrentSlug} activeSlug={currentSlug} />

      <div className="app-layout__main-column">
        <div className="app-layout__topbar">
          <span>Signed in as <strong>{user.username}</strong></span>
          <button type="button" className="app-layout__signout" onClick={logout}>
            Sign out
          </button>
        </div>

        <div className="app-layout__content">
          {currentSlug ? (
            <CollaborativeEditor pageSlug={currentSlug} username={user.username} />
          ) : (
            <div className="app-layout__placeholder">
              <h2>Welcome, {user.username}</h2>
              <p>Select a page from the sidebar or create a new one to get started.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
