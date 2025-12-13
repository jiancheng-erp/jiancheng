<template>
      <div class="actions">
        <el-button type="primary" @click="startCreate">新建模板</el-button>
        <el-button @click="fetchTemplates" :loading="loading">刷新</el-button>
      </div>
    <div class="layout">
      <el-card class="list-panel">
        <div class="list-title">模板列表</div>
        <el-table
          :data="templateRows"
          height="100%"
          border
          @row-click="handleRowClick"
          :row-class-name="rowClass"
        >
          <el-table-column prop="key" label="Key" width="200" />
          <el-table-column prop="description" label="描述" />
          <el-table-column prop="users" label="收件人" />
        </el-table>
      </el-card>
      <el-card class="detail-panel">
        <div class="detail-header">
          <div class="title">模板详情</div>
          <el-tag v-if="selectedKey" type="info">当前：{{ selectedKey }}</el-tag>
        </div>
        <el-form label-width="90px" :model="form" class="detail-form">
          <el-form-item label="Key">
            <el-input v-model="form.key" placeholder="如 production_status_cron" />
          </el-form-item>
          <el-form-item label="描述">
            <el-input v-model="form.description" placeholder="显示用说明" />
          </el-form-item>
          <el-form-item label="收件人">
            <el-select
              v-model="selectedRecipients"
              multiple
              filterable
              clearable
              placeholder="选择员工（值为微信ID）"
              style="width: 100%;"
            >
              <el-option
                v-for="item in staffOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="内容">
            <el-input
              v-model="form.content"
              type="textarea"
              :rows="10"
              placeholder="支持 {placeholders}"
            />
          </el-form-item>
          <el-form-item label="占位符">
            <div class="placeholder-list">
              <el-tag v-for="item in originalPlaceholders" :key="item" type="info" effect="plain">
                {{ '{' + item + '}' }}
              </el-tag>
              <span v-if="!originalPlaceholders.length">无</span>
            </div>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveTemplate" :loading="saving">保存</el-button>
            <el-button @click="resetForm">重置</el-button>
          </el-form-item>
        </el-form>
        <el-divider />
        <div class="preview-header">预览 / 测试</div>
        <el-form label-width="90px" class="detail-form">
          <el-form-item label="上下文JSON">
            <el-input
              v-model="previewContext"
              type="textarea"
              :rows="4"
              placeholder='{"order_rid": "K25-001", "order_shoe_rid": "S01"}'
            />
          </el-form-item>
          <el-form-item>
            <el-button @click="renderPreview" :loading="previewLoading">渲染预览</el-button>
            <el-input
              v-model="testUser"
              style="width: 240px; margin-left: 12px;"
              placeholder="测试接收人"
            />
            <el-button type="success" @click="sendTest" :loading="previewLoading">发送测试</el-button>
          </el-form-item>
          <el-form-item label="预览结果">
            <el-input v-model="previewResult" type="textarea" :rows="5" readonly />
          </el-form-item>
        </el-form>
      </el-card>
    </div>
</template>

<script>
import axios from 'axios'
import { ElMessage } from 'element-plus'

