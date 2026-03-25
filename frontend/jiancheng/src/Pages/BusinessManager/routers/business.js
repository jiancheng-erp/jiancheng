import BusinessOrderDetail from '../views/BusinessOrderDetail.vue'
export default [
  {
    path: '/business/businessorderdetail/orderid=:orderId/admin',
    name: 'business-orderdetail',
    component: BusinessOrderDetail,
    props: true,
    meta: {
      requiresAuth: true,
      role: 4
    }
  },
  {
    path: '/business/businessorderdetail/orderid=:orderId/clerk',
    name: 'business-orderdetail-clerk',
    component: BusinessOrderDetail,
    props: true,
    meta: {
      requiresAuth: true,
      role: 21
    }
  },
  {
    path: '/business/businessorderdetail/orderid=:orderId/finance',
    name: 'business-orderdetail-finance',
    component: BusinessOrderDetail,
    props: true,
    meta: {
      requiresAuth: true,
      role: 10
    }
  },
  // {
  //   path: '/logistics/secondpurchase/orderid=:orderId',
  //   name: 'logistics-secondpurchase',
  //   component: SecondLogisticsOrder,
  //   props: true,
  //   meta: {
  //     requiresAuth: true,
  //     role: 9
  //   }
  // },
  // {
  //   path: '/testgraph',
  //   name: 'testgraph',
  //   component: TestGraph,
  //   props: true,
  //   meta: {
  //     requiresAuth: true,
  //     role: 9
  //   }
  // },
]