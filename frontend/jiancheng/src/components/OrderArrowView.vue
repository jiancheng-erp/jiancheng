<template>
    <div class="order-lifecycle">
      <div v-for="(status, index) in orderWorkflow" :key="index" class="status-item">
        <div :class="[
          'status-circle', 
          { completed: currentStatus > index, current: currentStatus === index }
        ]"></div>
        <div :class="[
          'status-text', 
          { completed: currentStatus > index, current: currentStatus === index }
        ]">
          {{ status.stage }}<br />
        </div>
        <div v-if="index < orderWorkflow.length" :class="[
          'status-arrow', 
          { completed: currentStatus > index, current: currentStatus === index }
        ]">
          →
        </div>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    props: ['status'],
    data() {
      return {
        orderWorkflow: [
          { stage: '订单创建', department: '业务部' },
          { stage: '打样单创建', department: '业务部' },
          { stage: '打样单初步确认', department: '业务部' },
          { stage: '打样单分配', department: '开发部' },
          { stage: '打样单修改', department: '开发部' },
          { stage: '打样单最终确认', department: '业务部' },
          { stage: '生产订单创建', department: '业务部' },
          { stage: '生产订单总经理确认', department: '总经理' },
          { stage: '生产副总确认', department: '生产部' },
          { stage: '生产流程', department: '生产部' },
          { stage: '生产结束确认', department: '生产部' },
          { stage: '业务部确认', department: '业务部' },
          { stage: '业务部创建发货通知', department: '业务部' },
          { stage: '发货通知下发', department: '业务部' },
          { stage: '总经理确认', department: '总经理' },
          { stage: '成品仓发货', department: '总仓' },
          { stage: '发货量上传', department: '总仓' },
          { stage: '全部发货确认', department: '总仓' },
          { stage: '订单完成', department: '业务部' }
        ],
        currentStatus: this.status // Example: the current status index
      };
    }
  };
  </script>
  
  <style scoped>
  .order-lifecycle {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    overflow-x: auto;
    background-color: var(--el-color-white);
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
  
  .status-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    margin: 0 10px;
  }
  
  .status-circle {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background-color: #ccc;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 5px;
    transition: background-color 0.3s;
  }
  
  .status-circle.completed {
    background-color: #28a745; /* Green for completed steps */
  }
  
  .status-circle.current {
    background-color: #ff9800; /* Orange for current step */
  }
  
  .status-text {
    font-size: 10px;
    color: #999;
    transition: color 0.3s;
  }
  
  .status-text.completed {
    color: #28a745; /* Green for completed steps */
    font-weight: bold;
  }
  
  .status-text.current {
    color: #ff9800; /* Orange for current step */
    font-weight: bold;
  }
  
  .status-arrow {
    margin: 0 5px;
    color: #ccc;
    font-size: 16px;
    transition: color 0.3s;
  }
  
  .status-arrow.completed {
    color: #28a745; /* Green for completed steps */
  }
  
  .status-arrow.current {
    color: #ff9800; /* Orange for current step */
  }
  </style>
  