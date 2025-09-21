
import axios from 'axios';

// Base API URL - replace with your actual backend URL
const baseURL = 'http://localhost:8089';

const axiosInstance = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default axiosInstance;
