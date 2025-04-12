<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center"
            >客户管理</el-col
        >
    </el-row>
    <el-row :gutter="20">
        <el-col :span="4" :offset="0" style="white-space: nowrap">
            客户名称：
            <el-input v-model="searchName" placeholder="请输入要筛选的客户名称" clearable @input="getFilterData"></el-input>
        </el-col>
        <el-col :span="4" :offset="2" style="white-space: nowrap">
            客户商标：
            <el-input v-model="searchBrand" placeholder="请输入要筛选的客户商标" clearable @input="getFilterData"></el-input>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0">
            <el-table
                :data="customerTableData"
                style="width: 100%"
                stripe
                border
                height="500"
            >
                <el-table-column
                    prop="customerName"
                    label="客户名称"
                ></el-table-column>
                <el-table-column
                    prop="customerBrand"
                    label="客户商标"
                ></el-table-column>
                <el-table-column label="操作">
                    <template #default="scope">
                        <el-button
                            v-if = "allowEditCustomer"
                            type="primary"
                            size="small"
                            @click="openEditCustomerDialog(scope.row)"
                            >编辑客户</el-button
                        >
                        <el-button
                            type="primary"
                            size="small"
                            @click="openEditCustomerBatchDialog(scope.row)"
                            >配码管理</el-button
                        >
                        <el-button
                        v-if ="allowEditCustomer"
                            type="danger"
                            size="small"
                            @click="deleteCustomer(scope.row)"
                        >删除客户</el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0">
            <el-button type="primary" @click="openAddCustomerDialog">添加新客户</el-button>
        </el-col>
    </el-row>
    <el-dialog
        title="添加客户"
        v-model="addCustomerDialogVisible"
        width="30%">
        <el-form :model="customerForm" label-width="120px" :inline="false" size="default">
            <el-form-item label="客户名称">
                <el-input v-model="customerForm.customerName"></el-input>
            </el-form-item>
            <el-form-item label="客户商标">
                <el-input v-model="customerForm.customerBrand"></el-input>
            </el-form-item>
        </el-form>
        
        <template #footer>
        <span>
            <el-button @click="addCustomerDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="submitAddCustomerForm">确认提交</el-button>
        </span>
        </template>
    </el-dialog>

    <el-dialog
        title = "配码管理"
        v-model="editCustomerBatchDialogVisible"
        width = "100%">
        <el-tabs v-model="activeTab" type="card" tab-position="top" @tab-change="updateSelectedTab()" >
            <el-tab-pane v-for="currentTab in batchTypeTabs" :key="currentTab.batchInfoTypeId" :label="currentTab.batchInfoTypeName" :name="currentTab.batchInfoTypeId">
        <el-col :span="4" :offset="15"
            ><el-input
                v-model="batchNameFilter"
                placeholder="请输入配码名称"
                size="default"
                :suffix-icon="'el-icon-search'"
                clearable
                @input="filterBatchData(currentTab.batchInfoTypeId)"
            ></el-input>
        </el-col>
        <el-row :gutter="20">
            <el-col :span="24" :offset="0">
                <el-descriptions title="" :column="2" border>
                    <el-descriptions-item label="客户名称" align="center">{{
                        batchDialogCurCustomerName
                    }}</el-descriptions-item>
                    <el-descriptions-item label="客户商标" align="center">{{
                        batchDialogCurCustomerBrand
                    }}</el-descriptions-item>
                </el-descriptions>
            </el-col>
        </el-row>
        <el-row :gutter="20">
            <el-table :data="this.batchTabDisplayData[currentTab.batchInfoTypeId]" border stripe height="500">
                <el-table-column prop="packagingInfoName" label="配码名称" sortable
                width="120px"/>
                <el-table-column v-for ="col in Object.keys(this.attrMapping).filter(key => currentTab[key] != '')"
                                :label="currentTab[col]"
                                :prop="attrMapping[col]"
                                width="80px"></el-table-column>
                <el-table-column prop="totalQuantityRatio" label="对/件" sortable
                width="80px"/>
                <el-table-column label="操作">
                    <template #default="scope">
                        <el-button type="primary" size="default" @click="editBatchInfo(scope.row)"
                            >查看详情</el-button
                        >
                        <el-button  v-if ="allowEditCustomer" type="primary" size = "default" @click="deleteBatchInfo(scope.row)">
                        删除</el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-row>
        <span>
            <el-button @click="editCustomerBatchDialogVisible = false">取消</el-button>
            <el-button @click="openAddCustomerBatchDialog()"> 添加配码</el-button>
        </span>
    </el-tab-pane>

    </el-tabs>
    </el-dialog>

    <el-dialog
        title="添加配码"
        v-model="addCustomerBatchDialogVisible"
        width="30%"
        >
        <el-form :model="batchForm" label-width="120px" :inline="false" size="default" >
            <el-form-item label="配码名称">
                <el-input v-model="batchForm.packagingInfoName"></el-input>
            </el-form-item>
            <el-form-item label="配码地区">
                <el-input v-model="batchForm.packagingInfoLocale" :disabled="true"></el-input>
            </el-form-item>
            <el-form-item v-for ="col in Object.keys(this.attrMapping).filter(key => this.currentBatchType[key] != '')"
                                :label="this.currentBatchType[col]">
                                <el-input v-model=batchForm[attrMapping[col]]></el-input>
            </el-form-item>
        </el-form>
        
        <template #footer>
        <span>
            <el-button @click="addCustomerBatchDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="submitAddCustomerBatchForm">确认提交</el-button>
        </span>
        </template>
    </el-dialog>

    <el-dialog
        title="编辑配码"
        v-model="editBatchDialogVisible"
        width="30%"
        >
        <el-form :model="batchForm" label-width="120px" :inline="false" size="default" >
            <el-form-item label="配码名称">
                <el-input v-model="batchForm.packagingInfoName"></el-input>
            </el-form-item>
            <el-form-item label="配码地区">
                <el-input v-model="batchForm.packagingInfoLocale" :disabled="true"></el-input>
            </el-form-item>
            <el-form-item v-for ="col in Object.keys(this.attrMapping).filter(key => this.currentBatchType[key] != '')"
                                :label="this.currentBatchType[col]">
                                <el-input v-model=batchForm[attrMapping[col]]></el-input>
            </el-form-item>
        </el-form>
        
        <template #footer>
        <span>
            <el-button @click="editBatchDialogVisible=false">取消</el-button>
            <el-button type="primary" @click="submitEditCustomerBatchForm">确认提交</el-button>
        </span>
        </template>
    </el-dialog>

    <el-dialog
        title="编辑客户"
        v-model="editCustomerDialogVisible"
        width="30%">
        <el-form :model="customerForm" label-width="120px" :inline="false" size="default">
            <el-form-item label="客户名称">
                <el-input v-model="customerForm.customerName"></el-input>
            </el-form-item>
            <el-form-item label="客户商标">
                <el-input v-model="customerForm.customerBrand"></el-input>
            </el-form-item>
        </el-form>
        <template #footer>
        <span>
            <el-button @click="editCustomerDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="submitEditCustomerForm">确认</el-button>
        </span>
        </template>
    </el-dialog>
    
    
