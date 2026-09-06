<template>
  <div>
    <MermaidChart :chartDefinition="chartDefinition" />
    <div v-if="nodeData" :style="tooltipStyle" class="tooltip">
      处理中订单数： {{ 4 }}
      <el-table class="smalltable" :data="nodeData" border>
        <el-table-column prop="orderId" label="订单编号"></el-table-column>  
      </el-table>
      
    </div>
  </div>
</template>

<script>
import MermaidChart from './MermaidChart.vue';

export default {
  components: {
    MermaidChart,
  },
  data() {
    return {
      chartDefinition: `
      %%{init: {'theme': 'forest', 'themeVariables': { 'fontSize': '20px'}, 'flowchart':{'nodeSpacing':300, 'rankSpacing':30}, 'securityLevel':'loose'}}%%
      graph LR
        0[投产指令单创建]:::nodeStyle --> 1[投产指令单下发]:::nodeStyle
        1 --> 2[面料单位用量计算]:::nodeStyle
        2 --> 3[面料单位用量下发]:::nodeStyle
        3 --> 4[一次BOM填写]:::nodeStyle
        4 --> 5[一次BOM下发]:::nodeStyle
        5 --> 6[一次采购订单创建]:::nodeStyle
        6 --> 7[一次采购订单下发]:::nodeStyle
        7 --> 8[一次采购入库]:::nodeStyle
        3 --> 9[技术部调版分配]:::nodeStyle --> 10[技术部调版下发]:::nodeStyle
        10 --> 11[二次BOM填写]:::nodeStyle
        11 --> 12[二次BOM下发]:::nodeStyle
        12 --> 13[二次采购订单创建]:::nodeStyle
        13 --> 14[二次采购订单下发]:::nodeStyle
        14 --> 15[二次采购入库]:::nodeStyle
        16[材料到齐通知]:::nodeStyle
        10 --> 18:::nodeStyle
        1 --> 17[生产排期，分配]:::nodeStyle
        8 --> 16:::nodeStyle
        15 --> 16:::nodeStyle
        18 --> 20:::nodeStyle
        17 --> 18[生产开始]:::nodeStyle
        18 --> 23[裁断开始]:::nodeStyle
        19[裁断材料出库]:::nodeStyle --> 23
        20[裁断，批皮工价填报]:::nodeStyle --> 21[财务部审核]:::nodeStyle
        21 --> 22[生产副总审核]:::nodeStyle
        22 --> 23:::nodeStyle
        23 --> 24[裁断结束]:::nodeStyle
        24 --> 25[批皮开始]:::nodeStyle
        25 --> 26[批皮结束]:::nodeStyle
        26 --> 28:::nodeStyle
        26 --> 31[针车预备开始]:::nodeStyle
        27[针车材料出库]:::nodeStyle --> 31
        28[针车及预备工序填报]:::nodeStyle --> 29[财务部审核]:::nodeStyle
        29 --> 30[生产副总审核]:::nodeStyle
        30 --> 31:::nodeStyle
        31 --> 32[针车预备结束]:::nodeStyle
        32 --> 33[针车开始]:::nodeStyle
        33 --> 34[针车结束]:::nodeStyle
        34 --> 39[成型开始]:::nodeStyle
        35[成型材料出库]:::nodeStyle --> 39
        34 --> 36:::nodeStyle
        36[成型工价填报]:::nodeStyle --> 37[财务部审核]:::nodeStyle
        37 --> 38[生产副总审核]:::nodeStyle
        38 --> 39:::nodeStyle
        39 --> 40[成型结束]:::nodeStyle
        40 --> 41[生产结束]:::nodeStyle

      classDef nodeStyle fill:#f9f,stroke:#333,stroke-width:2px;
      linkStyle default interpolate basis;

      %% Add click events for tooltips
      click 0 call showTooltip('0')
      click 1 call showTooltip('1')
      click 2 call showTooltip('2')
      click 3 call showTooltip('3')
      click 4 call showTooltip('4')
      click 5 call showTooltip('5')
      click 6 call showTooltip('6')
      click 7 call showTooltip('7')
      click 8 call showTooltip('8')
      click 9 call showTooltip('9')
      click 10 call showTooltip('10')
      click 11 call showTooltip('11')
      click 12 call showTooltip('12')
      click 13 call showTooltip('13')
      click 14 call showTooltip('14')
      click 15 call showTooltip('15')
      click 16 call showTooltip('16')
      click 17 call showTooltip('17')
      click 18 call showTooltip('18')
      click 19 call showTooltip('19')
      click 20 call showTooltip('20')
      click 21 call showTooltip('21')
      click 22 call showTooltip('22')
      click 23 call showTooltip('23')
      click 24 call showTooltip('24')
      click 25 call showTooltip('25')
      click 26 call showTooltip('26')
      click 27 call showTooltip('27')
      click 28 call showTooltip('28')
      click 29 call showTooltip('29')
      click 30 call showTooltip('30')
      click 31 call showTooltip('31')
      click 32 call showTooltip('32')
      click 33 call showTooltip('33')
      click 34 call showTooltip('34')
      click 35 call showTooltip('35')
      click 36 call showTooltip('36')
      click 37 call showTooltip('37')
      click 38 call showTooltip('38')
      click 39 call showTooltip('39')
      click 40 call showTooltip('40')
      click 41 call showTooltip('41')
      `,
      tooltipContent: null,
      testData:[[{"orderId":"K24-02-211620"},{"orderId":"K24-02-211620"},{"orderId":"K24-02-211620"}],[{"orderId":"K24-02-211620"},{"orderId":"K24-02-211620"},{"orderId":"K24-02-211620"}]],
      nodeData:[],
      tooltipStyle: {
        position: 'absolute',
        display: 'none',
        background: '#fff',
        padding: '10px',
        zIndex: 1000,
      },
    };
  },
  methods: {
    showTooltip(nodeId, event) {
      console.log(nodeId);
      this.nodeData = this.getTooltipData(nodeId);
      this.tooltipStyle.display = 'block';
      this.tooltipStyle.fontSize = '12px'
      this.tooltipStyle.left = `${event.pageX + 10}px`;
      this.tooltipStyle.top = `${event.pageY + 10}px`;
    },
    hideTooltip() {
      this.tooltipContent = null;
      this.tooltipStyle.display = 'none';
    },
    getTooltipData(nodeId) {
        // Add similar entries for other nodes
      return this.testData[nodeId];
    },
    setupEventListeners() {
      const nodes = document.querySelectorAll('.node');
      nodes.forEach((node) => {
        const nodeId = node.getAttribute('data-id');
        node.addEventListener('click', (event) => {
          this.showTooltip(nodeId, event);
        });
        node.addEventListener('mouseover', (e) => {
          node.style.fill = '#f00'; // Change fill color on hover
        });
        node.addEventListener('mouseout', (e) => {
          node.style.fill = ''; // Reset fill color on mouse out
        });
      });
    },
  },
  mounted() {
    // Ensure global functions are available for Mermaid
    window.showTooltip = (nodeId) => {
      this.showTooltip(nodeId, window.event);
    };
    this.$nextTick(() => {
      this.setupEventListeners();
    });
  },
  beforeUnmount() {
    // Clean up global functions when component is destroyed
    delete window.showTooltip;
  },
  updated() {
    this.setupEventListeners();
  },
};
</script>

<style scoped>
.smalltable {
  font-size: 12px;
}
</style>
