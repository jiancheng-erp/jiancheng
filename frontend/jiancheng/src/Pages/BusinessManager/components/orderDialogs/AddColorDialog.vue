<template>
    <el-dialog title="添加/选择颜色" :model-value="visible" @update:model-value="$emit('update:visible', $event)"
        width="480px" append-to-body :close-on-click-modal="false" custom-class="add-color-dialog" @close="handleClose">
        <div style="margin-bottom:12px">
            <div style="margin-bottom:6px;font-weight:600">该鞋型已有颜色（可直接选择，已在订单中的颜色会被排除）</div>
            <el-select v-model="selectedExistingColorIds" multiple filterable collapse-tags placeholder="选择已有颜色"
                style="width:100%">
                <el-option v-for="c in shoeTypeOptions" :key="c.value" :label="c.label" :value="c.value" />
            </el-select>
        </div>
        <div style="margin-top:8px;margin-bottom:12px">
            <div style="margin-bottom:6px;font-weight:600">其他颜色 / 新颜色（可在下方输入新颜色）</div>
            <el-select v-model="selectedColorIds" multiple filterable collapse-tags placeholder="从所有颜色中选择"
                style="width:100%">
                <el-option v-for="c in colorOptions" :key="c.value" :label="c.label" :value="c.value" />
            </el-select>
        </div>
        <div style="margin-bottom:12px">
            <el-input v-model="newColorName" placeholder="输入新颜色名称后点击确定将创建颜色（可留空）" />
        </div>
        <template #footer>
            <el-button @click="handleClose">取消</el-button>
            <el-button type="primary" @click="onSubmit">确定</el-button>
        </template>
    </el-dialog>
</template>


<script>
import axios from 'axios'
import { ElMessage } from 'element-plus'
export default {
    name: 'AddColorDialog',
    props: {
        visible: {
            type: Boolean,
            default: false
        },
        shoeId: {
            type: [String, Number],
            default: ''
        },
        shoeRid: {
            type: String,
            default: ''
        },
        shoeTypeColors: {
            // expected: array of {value,label} or array of ids/labels
            type: Array,
            default: () => []
        }
    },
    data() {
        return {
            colorOptions: [],
            selectedColorIds: [],
            selectedExistingColorIds: [],
            newColorName: ''
        }
    },
    computed: {
        shoeTypeOptions() {
            return this.normalizeShoeTypeColors()
        }
    },
    watch: {
        shoeTypeColors(newVal) {
            console.debug('AddColorDialog shoeTypeColors prop changed:', newVal)
        },
        visible(val) {
            console.debug('AddColorDialog visible changed', val, 'shoeTypeOptions:', this.shoeTypeOptions)
            if (val) {
                this.loadColors()
                this.ensureTopmost()
            }
        }
    },
    methods: {
        handleClose() {
            this.$emit('update:visible', false)
            this.selectedColorIds = []
            this.selectedExistingColorIds = []
            this.newColorName = ''
        },
        async loadColors() {
            try {
                const resp = await axios.get(`${this.$apiBaseUrl}/general/allcolors`)
                this.colorOptions = resp.data
            } catch (e) {
                console.error('loadColors failed', e)
            }
        },
        async ensureTopmost() {
            await this.$nextTick()
            try {
                const el = document.querySelector('.add-color-dialog')
                if (el) {
                    if (el.parentNode !== document.body) document.body.appendChild(el)
                    el.style.zIndex = '10051'
                    el.style.position = 'fixed'
                }
            } catch (e) {
                console.warn('ensureTopmost failed', e)
            }
        },
        // Normalize shoeTypeColors (prop) into option objects {value,label}
        normalizeShoeTypeColors() {
            try {
                const input = this.shoeTypeColors || []
                const opts = input.map((c) => {
                    if (c == null) return null
                    if (typeof c === 'object') {
                        return { value: c.value || c.colorId || c.color_id || c.value, label: c.label || c.colorName || c.color_name || String(c.value || c.colorId || c.color_id) }
                    }
                    // c is primitive: could be id or label
                    const found = (this.colorOptions || []).find((co) => String(co.value) === String(c) || String(co.label) === String(c))
                    if (found) return { value: found.value, label: found.label }
                    return { value: c, label: String(c) }
                }).filter(Boolean)
                return opts
            } catch (e) {
                console.warn('normalizeShoeTypeColors failed', e)
                return []
            }
        },
        async onSubmit() {
            // ensure dialog is topmost when interacting
            this.ensureTopmost()
            try {
                const resultIds = []
                // include selected existing colors (from shoe-type options)
                if (Array.isArray(this.selectedExistingColorIds) && this.selectedExistingColorIds.length) {
                    this.selectedExistingColorIds.forEach((id) => resultIds.push(id))
                }
                // include selected from all colors
                if (Array.isArray(this.selectedColorIds) && this.selectedColorIds.length) {
                    this.selectedColorIds.forEach((id) => resultIds.push(id))
                }
                // if new color provided, create it then refresh list to get id
                if (this.newColorName && this.newColorName.trim()) {
                    const payload = { colorName: this.newColorName.trim() }
                    await axios.post(`${this.$apiBaseUrl}/general/addnewcolor`, payload)
                    // refresh colors
                    const refreshed = await axios.get(`${this.$apiBaseUrl}/general/allcolors`)
                    this.colorOptions = refreshed.data
                    const found = this.colorOptions.find((c) => String(c.label) === String(this.newColorName.trim()) || String(c.label).toLowerCase() === String(this.newColorName.trim()).toLowerCase())
                    if (found) resultIds.push(found.value)
                    else {
                        ElMessage.error('创建颜色成功，但未能获取到新颜色ID，请刷新后重试')
                    }
                }

                if (resultIds.length === 0) {
                    ElMessage.info('未选择或添加任何颜色')
                    return
                }

                // emit submit with selected color ids
                this.$emit('submit', { colorIds: resultIds })
                this.$emit('update:visible', false)
                this.selectedColorIds = []
                this.newColorName = ''
            } catch (e) {
                console.error('AddColorDialog submit failed', e)
                ElMessage.error('添加颜色失败')
            }
        }
    }
}
</script>

<style scoped></style>
