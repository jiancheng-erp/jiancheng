<template>
    <el-container direction="vertical">
        <el-main style="height: 100vh;">
            <el-row :gutter="20" style="text-align: center;">
                <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center;">
                    员工薪资管理
                </el-col>
            </el-row>
            <el-tabs v-model="activeTab" type="card" tab-position="top" @tab-click="">
                <el-tab-pane label="员工细节薪资管理" name="1">
                    <el-row :gutter="20">
                        <el-col :span="24" :offset="0">
                            <el-button type="primary" size="default" @click="">查询</el-button>
                            
                        </el-col>
                    </el-row>
                    
                    <el-row :gutter="20">
                        <el-col :span="24" :offset="0">
                            <el-table :data="staffSalaryTableData" border stripe>
                                <el-table-column prop="name" label="姓名"></el-table-column>
                                <el-table-column prop="department" label="部门"></el-table-column>
                                <el-table-column prop="position" label="职位"></el-table-column>
                                <el-table-column prop="salary" label="薪资"></el-table-column>
                                <el-table-column prop="bonus" label="奖金"></el-table-column>
                                <el-table-column prop="deduction" label="扣款"></el-table-column>
                                <el-table-column prop="total" label="总计"></el-table-column>
                            </el-table>
                        </el-col>
                    </el-row>


                </el-tab-pane>
                <el-tab-pane label="岗位基本薪资管理" :name="2">
                    <el-row :gutter="20">
                        <el-col :span="24" :offset="0"></el-col>
                    </el-row>

                </el-tab-pane>

            </el-tabs>

        </el-main>
    </el-container>

</template>

<script>
import axios from 'axios'

export default {
    data() {
        return {
            activeTab: '1',
            staffSalaryTableData: [],
            panes: [
                {
                    key: '1',
                    label: '员工薪资查询管理'
                },
                {
                    key: '2',
                    label: '岗位基本薪资管理'
                },
                {
                    key: '3',
                    label: '员工考勤状态录入'
                },
                {
                    key: '4',
                    label: '成型代班状态管理'
                }
            ]
        }
    },
    methods: {
        handleClick(tab, event) {
            console.log(tab, event);
        }
    }
}
</script>