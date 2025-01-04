<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center">鞋型管理</el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="4" :offset="0" style="white-space: nowrap">
            鞋型号搜索：
            <el-input v-model="inheritIdSearch" placeholder="" clearable @change="getFilterShoes"
                :suffix-icon="Search"></el-input>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0">
            <el-table :data="shoeTableData" style="width: 100%" stripe border height="580" :key="tableDataKey">
                <el-table-column type="expand">
                    <template #default="props">
                        <el-table :data="props.row.shoeTypeData" border :row-key="(row) => {
                                return `${row.shoeId}`
                            }
                            ">
                            <el-table-column type="index" />
                            <el-table-column prop="colorName" label="鞋型颜色" width="100px">
                            </el-table-column>
                            <el-table-column prop="shoeImageUrl" label="鞋型图片" align="center">
                                <template #default="scope">
                                    <el-image :src="getUniqueImageUrl(scope.row.shoeImageUrl)" style="width: 150px; height: 100px" loading="eager" />
                                </template>
                            </el-table-column>
                            <el-table-column label="操作">
                                <template #default="scope">
                                    <el-button type="primary"
                                        @click="openReUploadImageDialog(scope.row)">重新上传鞋图</el-button>
                                    <el-button type="danger" @click="deleteShoeModel(scope.row)">删除</el-button>
                                </template>
                            </el-table-column>
                        </el-table>
                    </template>
                </el-table-column>
                <el-table-column prop="shoeRid" label="鞋型编号" width="300px"></el-table-column>
                <el-table-column prop="shoeDesigner" label="设计师"></el-table-column>
                <el-table-column prop="shoeDepartmentId" label="设计部门"></el-table-column>
                <el-table-column label="操作">
                    <template #default="scope">
                        <el-button type="primary" @click="openEditShoeDialog(scope.row)">编辑</el-button>
                        <el-button type="primary" size="default" @click="addShoeModel(scope.row)">添加鞋款</el-button>

                    </template>
                </el-table-column>
            </el-table>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0">
            <el-button type="primary" @click="openAddShoeDialog">添加新鞋型</el-button>
            <el-button type="primary" icon="Edit" @click="openShoeColorDialog">添加鞋款颜色</el-button>
        </el-col>
    </el-row>
    <el-dialog title="添加鞋款颜色" v-model="addShoeColorDialogVis" width="50%">
        <el-form :model="colorForm" label-width="120px" :inline="false">
            <el-form-item label="颜色中文名称">
                <el-input v-model="colorForm.colorName"></el-input>
            </el-form-item>
            <el-form-item label="颜色英文名称">
                <el-input v-model="colorForm.colorNameEN"></el-input>
            </el-form-item>
            <el-form-item label="颜色西语名称">
                <el-input v-model="colorForm.colorNameSP"></el-input>
            </el-form-item>
            <el-form-item label="颜色意语名称">
                <el-input v-model="colorForm.colorNameIT"></el-input>
            </el-form-item>
        </el-form>
        <template #footer>
            <span>
                <el-button @click="addShoeColorDialogVis = false">取消</el-button>
                <el-button type="primary" @click="addShoeColor">提交新颜色</el-button>
            </span>
        </template>
    </el-dialog>
    <el-dialog title="添加新鞋型" v-model="addShoeDialogVis" width="50%">
        <el-form :model="orderForm" label-width="120px" :inline="false">
            <el-form-item label="鞋型编号">
                <el-input v-model="orderForm.shoeRid"></el-input>
            </el-form-item>
            <el-form-item label="设计师">
                <el-input v-model="orderForm.shoeDesigner"></el-input>
            </el-form-item>
            <el-form-item label="设计部门">
                <el-select v-model="orderForm.shoeDepartmentId" placeholder="请选择设计部门">
                    <el-option label="开发一部" value="开发一部"></el-option>
                    <el-option label="开发二部" value="开发二部"></el-option>
                    <el-option label="开发三部" value="开发三部"></el-option>
                </el-select>
            </el-form-item>
        </el-form>
        <template #footer>
            <span>
                <el-button @click="addShoeDialogVis = false">取消</el-button>
                <el-button type="primary" @click="addNewShoe">确认上传</el-button>
            </span>
        </template>
    </el-dialog>
    <el-dialog title="添加鞋款" v-model="shoeModel" width="50%">
        <el-form :model="orderForm" label-width="120px" :inline="false">
            <el-form-item label="所属鞋型编号">
                <el-input v-model="colorModel" :disabled="true"></el-input>
            </el-form-item>
            <el-form-item label="选择颜色">
                <el-select v-model="orderForm.colorId" placeholder="请选择" multiple>
                    <el-option v-for="item in colorOptions" :key="item.value" :label="item.label"
                        :value="item.value"></el-option>
                </el-select>
            </el-form-item>
        </el-form>
        <template #footer>
            <span>
                <el-button @click="shoeModel = false">取消</el-button>
                <el-button type="primary" @click="addShoeModel">确认上传</el-button>
            </span>
        </template>
    </el-dialog>
    <el-dialog title="编辑鞋型" v-model="editShoeDialogVis" width="50%">
        <el-form :model="orderForm" label-width="120px" :inline="false">
            <el-form-item label="鞋型编号">
                <el-input v-model="orderForm.shoeRid" :disabled="this.userRole == 21 ? true : false"></el-input>
            </el-form-item>
            <el-form-item label="设计师">
                <el-input v-model="orderForm.shoeDesigner" :disabled="this.userRole == 21 ? true : false"></el-input>
            </el-form-item>
            <el-form-item label="设计部门">
                <el-select v-model="orderForm.shoeDepartmentId" :disabled="this.userRole == 21 ? true : false">
                    <el-option label="开发一部" value="开发一部"></el-option>
                    <el-option label="开发二部" value="开发二部"></el-option>
                    <el-option label="开发三部" value="开发三部"></el-option>
                </el-select>
            </el-form-item>
        </el-form>
        <template #footer>
            <span>
                <el-button @click="editShoeDialogVis = false">取消</el-button>
                <el-button type="primary" @click="editExistingShoe">确认</el-button>
            </span>
        </template>
    </el-dialog>
    <el-dialog title="重新上传鞋图" v-model="reUploadImageDialogVis" width="50%">
        <el-upload :action="`${this.$apiBaseUrl}/shoemanage/uploadshoeimage`" :on-success="handleUploadSuccess"
            :on-error="handleUploadError" :on-exceed="handleUploadExceed" :headers="uploadHeaders"
            :list-type="'picture-card'" :auto-upload="false"
            :data="{ shoeRid: this.currentShoeImageId, shoeColorName: this.currentShoeColor, shoeColorId:this.currentShoeColorId }" :limit="1" :file-list="fileList"
            accept="image/*" ref="imageReUpload" :drag="true"></el-upload>
        <template #footer>
            <span>
                <el-button @click="reUploadImageDialogVis = false">取消</el-button>
                <el-button type="primary" @click="submitNewImage">确认上传</el-button>
            </span>
        </template>
    </el-dialog>
