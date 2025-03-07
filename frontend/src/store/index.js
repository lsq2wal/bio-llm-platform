import Vue from 'vue'
import Vuex from 'vuex'
import axios from 'axios'
import { setToken, removeToken, getToken, isAuthenticated } from '@/utils/auth'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    user: null,
    isAuthenticated: isAuthenticated()
  },
  mutations: {
    setUser(state, user) {
      state.user = user
      state.isAuthenticated = true
    },
    clearUser(state) {
      state.user = null
      state.isAuthenticated = false
    }
  },
  actions: {
    async login({ commit }, credentials) {
      try {
        const formData = new FormData()
        formData.append('username', credentials.username)
        formData.append('password', credentials.password)
        
        const response = await axios.post('/api/v1/login/access-token', formData)
        const token = response.data.access_token
        
        setToken(token)
        
        // 获取用户信息
        const userResponse = await axios.get('/api/v1/users/me', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        
        commit('setUser', userResponse.data)
        return true
      } catch (error) {
        console.error('登录失败:', error)
        return false
      }
    },
    
    logout({ commit }) {
      removeToken()
      commit('clearUser')
    }
  }
}) 