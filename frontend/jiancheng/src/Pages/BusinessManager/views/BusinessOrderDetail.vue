<template>
    <el-container>
        <el-header>
            <AllHeader></AllHeader>
        </el-header>
        <el-container>
            <el-main>
                <el-row :gutter="0">
                    <el-col :span="24" :offset="0">
                        <el-descriptions title="" :column="2" border>
                            <el-descriptions-item label="订单编号" align="center">{{
                                orderData.orderRid
                            }}</el-descriptions-item>
                            <el-descriptions-item label="客户订单" align="center">
                                <el-input
                                    style="width: 200px"
                                    v-model="orderData.orderCid"
                                    :disabled="editOrderInfoDisabled"
                                >
                                </el-input>
                            </el-descriptions-item>
                            <el-descriptions-item label="客户信息" align="center">{{
                                orderData.customerInfo
                            }}</el-descriptions-item>
                            <el-descriptions-item label="订单周期" align="center">{{
                                orderData.dateInfo
                            }}</el-descriptions-item>
                        </el-descriptions>
                    </el-col>
                </el-row>
                <el-row :gutter="20">
                    <el-col :span="24" :offset="0">
                        <el-descriptions title="" :column="2" border>
                            <el-descriptions-item label="配码类型" align="center">{{
                                orderData.batchInfoTypeName
                            }}</el-descriptions-item>
                            <el-descriptions-item label="包装资料上传状态" align="center"
                                >{{ orderData.wrapRequirementUploadStatus }}
                                <el-button
                                    v-if=" allowEditInfo
                                    " 
                                type="primary" size="default" @click="openSubmitDialog()"
                                    >上传</el-button
                                >
                                <el-button
                                    v-if="
                                        orderData.wrapRequirementUploadStatus === '已上传包装文件'
                                    "
                                    type="primary"
                                    size="default"
                                    @click="download(2)"
                                    >查看</el-button
                                >
                            </el-descriptions-item>
                            <el-descriptions-item label="订单业务员" align="center">
                                {{ orderData.orderStaffName }}
                            </el-descriptions-item>
                            <el-descriptions-item label="信息操作" align="center">
                                

                                <el-button v-if="allowEditInfo" @click="toggleEditInfo" type="warning">
                                    修改信息
                                </el-button>

                                <el-button v-if="allowEditInfo" @click="submitOrderInfo" type="primary">
                                    提交信息
                                </el-button>

                                <el-button v-if="orderClerkEditable" @click="proceedOrder" type="primary">
                                    提交订单下发
                                </el-button>
                                <el-button
                                    v-if="this.userIsManager && this.readyPending"
                                    type="warning"
                                    @click="sendOrderNext"
                                    :disabled="this.role == 21 ? true : false"
                                >
                                    下发
                                </el-button>

                                <el-button
                                    v-if="this.userIsManager && this.orderManagerEditable"
                                    type="warning"
                                    @click="sendOrderPrevious"
                                    :disabled="this.role == 21 ? true : false"
                                >
                                    退回
                                </el-button>
                                
                            </el-descriptions-item>
                        </el-descriptions>
                    </el-col>
                </el-row>
                <el-table
                    :data="orderShoeData"
                    border
                    stripe
                    height="700"
                    :row-key="
                        (row) => {
                            return `${row.orderShoeId}`
                        }
                    "
                    :default-expand-all="true"
                >
                    <el-table-column type="expand">
                        <template #default="props">
                            <el-table
                                :data="props.row.orderShoeTypes"
                                border
                                :row-key="
                                    (row) => {
                                        return `${row.orderShoeTypeId}`
                                    }
                                "
                                :default-expand-all="true"
                            >
                                <el-table-column type="expand">
                                    <template #default="scope">
                                        <el-table :data="scope.row.shoeTypeBatchInfoList">
                                            <el-table-column type="index"></el-table-column>
                                            <el-table-column
                                                prop="packagingInfoName"
                                                label="配码名称"
                                                width="360"
                                            />
                                            <el-table-column
                                                v-for="col in Object.keys(
                                                    this.attrMappingToRatio
                                                ).filter((key) => this.batchInfoType[key] != '')"
                                                :prop="attrMappingToRatio[col]"
                                                :label="batchInfoType[col]"
                                                width="70"
                                            ></el-table-column>
                                            <el-table-column
                                                prop="totalQuantityRatio"
                                                label="对/件"
                                                width="90"
                                            />
                                            <el-table-column prop="unitPerRatio" label="件数" 
                                            width="90"/>
                                            <el-table-column
                                                prop="total"
                                                label="配码总数"
                                                width="120"></el-table-column>
                                        </el-table>
                                    </template>
                                </el-table-column>
                                <el-table-column
                                    prop="shoeTypeColorName"
                                    label="颜色名称"
                                    width="90"
                                />
                                <el-table-column
                                width="170">
                                    <template #default="scope">
                                    <el-image :src="scope.row.shoeTypeImgUrl"
                                        style="width: 150px; height: 100px" loading="eager" />
                                    </template>
                                </el-table-column>
                                <el-table-column
                                    label="客户颜色"
                                    width="100">
                                <template #default="scope">
                                    <el-input
                                        size="small"
                                        controls-position="right"
                                        v-model="this.orderShoeTypeCustomerColorForm[scope.row.orderShoeTypeId]"
                                        :disabled="editOrderInfoDisabled"
                                    >
                                    </el-input>
                                </template>
                                </el-table-column>
                                
                                <!-- <el-table-column v-for="col in Object.keys(attrMappingToAmount).filter(key=>batchInfoType[key] != null)"
                                        :prop="props.row.orderShoeTypes.shoeTypeBatchData[]"
                                        :label="batchInfoType[col]">
                        </el-table-column> -->
                                <el-table-column
                                    v-for="col in Object.keys(this.attrMappingToAmount).filter(
                                        (key) => this.batchInfoType[key] != ''
                                    )"
                                    :prop="`shoeTypeBatchData.${attrMappingToAmount[col]}`"
                                    :label="batchInfoType[col]"
                                    width="70"
                                ></el-table-column>
                                <el-table-column
                                    prop="shoeTypeBatchData.totalAmount"
                                    label="总数量"
                                    width="90"
                                />
                                <el-table-column label="金额" width="80">
                                    <template #default="scope">
                                        <el-input
                                            size="small"
                                            controls-position="right"
                                            @change="updateValue(scope.row)"
                                            v-model="scope.row.shoeTypeBatchData.unitPrice"
                                            :disabled="editOrderInfoDisabled"
                                        >
                                        </el-input>
                                    </template>
                                </el-table-column>
                                <el-table-column label="金额单位">
                                    <template #default="scope">
                                        <el-input
                                            size="small"
                                            controls-position="right"
                                            @change="updateCurrencyUnit(scope.row)"
                                            v-model="this.orderCurrencyUnit"
                                            :disabled="editOrderInfoDisabled"
                                        >
                                        </el-input>
                                    </template>
                                </el-table-column>
                                <el-table-column
                                    prop="shoeTypeBatchData.totalPrice"
                                    label="总金额"
                                />
                            </el-table>
                        </template>
                    </el-table-column>
                    <el-table-column prop="shoeRid" label="鞋型编号" sortable />
                    <el-table-column label="客户鞋型编号">
                        <template #default="scope">
                            <el-input
                                style="width: 200px"
                                v-model="scope.row.shoeCid"
                                :disabled="editOrderInfoDisabled"
                            >
                            </el-input>
                        </template>
                    </el-table-column>
                    <el-table-column prop="currentStatus" label="鞋型状态" />

                    <el-table-column label="备注">
                        <template #default="scope">
                            <el-button
                                v-if="!scope.row.orderShoeRemarkExist"
                                type="primary"
                                size="default"
                                @click="openRemarkDialog(scope.row)"
                                style="margin-left: 20px"
                                >添加备注
                            </el-button>

                            <el-text v-if="scope.row.orderShoeRemarkExist" style="display: inline-block;">{{
                                scope.row.orderShoeRemarkRep
                            }}</el-text>
                            <el-button
                                v-if="scope.row.orderShoeRemarkExist"
                                type="warning"
                                size="default"
                                @click="openEditRemarkDialog(scope.row)"
                                style="margin-left: 20px"
                            >
                                编辑备注
                            </el-button>
                        </template>
                    </el-table-column>
                </el-table>
            </el-main>
        </el-container>
    </el-container>

    <el-dialog title="鞋型备注" v-model="remarkDialogVis" width="50%">
        <el-form>
            <el-form-item label="工艺备注">
                <el-input
                    type="textarea"
                    :rows="2"
                    v-model="this.remarkForm.technicalRemark"
                    :show-word-limit="true"
                    :maxlength="255"
                ></el-input>
            </el-form-item>

            <el-form-item label="材料备注">
                <el-input
                    type="textarea"
                    :rows="2"
                    v-model="this.remarkForm.materialRemark"
                    :show-word-limit="true"
                    :maxlength="255"
                ></el-input>
            </el-form-item>
        </el-form>

        <template #footer>
            <span>
                <el-button @click="remarkDialogVis = false">取消</el-button>

                <el-button type="primary" @click="submitRemarkForm">提交备注</el-button>
            </span>
        </template>
    </el-dialog>
    <el-dialog title="包装资料上传" v-model="isSubmitDocVis" width="30%" @close="handleDialogClose">
        <el-upload
            ref="uploadDoc"
            :action="`${this.$apiBaseUrl}/orderimport/submitdoc`"
            :headers="uploadHeaders"
            :auto-upload="false"
            accept=".xls,.xlsx"
            :file-list="fileList"
            :limit="1"
            :data="{ fileType: 2, orderRid: orderData.orderRid }"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
        >
            <el-button type="primary">选择文件</el-button>
        </el-upload>

        <template #footer>
            <span>
                <el-button @click="isSubmitDocVis = false">取消</el-button>
                <el-button type="primary" @click="submitDoc">上传</el-button>
            </span>
        </template>
    </el-dialog>
