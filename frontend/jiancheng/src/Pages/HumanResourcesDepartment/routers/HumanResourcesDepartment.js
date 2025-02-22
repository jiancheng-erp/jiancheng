
import SalaryManagementView from "../views/SalaryManagementView.vue";

export default [
    {
        path: '/humanresources/salarymanagement',
        name: 'salarymanagement',
        component: SalaryManagementView,
        props: true,
        meta: {
            requiresAuth: true,
            role: 14
        }
    }
]