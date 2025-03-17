import AdjustUpload from "../views/AdjustUpload.vue";
import BOMReview from "../views/BOMReview.vue";
import RevertCraftSheet from "../views/RevertCraftSheet.vue";
export default [
    {
        path: '/processsheet/orderid=:orderId',
        name: 'technicalmanager-uploadprocesssheet',
        component: AdjustUpload,
        props: true,
        meta: {
          requiresAuth: true,
          role: [3, 5, 6, 8, 1, 17]
        }
    },
    {
        path: '/technicalmanager/secondbomusagereview/orderid=:orderId',
        name: 'technicalmanager-secondbomusagereview',
        component: BOMReview,
        props: true,
        meta: {
          requiresAuth: true,
          role: [5, 17]
        }
    },
    {
        path: '/technicalmanager/revertcraftsheet/orderid=:orderId',
        name: 'technicalmanager-revertcraftsheet',
        component: RevertCraftSheet,
        props: true,
        meta: {
          requiresAuth: true,
          role: [5, 17]
        }
    }
]