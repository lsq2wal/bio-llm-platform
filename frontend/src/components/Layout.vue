<template>
  <el-container class="app-container">
    <el-header style="height: 60px;">
      <div class="header-left">
        <h2>生物数据分析平台</h2>
      </div>
      <div class="header-right">
        <el-dropdown trigger="click" @command="handleCommand">
          <span class="el-dropdown-link">
            {{ username }}<i class="el-icon-arrow-down el-icon--right"></i>
          </span>
          <el-dropdown-menu slot="dropdown">
            <el-dropdown-item command="profile">个人信息</el-dropdown-item>
            <el-dropdown-item command="logout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </el-dropdown>
      </div>
    </el-header>
    
    <el-container>
      <el-aside width="200px">
        <el-menu
          default-active="dashboard"
          class="el-menu-vertical"
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
          router
        >
          <el-menu-item index="/dashboard">
            <i class="el-icon-s-home"></i>
            <span slot="title">控制面板</span>
          </el-menu-item>
          
          <el-menu-item index="/data">
            <i class="el-icon-document"></i>
            <span slot="title">数据管理</span>
          </el-menu-item>
          
          <el-menu-item index="/analysis">
            <i class="el-icon-s-operation"></i>
            <span slot="title">分析任务</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      
      <el-main>
        <slot></slot>
      </el-main>
    </el-container>
  </el-container>
</template>

<script>
export default {
  name: 'Layout',
  computed: {
    username() {
      return (this.$store.state.user && this.$store.state.user.username) || '用户'
    }
  },
  methods: {
    handleCommand(command) {
      if (command === 'logout') {
        this.$store.dispatch('logout')
        this.$router.push('/login')
      } else if (command === 'profile') {
        // 处理个人信息
      }
    }
  }
}
</script>

<style scoped>
.app-container {
  height: 100%;
}

.el-header {
  background-color: #fff;
  color: #333;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e6e6e6;
}

.header-left h2 {
  margin: 0;
}

.el-dropdown-link {
  cursor: pointer;
  color: #409EFF;
}

.el-aside {
  background-color: #304156;
  color: #bfcbd9;
}

.el-menu {
  border-right: none;
}

.el-menu-vertical:not(.el-menu--collapse) {
  width: 200px;
  min-height: 400px;
}
</style> 