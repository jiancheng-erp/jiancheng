import ProductionOrderCreateView from "../views/ProductionOrderCreateView.vue";
import RevertOrderDealView from "../views/RevertOrderDealView.vue";

export default [
    {
        path: "/developmentmanager/productionorder/create/orderid=:orderId",
        name: "developmentmanager-productionorder-create",
        component: ProductionOrderCreateView,
        props: true,
        meta: {
            requiresAuth: true,
            role: [7,1,17]
        }
    },
    {
        path: "/developmentmanager/revertproductionorder/orderid=:orderId",
        name: "developmentmanager-revertproductionorder",
        component: RevertOrderDealView,
        props: true,
        meta: {
            requiresAuth: true,
            role: [7,17]
        }
    }

];