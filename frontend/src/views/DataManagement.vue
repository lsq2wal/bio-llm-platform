<template>
  <div class="data-management">
    <h1>数据管理</h1>
    
    <!-- 上传数据表单 -->
    <el-card class="upload-card">
      <div slot="header">
        <span>上传数据</span>
      </div>
      <el-upload
        class="upload-demo"
        drag
        :action="uploadUrl"
        :headers="headers"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :before-upload="beforeUpload"
      >
        <i class="el-icon-upload"></i>
        <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
        <div class="el-upload__tip" slot="tip">
          支持 .h5ad、.mtx、.csv 等格式的生物数据文件
        </div>
      </el-upload>
      
      <el-form :model="uploadForm" label-width="120px" class="upload-form">
        <el-form-item label="数据类型">
          <el-select v-model="uploadForm.dataType" placeholder="选择数据类型">
            <el-option label="单细胞RNA测序" value="sc_rnaseq"></el-option>
            <el-option label="批量RNA测序" value="bulk_rnaseq"></el-option>
            <el-option label="ATAC测序" value="atac_seq"></el-option>
            <el-option label="空间转录组" value="spatial"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            type="textarea"
            v-model="uploadForm.description"
            placeholder="请简要描述数据来源、实验条件等"
          ></el-input>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 数据列表 -->
    <el-card class="data-list-card">
      <div slot="header">
        <span>我的数据</span>
        <el-input
          placeholder="搜索文件名"
          v-model="searchQuery"
          class="search-input"
          prefix-icon="el-icon-search"
          clearable
        ></el-input>
        <el-select v-model="dataTypeFilter" placeholder="数据类型" clearable class="type-filter">
          <el-option label="全部类型" value=""></el-option>
          <el-option label="单细胞RNA测序" value="sc_rnaseq"></el-option>
          <el-option label="批量RNA测序" value="bulk_rnaseq"></el-option>
          <el-option label="ATAC测序" value="atac_seq"></el-option>
          <el-option label="空间转录组" value="spatial"></el-option>
        </el-select>
      </div>
      
      <el-table
        :data="filteredDataList"
        stripe
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column prop="filename" label="文件名"></el-table-column>
        <el-table-column prop="data_type" label="数据类型">
          <template slot-scope="scope">
            <el-tag :type="getDataTypeTag(scope.row.data_type)">
              {{ formatDataType(scope.row.data_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="upload_time" label="上传时间"></el-table-column>
        <el-table-column prop="size" label="大小">
          <template slot-scope="scope">
            {{ formatFileSize(scope.row.size) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template slot-scope="scope">
            <el-button size="mini" type="primary" @click="viewData(scope.row)">查看</el-button>
            <el-button size="mini" type="success" @click="analyzeData(scope.row)">分析</el-button>
            <el-button size="mini" type="danger" @click="deleteData(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          :current-page="currentPage"
          :page-sizes="[10, 20, 50, 100]"
          :page-size="pageSize"
          layout="total, sizes, prev, pager, next, jumper"
          :total="totalItems"
        ></el-pagination>
      </div>
    </el-card>
    
    <!-- 数据详情对话框 -->
    <el-dialog title="数据详情" :visible.sync="dataDetailVisible" width="70%">
      <div v-if="selectedData" class="data-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="ID">{{ selectedData.id }}</el-descriptions-item>
          <el-descriptions-item label="文件名">{{ selectedData.filename }}</el-descriptions-item>
          <el-descriptions-item label="数据类型">{{ formatDataType(selectedData.data_type) }}</el-descriptions-item>
          <el-descriptions-item label="大小">{{ formatFileSize(selectedData.size) }}</el-descriptions-item>
          <el-descriptions-item label="上传时间">{{ selectedData.upload_time }}</el-descriptions-item>
          <el-descriptions-item label="用户">{{ selectedData.user }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ selectedData.description }}</el-descriptions-item>
        </el-descriptions>
        
        <div class="data-preview">
          <h3>数据预览</h3>
          <!-- 这里可以放数据预览的图表或表格 -->
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import axios from 'axios';
import { getAuthHeader } from '@/utils/auth';

export default {
  name: 'DataManagement',
  data() {
    return {
      uploadUrl: `${process.env.VUE_APP_API_URL}/api/v1/analysis/upload_data`,
      headers: getAuthHeader(),
      uploadForm: {
        dataType: '',
        description: ''
      },
      searchQuery: '',
      dataTypeFilter: '',
      dataList: [],
      loading: false,
      currentPage: 1,
      pageSize: 10,
      totalItems: 0,
      dataDetailVisible: false,
      selectedData: null
    };
  },
  computed: {
    filteredDataList() {
      let result = this.dataList;
      
      // 搜索过滤
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase();
        result = result.filter(item => 
          item.filename.toLowerCase().includes(query) ||
          (item.description && item.description.toLowerCase().includes(query))
        );
      }
      
      // 数据类型过滤
      if (this.dataTypeFilter) {
        result = result.filter(item => item.data_type === this.dataTypeFilter);
      }
      
      return result;
    }
  },
  mounted() {
    this.fetchDataList();
  },
  methods: {
    async fetchDataList() {
      this.loading = true;
      try {
        const response = await axios.get(
          `${process.env.VUE_APP_API_URL}/api/v1/data`,
          { 
            headers: getAuthHeader(),
            params: {
              skip: (this.currentPage - 1) * this.pageSize,
              limit: this.pageSize,
              data_type: this.dataTypeFilter || undefined
            }
          }
        );
        this.dataList = response.data;
        this.totalItems = response.headers['x-total-count'] || this.dataList.length;
      } catch (error) {
        console.error('获取数据列表失败:', error);
        this.$message.error('获取数据列表失败');
      } finally {
        this.loading = false;
      }
    },
    
    formatDataType(type) {
      const typeMap = {
        'sc_rnaseq': '单细胞RNA测序',
        'bulk_rnaseq': '批量RNA测序',
        'atac_seq': 'ATAC测序',
        'spatial': '空间转录组'
      };
      return typeMap[type] || type;
    },
    
    getDataTypeTag(type) {
      const tagMap = {
        'sc_rnaseq': 'success',
        'bulk_rnaseq': 'primary',
        'atac_seq': 'warning',
        'spatial': 'danger'
      };
      return tagMap[type] || '';
    },
    
    formatFileSize(bytes) {
      if (bytes === 0) return '0 B';
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    handleSizeChange(size) {
      this.pageSize = size;
      this.fetchDataList();
    },
    
    handleCurrentChange(page) {
      this.currentPage = page;
      this.fetchDataList();
    },
    
    viewData(data) {
      this.selectedData = data;
      this.dataDetailVisible = true;
    },
    
    analyzeData(data) {
      // 导航到分析页面，并传递数据ID
      this.$router.push({
        name: 'analysis',
        params: { dataId: data.id }
      });
    },
    
    async deleteData(data) {
      try {
        await this.$confirm(`确定要删除数据 "${data.filename}" 吗？`, '警告', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        });
        
        await axios.delete(
          `${process.env.VUE_APP_API_URL}/api/v1/data/${data.id}`,
          { headers: getAuthHeader() }
        );
        
        this.$message.success('数据删除成功');
        this.fetchDataList();
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除数据失败:', error);
          this.$message.error('删除数据失败');
        }
      }
    },
    
    handleUploadSuccess(response, file, fileList) {
      this.$message.success(`文件 ${file.name} 上传成功`);
      this.fetchDataList();
    },
    
    handleUploadError(err, file, fileList) {
      this.$message.error(`文件 ${file.name} 上传失败`);
    },
    
    beforeUpload(file) {
      // 文件类型和大小检查
      const validTypes = ['.h5ad', '.mtx', '.csv', '.tsv', '.txt', '.rds'];
      const isValidType = validTypes.some(type => file.name.endsWith(type));
      const isLessThan2G = file.size / 1024 / 1024 / 1024 < 2;
      
      if (!isValidType) {
        this.$message.error('只能上传生物数据文件!');
        return false;
      }
      
      if (!isLessThan2G) {
        this.$message.error('文件大小不能超过2GB!');
        return false;
      }
      
      return true;
    }
  }
};
</script>

<style scoped>
.data-management {
  padding: 20px;
}

.upload-card {
  margin-bottom: 20px;
}

.upload-form {
  margin-top: 20px;
}

.data-list-card {
  margin-bottom: 20px;
}

.search-input {
  float: right;
  width: 200px;
  margin-left: 10px;
}

.type-filter {
  float: right;
  width: 140px;
}

.pagination-container {
  margin-top: 20px;
  text-align: right;
}

.data-detail {
  padding: 10px;
}

.data-preview {
  margin-top: 20px;
  border-top: 1px solid #EBEEF5;
  padding-top: 20px;
}
</style> 