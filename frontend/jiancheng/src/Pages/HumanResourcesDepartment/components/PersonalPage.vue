<template>
    <el-row :gutter="20">
        <el-col class="u-page-title" :span="24" :offset="0"
            >个人页面</el-col
        >
    </el-row>
    <el-row>
        <el-table :data="userData" border stripe>
            <el-table-column type="index" width="50" />
            <el-table-column v-for="col in columns"
                :prop="col.id"
                :key="col.id"
                :label="col.label"
                :width="col.width">
            </el-table-column>
        </el-table>
        
    </el-row>

</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'

export default {
    data() {
        return {
            userData: []
        }
    },
    methods: {
        async getUserData() {
            const response = await axios.get('http://localhost:3000/users')
            this.userData = response.data
        }
    },
}
</script>