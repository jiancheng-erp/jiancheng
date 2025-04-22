<template>
    <ProcedureManagement :teams="['裁断', '针车预备', '针车']"></ProcedureManagement>
</template>
<script>
import ProcedureManagement from '../../ProductionSharedPages/ProcedureManagement.vue';
export default {
    components: {
        ProcedureManagement
    }
}
</script>