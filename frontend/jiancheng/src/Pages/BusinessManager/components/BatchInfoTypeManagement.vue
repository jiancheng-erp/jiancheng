<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center"
            >码段管理</el-col
        >
    </el-row>
    <!-- <el-button type="primary" @click="testData">123</el-button> -->
    <el-row :gutter="20">
        <el-col :span="24" :offset="0">
            <el-table
                :data="displayBatchInfoTypes"
                style="width: 100%"
                stripe
                height="500"
            >
                <el-table-column
                    prop="batchInfoTypeName"
                    label="码段种类"
                ></el-table-column>
                <el-table-column
                    prop="size34Name"
                    label="码号1"
                ></el-table-column>
                <el-table-column
                    prop="size35Name"
                    label="码号2"
                ></el-table-column>
                <el-table-column
                    prop="size36Name"
                    label="码号3"
                ></el-table-column>
                <el-table-column
                    prop="size37Name"
                    label="码号4"
                ></el-table-column>
                <el-table-column
                    prop="size38Name"
                    label="码号5"
                ></el-table-column>
                <el-table-column
                    prop="size39Name"
                    label="码号6"
                ></el-table-column>
                <el-table-column
                    prop="size40Name"
                    label="码号7"
                ></el-table-column>
                <el-table-column
                    prop="size41Name"
                    label="码号8"
                ></el-table-column>
                <el-table-column
                    prop="size42Name"
                    label="码号9"
                ></el-table-column>
                <el-table-column
                    prop="size43Name"
                    label="码号10"
                ></el-table-column>
                <el-table-column
                    prop="size44Name"
                    label="码号11"
                ></el-table-column>
                <el-table-column
                    prop="size45Name"
                    label="码号12"
                ></el-table-column>
                <el-table-column
                    prop="size46Name"
                    label="码号13"
                ></el-table-column>
                <el-table-column label="操作"
                v-if="allowModifyBatchInfoType">
                    <template #default="scope">
                        <el-button
                            type="danger"
                            size="small"
                            @click="deleteBatchType(scope.row)"
                            >删除码段</el-button
                        >
                    </template>
                </el-table-column>
            </el-table>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0">
            <el-button v-if="allowModifyBatchInfoType" type="primary" @click="openAddBatchTypeDialog">添加新码段</el-button>
        </el-col>
    </el-row>

    <el-dialog
        title="码段表格"
        v-model="addBatchTypeDialogVis"
        width="30%">
        <el-form :model="batchInfoTypeForm" label-width="120px" :inline="false" size="">
            <el-form-item label="码段名称">
                <el-input v-model="batchInfoTypeForm.batchInfoTypeName"></el-input>
            </el-form-item>
            <el-form-item label="码数1">
                <el-input v-model="batchInfoTypeForm.size34Name"></el-input>
            </el-form-item>
            <el-form-item label="码数2">
                <el-input v-model="batchInfoTypeForm.size35Name"></el-input>
            </el-form-item>
            <el-form-item label="码数3">
                <el-input v-model="batchInfoTypeForm.size36Name"></el-input>
            </el-form-item>
            <el-form-item label="码数4">
                <el-input v-model="batchInfoTypeForm.size37Name"></el-input>
            </el-form-item>
            <el-form-item label="码数5">
                <el-input v-model="batchInfoTypeForm.size38Name"></el-input>
            </el-form-item>
            <el-form-item label="码数6">
                <el-input v-model="batchInfoTypeForm.size39Name"></el-input>
            </el-form-item>
            <el-form-item label="码数7">
                <el-input v-model="batchInfoTypeForm.size40Name"></el-input>
            </el-form-item>
            <el-form-item label="码数8">
                <el-input v-model="batchInfoTypeForm.size41Name"></el-input>
            </el-form-item>
            <el-form-item label="码数9">
                <el-input v-model="batchInfoTypeForm.size42Name"></el-input>
            </el-form-item>
            <el-form-item label="码数10">
                <el-input v-model="batchInfoTypeForm.size43Name"></el-input>
            </el-form-item>
            <el-form-item label="码数11">
                <el-input v-model="batchInfoTypeForm.size44Name"></el-input>
            </el-form-item>
            <el-form-item label="码数12">
                <el-input v-model="batchInfoTypeForm.size45Name"></el-input>
            </el-form-item>
            <el-form-item label="码数13">
                <el-input v-model="batchInfoTypeForm.size46Name"></el-input>
            </el-form-item>

        </el-form>
        
        <template #footer>
        <span>
            <el-button @click="editBatchDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="submitNewBatchInfoTypeForm">确认提交</el-button>
        </span>
        </template>
    </el-dialog>
