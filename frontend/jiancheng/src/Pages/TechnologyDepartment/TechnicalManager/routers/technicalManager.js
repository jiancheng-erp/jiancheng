import AdjustUpload from "../views/AdjustUpload.vue";
import BOMReview from "../views/BOMReview.vue";
export default [
    {
        path: '/processsheet/orderid=:orderId',
        name: 'technicalmanager-uploadprocesssheet',
        component: AdjustUpload,
        props: true,
        meta: {
          requiresAuth: true,
          role: [3, 5, 6, 8, 1]
        }
    },
    {
        path: '/technicalmanager/secondbomusagereview/orderid=:orderId',
        name: 'technicalmanager-secondbomusagereview',
        component: BOMReview,
        props: true,
        meta: {
          requiresAuth: true,
          role: 5
        }

    }
]