export default {
  name: 'WechatTemplateManager',
  data() {
    return {
      loading: false,
      saving: false,
      previewLoading: false,
      templates: {},
      selectedKey: '',
      form: {
        key: '',
        description: '',
        users: '',
        content: ''
      },
      originalPlaceholders: [],
      selectedRecipients: [],
      staffOptions: [],
      previewContext: '{\n  \n}',
      previewResult: '',
      testUser: ''
    }
  },
  computed: {
    templateRows() {
      return Object.keys(this.templates)
        .sort()
        .map((key) => ({
          key,
          description: this.templates[key]?.description || '',
          users: this.templates[key]?.users || ''
        }))
    }
  },
  mounted() {
    this.fetchTemplates()
    this.fetchStaff()
  },
  methods: {
    rowClass({ row }) {
      return row.key === this.selectedKey ? 'is-active' : ''
    },
    startCreate() {
      this.selectedKey = ''
      this.form = {
        key: '',
        description: '',
        users: '',
        content: ''
      }
      this.originalPlaceholders = []
      this.selectedRecipients = []
      this.previewResult = ''
    },
    async fetchTemplates() {
      this.loading = true
      try {
        const res = await axios.get(`${this.$apiBaseUrl}/wechat/templates`)
        this.templates = res.data || {}
        const firstKey = Object.keys(this.templates)[0]
        if (firstKey) {
          this.applyTemplate(firstKey)
        } else {
          this.startCreate()
        }
      } catch (err) {
        ElMessage.error(err?.message || '加载模板失败')
      } finally {
        this.loading = false
      }
    },
    applyTemplate(key) {
      this.selectedKey = key
      const tpl = this.templates[key] || {}
      this.form = {
        key,
        description: tpl.description || '',
        users: tpl.users || '',
        content: tpl.content || ''
      }
      this.originalPlaceholders = this.extractPlaceholders(this.form.content)
      this.selectedRecipients = (tpl.users || '')
        .split('|')
        .map((u) => u.trim())
        .filter(Boolean)
      this.previewResult = ''
    },
    handleRowClick(row) {
      this.applyTemplate(row.key)
    },
    resetForm() {
      if (this.selectedKey && this.templates[this.selectedKey]) {
        this.applyTemplate(this.selectedKey)
      } else {
        this.startCreate()
      }
    },
    async saveTemplate() {
      if (!this.form.key || !this.form.content || !this.form.users) {
        ElMessage.warning('Key、内容和收件人不能为空')
        return
      }
      const currentPlaceholders = this.extractPlaceholders(this.form.content)
      const isExisting = !!this.templates[this.form.key]
      if (isExisting && !this.samePlaceholders(currentPlaceholders, this.originalPlaceholders)) {
        ElMessage.error('模板占位符不可修改，请保持 {} 中的变量名称不变')
        return
      }
      this.form.users = this.selectedRecipients.join('|')
      this.saving = true
      try {
        await axios.put(`${this.$apiBaseUrl}/wechat/templates/${this.form.key}`, {
          content: this.form.content,
          users: this.form.users,
          description: this.form.description
        })
        ElMessage.success('保存成功')
        await this.fetchTemplates()
        this.applyTemplate(this.form.key)
      } catch (err) {
        ElMessage.error(err?.response?.data?.error || '保存失败')
      } finally {
        this.saving = false
      }
    },
    parseContext() {
      if (!this.previewContext.trim()) return {}
      try {
        return JSON.parse(this.previewContext)
      } catch (err) {
        ElMessage.error('上下文 JSON 解析失败')
        throw err
      }
    },
    async renderPreview() {
      if (!this.selectedKey) {
        ElMessage.warning('请先选择或保存模板')
        return
      }
      this.previewLoading = true
      try {
        const context = this.parseContext()
        const res = await axios.post(
          `${this.$apiBaseUrl}/wechat/templates/${this.selectedKey}/render`,
          { context }
        )
        this.previewResult = res.data?.rendered || ''
      } catch (err) {
        ElMessage.error(err?.response?.data?.error || '渲染失败')
      } finally {
        this.previewLoading = false
      }
    },
    async sendTest() {
      if (!this.selectedKey) {
        ElMessage.warning('请先选择或保存模板')
        return
      }
      if (!this.testUser) {
        ElMessage.warning('请输入测试接收人')
        return
      }
      this.previewLoading = true
      try {
        const context = this.parseContext()
        await axios.post(
          `${this.$apiBaseUrl}/wechat/templates/${this.selectedKey}/send-test`,
          { touser: this.testUser, context }
        )
        ElMessage.success('测试发送已触发')
      } catch (err) {
        ElMessage.error(err?.response?.data?.error || '发送失败')
      } finally {
        this.previewLoading = false
      }
    },
    extractPlaceholders(content) {
      const matches = [...(content || '').matchAll(/{([^{}]+)}/g)]
      const unique = Array.from(new Set(matches.map((m) => m[1].trim()).filter(Boolean)))
      return unique
    },
    samePlaceholders(a, b) {
      if (a.length !== b.length) return false
      const setA = new Set(a)
      const setB = new Set(b)
      if (setA.size !== setB.size) return false
      for (const key of setA) {
        if (!setB.has(key)) return false
      }
      return true
    },
    async fetchStaff() {
      try {
        const res = await axios.get(`${this.$apiBaseUrl}/staffmanage/getallstaff`)
        this.staffOptions = (res.data || [])
          .filter((s) => s.wechatId)
          .map((s) => ({
            label: s.staffName,
            value: s.wechatId
          }))
      } catch (err) {
        ElMessage.error(err?.message || '加载员工列表失败')
      }
    }
  }
}
</script>

<style scoped>
.wechat-template-manager {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 12px;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.layout {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 16px;
}
.list-panel,
.detail-panel {
  height: calc(100vh - 160px);
  display: flex;
  flex-direction: column;
}
.list-title,
.detail-header {
  font-weight: 600;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.detail-form {
  width: 100%;
}
.actions {
  display: flex;
  gap: 8px;
  align-items:end
}
.el-table .is-active {
  background: #f5f7fa;
}
.placeholder-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
</style>
