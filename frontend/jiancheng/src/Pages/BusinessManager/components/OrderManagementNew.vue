<template>
  <div>
    <!-- Header / filters / buttons can also live in parent or be in child -->
    <BusinessOrderTable />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useOrderStore } from '@/stores/businessOrderStore'
import BusinessOrderTable from './BusinessOrderTable.vue'

const store = useOrderStore()
const userRole = ref(localStorage.getItem('role' || ''))

onMounted(async () => {
  console.log(userRole.value)
  // const response = await axios.get(`${this.$apiBaseUrl}/order/onmount`)
  // console.log(response.data)
  { currentStaffId: localStorage.getItem('staffid') }
  await store.fetchOrders()
})
</script>