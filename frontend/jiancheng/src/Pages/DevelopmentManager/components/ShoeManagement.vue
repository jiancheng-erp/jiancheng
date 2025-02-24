<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center"
            >鞋型管理</el-col
        >
    </el-row>
    <el-row :gutter="20">
        <el-col :span="4" :offset="0" style="white-space: nowrap;">
            鞋型号搜索：
            <el-input v-model="inheritIdSearch" placeholder="" clearable @change="getFilterShoes" :suffix-icon="Search"></el-input>
        </el-col>
        
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0">
            <el-table
                :data="shoeTableData"
                style="width: 100%"
                stripe
                border
                height="500"
            >
                <el-table-column
                    prop="shoeRId"
                    label="鞋型编号"
                ></el-table-column>
                <el-table-column
                    prop="shoeColor"
                    label="鞋型颜色"
                ></el-table-column>
                <el-table-column
                    prop="shoeImage"
                    label="鞋型图片"
                    align="center">
                    <template #default="scope">
                        <el-image :src="scope.row.shoeImage" style="width: 150px; height: 100px;"/>
                        <!-- {{ scope.row.shoeImage }} -->
                    </template>
                </el-table-column>
                <el-table-column
                    prop="shoeDesigner"
                    label="设计师"
                ></el-table-column>
                <el-table-column label="操作">
                    <template #default="scope">
                        <el-button
                            type="primary"
                            size="mini"
                            @click="openEditShoeDialog(scope.row)"
                            >编辑</el-button
                        >
                        <el-button type="primary" size="default" @click="openReUploadImageDialog(scope.row)">重新上传鞋图</el-button>
                        
                    </template>
                </el-table-column>
            </el-table>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0">
            <el-button type="primary" @click="openAddShoeDialog">添加新鞋型</el-button>
        </el-col>
    </el-row>
    <el-dialog
        title="添加新鞋型"
        v-model="addShoeDialogVis"
        width="50%"
        >
        <el-form :model="orderForm" label-width="120px" :inline="false" size="">
            <el-form-item label="鞋型编号">
                <el-input v-model="orderForm.shoeRId"></el-input>
            </el-form-item>
            <el-form-item label="选择颜色">
                <el-select v-model="orderForm.shoeColor" placeholder="请选择">
                    <el-option
                        v-for="item in colorOptions"
                        :key="item.value"
                        :label="item.label"
                        :value="item.value"
                    ></el-option>
                </el-select>
            </el-form-item>
            <el-form-item label="设计师">
                <el-input v-model="orderForm.shoeDesigner"></el-input>
            </el-form-item>
        </el-form>
        <template #footer>
        <span>
            <el-button @click="addShoeDialogVis = false">取消</el-button>
            <el-button type="primary" @click="addNewShoe">确认上传</el-button>
        </span>
        </template>
    </el-dialog>
    <el-dialog
        title="编辑鞋型"
        v-model="editShoeDialogVis"
        width="50%">
        <el-form :model="orderForm" label-width="120px" :inline="false" size="">
            <el-form-item label="鞋型编号">
                <el-input v-model="orderForm.shoeRId"></el-input>
            </el-form-item>
            <el-form-item label="选择颜色">
                <el-select v-model="orderForm.shoeColor" placeholder="请选择">
                    <el-option
                        v-for="item in colorOptions"
                        :key="item.value"
                        :label="item.label"
                        :value="item.value"
                    ></el-option>
                </el-select>
            </el-form-item>
            <el-form-item label="设计师">
                <el-input v-model="orderForm.shoeDesigner"></el-input>
            </el-form-item>
        </el-form>
        <template #footer>
        <span>
            <el-button @click="editShoeDialogVis = false">取消</el-button>
            <el-button type="primary" @click="editExistingShoe">确认</el-button>
        </span>
        </template>
    </el-dialog>
    <el-dialog
        title="重新上传鞋图"
        v-model="reUploadImageDialogVis"
        width="50%">
        <el-upload
            :action="`${this.$apiBaseUrl}/shoemanage/uploadshoeimage`"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
            :on-exceed="handleUploadExceed"
            :headers="uploadHeaders"
            :list-type="'picture-card'"
            :auto-upload="false"
            :data="{shoeRId: currentShoeImageId, shoeColor: currentShoeColor}"
            :limit="1"
            :file-list="fileList"
            accept="image/*"
            ref="imageReUpload"
            :drag="true"
        ></el-upload>
        <template #footer>
        <span>
            <el-button @click="reUploadImageDialogVis = false">取消</el-button>
            <el-button type="primary" @click="submitNewImage">确认上传</el-button>
        </span>
        </template>
    </el-dialog>
    
    
    
