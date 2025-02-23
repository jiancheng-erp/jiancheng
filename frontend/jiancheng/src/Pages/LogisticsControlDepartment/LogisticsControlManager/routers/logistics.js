import FirstLogisticsOrder from '../views/FirstOrderBOMView.vue'
import SecondLogisticsOrder from '../views/SecondOrderBOMView.vue'
import TestGraph from '../views/TestGraphView.vue'
import CreateAssetPurchaseView from '../views/CreateAssetPurchaseView.vue'
import PackagePurchaseView from '@/components/PackagePurchaseView.vue'
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
      role: [9, 8]
    }
  },
  {
    path: '/logistics/createassetpurchase/purchaseorderid=:purchaseorderid',
    name: 'logistics-createassetpurchase',
    component: CreateAssetPurchaseView,
    props: true,
    meta: {
      requiresAuth: true,
      role: [9, 8]
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
  {
    path: '/packagepurchase',
    name: 'packagepurchase',
    component: PackagePurchaseView,
    props: true,
    meta: {
      requiresAuth: true,
      role: [3, 9]
    }

  }
]