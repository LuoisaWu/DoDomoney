import axios from 'axios'

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

function requestError(error, action) {
  const detail = error.response?.data?.detail
  const message = typeof detail === 'string' ? detail : error.message
  throw new Error(`${action}失败：${message || '无法连接数据服务'}`)
}

export async function getGames() {
  try {
    const { data } = await api.get('/api/games')
    return data
  } catch (error) {
    requestError(error, '获取游戏数据')
  }
}

export async function chatAnalysis(query) {
  try {
    const { data } = await api.post('/api/chat', { query })
    return data
  } catch (error) {
    requestError(error, '智能分析')
  }
}