</template>

<script>
import axios from 'axios'
import { Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus';

export default {
    data() {
        return {
            token: localStorage.getItem('token'),
            currentShoeImageId: '',
            currentShoeColor: '',
            currentShoeColorId: 0,
            fileList: [],
            orderForm: {
                shoeId: '',
                shoeRid: '',
                shoeDesigner: '',
                shoeAdjuster: '',
                colorId: '',
                shoeDepartmentId: ''
            },
            colorForm: {
                colorName: '',
                colorNameEN: '',
                colorNameIT: '',
                colorNameSP: ''
            },
            tableDataKey: 0,
            reUploadImageDialogVis: false,
            editShoeDialogVis: false,
            addShoeDialogVis: false,
            addShoeColorDialogVis: false,
            Search,
            inheritIdSearch: '',
            shoeTableData: [],
            colorOptions: [],
            userRole: localStorage.getItem('role'),
            shoeModel: false,
            colorModel: '',
            idModel: '',
        }
    },
    mounted() {
        this.getAllColors()
        this.getAllShoes()
    },
    computed: {
        uploadHeaders() {
            return {
                Authorization: `Bearer ${this.token}`
            }
        }
    },
    methods: {
        getUniqueImageUrl(imageUrl) {
            return `${imageUrl}?timestamp=${new Date().getTime()}`;
        },
        async getAllColors() {
            const response = await axios.get(`${this.$apiBaseUrl}/general/allcolors`)
            this.colorOptions = response.data
        },
        async getAllShoes() {
            // new api call
            const response = await axios.get(`${this.$apiBaseUrl}/shoe/getallshoesnew`)
            this.shoeTableData = response.data
        },
        async getFilterShoes() {
            const response = await axios.get(`${this.$apiBaseUrl}/shoe/getallshoesnew`, {
                params: { shoerid: this.inheritIdSearch }
            })
            this.shoeTableData = response.data
        },
        openAddShoeDialog() {
            this.addShoeDialogVis = true
            this.orderForm = {
                shoeId: '',
                shoeRid: '',
                shoeDesigner: '',
                shoeAdjuster: '',
                shoeDepartmentId: ''
            }
        },
        openEditShoeDialog(row) {
            this.orderForm = row
            this.editShoeDialogVis = true
        },
        openReUploadImageDialog(row) {
            this.reUploadImageDialogVis = true
            this.currentShoeImageId = row.shoeRid
            this.currentShoeColor = row.colorName
            this.currentShoeColorId = row.colorId
        },
        async handleUploadSuccess() {
            this.$message({
                message: '上传成功',
                type: 'success'
            })
            this.reUploadImageDialogVis = false
            this.fileList = []
            await this.getAllShoes()
            this.$forceUpdate();
            this.tableDataKey++
        },
        handleUploadError() {
            this.fileList = []
            this.$message.error('上传失败')
        },
        handleUploadExceed() {
            this.$message.error('上传文件数量超出限制')
            this.fileList.pop()
        },
        submitNewImage() {
            this.$refs.imageReUpload.submit()
        },
        openShoeColorDialog() {
            this.addShoeColorDialogVis = true
        },
        async addShoeColor() {
            const response = await axios.post(
                `${this.$apiBaseUrl}/general/addnewcolor`,
                this.colorForm
            )
            if (response.status === 200) {
                this.$message({
                        type: 'success',
                        message: '添加成功'
                    })
            }
            this.getAllColors()
            this.addShoeColorDialogVis = false
            
            this.colorForm = {
                colorName: '',
                colorNameEN: '',
                colorNameIT: '',
                colorNameSP: ''
            }
            // to do handle on success/ fail
            return
        },
        addNewShoe() {
            this.$confirm('确认添加新鞋型？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(async () => {
                this.currentShoeImageId = this.orderForm.shoeRid
                const response = await axios.post(
                    `${this.$apiBaseUrl}/shoemanage/addshoe`,
                    this.orderForm
                )
                if (response.status === 200) {
                    this.$message({
                        type: 'success',
                        message: '添加成功'
                    })
                    this.addShoeDialogVis = false
                    this.orderForm = {
                        shoeId: '',
                        shoeRid: '',
                        shoeDesigner: '',
                        shoeAdjuster: '',
                        shoeDepartmentId: ''
                    }
                    this.getAllShoes()
                }
            })
        },
        editExistingShoe() {
            this.$confirm('确认修改鞋型信息？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(async () => {
                const response = await axios.post(
                    `${this.$apiBaseUrl}/shoemanage/editshoe`,
                    this.orderForm
                )
                if (response.status === 200) {
                    this.$message({
                        type: 'success',
                        message: '修改成功'
                    })
                    this.editShoeDialogVis = false
                    this.orderForm = {
                        shoeId: '',
                        shoeRid: '',
                        shoeDesigner: '',
                        shoeAdjuster: '',
                        shoeDepartmentId: ''
                    }
                    this.getAllShoes()
                }
            })
        },
        addShoeModel(value) {
            if (!this.shoeModel) {
                this.shoeModel = true
                this.colorModel = value.shoeRid
                this.idModel = value.shoeId
            } else {
                this.$confirm('确认上传鞋款？', '提示', {
                    confirmButtonText: '确定',
                    cancelButtonText: '取消',
                    type: 'warning'
                }).then(async () => {
                    if (this.orderForm.colorId == '') {
                        ElMessage.warning('请选择鞋款颜色')
                    } else {
                        this.orderForm.shoeId = this.idModel
                        const response = await axios.post(
                            `${this.$apiBaseUrl}/shoemanage/addshoetype`,
                            this.orderForm
                        )
                        if (response.status === 200) {
                            this.$message({
                                type: 'success',
                                message: '上传成功'
                            })
                            this.shoeModel = false
                            this.orderForm = {
                                shoeId: '',
                                shoeRid: '',
                                shoeDesigner: '',
                                shoeAdjuster: '',
                                shoeDepartmentId: ''
                            }
                            this.colorModel = ''
                            this.idModel = ''
                            this.getAllShoes()
                        }
                    }
                })
            }
        },
        deleteShoeModel(value) {
            this.$confirm('确认删除鞋款？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(async () => {
                // 更换删除鞋款的路由
                const response = await axios.post(
                    `${this.$apiBaseUrl}/shoemanage/deleteshoetype`,
                    {
                        colorId: value.colorId,
                        shoeId: value.shoeId,
                        shoeImageUrl: value.shoeImageUrl,
                        shoeTypeId: value.shoeTypeId
                    }
                )
                if (response.status === 200) {
                    this.$message({
                        type: 'success',
                        message: '删除成功'
                    })
                    this.getAllShoes()
                }
            })

        }
    }
}
</script>
