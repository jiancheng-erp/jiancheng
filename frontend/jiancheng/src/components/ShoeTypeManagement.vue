<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center">鞋型管理</el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="4" :offset="0" style="white-space: nowrap">
            鞋型号搜索：
            <el-input v-model="inheritIdSearch" placeholder="" clearable @change="getFilterShoes" :suffix-icon="Search"></el-input>
        </el-col>
        <el-col :span="6" :offset="10">
            <el-button type="primary" @click="openAddShoeDialog">添加新鞋型</el-button>
            <el-button type="primary" icon="Edit" @click="openShoeColorDialog">添加鞋款颜色</el-button>
        </el-col>

        <el-col :span="2" :offset="0">
            <el-button v-if='userRole == 4' type="warning" @click="openShoeColorManagementDialog"> 颜色管理 </el-button>
        </el-col>
        

    </el-row>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0">
            <el-table :data="shoeTableData" style="width: 100%" stripe border height="580" row-key="shoeId">
                <el-table-column type="expand">
                    <template #default="props">
                        <el-table
                            :data="props.row.shoeTypeData"
                            border
                            :row-key="
                                (row) => {
                                    return `${row.shoeId}`
                                }
                            "
                        >
                            <el-table-column type="index" />
                            <el-table-column prop="colorName" label="鞋型颜色" width="100px"> </el-table-column>
                            <el-table-column prop="shoeImageUrl" label="鞋型图片" align="center">
                                <template #default="scope">
                                    <el-image :src="getUniqueImageUrl(scope.row.shoeImageUrl)" style="width: 150px; height: 100px" loading="eager" />
                                </template>
                            </el-table-column>
                            <el-table-column label="操作">
                                <template #default="scope">
                                    <el-button type="primary" @click="openReUploadImageDialog(scope.row)">重新上传鞋图</el-button>
                                    <el-button v-if="allowDelete" type="danger" @click="deleteShoeModel(scope.row)">删除</el-button>
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
    <el-row :gutter="0">
        
        <el-col :span="8" :offset="2">
            <el-pagination
                @size-change="handleSizeChange"
                @current-change="handlePageChange"
                :current-page="currentPage"
                :page-sizes="[20, 40, 60, 100]"
                :page-size="pageSize"
                layout="total, sizes, prev, pager, next, jumper"
                :total="totalItems"
            />
        </el-col>
    </el-row>
    <el-dialog title="鞋款颜色管理" v-model="colorManagementDialogVis" width="80%">
        <el-row>
            <el-col :span="1" :offset="2">
                <el-button type="warning" @click="clearColorSelect">清除所选</el-button>
            </el-col>
            <el-col :span="1" :offset="1">
                <el-button type="primary" @click="mergeSelectedColor">颜色合并</el-button>
            </el-col>
        </el-row>
        <el-table :data="colorInfoList" row-key="colorId" ref="colorSelectionTable" @selection-change="handleColorSelect">
            <el-table-column size="small" type="selection" align="center"> </el-table-column>
            <el-table-column sortable prop="colorNameCN" label="颜色中文"></el-table-column>
            <el-table-column prop="colorNameEN" label="颜色英文"></el-table-column>
            <el-table-column prop="colorNameSP" label="颜色西语"></el-table-column>
            <el-table-column sortable prop="colorBoundCount" label="当前颜色绑定鞋款"></el-table-column>
        </el-table>
    </el-dialog>
    <el-dialog title="添加鞋款颜色" v-model="addShoeColorDialogVis" width="50%">
                <el-input v-model="colorForm.colorName" @input="filterColorInfoList"></el-input>

            <!-- <el-form-item label="颜色英文名称">
                <el-input v-model="colorForm.colorNameEN"></el-input>
            </el-form-item>
            <el-form-item label="颜色西语名称">
                <el-input v-model="colorForm.colorNameSP"></el-input>
            </el-form-item>
            <el-form-item label="颜色意语名称">
                <el-input v-model="colorForm.colorNameIT"></el-input>
            </el-form-item> -->
        <el-table :data="displayColorInfoList" row-key="colorId" ref="colorSelectionTable" >
            <el-table-column sortable prop="colorNameCN" label="颜色中文"></el-table-column>
            <el-table-column prop="colorNameEN" label="颜色英文"></el-table-column>
            <el-table-column prop="colorNameSP" label="颜色西语"></el-table-column>
            <el-table-column sortable prop="colorBoundCount" label="当前颜色绑定鞋款"></el-table-column>
        </el-table>
        <template #footer>
            <span>
                <el-button @click="addShoeColorDialogVis = false">取消</el-button>
                <el-button type="primary" @click="addShoeColor">提交新颜色</el-button>
            </span>
        </template>
    </el-dialog>
    <el-dialog title="添加新鞋型" v-model="addShoeDialogVis" width="50%">
        <el-form :model="shoeForm" label-width="120px" :inline="false">
            <el-form-item label="鞋型编号">
                <el-input v-model="shoeForm.shoeRid"></el-input>
            </el-form-item>
            <el-form-item label="设计师">
                <el-input v-model="shoeForm.shoeDesigner"></el-input>
            </el-form-item>
            <el-form-item label="设计部门">
                <el-select v-model="shoeForm.shoeDepartmentId" placeholder="请选择设计部门">
                    <el-option label="开发一部" value="开发一部"></el-option>
                    <el-option label="开发二部" value="开发二部"></el-option>
                    <el-option label="开发三部" value="开发三部"></el-option>
                    <el-option label="开发五部" value="开发五部"></el-option>
                </el-select>
            </el-form-item>
            <el-form-item label="选择颜色">
                <el-select v-model="shoeForm.colorId" placeholder="请选择" multiple>
                    <el-option v-for="item in colorOptions" :key="item.value" :label="item.label" :value="item.value"></el-option>
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
        <el-form :model="shoeForm" label-width="120px" :inline="false">
            <el-form-item label="所属鞋型编号">
                <el-input v-model="colorModel" :disabled="true"></el-input>
            </el-form-item>
            <el-form-item label="选择颜色">
                <el-select v-model="shoeForm.colorId" placeholder="请选择" multiple>
                    <el-option v-for="item in colorOptions" :key="item.value" :label="item.label" :value="item.value"></el-option>
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
        <el-form :model="shoeForm" label-width="120px" :inline="false">
            <el-form-item label="鞋型编号">
                <el-input v-model="shoeForm.shoeRid" :disabled="this.userRole == 21 ? true : false"></el-input>
            </el-form-item>
            <el-form-item label="设计师">
                <el-input v-model="shoeForm.shoeDesigner" :disabled="this.userRole == 21 ? true : false"></el-input>
            </el-form-item>
            <el-form-item label="选择颜色">
                <el-select v-model="shoeForm.shoeTypeColors" placeholder="请选择" multiple>
                    <el-option v-for="item in colorOptions" :key="item.value" :label="item.label" :value="item.value"></el-option>
                </el-select>
            </el-form-item>
            <el-form-item label="设计部门">
                <el-select v-model="shoeForm.shoeDepartmentId" :disabled="this.userRole == 21 ? true : false">
                    <el-option label="开发一部" value="开发一部"></el-option>
                    <el-option label="开发二部" value="开发二部"></el-option>
                    <el-option label="开发三部" value="开发三部"></el-option>
                    <el-option label="开发五部" value="开发五部"></el-option>
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
    <el-dialog title="裁剪并上传鞋图" v-model="reUploadImageDialogVis" width="60%" :close-on-click-modal="false">
        <!-- 文件选择器 -->
        <input type="file" accept="image/*" @change="onFileChange" />

        <!-- 裁剪器 -->
        <cropper
            v-if="imageUrl"
            ref="cropper"
            :src="imageUrl"
            :auto-zoom="true"
            :resize-image="true"
            :background-class="'cropper-background'"
        />

        <!-- 底部按钮 -->
        <template #footer>
            <el-button @click="reUploadImageDialogVis = false">取消</el-button>
            <el-button type="primary" :disabled="!imageUrl" @click="uploadCroppedImage"> 确认上传 </el-button>
        </template>
    </el-dialog>
