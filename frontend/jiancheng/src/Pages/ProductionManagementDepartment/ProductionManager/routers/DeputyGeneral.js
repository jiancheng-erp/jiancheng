import OrderDetails from '../components/OrderDetailView.vue'
import OrdershoeOutSourceApprovalView from "../views/OrdershoeOutSourceApprovalView.vue"
import WagesApprovalPage from "../views/WagesApprovalPage.vue"
export default [
  {
    path: '/productionmanager/productiondetail',
    name: 'deputy-inproduction-details',
    component: OrderDetails,
    props: route => (
      {
        orderId: route.query.orderId,
        orderRId: route.query.orderRId,
      }
    )
  },
  {
    path: '/productionmanager/productionoutsource/orderid=:orderId&ordershoeid=:orderShoeId',
    name: 'deputy-outsource-page',
    component: OrdershoeOutSourceApprovalView,
    props: true
  },
  {
    path: '/productionmanager/productionwageapproval',
    name: 'wage-approval-page',
    component: WagesApprovalPage,
    props: route => (
      {
        orderShoeId: route.query.orderShoeId,
        orderId: route.query.orderId,
      }
    )
  },

]
