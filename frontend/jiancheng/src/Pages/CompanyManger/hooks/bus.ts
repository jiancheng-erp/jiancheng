import mitt from 'mitt'

// 统一“导航”事件的载荷类型
type NavPayload = {
  to: 'CustomerAnalysis' | 'BusinessAnalysis' | 'MainBoardPage' | string
  props?: Record<string, any>
}

export const bus = mitt<{
  'nav:goto': NavPayload
}>()
