import Cookies from 'js-cookie'

/**
 * 获取认证请求头
 * @returns {Object} 包含Authorization头的对象
 */
export function getAuthHeader() {
  const token = Cookies.get('token')
  return token ? { 'Authorization': `Bearer ${token}` } : {}
}

/**
 * 保存认证令牌
 * @param {string} token - JWT令牌
 * @param {number} expires - 过期天数
 */
export function setToken(token, expires = 7) {
  return Cookies.set('token', token, { expires: expires })
}

/**
 * 获取认证令牌
 * @returns {string|null} JWT令牌
 */
export function getToken() {
  return Cookies.get('token')
}

/**
 * 移除认证令牌
 */
export function removeToken() {
  return Cookies.remove('token')
}

/**
 * 检查用户是否已认证
 * @returns {boolean} 是否已认证
 */
export function isAuthenticated() {
  return !!getToken()
} 