<template>
  <Layout>
    <div class="dashboard">
      <el-row :gutter="20">
        <!-- 数据统计卡片 -->
        <el-col :span="6">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-icon">
                <i class="el-icon-document"></i>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.dataCount }}</div>
                <div class="stat-label">数据集</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-icon">
                <i class="el-icon-s-operation"></i>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.analysisCount }}</div>
                <div class="stat-label">分析任务</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-icon">
                <i class="el-icon-cpu"></i>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.gpuUsage }}%</div>
                <div class="stat-label">GPU利用率</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-icon">
                <i class="el-icon-data-line"></i>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ formatDiskUsage(stats.storageUsage) }}</div>
                <div class="stat-label">存储使用</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <!-- 最近任务和快速启动 -->
      <el-row :gutter="20" class="dashboard-row">
        <el-col :span="16">
          <el-card class="recent-tasks">
            <div slot="header">
              <span>最近分析任务</span>
              <el-button style="float: right; padding: 3px 0" type="text" @click="viewAllTasks">
                查看全部
              </el-button>
            </div>
            
            <el-table :data="recentTasks" stripe style="width: 100%">
              <el-table-column prop="taskName" label="任务名称" width="240">
                <template slot-scope="scope">
                  <el-link type="primary" @click="viewTaskDetail(scope.row)">
                    {{ scope.row.taskName }}
                  </el-link>
                </template>
              </el-table-column>
              <el-table-column prop="taskType" label="类型" width="120">
                <template slot-scope="scope">
                  <el-tag :type="getTaskTypeTag(scope.row.taskType)">
                    {{ formatTaskType(scope.row.taskType) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="submitTime" label="提交时间" width="180"></el-table-column>
              <el-table-column prop="status" label="状态" width="100">
                <template slot-scope="scope">
                  <el-tag :type="getStatusTag(scope.row.status)">
                    {{ formatStatus(scope.row.status) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="progress" label="进度" width="180">
                <template slot-scope="scope">
                  <el-progress 
                    :percentage="Math.round(scope.row.progress * 100)" 
                    :status="getProgressStatus(scope.row.status)"
                  ></el-progress>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>
        
        <el-col :span="8">
          <el-card class="quick-start">
            <div slot="header">
              <span>快速操作</span>
            </div>
            
            <el-button type="primary" icon="el-icon-upload" @click="goToUploadData" class="quick-button">
              上传数据
            </el-button>
            
            <el-button type="success" icon="el-icon-s-promotion" @click="goToNewAnalysis" class="quick-button">
              新建分析
            </el-button>
            
            <div class="quick-ask">
              <h4>生物学问答</h4>
              <el-input
                type="textarea"
                v-model="quickQuestion"
                placeholder="输入生物学问题，如'T细胞亚群的主要marker基因有哪些？'"
                :rows="3"
              ></el-input>
              <div class="ask-actions">
                <el-button type="primary" size="small" @click="askBioQuestion" :loading="loading">提问</el-button>
              </div>
              
              <div v-if="quickAnswer" class="answer-box">
                <h4>回答:</h4>
                <div class="answer-content">{{ quickAnswer }}</div>
                <div class="answer-sources" v-if="quickSources && quickSources.length">
                  <h5>参考来源:</h5>
                  <ul>
                    <li v-for="(source, index) in quickSources" :key="index">
                      {{ source }}
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <!-- 系统状态 -->
      <el-row :gutter="20" class="dashboard-row">
        <el-col :span="24">
          <el-card class="system-status">
            <div slot="header">
              <span>系统状态</span>
              <el-tag :type="getSystemStatusType(systemStatus.status)" class="status-tag">
                {{ formatSystemStatus(systemStatus.status) }}
              </el-tag>
            </div>
            
            <el-row :gutter="20" class="status-row">
              <el-col :span="8">
                <el-card shadow="never" class="status-item">
                  <div slot="header">计算资源</div>
                  <div class="resource-meters">
                    <div class="meter">
                      <span>CPU使用率:</span>
                      <el-progress :percentage="systemStatus.cpuUsage" :color="getResourceColor(systemStatus.cpuUsage)"></el-progress>
                    </div>
                    <div class="meter">
                      <span>内存使用率:</span>
                      <el-progress :percentage="systemStatus.memoryUsage" :color="getResourceColor(systemStatus.memoryUsage)"></el-progress>
                    </div>
                    <div class="meter">
                      <span>GPU使用率:</span>
                      <el-progress :percentage="systemStatus.gpuUsage" :color="getResourceColor(systemStatus.gpuUsage)"></el-progress>
                    </div>
                  </div>
                </el-card>
              </el-col>
              
              <el-col :span="8">
                <el-card shadow="never" class="status-item">
                  <div slot="header">队列状态</div>
                  <div class="queue-status">
                    <div class="queue-item">
                      <span>排队作业数:</span>
                      <span class="queue-value">{{ systemStatus.queuedJobs }}</span>
                    </div>
                    <div class="queue-item">
                      <span>运行作业数:</span>
                      <span class="queue-value">{{ systemStatus.runningJobs }}</span>
                    </div>
                    <div class="queue-item">
                      <span>平均等待时间:</span>
                      <span class="queue-value">{{ systemStatus.avgWaitTime }}</span>
                    </div>
                  </div>
                </el-card>
              </el-col>
              
              <el-col :span="8">
                <el-card shadow="never" class="status-item">
                  <div slot="header">服务状态</div>
                  <div class="services-status">
                    <div v-for="(service, index) in systemStatus.services" :key="index" class="service-item">
                      <span>{{ service.name }}:</span>
                      <el-tag :type="getServiceStatusType(service.status)" size="small">
                        {{ formatServiceStatus(service.status) }}
                      </el-tag>
                    </div>
                  </div>
                </el-card>
              </el-col>
            </el-row>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </Layout>
</template>

<script>
import axios from 'axios';
import { getAuthHeader } from '@/utils/auth';
import Layout from '@/components/Layout.vue'

export default {
  name: 'Dashboard',
  components: {
    Layout
  },
  data() {
    return {
      loading: false,
      stats: {
        dataCount: 0,
        analysisCount: 0,
        gpuUsage: 0,
        storageUsage: 0
      },
      recentTasks: [],
      systemStatus: {
        status: 'normal',
        cpuUsage: 0,
        memoryUsage: 0,
        gpuUsage: 0,
        queuedJobs: 0,
        runningJobs: 0,
        avgWaitTime: '0分钟',
        services: [
          { name: 'FastAPI', status: 'running' },
          { name: 'ChromaDB', status: 'running' },
          { name: '多瑙调度器', status: 'running' },
          { name: 'LLM服务', status: 'running' }
        ]
      },
      quickQuestion: '',
      quickAnswer: null,
      quickSources: []
    };
  },
  mounted() {
    this.fetchDashboardData();
  },
  methods: {
    fetchDashboardData() {
      this.loading = true;
      
      // 获取统计数据
      axios.get(`${process.env.VUE_APP_API_URL}/api/v1/dashboard/stats`, {
        headers: getAuthHeader()
      })
      .then(response => {
        this.stats = response.data;
      })
      .catch(error => {
        console.error('获取统计数据失败:', error);
        this.$message.error('获取统计数据失败');
      });
      
      // 获取最近任务
      axios.get(`${process.env.VUE_APP_API_URL}/api/v1/analysis/recent`, {
        headers: getAuthHeader()
      })
      .then(response => {
        this.recentTasks = response.data;
      })
      .catch(error => {
        console.error('获取最近任务失败:', error);
        this.$message.error('获取最近任务失败');
      });
      
      // 获取系统状态
      axios.get(`${process.env.VUE_APP_API_URL}/api/v1/dashboard/system-status`, {
        headers: getAuthHeader()
      })
      .then(response => {
        this.systemStatus = response.data;
      })
      .catch(error => {
        console.error('获取系统状态失败:', error);
        this.$message.error('获取系统状态失败');
      })
      .finally(() => {
        this.loading = false;
      });
    },
    
    formatDiskUsage(bytes) {
      const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
      if (bytes === 0) return '0 B';
      const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)), 10);
      if (i === 0) return `${bytes} ${sizes[i]}`;
      return `${(bytes / (1024 ** i)).toFixed(1)} ${sizes[i]}`;
    },
    
    getTaskTypeTag(type) {
      const types = {
        'cell_annotation': 'success',
        'gene_perturbation': 'warning',
        'pathway_analysis': 'primary',
        'batch_correction': 'info',
        'differential_expression': 'danger'
      };
      return types[type] || 'info';
    },
    
    formatTaskType(type) {
      const types = {
        'cell_annotation': '细胞注释',
        'gene_perturbation': '基因扰动',
        'pathway_analysis': '通路分析',
        'batch_correction': '批次校正',
        'differential_expression': '差异表达'
      };
      return types[type] || type;
    },
    
    getStatusTag(status) {
      const statuses = {
        'pending': 'info',
        'running': 'primary',
        'completed': 'success',
        'failed': 'danger',
        'stopped': 'warning'
      };
      return statuses[status] || 'info';
    },
    
    formatStatus(status) {
      const statuses = {
        'pending': '等待中',
        'running': '运行中',
        'completed': '已完成',
        'failed': '失败',
        'stopped': '已停止'
      };
      return statuses[status] || status;
    },
    
    getProgressStatus(status) {
      if (status === 'completed') return 'success';
      if (status === 'failed') return 'exception';
      return '';
    },
    
    getSystemStatusType(status) {
      const types = {
        'normal': 'success',
        'warning': 'warning',
        'critical': 'danger',
        'maintenance': 'info'
      };
      return types[status] || 'info';
    },
    
    formatSystemStatus(status) {
      const statuses = {
        'normal': '正常',
        'warning': '警告',
        'critical': '严重',
        'maintenance': '维护中'
      };
      return statuses[status] || status;
    },
    
    getResourceColor(percentage) {
      if (percentage < 70) return '#67c23a';
      if (percentage < 90) return '#e6a23c';
      return '#f56c6c';
    },
    
    getServiceStatusType(status) {
      const types = {
        'running': 'success',
        'warning': 'warning',
        'error': 'danger',
        'stopped': 'info'
      };
      return types[status] || 'info';
    },
    
    formatServiceStatus(status) {
      const statuses = {
        'running': '运行中',
        'warning': '警告',
        'error': '错误',
        'stopped': '已停止'
      };
      return statuses[status] || status;
    },
    
    viewAllTasks() {
      this.$router.push('/tasks');
    },
    
    viewTaskDetail(task) {
      this.$router.push(`/tasks/${task.id}`);
    },
    
    goToUploadData() {
      this.$router.push('/data');
    },
    
    goToNewAnalysis() {
      this.$router.push('/analysis/new');
    },
    
    askBioQuestion() {
      if (!this.quickQuestion) {
        this.$message.warning('请输入问题');
        return;
      }
      
      this.loading = true;
      this.quickAnswer = null;
      this.quickSources = [];
      
      axios.post(`${process.env.VUE_APP_API_URL}/api/v1/rag/query`, {
        query: this.quickQuestion
      }, {
        headers: getAuthHeader()
      })
      .then(response => {
        this.quickAnswer = response.data.response;
        this.quickSources = response.data.sources || [];
      })
      .catch(error => {
        console.error('生物问答请求失败:', error);
        this.$message.error('生物问答请求失败');
      })
      .finally(() => {
        this.loading = false;
      });
    }
  }
};
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.dashboard-row {
  margin-top: 20px;
}

.stat-card {
  height: 120px;
}

.stat-content {
  display: flex;
  align-items: center;
}

.stat-icon {
  font-size: 48px;
  color: #409EFF;
  margin-right: 20px;
}

.stat-info {
  flex-grow: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.recent-tasks, .quick-start, .system-status {
  width: 100%;
  margin-bottom: 20px;
}

.quick-button {
  display: block;
  width: 100%;
  margin-bottom: 10px;
}

.quick-ask {
  margin-top: 20px;
}

.ask-actions {
  margin-top: 10px;
  text-align: right;
}

.answer-box {
  margin-top: 15px;
  padding: 15px;
  border-radius: 4px;
  background-color: #f5f7fa;
}

.answer-content {
  line-height: 1.6;
  margin-bottom: 10px;
}

.answer-sources {
  font-size: 12px;
  color: #606266;
}

.status-tag {
  float: right;
  margin-top: 3px;
}

.status-row {
  margin-top: 10px;
}

.status-item {
  height: 100%;
}

.resource-meters, .queue-status, .services-status {
  padding: 10px;
}

.meter, .queue-item, .service-item {
  margin-bottom: 15px;
}

.queue-value {
  font-weight: bold;
  margin-left: 10px;
}
</style> 