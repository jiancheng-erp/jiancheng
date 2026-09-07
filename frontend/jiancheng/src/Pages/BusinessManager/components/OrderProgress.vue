<template>
    <OrderProgress :editable="false" :show-prod-detail="false"/>
</template>
<script>
import OrderProgress from '../../ProductionManagementDepartment/ProductionSharedPages/OrderProgress.vue';
export default {
    components: {
        OrderProgress
    },
}
</script>
