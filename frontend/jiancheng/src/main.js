import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus, { ElDialog } from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import axios from 'axios'
import print from 'vue3-print-nb'
import VxeUI from 'vxe-pc-ui'
import 'vxe-pc-ui/lib/style.css'
import VxeUITable from 'vxe-table'
import 'vxe-table/lib/style.css'
import VxeUIPluginRenderElement from '@vxe-ui/plugin-render-element'
import '@vxe-ui/plugin-render-element/dist/style.css'

const app = createApp(App)
fetch('/frontend_config.json')
    .then((response) => response.json())
    .then((config) => {
        app.config.globalProperties.$axios = axios
        app.config.globalProperties.$apiBaseUrl = config.api_base_url
        app.config.globalProperties.$setAxiosToken = function () {
            const token = localStorage.getItem('token') // Get token from localStorage
            if (token) {
                axios.defaults.headers.common['Authorization'] = `Bearer ${token}` // Set the Authorization header globally
                axios.defaults.timeout = 10000

            } else {
                delete axios.defaults.headers.common['Authorization'] // Remove the Authorization header if no token is found
                router.push({ name: 'login' }) // Redirect to the login page
            }
        }
        
        const token = localStorage.getItem('token') // Get token from localStorage
        if (token) {
            axios.defaults.headers.common['Authorization'] = `Bearer ${token}` // Set the Authorization header globally
        } else {
            delete axios.defaults.headers.common['Authorization'] // Remove the Authorization header if no token is found
            router.push({ name: 'login' }) // Redirect to the login page
        }
        for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
            app.component(key, component)
        }
        axios.interceptors.response.use(
            response => response, // If the response is successful, return it
            error => {
                if (error.response) {
                    if (error.response.status === 500) {
                        console.error('Internal Server Error:', error.response.data)
                        app.config.globalProperties.$message.error('服务器存在错误，请联系管理员') // Display an error message
                    } else if (error.response.status === 401) {
                        // Handle unauthorized access
                        localStorage.removeItem('token')
                        app.config.globalProperties.$message.error('登陆过期')
                        router.push({ name: 'login' })
                    }
                } else {
                    console.error('Network error or no response from server:', error)
                    app.config.globalProperties.$message.error('网络错误或服务器无响应，请联系管理员') // Display an error message
                }
                return Promise.reject(error) // Reject the error to allow specific handling in requests
            }
        )

        ElDialog.props.top.default = '15px'
        ElDialog.props.closeOnClickModal.default = false

        app.use(createPinia())
        app.use(router)
        app.use(ElementPlus, { locale: zhCn })
        app.use(print)
        VxeUI.use(VxeUIPluginRenderElement)
        app.use(VxeUI)
        app.use(VxeUITable)
        app.mount('#app')
    })

export default app
