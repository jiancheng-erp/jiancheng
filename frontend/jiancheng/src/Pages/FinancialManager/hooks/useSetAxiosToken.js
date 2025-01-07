import axios from 'axios';
import { useRouter } from "vue-router";

export default function () {
  function setAxiosToken () {
    const router = useRouter();
    const token = localStorage.getItem('token') // Get token from localStorage
    if (token) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}` // Set the Authorization header globally
    } else {
        delete axios.defaults.headers.common['Authorization'] // Remove the Authorization header if no token is found
        router.push({ name: 'login' }) // Redirect to the login page
    }
  }
  return {setAxiosToken};
}