</template>

<script>
import AllHeader from '@/components/AllHeader.vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

export default {
    props: ['orderId'],
    components: {
        AllHeader
    },
    computed: {
        uploadHeaders() {
            return {
                Authorization: `Bearer ${this.token}`
            }
        },
        orderManagerEditable() {
            return this.orderCurStatus == 6 && this.orderCurStatusVal == 1
        },
        userIsManager() {
            return this.role == 4
        },
        orderClerkEditable(){
            return this.orderCurStatus == 6 && this.orderCurStatusVal == 0
        },
        orderEditable(){
            return this.orderCurStatus == 6
        },
        allowInput() {
            this.orderCurStatus == 6
        },
        allowEditInfo(){
            return (this.orderClerkEditable || this.userIsManager) && this.orderEditable
        },
        readyPending(){
            return this.orderCurStatus == 6 && this.orderCurStatusVal == 1
        },
        // allowChangeUnitPrice: function(row)
        // {
        //     return this.unitPriceAccessMapping[row.orderShoeTypeId]
        // },
        priceUpdateButtonVis() {
            return (
                Object.values(this.unitPriceAccessMapping).includes(true) ||
                Object.values(this.currencyTypeAccessMapping).includes(true)
            )
        },
        customerColorBtnVis() {
            return (
                Object.values(this.customerColorAccessMapping).includes(true)
            )
        }
    },
    data() {
        return {
            token: localStorage.getItem('token'),
            role: localStorage.getItem('role'),
            staffId: localStorage.getItem('staffid'),
            orderData: {},
            orderDBId: '',
            orderCurStatus: '',
            orderCurStatusVal: '',
            orderCurrencyUnit:'',
            orderShoeData: [],
            orderDocData: {},
            expandedRowKeys: [],
            orderShoeTypeIdToUnitPrice: {},
            orderShoeTypeIdToCurrencyType: {},
            orderShoeTypeCustomerColorForm:{},
            isSubmitDocVis: false,
            remarkDialogVis: false,
            priceChangeNotAllowed: false,
            unitChangeNotAllowed: false,
            editOrderInfoDisabled:true,
            remarkForm: {
                orderShoeId: '',
                technicalRemark: '',
                materialRemark: ''
            },
            unitPriceAccessMapping: {},
            currencyTypeAccessMapping: {},
            customerColorAccessMapping: {},
            batchInfoType: {},
            attrMappingToRatio: {
                size34Name: 'size34Ratio',
                size35Name: 'size35Ratio',
                size36Name: 'size36Ratio',
                size37Name: 'size37Ratio',
                size38Name: 'size38Ratio',
                size39Name: 'size39Ratio',
                size40Name: 'size40Ratio',
                size41Name: 'size41Ratio',
                size42Name: 'size42Ratio',
                size43Name: 'size43Ratio',
                size44Name: 'size44Ratio',
                size45Name: 'size45Ratio',
                size46Name: 'size46Ratio'
            },
            attrMappingToAmount: {
                size34Name: 'size34Amount',
                size35Name: 'size35Amount',
                size36Name: 'size36Amount',
                size37Name: 'size37Amount',
                size38Name: 'size38Amount',
                size39Name: 'size39Amount',
                size40Name: 'size40Amount',
                size41Name: 'size41Amount',
                size42Name: 'size42Amount',
                size43Name: 'size43Amount',
                size44Name: 'size44Amount',
                size45Name: 'size45Amount',
                size46Name: 'size46Amount'
            },
            customerOrderBtn: '修改数据',
            customerShoeBtn: '修改数据',
            customerOrderEditDisabled: true,
            customerShoeIdEditDisabled: true,
            customerColorEditDisabled: true
        }
    },
    mounted() {
        this.getOrderInfo()
        // this.getOrderOrderShoe()
        // this.getOrderOrderShoe()
        console.log(this.role)
    },
    methods: {
        getUniqueImageUrl(imageUrl) {
            return `${imageUrl}?timestamp=${new Date().getTime()}`;
        },
        async getOrderInfo() {
            const response = await axios.get(
                `${this.$apiBaseUrl}/order/getbusinessorderinfo?orderid=${this.orderId}`
            )
            console.log(response.data)
            this.orderData = response.data
            this.orderShoeData = response.data.orderShoeAllData
            this.batchInfoType = response.data.batchInfoType
            this.orderDBId = this.orderData.orderId
            this.orderCurStatus = this.orderData.orderStatus
            this.orderCurStatusVal = this.orderData.orderStatusVal
            this.orderData.orderShoeAllData.forEach((orderShoe) =>
                orderShoe.orderShoeTypes.forEach((orderShoeType) => {
                    this.orderShoeTypeIdToUnitPrice[orderShoeType.orderShoeTypeId] =
                        orderShoeType.shoeTypeBatchData.unitPrice
                    this.orderShoeTypeIdToCurrencyType[orderShoeType.orderShoeTypeId] =
                        orderShoeType.shoeTypeBatchData.currencyType
                    this.orderShoeTypeCustomerColorForm[orderShoeType.orderShoeTypeId] =
                        orderShoeType.customerColorName
                    // bad fix TODO
                    this.orderCurrencyUnit = orderShoeType.shoeTypeBatchData.currencyType
                })
            )
        },
        updateStatus() {
            return
        },
        toggleEditInfo(){
            console.log(this.editOrderInfoDisabled)
            this.editOrderInfoDisabled = !this.editOrderInfoDisabled;
            console.log(this.editOrderInfoDisabled)
            console.log(this.orderCurStatus)
            console.log(this.orderCurStatus == 6)
        },
        async submitOrderInfo(){

            const response = await axios.post(`${this.$apiBaseUrl}/ordercreate/updateordercid`, {
                                orderId: this.orderId,
                                orderCid: this.orderData.orderCid
                            })
            
            
            const updateOrderShoeid = this.orderData.orderShoeAllData[0].orderShoeId
            const updateOrderShoeCid = this.orderData.orderShoeAllData[0].shoeCid
            
            const response2 = await axios.post(`${this.$apiBaseUrl}/ordercreate/updateordershoecustomername`, {
                orderShoeId: updateOrderShoeid,
                shoeCid: updateOrderShoeCid
            })

            this.submitCustomerColorForm()
            this.submitPriceForm()
            // this.submitCustomerColorForm()
            this.editOrderInfoDisabled = true
        },
        async proceedOrder(){
            const response = await axios.post(`${this.$apiBaseUrl}/ordercreate/proceedevent`,{
                orderId: this.orderDBId,
                staffId: this.staffId
            })
            console.log(response)
            if (response.status === 200){
                ElMessage.success('提交订单至业务经理成功')
                this.getOrderInfo()
            }
            else {
                ElMessage.error('提交失败 金额信息或包材未上传')
            }
        },
        async submitCustomerColorForm()
        {
            console.log(this.orderShoeTypeCustomerColorForm)
            const response = await axios.post(`${this.$apiBaseUrl}/ordercreate/updatecustomercolorname`, {
                orderShoeTypeCustomerColorForm : this.orderShoeTypeCustomerColorForm
            })
            if (response.status === 200) {
                ElMessage.success('客户颜色添加成功')
                this.getOrderInfo()
            } else {
                ElMessage.error('客户颜色添加失败')
            }
        },
        async submitPriceForm() {
            console.log(this.orderShoeTypeIdToCurrencyType)
            const response = await axios.post(`${this.$apiBaseUrl}/ordercreate/updateprice`, {
                unitPriceForm: this.orderShoeTypeIdToUnitPrice,
                currencyTypeForm: this.orderShoeTypeIdToCurrencyType,
                orderId: this.orderDBId,
                staffId: this.staffId
            })
            if (response.status === 200) {
                ElMessage.success('变更成功')
                this.getOrderInfo()
            } else {
                ElMessage.error('备注变更失败')
            }
            return
        },

        showMessage (key, value) {
            ElMessageBox.alert('是否确认更新数据', '', {
                confirmButtonText: '确认',
                showCancelButton: true,
                callback: async (action) => {
                    if (action === 'confirm') {
                        if (key === 'customOrderId') {
                            const response = await axios.post(`${this.$apiBaseUrl}/ordercreate/updateordercid`, {
                                orderId: this.orderId,
                                orderCid: value
                            })
                            if (response.status === 200) {
                                ElMessage.success('更新成功，正在重新加载数据')
                                setTimeout(()=>{
                                    location.reload(location.href)
                                }, 500)
                            } else {
                                ElMessage.error('更新失败')
                            }
                        }
                        if (key === 'customShoeId') {
                            const response = await axios.post(`${this.$apiBaseUrl}/ordercreate/updateordershoecustomername`, {
                                orderShoeId: value.orderShoeId,
                                shoeCid: value.shoeCid
                            })
                            if (response.status === 200) {
                                ElMessage.success('更新成功，正在重新加载数据')
                                setTimeout(()=>{
                                    location.reload(location.href)
                                }, 500)
                            } else {
                                ElMessage.error('更新失败')
                            }
                        }
                    }
                }
            })
        }

        ,
        changeCustomerColorMgt(){
            Object.keys(this.customerColorAccessMapping).forEach(
                (key) => (this.customerColorAccessMapping[key] = true)
            )
        },

        openRemarkDialog(row) {
            console.log(row.orderShoeId)
            this.remarkForm.orderShoeId = row.orderShoeId
            this.remarkDialogVis = true
        },
        openEditRemarkDialog(row) {
            this.remarkForm.orderShoeId = row.orderShoeId
            this.remarkForm.technicalRemark = row.orderShoeTechnicalRemark
            this.remarkForm.materialRemark = row.orderShoeMaterialRemark
            this.remarkDialogVis = true
        },
        async sendOrderPrevious(){
            const response = await axios.post(
                `${this.$apiBaseUrl}/ordercreate/sendprevious`,
                {
                    orderId: this.orderDBId,
                    staffId: this.staffId
                }
            )
            if (response.status === 200)
            {
                ElMessage.success('退回成功')
            }
            else{
                ElMessage.error('退回错误')
            }
            this.getOrderInfo()
            // #!TODO
        },
        sendOrderNext() {
            if (this.orderData.wrapRequirementUploadStatus === '已上传包装文件') {
                const value = [...Object.values(this.orderShoeTypeIdToUnitPrice)]
                const unit = [...Object.values(this.currencyTypeAccessMapping)]
                if (value.includes(0)) {
                    ElMessage.error('请检查订单中的金额数据，不允许值为0')
                    return
                }
                if (unit.includes(true)) {
                    ElMessage.error('请检查订单中的金额单位，不允许单位为空')
                    return
                }
                this.$confirm('确认下发订单？', '提示', {
                    confirmButtonText: '确定',
                    cancelButtonText: '取消',
                    type: 'warning'
                })
                    .then(async () => {
                        const result = await axios.post(
                            `${this.$apiBaseUrl}/ordercreate/sendnext`,
                            {
                                orderId: this.orderDBId,
                                staffId: this.staffId
                            }
                        )
                        if (result.status === 200) {
                            ElMessage.success('下发成功,正在重新加载数据')
                        } else {
                            ElMessage.error('下发失败')
                        }
                    })
                    .then(async () => {
                        this.getOrderInfo()
                    })
            } else {
                ElMessage.error('包装文件未上传,请上传包装文件后再下发！')
                return
            }
        },
        expandOpen(row, expand) {
            console.log(this.expandedRowKeys)
            this.expandedRowKeys.push(row.shoeTypeId)
            // row.batchQuantityMapping = row.orderShoeTypeBatchInfo.map((batchInfo) => { return batchInfo.packagingInfoId:batchInfo.unitQuantityInPair})Id})
        },
        updateValue(row) {
            let result = row.shoeTypeBatchData.unitPrice * row.shoeTypeBatchData.totalAmount
            row.shoeTypeBatchData.totalPrice = parseFloat(result.toFixed(2));
            this.orderShoeTypeIdToUnitPrice[row.orderShoeTypeId] = row.shoeTypeBatchData.unitPrice
        },
        updateCurrencyUnit(row) {
            this.orderData.orderShoeAllData.forEach((orderShoe) =>
                orderShoe.orderShoeTypes.forEach((orderShoeType) => {
                    this.orderShoeTypeIdToCurrencyType[orderShoeType.orderShoeTypeId] = this.orderCurrencyUnit
                        orderShoeType.shoeTypeBatchData.currencyType = this.orderCurrencyUnit
                }))
        },
        
        async submitRemarkForm() {
            console.log(this.remarkForm)
            const response = await axios.post(`${this.$apiBaseUrl}/ordercreate/updateremark`, {
                orderShoeRemarkForm: this.remarkForm
            })
            if (response.status === 200) {
                ElMessage.success('信息变更成功')
                this.getOrderInfo()
                this.remarkDialogVis = false
            } else {
                ElMessage.error('信息变更失败')
            }
        },
        openSubmitDialog() {
            this.isSubmitDocVis = true
        },
        handleUploadSuccess(response, file) {
            // Handle the successful response
            console.log('Upload successful:', response)
            ElMessage.success('上传成功')
            this.isSubmitDocVis = false
            this.getOrderInfo()
        },
        handleUploadError(error, file) {
            // Handle any errors that occurred during the upload
            console.error('Upload error:', error)
            ElMessage.error('上传失败')
            this.fileList = []
            this.isSubmitDocVis = false
        },
        download(type) {
            window.open(
                `${this.$apiBaseUrl}/orderimport/downloadorderdoc?orderrid=${this.orderData.orderRid}&filetype=${type}`
            )
        },
        async submitDoc() {
            try {
                const loadingInstance = this.$loading({
                    lock: true,
                    text: '等待中，请稍后...',
                    background: 'rgba(0, 0, 0, 0.7)'
                })
                // Manually submit the file without reopening the dialog
                console.log(this.$refs.uploadDoc)
                await this.$refs.uploadDoc.submit()
                loadingInstance.close()
                this.getOrderInfo()
            } catch (error) {
                console.error('Upload error:', error)
                ElMessage.error('上传失败')
            }
        },

        handleDialogClose() {
            console.log('TODO handle dialog close in OrderManagement.Vue')
        },


        
    }
}
</script>
<style>
/* Add your styles here */
.el-table .cell {
    white-space: pre-line !important;
}
</style>
