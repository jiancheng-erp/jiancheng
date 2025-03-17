import UsageCalculationInput from "../views/UsageCalculationInput.vue";
import SecondBOMCreate from "../views/SecondBOMCreateView.vue";
import RevertUsageView from "../views/RevertUsageView.vue";
import RevertSecondUsageView from "../views/RevertSecondUsageView.vue";
export default [
    {
        path: '/usagecalculation/usagecalculationinput/orderid=:orderId',
        name: 'usagecalculation-usagecalculationinput',
        component: UsageCalculationInput,
        props: true,
        meta: {
            requiresAuth: true,
            role: [18, 1]
        }
    },
    {
        path: '/usagecalculation/secondBOM/orderid=:orderId',
        name: 'usagecalculation-secondBOM',
        component: SecondBOMCreate,
        props: true,
        meta: {
          requiresAuth: true,
          role: [18, 1]
        }
    },
    {
        path: '/usagecalculation/revertusagecalculation/orderid=:orderId',
        name: 'usagecalculation-revertusagecalculation',
        component: RevertUsageView,
        props: true,
        meta: {
          requiresAuth: true,
          role: 18
        }
    },
    {
        path: '/usagecalculation/revertsecondusagecalculation/orderid=:orderId',
        name: 'usagecalculation-revertsecondusagecalculation',
        component: RevertSecondUsageView,
        props: true,
        meta: {
          requiresAuth: true,
          role: 18
        }
    }
]