</template>

<script>
import axios from 'axios'
import { ElMessage } from 'element-plus';
export default {
    data() {
        return {
            token: localStorage.getItem('token'),
            addBatchTypeDialogVis:false,
            editBatchTypeDialogVis:false,
            displayBatchInfoTypes:[],
            totalBatchInfoTypes:[],
            userRole:'',
            userName:'',
            // allowModifyBatchInfoType:false,
            batchInfoTypeForm:
            {
                batchInfoTypeId:"",
                batchInfoTypeName:"",
                size34Name:"",
                size35Name:"",
                size36Name:"",
                size37Name:"",
                size38Name:"",
                size39Name:"",
                size40Name:"",
                size41Name:"",
                size42Name:"",
                size43Name:"",
                size44Name:"",
                size45Name:"",
                size46Name:"",

            },
        }
    },
    computed: {
        allowModifyBatchInfoType()
        {
            return this.userRole == 4
        }
    },
    mounted() {
        this.$setAxiosToken()
        this.getBatchTypes()
        this.userInfo()
    },
    methods: {
        resetForm(inputForm)
        {
            console.log(inputForm.keys())
        },
        openAddBatchTypeDialog(){
            this.addBatchTypeDialogVis=true
        },
        openEditBatchTypeDialog(){

        },
        // async testData(){
		// 	const response = await axios.get(`${this.$apiBaseUrl}/batchtype/getorderbatchtype`, {params:{"orderId": 19} })
        // },
        async userInfo()
        {
           const response = await axios.get(`${this.$apiBaseUrl}/order/onmount`)
           this.userName = response.data.staffName
           this.userRole = response.data.role
           console.log(this.userRole)
        },
        async getBatchTypes(){
            const response = await axios.get(`${this.$apiBaseUrl}/batchtype/getallbatchtypesbusiness`)
            this.displayBatchInfoTypes = response.data.batchDataTypes
            console.log(response)
        },
        generalAPICall(warning_type, apiurl, requestbody){   
            this.$confirm("确认"+warning_type+"信息？",'提示',
                {
                    confirmButtonText:'确定',
                    cancelButtonText:'取消',
                    type:'warning'
                }
            ).then(async () => {
                try{
                    if (warning_type == "添加")
                    {
                    await axios.post(`${this.$apiBaseUrl}` + apiurl, requestbody)
                    }
                    else if (warning_type == "删除")
                    {
                    await axios.delete(`${this.$apiBaseUrl}`+apiurl, {params:requestbody})
                    }
                    console.log("SUCCESS")
                    ElMessage.success(warning_type + "成功")
                    this.getBatchTypes()
                    // this.resetForm(requestbody)
                }
                catch(error){
                    console.log("ERROR")
                    this.$message({
                        type:'error',
                        message: warning_type +'失败'
                    })

                }
            }).catch(()=>{
                this.$message({
                type:'info',
                message:'已取消' + warning_type
                })
            })
        },
        async deleteBatchType(row)
        {
            await this.generalAPICall("删除", "/batchtype/deletebatchtypebusiness",{"batchTypeId":row.batchInfoTypeId})
            await this.getBatchTypes()
        }
        ,  
        submitNewBatchInfoTypeForm()
        {
            console.log(this.batchInfoTypeForm)
            this.$confirm("确认添加信息？", '提示', 
                {
                    confirmButtonText:'确定',
                    cancelButtonText:'取消',
                    type:'warning'
                }).then(async ()=>
            {
                const response = await axios.post(`${this.$apiBaseUrl}/batchtype/addbatchtypebusiness`, this.batchInfoTypeForm)
                if (response.status == 200){
                    this.$message({
                        type:"success",
                        message:"添加成功"
                    })
                    this.batchInfoTypeForm = {
                        batchInfoTypeId:"",
                        batchInfoTypeName:"",
                        size34Name:"",
                        size35Name:"",
                        size36Name:"",
                        size37Name:"",
                        size38Name:"",
                        size39Name:"",
                        size40Name:"",
                        size41Name:"",
                        size42Name:"",
                        size43Name:"",
                        size44Name:"",
                        size45Name:"",
                        size46Name:"",
                        }
                    this.addBatchTypeDialogVis=false
                    this.getBatchTypes()
                }
                else {
                    this.$message({
                        type:'error',
                        message:'添加失败'
                    })
                }
            }).catch( () => {
                this.$message({
                    type:'info',
                    message:'已取消添加'
                })
            })
        }
    }
}
</script>
