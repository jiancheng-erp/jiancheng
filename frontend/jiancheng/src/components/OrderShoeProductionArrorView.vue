<template>
    <div class="order-lifecycle">
        <div v-for="(status, index) in currentWorkflow" :key="index" class="status-item">
            <div :class="[
                'status-circle',
                { completed: this.$props.status > index, current: this.$props.status === index }
            ]">
            </div>
            <div :class="[
                'status-text',
                { completed: this.$props.status > index, current: this.$props.status === index }
            ]">
                {{ status.stage }}<br />
            </div>
            <div v-if="index < productionWorkflow.length" :class="[
                'status-arrow',
                { completed: this.$props.status > index, current: this.$props.status === index }
            ]">
                →
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: ['status', 'workflowType'],
    data() {
        return {
            currentWorkflow: [],
            productionWorkflow: [
                { stage: '生产前' },
                { stage: '裁断开始' },
                { stage: '裁断结束' },
                { stage: '针车预备开始' },
                { stage: '针车预备结束' },
                { stage: '针车开始' },
                { stage: '针车结束' },
                { stage: '成型开始' },
                { stage: '成型结束' },
                { stage: '生产结束' }
            ],
            outsourceWorkflow: [
                { stage: '外包前' },
                { stage: '材料出库' },
                { stage: '生产中' },
                { stage: '成品入库' },
                { stage: '外包结束' },
            ],
        };
    },
    mounted() {
        if (this.$props.workflowType == 1) {
            this.currentWorkflow = this.productionWorkflow
        }
        else {
            this.currentWorkflow = this.outsourceWorkflow
        }
    },
};
</script>

<style scoped>
.order-lifecycle {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    overflow-x: auto;
    background-color: var(--el-color-white);
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.status-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    margin: 0 10px;
}

.status-circle {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background-color: #ccc;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 5px;
    transition: background-color 0.3s;
}

.status-circle.completed {
    background-color: #28a745;
    /* Green for completed steps */
}

.status-circle.current {
    background-color: #ff9800;
    /* Orange for current step */
}

.status-text {
    font-size: 10px;
    color: #999;
    transition: color 0.3s;
}

.status-text.completed {
    color: #28a745;
    /* Green for completed steps */
    font-weight: bold;
}

.status-text.current {
    color: #ff9800;
    /* Orange for current step */
    font-weight: bold;
}

.status-arrow {
    margin: 0 5px;
    color: #ccc;
    font-size: 16px;
    transition: color 0.3s;
}

.status-arrow.completed {
    color: #28a745;
    /* Green for completed steps */
}

.status-arrow.current {
    color: #ff9800;
    /* Orange for current step */
}
</style>