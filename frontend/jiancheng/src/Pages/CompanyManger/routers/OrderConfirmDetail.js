import OrderConfirmDetail from '../components/OrderConfirmation/OrderConfirmDetail.vue'

export default [
    {
        path: '/companyManager/orderConfirmDetail/orderid=:orderId',
        name: 'OrderConfirmDetail',
        component: OrderConfirmDetail,
        props: true,
        meta: {
            requiresAuth: true,
            role: [1, 2]
        }
    }
]
