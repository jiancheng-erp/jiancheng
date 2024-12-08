import FirstWarehouseCreate from '../views/FirstWarehousingView.vue'
import SecondWarehouseCreate from '../views/SecondWarehousingView.vue'
import AdjustUpload from '@/Pages/TechnologyDepartment/TechnicalManager/views/AdjustUpload.vue'
export default [
  {
    path: '/headofwarehouse/firstWarehousing/orderid=:orderId',
    name: 'headofwarehouse-firstWarehousing',
    component: FirstWarehouseCreate,
    props: true,
    meta: {
      requiresAuth: true,
      role: 8
    }
  },
  {
    path: '/headofwarehouse/secondWarehousing/orderid=:orderId',
    name: 'headofwarehouse-secondWarehousing',
    component: SecondWarehouseCreate,
    props: true,
    meta: {
      requiresAuth: true,
      role: 8
    }
  },
  {
    path: '/headofwarehouse/viewprocessheet/orderid=:orderId',
    name: 'headofwarehouse-viewprocessheet',
    component: AdjustUpload,
    props: true,
    meta: {
      requiresAuth: true,
      role: 8
    }
},
]