</template>

<script>
import axios from 'axios';
export default {
    data() {
        return {
            activeTab:0,
            customerForm: {
                customerId: '',
                customerName: '',
                customerBrand: '',
                customerBatchInfos:[]
            },
            batchForm: {
                customerId:'',
                packagingInfoName: '',
                packagingInfoLocale: '',
                batchInfoTypeId:'',
                size34Ratio: 0,
                size35Ratio: 0,
                size36Ratio: 0,
                size37Ratio: 0,
                size38Ratio: 0,
                size39Ratio: 0,
                size40Ratio: 0,
                size41Ratio: 0,
                size42Ratio: 0,
                size43Ratio: 0,
                size44Ratio: 0,
                size45Ratio: 0,
                size46Ratio: 0,
                totalQuantityRatio:0
                },
            attrMapping:{
                "size34Name":"size34Ratio",
                "size35Name":"size35Ratio",
                "size36Name":"size36Ratio",
                "size37Name":"size37Ratio",
                "size38Name":"size38Ratio",
                "size39Name":"size39Ratio",
                "size40Name":"size40Ratio",
                "size41Name":"size41Ratio",
                "size42Name":"size42Ratio",
                "size43Name":"size43Ratio",
                "size44Name":"size44Ratio",
                "size45Name":"size45Ratio",
                "size46Name":"size46Ratio",
            },
            addCustomerDialogVisible: false,
            editCustomerDialogVisible: false,
            addCustomerBatchDialogVisible: false,
            editCustomerBatchDialogVisible: false,
            editBatchDialogVisible:false,
            batchNameFilter: '',
            batchTypeTabs:[],
            customerTableData: [],
            customerBatchData: [],
            customerDisplayBatchData: [],
            customerFilteredBatchData: [],
            batchDialogCurCustomerName:'',
            batchDialogCurCustomerBrand:'',
            batchDialogCurCustomerId:'',
            batchTabDisplayData:{},
            colNameToProp:[],
            currentBatchType:{},
            userName:'',
            userRole:'',
            searchName: '',
            searchBrand: '',
            filterArray: []
        }
    },
    computed:
    {
        allowEditCustomer()
        {
            return this.userRole == 4
        }

    },
    mounted() {
        this.$setAxiosToken()
        this.getCustomerList()
        this.userInfo()
        this.getAllBatchTypes()
        console.log(this.currentBatchType)
    },
    methods: {
        async userInfo()
        {
           const response = await axios.get(`${this.$apiBaseUrl}/order/onmount`)
           this.userName = response.data.staffName
           this.userRole = response.data.role
           console.log(this.userRole)
        },
        async getCustomerList() {
            const response = await axios.get(`${this.$apiBaseUrl}/customer/getcustomerdetails`)
            this.customerTableData = response.data
            this.filterArray = response.data
        },
        async getCustomerBatchInfo(customerId) {
            const response = await axios.get(`${this.$apiBaseUrl}/customer/getcustomerbatchinfo`,{
                params: {
                    customerid: customerId
                }
            })
            console.log(response.data)
            this.batchTypeTabs = response.data
            this.batchTypeTabs.forEach((info_type) => {this.batchTabDisplayData[info_type.batchInfoTypeId] = info_type.batchInfoList})
            this.currentBatchType = this.batchTypeTabs[0]
            this.activeTab = this.currentBatchType.batchInfoTypeId
        },
        async getAllBatchTypes(){
            const response = await axios.get(`${this.$apiBaseUrl}/batchtype/getallbatchtypesbusiness`)
            console.log(response.data["batchDataTypes"])
            this.batchTypeTabs = response.data["batchDataTypes"]
            console.log(this.batchTypeTabs[0].batchInfoTypeName)
        },
        
        updateSelectedTab(){
            console.log(this.activeTab)
            this.currentBatchType = this.batchTypeTabs.find((batchtype) => batchtype.batchInfoTypeId == this.activeTab)
        },
        editBatchInfo(row){
            console.log("editing batch info")
            this.resetBatchForm()
            this.editBatchDialogVisible = true
            this.batchForm = row
        },
        resetBatchForm(){
            console.log("resetting")
            this.batchForm = {
                        customerId:'',
                        packagingInfoName: '',
                        packagingInfoLocale: '',
                        batchInfoTypeId:'',
                        size34Ratio: 0,
                        size35Ratio: 0,
                        size36Ratio: 0,
                        size37Ratio: 0,
                        size38Ratio: 0,
                        size39Ratio: 0,
                        size40Ratio: 0,
                        size41Ratio: 0,
                        size42Ratio: 0,
                        size43Ratio: 0,
                        size44Ratio: 0,
                        size45Ratio: 0,
                        size46Ratio: 0,
                        totalQuantityInRatio:0
                        }
        },

        openAddCustomerBatchDialog() {
            // console.log(this.)
            console.log("adding batch info")
            this.resetBatchForm()
            this.batchForm.customerId = this.batchDialogCurCustomerId
            this.batchForm.batchInfoTypeId = this.activeTab
            this.batchForm.packagingInfoLocale = this.currentBatchType.batchInfoTypeName
            this.addCustomerBatchDialogVisible = true
        },
        openEditCustomerBatchDialog(row) {
            this.resetBatchForm()
            this.batchDialogCurCustomerName = row.customerName
            this.batchDialogCurCustomerBrand = row.customerBrand
            this.batchDialogCurCustomerId = row.customerId
            this.getCustomerBatchInfo(row.customerId)
            this.editCustomerBatchDialogVisible = true
        },
        closeEditBatchDialog(){
            console.log(123)
            this.editBatchDialogVisible=false
            this.resetBatchForm()
        },
        closeAddBatchDialog(){
            this.addCustomerBatchDialogVisible=false
            this.resetBatchForm()
        },
        deleteCustomer(row)
        {
            console.log(row)
            this.$confirm('确定删除此客户商标吗？', '提示', {
                confirmButtonText:'确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then( async () => {
                const body = {
                        params:{
                            customerId:row.customerId,
                        }
                    }
                const response = await axios.delete(
                    `${this.$apiBaseUrl}/customer/deletecustomer`,
                    body)
                if (response.status === 200){
                    this.$message({
                        type:'success',
                        message:'删除成功'
                    })
                    this.getCustomerList()
                }
                else {
                    this.$message({
                        type:'error',
                        message:'删除失败'
                    })
                }
            })
        },
        deleteBatchInfo(row){
            this.$confirm('确定删除此配码吗？', '提示', {
                confirmButtonText:'确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then( async () => {
                const body = {
                        params:{
                            customerId:this.batchDialogCurCustomerId,
                            packagingInfoId:row.packagingInfoId
                        }
                    }
                const response = await axios.delete(
                    `${this.$apiBaseUrl}/customer/deletebatchinfo`,
                    body)
                if (response.status === 200){
                    this.$message({
                        type:'success',
                        message:'删除成功'
                    })
                    this.getCustomerBatchInfo(this.batchDialogCurCustomerId)
                }
                else {
                    this.$message({
                        type:'error',
                        message:'删除失败'
                    })
                }
            })
            this.batchDialogCurCustomerId
        },
        openAddCustomerDialog() {
            this.addCustomerDialogVisible = true
        },
        openEditCustomerDialog(row) {
            this.editCustomerDialogVisible = true
            this.customerForm = row
        },
        submitAddCustomerForm() {
            console.log(this.customerForm)
            this.$confirm('确认添加客户信息？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(async () => {
                try {
                    await axios.post(`${this.$apiBaseUrl}/customer/addcustomer`, this.customerForm)
                    this.$message({
                        type: 'success',
                        message: '添加成功'
                    })
                    this.addCustomerDialogVisible = false
                    this.customerForm = {
                        customerId: '',
                        customerName: '',
                        customerBrand: ''
                    }
                    this.getCustomerList()
                }
                catch(error) {
                    this.$message({
                        type: 'error',
                        message: error.response.data.message
                    })
                }

            }).catch(() => {
                this.$message({
                    type: 'info',
                    message: '已取消添加'
                })
            })
        },
        submitAddCustomerBatchForm() {
            this.$confirm('确认添加客户配码信息？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(async () => {
                console.log(this.batchForm)
                const response = await axios.post(`${this.$apiBaseUrl}/customer/addcustomerbatchinfo`, this.batchForm)
            }).then( async () => {
                this.getCustomerBatchInfo(this.batchDialogCurCustomerId)
                this.resetBatchForm()
                this.batchForm ={
                    customerId:'',
                    packagingInfoName: '',
                    packagingInfoLocale: '',
                    batchInfoTypeId:'',
                    size34Ratio: 0,
                    size35Ratio: 0,
                    size36Ratio: 0,
                    size37Ratio: 0,
                    size38Ratio: 0,
                    size39Ratio: 0,
                    size40Ratio: 0,
                    size41Ratio: 0,
                    size42Ratio: 0,
                    size43Ratio: 0,
                    size44Ratio: 0,
                    size45Ratio: 0,
                    size46Ratio: 0,
                    totalQuantityRatio:0
                }
            })
            this.addCustomerBatchDialogVisible = false
        },
        submitEditCustomerBatchForm(){
            console.log(this.batchForm)
             this.$confirm('确认修改客户配码信息？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(async () => {
                const response = await axios.post(`${this.$apiBaseUrl}/customer/editbatchinfo`, this.batchForm)
                if (response.status === 200) {
                    this.$message({
                        type: 'success',
                        message: '修改成功'
                    })
                    this.editBatchDialogVisible = false
                    this.resetBatchForm()
                    this.getCustomerBatchInfo(this.batchDialogCurCustomerId)
                // this.getCustomerList()
                } else {
                    this.$message({
                        type: 'error',
                        message: '修改失败'
                    })
                }

            }).catch(() => {
                this.$message({
                    type: 'info',
                    message: '已取消修改'
                })
            })

        },
        submitEditCustomerForm() {
            console.log(this.customerForm)
            this.$confirm('确认修改客户信息？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(async () => {
                const response = await axios.post(`${this.$apiBaseUrl}/customer/editcustomer`, this.customerForm)
                if (response.status === 200) {
                    this.$message({
                        type: 'success',
                        message: '修改成功'
                    })
                    this.editCustomerDialogVisible = false
                    this.customerForm = {
                        customerId: '',
                        customerName: '',
                        customerBrand: ''
                    }
                    this.getCustomerList()
                } else {
                    this.$message({
                        type: 'error',
                        message: '修改失败'
                    })
                }

            }).catch(() => {
                this.$message({
                    type: 'info',
                    message: '已取消修改'
                })
            })
        },
        getFilterData() {
            if (this.searchName !== '' || this.searchBrand !== '') {
                console.log(this.searchName)
                console.log(this.searchBrand)
                this.customerTableData = this.filterArray.filter((item) => {
                    if (this.searchName !== '' && this.searchBrand !== '') {
                        return item.customerName.indexOf(this.searchName) !== -1 && item.customerBrand.indexOf(this.searchBrand) !== -1
                    } else {
                        if (this.searchName !== '') {
                            return item.customerName.indexOf(this.searchName) !== -1
                        }
                        if (this.searchBrand !== '') {
                            return item.customerBrand.indexOf(this.searchBrand) !== -1
                        }
                    }
                    
                })
            } else {
                this.customerTableData = this.filterArray
            }
        }
    },
}
</script>