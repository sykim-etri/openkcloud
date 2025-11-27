// SignInPage.jsx
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Typography, Input, Button } from "@material-tailwind/react";
import { EyeSlashIcon, EyeIcon } from "@heroicons/react/24/solid";
// import { loginUser } from "../utils/mockAuth";

// Base64 URL encoding function
const base64url = (source) => {
  return btoa(source)
    .replace(/=+$/, '')
    .replace(/\+/g, '-')
    .replace(/\//g, '_');
};

  const API_URL = window.ENV?.API_URL || import.meta.env.VITE_API_URL || '';

export const loginUser = async (email, password) => {
  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded"
    },
    credentials: "include",
    body: new URLSearchParams({
      username: email,
      password: password
    })
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Login failed");
  }

  return res.json();
};


export function SignInPage() {
  const [passwordShown, setPasswordShown] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const togglePasswordVisibility = () => setPasswordShown((cur) => !cur);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const result = await loginUser(email, password);

      // Save user information
      localStorage.setItem("user", JSON.stringify(result.user));
      localStorage.setItem("access_token", result.access_token); 
      document.cookie = `access_token=${result.token}; path=/; secure; samesite=strict`;

      // // Generate dummy JWT token (expires in 1 hour)
      // const dummyPayload = { exp: Math.floor(Date.now() / 1000) + 3600 };
      // const base64Payload = base64url(JSON.stringify(dummyPayload));
      // const dummyToken = `dummyHeader.${base64Payload}.dummySignature`;
      // localStorage.setItem("token", dummyToken);
      

      // Redirect based on user role
      if (result.user.role === "admin") {    
        navigate("/admin/home");     
      } else {
        navigate("/user/dashboard");
      }
    } catch (err) {
      console.error("Login error:", err);
      setError(err.message || "Login failed");
      setIsLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 h-screen">
      <div className="flex flex-col justify-center items-center p-8">
        <div className="w-full max-w-md">
          <Typography variant="h3" color="blue-gray" className="mb-2 text-2xl font-medium">
            Sign In
          </Typography>
          <Typography className="mb-16 text-gray-600 font-normal text-[18px]">
            Enter your email and password to sign in
          </Typography>

          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
              {error}
            </div>
          )}

          <form onSubmit={handleLogin} className="text-left">
            <div className="mb-6">
              <label htmlFor="email">
                <Typography variant="small" className="mb-2 block font-medium text-gray-900">
                  Email
                </Typography>
              </label>
              <Input
                id="email"
                color="gray"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                name="email"
                placeholder="name@mail.com"
                className="w-full placeholder:opacity-100 focus:border-t-primary border-t-blue-gray-200 rounded-lg pl-4"
                labelProps={{ className: "hidden" }}
                required
              />
            </div>
            <div className="mb-6">
              <label htmlFor="password">
                <Typography variant="small" className="mb-2 block font-medium text-gray-900">
                  Password
                </Typography>
              </label>
              <div className="relative">
                <Input
                  placeholder="********"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  labelProps={{ className: "hidden" }}
                  className="w-full placeholder:opacity-100 focus:border-t-primary border-t-blue-gray-200 rounded-lg pr-10 pl-4"
                  type={passwordShown ? "text" : "password"}
                  required
                />
                <div
                  className="absolute inset-y-0 right-0 flex items-center pr-3 cursor-pointer"
                  onClick={togglePasswordVisibility}
                >
                  {passwordShown ? (
                    <EyeIcon className="h-5 w-5 text-gray-600" />
                  ) : (
                    <EyeSlashIcon className="h-5 w-5 text-gray-600" />
                  )}
                </div>
              </div>
            </div>
            <div className="flex justify-between items-center mb-6">
              <label className="flex items-center">
                <input type="checkbox" className="mr-2" />
                Remember Me
              </label>
              <Typography as="a" href="#" color="blue-gray" variant="small" className="font-medium">
                Forgot password
              </Typography>
            </div>
            <div>
              <Button 
                type="submit"
                color="blue" 
                size="lg" 
                fullWidth 
                disabled={isLoading}
                className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg"
              >
                {isLoading ? "Signing In..." : "SIGN IN"}
              </Button>
            </div>
          </form>
        </div>
      </div>

      {/* Right information section */}
      <div className="hidden md:flex flex-col justify-center p-12 bg-black bg-[url('https://www.material-tailwind.com/image/dark-image.png')] bg-cover bg-center rounded-tl-3xl rounded-bl-3xl">
        <Typography variant="h3" className="mb-2 text-4xl font-bold text-white">
          Welcome to
        </Typography>
        <Typography variant="h3" className="mb-2 text-4xl font-bold text-blue-700">
          AI SOFTWARE IDE
        </Typography>
        <Typography variant="h3" className="mb-6 text-4xl font-bold text-blue-700">
          AI Software IDE!
        </Typography>
        <Typography className="mb-20 text-white leading-loose">
          AI SOFTWARE IDE is a web page that monitors GPU resources in real-time and allows you to directly deploy available GPU servers.
          You can check GPU usage and memory status at a glance, and easily create new GPU servers with your desired settings, enabling more efficient management and utilization of resources in research or development environments.
        </Typography>
        <Typography className="mb-10 text-white">
          <strong className="underline">Created by</strong>
          <br />
          Okestro &gt; <strong className="text-blue-300">yb.jo</strong>
        </Typography>

        <div className="flex items-center gap-2 text-white">
          <span className="text-yellow-400 text-xl"></span>
          <Typography>Openkcloud</Typography>
        </div>
      </div>
    </div>
  );
}

export default SignInPage;