</template>

<script>
import axios from 'axios';
import { Search } from '@element-plus/icons-vue';

export default {
    data() {
        return {
            token: localStorage.getItem('token'),
            currentShoeImageId: "",
            currentShoeColor: 0,
            fileList: [],
            orderForm: {
                shoeId: "",
                shoeRId: "",
                shoeDesigner: "",
                shoeAdjuster: "",
                shoeColor: "",
            },
            reUploadImageDialogVis: false,
            editShoeDialogVis: false,
            addShoeDialogVis: false,
            Search,
            inheritIdSearch: "",
            shoeTableData: [],
            colorOptions: [],
        };
    },
    mounted() {
        this.getAllColors();
        this.getAllShoes();
    },
    computed: {
        uploadHeaders() {
            return {
                Authorization: `Bearer ${this.token}`
            }
        }
    },
    methods: {
        async getAllColors() {
            const response = await axios.get(`${this.$apiBaseUrl}/general/allcolors`);
            this.colorOptions = response.data;
        },
        async getAllShoes() {
            const response = await axios.get(`${this.$apiBaseUrl}/shoe/getallshoes`);
            this.shoeTableData = response.data;
        },
        async getFilterShoes() {
            const response = await axios.get(`${this.$apiBaseUrl}/shoe/getallshoes`, 
                {params: {shoerid: this.inheritIdSearch}});
            this.shoeTableData = response.data;
        },
        openAddShoeDialog() {
            this.addShoeDialogVis = true;
        },
        openEditShoeDialog(row) {
            this.orderForm = row;
            this.editShoeDialogVis = true;
        },
        openReUploadImageDialog(row) {
            this.reUploadImageDialogVis = true;
            this.currentShoeImageId = row.shoeRId;
            this.currentShoeColor = row.shoeColor;
        },
        handleUploadSuccess() {
            this.$message({
                message: '上传成功',
                type: 'success'
            });
            this.reUploadImageDialogVis = false;
            this.getAllShoes();
        },
        handleUploadError() {
            this.$message.error('上传失败');
        },
        handleUploadExceed() {
            this.$message.error('上传文件数量超出限制');
            this.fileList.pop();
        },
        submitNewImage() {
            this.$refs.imageReUpload.submit();
        },
        addNewShoe() {
            console.log(this.orderForm);
            this.$confirm('确认添加新鞋型？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(async () => {
                this.currentShoeImageId = this.orderForm.shoeRId;
                const response = await axios.post(`${this.$apiBaseUrl}/shoemanage/addnewshoe`, this.orderForm);
                if (response.status === 200) {
                    this.$message({
                        type: 'success',
                        message: '添加成功'
                    });

                    this.$refs.imageUpload.submit();
                    this.addShoeDialogVis = false;
                    this.orderForm = {
                        shoeId: "",
                        shoeRId: "",
                        shoeDesigner: "",
                        shoeAdjuster: "",
                    };
                    this.getAllShoes();
                }
            });
        },
        editExistingShoe() {
            console.log(this.orderForm);
            this.$confirm('确认修改鞋型信息？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(async () => {
                const response = await axios.post(`${this.$apiBaseUrl}/shoemanage/editshoe`, this.orderForm);
                if (response.status === 200) {
                    this.$message({
                        type: 'success',
                        message: '修改成功'
                    });
                    this.editShoeDialogVis = false;
                    this.orderForm = {
                        shoeId: "",
                        shoeRId: "",
                        shoeDesigner: "",
                        shoeAdjuster: "",
                    };
                    this.getAllShoes();
                }
            });
        },
    },

};

</script>
