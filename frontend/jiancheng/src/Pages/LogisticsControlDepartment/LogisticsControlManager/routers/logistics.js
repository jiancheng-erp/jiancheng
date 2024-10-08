import FirstLogisticsOrder from '../views/FirstOrderBOMView.vue'
import SecondLogisticsOrder from '../views/SecondOrderBOMView.vue'
import TestGraph from '../views/TestGraphView.vue'
export default [
  {
    path: '/logistics/firstpurchase/orderid=:orderId',
    name: 'logistics-firstpurchase',
    component: FirstLogisticsOrder,
    props: true,
    meta: {
      requiresAuth: true,
      role: 9
    }
  },
  {
    path: '/logistics/secondpurchase/orderid=:orderId',
    name: 'logistics-secondpurchase',
    component: SecondLogisticsOrder,
    props: true,
    meta: {
      requiresAuth: true,
      role: 9
    }
  },
  {
    path: '/testgraph',
    name: 'testgraph',
    component: TestGraph,
    props: true,
    meta: {
      requiresAuth: true,
      role: 9
    }
  },
]