</template>

<script>
import axios from 'axios'
import { Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { Cropper } from 'vue-advanced-cropper'
import 'vue-advanced-cropper/dist/style.css'

export default {
    components: {
        Cropper
    },
    data() {
        return {
            token: localStorage.getItem('token'),
            currentShoeImageId: '',
            currentShoeColor: '',
            currentShoeColorId: 0,
            currentPage: 1,
            pageSize: 20,
            totalItems: 0,
            fileList: [],
            shoeForm: {
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
            reUploadImageDialogVis: false,
            editShoeDialogVis: false,
            addShoeDialogVis: false,
            addShoeColorDialogVis: false,
            colorManagementDialogVis: false,
            colorInfoList: [],
            Search,
            inheritIdSearch: '',
            shoeTableData: [],
            colorOptions: [],
            userRole: localStorage.getItem('role'),
            staffRole: localStorage.getItem('staffid'),
            shoeModel: false,
            colorModel: '',
            idModel: '',
            currentImageRow: {},
            expandedRows: [],
            imageUrl: ''
        }
    },
    mounted() {
        this.getAllColors()
        this.getAllShoes()
        this.updateColorInfo()
    },
    computed: {
        uploadHeaders() {
            return {
                Authorization: `Bearer ${this.token}`
            }
        },
        allowDelete() {
            return userRole != 21
        },
        userIsManager(){
            return userRole == 4
        },
        userIsClerk(){
            return userRole == 21
        }
    },
    methods: {
        getUniqueImageUrl(imageUrl) {
            return `${imageUrl}?timestamp=${new Date().getTime()}`
        },
        async getAllColors() {
            const response = await axios.get(`${this.$apiBaseUrl}/general/allcolors`)
            this.colorOptions = response.data
        },
        async getAllShoes() {
            // new api call
            const response = await axios.get(`${this.$apiBaseUrl}/shoe/getallshoesnew`, {
                params: { shoerid: this.inheritIdSearch, role: this.staffRole, page: this.currentPage, pageSize: this.pageSize }
            })
            this.shoeTableData = response.data.shoeTable
            this.totalItems = response.data.total
        },
        async getFilterShoes() {
            this.currentPage = 1
            const response = await axios.get(`${this.$apiBaseUrl}/shoe/getallshoesnew`, {
                params: { shoerid: this.inheritIdSearch, role: this.staffRole, page: this.currentPage, pageSize: this.pageSize }
            })
            this.shoeTableData = response.data.shoeTable
            this.totalItems = response.data.total
        },
        async updateColorInfo() {
            const response = await axios.get(`${this.$apiBaseUrl}/shoe/shoecolorinfo`)
            this.colorInfoList = response.data.colorInfo
            this.displayColorInfoList = this.colorInfoList
            
        },
        filterColorInfoList(){
            console.log(this.colorInfoList)
            console.log(this.colorForm.colorName)
            this.displayColorInfoList = this.colorInfoList.filter(color => color.colorNameCN.includes(this.colorForm.colorName))
            console.log(this.displayColorInfoList)
            
            // this.displayColorInfoList = this.colorInfoList.filter(color => color.)
        },
        openShoeColorManagementDialog() {
            this.colorManagementDialogVis = true
        },
        clearColorSelect() {
            this.$refs.colorSelectionTable.clearSelection()
        },
        handleColorSelect(selection) {
            console.log(selection)
        },
        handleSizeChange(value) {
            this.pageSize = value
            this.getAllShoes()
        },
        handlePageChange(value) {
            this.currentPage = value
            this.getAllShoes()
        },
        async mergeSelectedColor() {
            console.log(this.$refs.colorSelectionTable.getSelectionRows())
            const res = await axios.post(`${this.$apiBaseUrl}/shoe/shoecolormerge`, {
                colorList: this.$refs.colorSelectionTable.getSelectionRows()
            })
            await this.updateColorInfo()
        },
        openAddShoeDialog() {
            this.addShoeDialogVis = true
            this.shoeForm = {
                shoeId: '',
                shoeRid: '',
                shoeDesigner: '',
                shoeAdjuster: '',
                shoeDepartmentId: ''
            }
        },
        openEditShoeDialog(row) {
            this.shoeForm = row
            this.editShoeDialogVis = true
        },
        openReUploadImageDialog(row) {
            this.reUploadImageDialogVis = true
            this.currentShoeImageId = row.shoeRid
            this.currentShoeColor = row.colorName
            this.currentShoeColorId = row.colorId
            this.currentImageRow = row
        },
        async handleUploadSuccess() {
            // const localImageUrl = URL.createObjectURL(this.fileList[0]);
            // this.$set(row, "shoeImageUrl", localImageUrl);
            this.$message({
                message: '上传成功',
                type: 'success'
            })
            this.reUploadImageDialogVis = false
            this.fileList = []
            await this.getFilterShoes()
            this.$forceUpdate()
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
            const response = await axios.post(`${this.$apiBaseUrl}/general/addnewcolor`, this.colorForm)
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
            console.log(this.shoeForm)
            this.$confirm('确认添加新鞋型？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(async () => {
                this.currentShoeImageId = this.shoeForm.shoeRid
                const response = await axios.post(`${this.$apiBaseUrl}/shoemanage/addshoe`, this.shoeForm)
                if (response.status === 200) {
                    this.$message({
                        type: 'success',
                        message: '添加成功'
                    })
                    this.addShoeDialogVis = false
                    this.shoeForm = {
                        shoeId: '',
                        shoeRid: '',
                        shoeDesigner: '',
                        shoeAdjuster: '',
                        shoeDepartmentId: '',
                        colorId: ''
                    }
                    this.inheritIdSearch = ''
                    await this.getAllShoes()
                }
            })
        },
        editExistingShoe() {
            this.$confirm('确认修改鞋型信息？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(async () => {
                const response = await axios.post(`${this.$apiBaseUrl}/shoemanage/editshoe`, this.shoeForm)
                if (response.status === 200) {
                    this.$message({
                        type: 'success',
                        message: '修改成功'
                    })
                    this.editShoeDialogVis = false
                    this.shoeForm = {
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
                this.shoeForm.colorId = value.shoeTypeColors.map((colorEntity) => colorEntity.value)
            } else {
                this.$confirm('确认上传鞋款？', '提示', {
                    confirmButtonText: '确定',
                    cancelButtonText: '取消',
                    type: 'warning'
                }).then(async () => {
                    if (this.shoeForm.colorId == '') {
                        ElMessage.warning('请选择鞋款颜色')
                    } else {
                        this.shoeForm.shoeId = this.idModel
                        console.log(this.shoeForm)
                        const response = await axios.post(`${this.$apiBaseUrl}/shoemanage/addshoetype`, this.shoeForm)
                        if (response.status === 200) {
                            this.$message({
                                type: 'success',
                                message: '上传成功'
                            })
                            this.shoeModel = false
                            this.shoeForm = {
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
                const response = await axios.post(`${this.$apiBaseUrl}/shoemanage/deleteshoetype`, {
                    colorId: value.colorId,
                    shoeId: value.shoeId,
                    shoeImageUrl: value.shoeImageUrl,
                    shoeTypeId: value.shoeTypeId
                })
                if (response.status === 200) {
                    this.$message({
                        type: 'success',
                        message: '删除成功'
                    })
                    this.getAllShoes()
                }
            })
        },
        onFileChange(event) {
            const file = event.target.files[0]
            if (!file) return

            const reader = new FileReader()
            reader.onload = () => {
                this.imageUrl = reader.result
            }
            reader.readAsDataURL(file)
        },
        uploadCroppedImage() {
            const result = this.$refs.cropper.getResult()
            const canvas = result.canvas
            if (!canvas) return

            canvas.toBlob((blob) => {
                const formData = new FormData()
                formData.append('file', blob, 'cropped.jpg')
                formData.append('shoeRid', this.currentShoeImageId)
                formData.append('shoeColorId', this.currentShoeColorId)
                formData.append('shoeColorName', this.currentShoeColor)
                // 你可以根据需要添加其他字段
                // formData.append('shoeRid', this.currentShoeImageId)

                this.$axios
                    .post(`${this.$apiBaseUrl}/shoemanage/uploadshoeimage`, formData)
                    .then(() => {
                        this.$message.success('上传成功')
                        this.dialogVisible = false
                        this.imageUrl = null
                    })
                    .catch(() => {
                        this.$message.error('上传失败')
                    })
            }, 'image/jpeg')
        }
    }
}
</script>
