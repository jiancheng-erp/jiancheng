<template>
    <el-row :gutter="20">
        <el-col :span="24">
            <el-tabs>
                <el-tab-pane label="入库记录">
                    <InboundRecords />
                </el-tab-pane>
                <el-tab-pane label="出库记录">
                    <OutboundRecords />
                </el-tab-pane>
            </el-tabs>
        </el-col>
    </el-row>
</template>
<script>
import InboundRecords from './InboundRecords.vue'
import OutboundRecords from './OutboundRecords.vue'
export default {
    components: {
        InboundRecords,
        OutboundRecords
    }
}
</script>