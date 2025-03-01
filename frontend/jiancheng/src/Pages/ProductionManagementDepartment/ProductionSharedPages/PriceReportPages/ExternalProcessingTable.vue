<template>
    <div>
        <vxe-button v-if="editable" status="primary" @click="pushEvent">新增一行</vxe-button>
        <vxe-button v-if="editable" status="danger" @click="removeSelectEvent">批量删除</vxe-button>
        <vxe-grid ref="gridRef" v-bind="gridOptions">
        </vxe-grid>
    </div>
</template>

<script setup>
import { VxeUI } from 'vxe-table'
import { defineProps, onMounted, nextTick, ref, reactive, watch, defineExpose, defineEmits, computed } from 'vue';

const props = defineProps(['readOnly', 'tableData', 'supplierOptions']);
const emit = defineEmits(["update-items"]);
const gridRef = ref();

const editable = computed(() => {
    return !props.readOnly;
});

const supplierEditRender = reactive({
    name: 'ElAutocomplete',
    attrs: {
        fetchSuggestions(queryString, cb) {
            const results = props.supplierOptions
                .filter(supplierObj => supplierObj.supplierName.includes(queryString))
                .map(supplierObj => ({ value: supplierObj.supplierName, id: supplierObj.supplierId }));
            cb(results);
        },
    },
    events: {
        select({ $rowIndex, row }, selectedItem) {
            row.supplierName = selectedItem.value;
            row.supplierId = selectedItem.id;
        }
    }
});

// Ensure grid updates when tableData changes
const gridOptions = reactive({
    border: true,
    showOverflow: true,
    height: 400,
    editConfig: {
        trigger: 'click',
        mode: 'cell',
        enabled: editable
    },
    columns: [
        editable ? { type: 'checkbox', width: 70 } : null,
        {
            field: 'procedureName',
            title: '工序',
            editRender: editable ? { name: 'VxeInput', props: { clearable: true } } : null
        },
        {
            field: 'supplierName',
            title: '加工厂家',
            editRender: editable ? supplierEditRender : null
        },
        {
            field: 'price',
            title: '工价',
            editRender: editable ? { name: 'VxeNumberInput', props: { type: 'amount', min: 0 } } : null
        },
        {
            field: 'note',
            title: '备注',
            editRender: editable ? { name: 'VxeInput', props: { clearable: true } } : null
        },
    ].filter(Boolean),
    data: props.tableData
});

// Expose the array for parent access
defineExpose({ gridOptions });

const pushEvent = async () => {
    const newRow = { rowId: 0, procedure: '', supplierId: null, supplierName: '', price: '0.00', note: '' };
    gridOptions.data.push(newRow)
    nextTick(() => {
        const $grid = gridRef.value
        if ($grid) {
            $grid.setEditRow(newRow)
        }
    })
    emit("update-items", gridOptions.data);
}

// Watch for updates in tableData
watch(
    () => props.tableData,
    (newData) => {
        gridOptions.data = newData;
    },
    { deep: true } // Detects changes inside arrays/objects
);

const removeSelectEvent = async () => {
    const $grid = gridRef.value
    if ($grid) {
        const selectRecords = $grid.getCheckboxRecords()
        if (selectRecords.length > 0) {
            gridOptions.data = gridOptions.data.filter(item => !selectRecords.some(row => row._X_ROW_KEY === item._X_ROW_KEY))
            VxeUI.modal.message({
                content: '已删除选中',
                status: 'success'
            })
            emit("update-items", gridOptions.data);
        } else {
            VxeUI.modal.message({
                content: '未选择数据',
                status: 'info'
            })
        }
    }
}
</script>
