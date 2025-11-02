import axios from 'axios';

const axiosInstance = axios.create({
  baseURL: import.meta.env.VITE_APP_API_BASE_URL, // Your API base URL
  timeout: 10000, // Set an appropriate timeout
});

// Add a request interceptor to attach the token before each request
axiosInstance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token'); // Or wherever you store your token
    console.log(token)
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`; // Attach token to request headers
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// You can also add a response interceptor if needed
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle global errors here, like unauthorized access (401)
    if (error.response && error.response.status === 401) {
      // Redirect to login, or log the user out
      console.log('Unauthorized access');
    }
    return Promise.reject(error);
  }
);

export default axiosInstance;