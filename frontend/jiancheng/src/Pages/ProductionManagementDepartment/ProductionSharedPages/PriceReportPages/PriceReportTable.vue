<template>
    <div>
        <vxe-button v-if="editable" status="primary" @click="pushEvent">新增一行</vxe-button>
        <vxe-button v-if="editable" status="danger" @click="removeSelectEvent">批量删除</vxe-button>
        <vxe-grid ref="gridRef" v-bind="gridOptions">
            <!-- <template #action="{ row }">
                <vxe-button status="danger" @click="removeRow(row)">删除</vxe-button>
            </template> -->
        </vxe-grid>
    </div>
</template>

<script setup>
import { VxeUI } from 'vxe-table'
import { defineProps, onMounted, nextTick, ref, reactive, watch, defineExpose, defineEmits, computed } from 'vue';
import XEUtils from 'xe-utils';

const props = defineProps(['procedureInfo', 'readOnly', 'team', 'tableData']);
const emit = defineEmits(["update-items"]);
const gridRef = ref();

const editable = computed(() => {
    console.log(props.readOnly);
    return !props.readOnly;
});

const procedureEditRender = reactive({
    name: 'ElAutocomplete',
    props: {
        fetchSuggestions(queryString, cb) {
            const results = props.procedureInfo
                .filter(proc => proc.procedureName.toLowerCase().startsWith(queryString.toLowerCase()))
                .map(proc => ({ value: proc.procedureName, price: proc.price }));
            cb(results);
        },
        onSelect(info, row) {
            console.log(info, row);
            row.procedure = info.value;
            row.price = info.price;
        }
    }
});

const sectionEditRender = reactive({
    name: 'VxeSelect',
    options: [
        { label: '前段', value: '前段' },
        { label: '中段', value: '中段' },
        { label: '后段', value: '后段' }
    ]
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
        { type: 'seq', width: 55 },
        props.team === '成型' ? {
            field: 'productionSection',
            title: '工段',
            editRender: editable ? sectionEditRender : null
        } : null,
        {
            field: 'procedure',
            title: '工序',
            editRender: editable ? procedureEditRender : null
        },
        props.team !== '成型' ? {
            field: 'price',
            title: '工价',
            editRender: editable ? { name: 'VxeNumberInput', props: { type: 'amount', min: 0 } } : null
        } : null,
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
    const newRow = { rowId: 0, procedure: '', price: '0.00', note: '' };
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

const injectData = (data) => {
    gridOptions.data = data;
}

const getTableData = () => {
    return gridOptions.data;
}
</script>
