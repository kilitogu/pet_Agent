import request from '@/utils/request'

/** 获取首页统计数据 */
export function getDashboardStatsApi() {
  return request({
    url: '/api/dashboard/stats',
    method: 'get'
  })
}