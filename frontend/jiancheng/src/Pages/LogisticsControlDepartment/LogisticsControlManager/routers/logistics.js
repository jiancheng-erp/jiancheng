import FirstLogisticsOrder from '../views/FirstOrderBOMView.vue'
import SecondLogisticsOrder from '../views/SecondOrderBOMView.vue'
import TestGraph from '../views/TestGraphView.vue'
import CreateAssetPurchaseView from '../views/CreateAssetPurchaseView.vue'
import PackagePurchaseView from '@/components/PackagePurchaseView.vue'
import LastPurchaseView from '@/components/LastPurchaseView.vue'
import CutModelPurchaseView from '@/components/CutModelPurchaseView.vue'
export default [
  {
    path: '/logistics/firstpurchase/orderid=:orderId',
    name: 'logistics-firstpurchase',
    component: FirstLogisticsOrder,
    props: true,
    meta: {
      requiresAuth: true,
      role: [9, 1]
    }
  },
  {
    path: '/logistics/secondpurchase/orderid=:orderId',
    name: 'logistics-secondpurchase',
    component: SecondLogisticsOrder,
    props: true,
    meta: {
      requiresAuth: true,
      role: [9, 8, 1]
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
    path: '/packagepurchase/orderid=:orderid',
    name: 'packagepurchase',
    component: PackagePurchaseView,
    props: true,
    meta: {
      requiresAuth: true,
      role: [3, 9]
    }

  },
  {
    path: '/lastpurchase/orderid=:orderid',
    name: 'lastpurchase',
    component: LastPurchaseView,
    props: true,
    meta: {
      requiresAuth: true,
      role: [3, 9]
    }
  },
  {
    path: '/cutmodelpurchase/orderid=:orderid',
    name: 'cutmodelpurchase',
    component: CutModelPurchaseView,
    props: true,
    meta: {
      requiresAuth: true,
      role: [3, 9]
    }
  }
]