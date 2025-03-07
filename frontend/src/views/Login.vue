<template>
  <div class="login-container">
    <el-card class="login-card">
      <div class="logo">
        <h1>生物数据分析平台</h1>
      </div>
      
      <el-form :model="loginForm" :rules="loginRules" ref="loginForm">
        <el-form-item prop="username">
          <el-input 
            v-model="loginForm.username" 
            prefix-icon="el-icon-user" 
            placeholder="用户名"
          ></el-input>
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input 
            v-model="loginForm.password" 
            prefix-icon="el-icon-lock" 
            placeholder="密码"
            type="password"
            @keyup.enter.native="handleLogin"
          ></el-input>
        </el-form-item>
        
        <el-form-item>
          <el-button 
            type="primary" 
            :loading="loading" 
            @click="handleLogin" 
            style="width: 100%"
          >登录</el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-info">
        <p>测试账号: testuser</p>
        <p>测试密码: password</p>
      </div>
    </el-card>
  </div>
</template>

<script>
export default {
  name: 'Login',
  data() {
    return {
      loginForm: {
        username: '',
        password: ''
      },
      loginRules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' }
        ]
      },
      loading: false
    }
  },
  methods: {
    async handleLogin() {
      this.$refs.loginForm.validate(async valid => {
        if (valid) {
          this.loading = true
          
          try {
            const result = await this.$store.dispatch('login', {
              username: this.loginForm.username,
              password: this.loginForm.password
            })
            
            if (result) {
              const redirectPath = this.$route.query.redirect || '/dashboard'
              this.$router.push(redirectPath)
              this.$message.success('登录成功')
            } else {
              this.$message.error('登录失败，请检查用户名和密码')
            }
          } catch (error) {
            this.$message.error('登录时发生错误')
            console.error(error)
          } finally {
            this.loading = false
          }
        }
      })
    }
  }
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f7fa;
}

.login-card {
  width: 400px;
  padding: 20px;
}

.logo {
  text-align: center;
  margin-bottom: 30px;
}

.login-info {
  margin-top: 20px;
  color: #909399;
  font-size: 14px;
  text-align: center;
}
</style> 