import PriceReportView from '../../ProductionSharedPages/PriceReportPages/PriceReportView.vue'

export default [
    {
        path: '/sewingmachine/pricereport',
        name: 'sewingmachine-priceReport',
        component: PriceReportView,
        props: route => (
            {
                orderId: route.query.orderId,
                orderShoeId: route.query.orderShoeId,
                teams: route.query.teams
            })
    },
    {
        path: '/fabriccutting/pricereport',
        name: 'fabriccutting-priceReport',
        component: PriceReportView,
        props: route => (
            {
                orderId: route.query.orderId,
                orderShoeId: route.query.orderShoeId,
                teams: route.query.teams
            })
    }
]