import { createContext, useContext, useEffect, useState } from "react";
// api import removed because it's not used in this file

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadUser() {
      const savedToken = localStorage.getItem("token");

      if (!savedToken) {
        setLoading(false);
        return;
      }

      try {
        setToken(savedToken);

        const savedUser = localStorage.getItem("user");

        setToken(savedToken);

        if (savedUser) {
          setUser(JSON.parse(savedUser));
        }
      } catch {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        setToken(null);
        setUser(null);
      }

      setLoading(false);
    }

    loadUser();
  }, []);

  const login = (jwtToken, currentUser) => {
    localStorage.setItem("token", jwtToken);
    localStorage.setItem("user", JSON.stringify(currentUser));

    setToken(jwtToken);
    setUser(currentUser);
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        setUser,
        login,
        logout,
        loading,
        isAuthenticated: !!token,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}