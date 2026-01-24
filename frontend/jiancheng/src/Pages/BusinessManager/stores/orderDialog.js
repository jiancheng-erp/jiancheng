import { defineStore } from 'pinia'

export const useOrderDialogStore = defineStore('orderDialog', {
    state: () => ({
        addShoeDialogVis: false,
        addShoeTypeDialogVis: false,
        addColorDialogVis: false,
        addBatchInfoDialogVis: false,
        newOrderTemplateVis: false,
        addCustomerBatchDialogVisible: false,
        customerBatchTemplateVis: false,
        customerBatchTemplateSaveVis: false,
        reUploadImageDialogVis: false,
        orderCreationInfoVis: false,
        orderCreationSecondInfoVis: false,
        shoeForm: {
            shoeId: '',
            shoeRid: '',
            shoeDesigner: '',
            shoeAdjuster: '',
            colorId: '',
            shoeDepartmentId: ''
        },
        shoeColorForm: {
            shoeId: '',
            shoeTypeColors: '',
            colorId: '',
            displayRid: ''
        }
        ,
        addColorForm: {
            shoeId: '',
            shoeRid: '',
            shoeTypeColors: [],
            // when set, should be a reference to the orderShoeTypes row being edited
            editTargetRow: null
        }
    }),
    actions: {
        openAddShoeDialog() {
            this.addShoeDialogVis = true
        },
        closeAddShoeDialog() {
            this.addShoeDialogVis = false
        },
        openAddBatchInfoDialog() {
            this.addBatchInfoDialogVis = true
        },
        closeAddBatchInfoDialog() {
            this.addBatchInfoDialogVis = false
        },
        openCustomerBatchDialog() {
            this.addCustomerBatchDialogVisible = true
        },
        closeCustomerBatchDialog() {
            this.addCustomerBatchDialogVisible = false
        },
        openTemplateDialog() {
            this.newOrderTemplateVis = true
        },
        closeTemplateDialog() {
            this.newOrderTemplateVis = false
        },
        openBatchTemplateDialog() {
            this.customerBatchTemplateVis = true
        },
        closeBatchTemplateDialog() {
            this.customerBatchTemplateVis = false
        },
        openBatchTemplateSaveDialog() {
            this.customerBatchTemplateSaveVis = true
        },
        closeBatchTemplateSaveDialog() {
            this.customerBatchTemplateSaveVis = false
        },
        openReUploadImageDialog() {
            this.reUploadImageDialogVis = true
        },
        closeReUploadImageDialog() {
            this.reUploadImageDialogVis = false
        },
        openOrderCreationDialog() {
            this.orderCreationInfoVis = true
        },
        closeOrderCreationDialog() {
            this.orderCreationInfoVis = false
        },
        openOrderDetailDialog() {
            this.orderCreationSecondInfoVis = true
        },
        closeOrderDetailDialog() {
            this.orderCreationSecondInfoVis = false
        },
        openAddShoeTypeDialog({ shoeRid, shoeId, shoeTypeColors }) {
            this.shoeColorForm.displayRid = shoeRid
            this.shoeColorForm.shoeId = shoeId
            this.shoeColorForm.shoeTypeColors = shoeTypeColors
            this.addShoeTypeDialogVis = true
        },
        openAddColorDialog({ shoeRid, shoeId, shoeTypeColors }) {
            this.addColorForm.shoeRid = shoeRid
            this.addColorForm.shoeId = shoeId
            this.addColorForm.shoeTypeColors = shoeTypeColors || []
            this.addColorDialogVis = true
        },
        closeAddColorDialog() {
            this.addColorDialogVis = false
        },
        resetAddColorForm() {
            this.addColorForm = {
                shoeId: '',
                shoeRid: '',
                shoeTypeColors: [],
                editTargetRow: null
            }
        },
        closeAddShoeTypeDialog() {
            this.addShoeTypeDialogVis = false
        },
        resetShoeForm() {
            this.shoeForm = {
                shoeId: '',
                shoeRid: '',
                shoeDesigner: '',
                shoeAdjuster: '',
                colorId: '',
                shoeDepartmentId: ''
            }
        },
        resetShoeColorForm() {
            this.shoeColorForm = {
                shoeId: '',
                shoeTypeColors: '',
                colorId: '',
                displayRid: ''
            }
        }
    }
})
