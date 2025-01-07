import axios from 'axios';

axios.interceptors.response.use(
    response => response,
    error => {
        if (error.response && error.response.status === 500) {
            return Promise.reject(new Error('服务器内部错误，请联系管理员'));
        }
        return Promise.reject(error);
    }
);

axios.interceptors.request.use(config => {
    config.timeout = 20000; // Apply timeout globally
    return config;
}, error => {
    return Promise.reject(error);
});