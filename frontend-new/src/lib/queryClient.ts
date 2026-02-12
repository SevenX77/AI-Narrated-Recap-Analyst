import { QueryClient } from '@tanstack/react-query'

/**
 * TanStack Query 客户端配置
 * 用于数据缓存和请求管理
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // 数据保持新鲜的时间（5分钟）
      staleTime: 5 * 60 * 1000,
      // 缓存时间（10分钟）
      gcTime: 10 * 60 * 1000,
      // 失败重试配置
      retry: 1,
      // 不在窗口聚焦时自动重新获取
      refetchOnWindowFocus: false,
    },
    mutations: {
      // 失败重试配置
      retry: 0,
    },
  },
})
