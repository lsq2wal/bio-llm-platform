<template>
  <div class="analysis-panel">
    <h2>生物数据分析</h2>
    
    <el-steps :active="currentStep" finish-status="success" align-center class="analysis-steps">
      <el-step title="选择数据" icon="el-icon-folder"></el-step>
      <el-step title="配置分析" icon="el-icon-setting"></el-step>
      <el-step title="任务状态" icon="el-icon-loading"></el-step>
      <el-step title="查看结果" icon="el-icon-data-analysis"></el-step>
    </el-steps>
    
    <!-- 步骤1: 选择数据 -->
    <div v-if="currentStep === 0" class="step-content">
      <h3>选择分析数据</h3>
      
      <el-table
        :data="dataList"
        style="width: 100%"
        @selection-change="handleDataSelectionChange"
        v-loading="loading"
      >
        <el-table-column type="selection" width="55"></el-table-column>
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
      </el-table>
      
      <div class="step-actions">
        <el-button type="primary" @click="nextStep" :disabled="!selectedData">下一步</el-button>
      </div>
    </div>
    
    <!-- 步骤2: 配置分析 -->
    <div v-if="currentStep === 1" class="step-content">
      <h3>配置分析参数</h3>
      
      <el-form :model="analysisForm" label-width="120px" size="small">
        <el-form-item label="分析类型">
          <el-select v-model="analysisForm.taskType" placeholder="选择分析类型">
            <el-option label="细胞注释" value="cell_annotation"></el-option>
            <el-option label="基因扰动分析" value="gene_perturbation"></el-option>
            <el-option label="通路富集分析" value="pathway_analysis"></el-option>
            <el-option label="批次效应校正" value="batch_correction"></el-option>
            <el-option label="差异表达分析" value="differential_expression"></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="分析描述">
          <el-input
            type="textarea"
            v-model="analysisForm.description"
            placeholder="请描述您的分析需求，如'鉴定样本中的T细胞亚群并注释'"
          ></el-input>
        </el-form-item>
        
        <!-- 动态参数表单 -->
        <div class="parameters" v-if="analysisForm.taskType">
          <h4>分析参数</h4>
          
          <!-- 批次效应校正参数 -->
          <div v-if="analysisForm.taskType === 'batch_correction'">
            <el-form-item label="校正方法">
              <el-select v-model="analysisForm.parameters.method">
                <el-option label="Harmony" value="harmony"></el-option>
                <el-option label="BBKNN" value="bbknn"></el-option>
                <el-option label="Scanorama" value="scanorama"></el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="批次列名">
              <el-input v-model="analysisForm.parameters.batch_key"></el-input>
            </el-form-item>
          </div>
          
          <!-- 细胞注释参数 -->
          <div v-if="analysisForm.taskType === 'cell_annotation'">
            <el-form-item label="注释模型">
              <el-select v-model="analysisForm.parameters.model">
                <el-option label="scGPT" value="scgpt"></el-option>
                <el-option label="Geneformer" value="geneformer"></el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="置信度阈值">
              <el-slider v-model="analysisForm.parameters.confidence_threshold" :min="0" :max="1" :step="0.05"></el-slider>
            </el-form-item>
          </div>
          
          <!-- 预处理参数（通用） -->
          <div class="preprocessing-params">
            <h4>预处理参数</h4>
            <el-form-item label="最小基因数">
              <el-input-number v-model="analysisForm.parameters.min_genes" :min="10" :max="1000" :step="10"></el-input-number>
            </el-form-item>
            <el-form-item label="最小细胞数">
              <el-input-number v-model="analysisForm.parameters.min_cells" :min="1" :max="50" :step="1"></el-input-number>
            </el-form-item>
            <el-form-item label="最大线粒体比例">
              <el-input-number v-model="analysisForm.parameters.max_mt_percent" :min="1" :max="50" :step="1"></el-input-number>%
            </el-form-item>
          </div>
        </div>
        
        <div class="llm-enhanced">
          <el-checkbox v-model="useLLM">使用大模型增强分析</el-checkbox>
          <div v-if="useLLM" class="llm-options">
            <el-form-item label="模型">
              <el-select v-model="llmOptions.model">
                <el-option label="Llama 3" value="llama3"></el-option>
                <el-option label="scGPT" value="scgpt"></el-option>
                <el-option label="Geneformer" value="geneformer"></el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="知识增强">
              <el-switch v-model="llmOptions.rag_enabled"></el-switch>
            </el-form-item>
          </div>
        </div>
        
        <div class="step-actions">
          <el-button @click="prevStep">上一步</el-button>
          <el-button type="primary" @click="submitAnalysis">提交分析</el-button>
        </div>
      </el-form>
    </div>
    
    <!-- 步骤3: 任务状态 -->
    <div v-if="currentStep === 2" class="step-content">
      <h3>分析任务状态</h3>
      
      <el-card class="task-status-card" v-if="currentTask">
        <div slot="header">
          <span>任务ID: {{ currentTask.taskId }}</span>
        </div>
        
        <div class="status-info">
          <p><strong>状态:</strong> {{ getStatusLabel(currentTask.status) }}</p>
          <p><strong>任务类型:</strong> {{ formatTaskType(currentTask.taskType) }}</p>
          <p><strong>提交时间:</strong> {{ currentTask.submitTime }}</p>
          <p><strong>描述:</strong> {{ currentTask.description }}</p>
        </div>
        
        <div class="progress-wrapper">
          <el-progress 
            :percentage="currentTask.progress * 100" 
            :status="getProgressStatus(currentTask)"
          ></el-progress>
        </div>
        
        <div class="task-logs" v-if="taskLogs.length > 0">
          <h4>任务日志</h4>
          <div class="log-container">
            <p v-for="(log, index) in taskLogs" :key="index" class="log-entry">
              {{ log }}
            </p>
          </div>
        </div>
      </el-card>
      
      <div class="step-actions">
        <el-button @click="prevStep" :disabled="isTaskRunning">上一步</el-button>
        <el-button type="success" @click="nextStep" :disabled="!isTaskCompleted">查看结果</el-button>
      </div>
    </div>
    
    <!-- 步骤4: 查看结果 -->
    <div v-if="currentStep === 3" class="step-content">
      <h3>分析结果</h3>
      
      <div class="results-tabs">
        <el-tabs v-model="activeResultTab">
          <el-tab-pane label="可视化" name="visualization">
            <div class="visualization-container">
              <!-- Plotly.js 可视化组件 -->
              <div ref="plotlyContainer" class="plotly-chart">
                <!-- UMAP聚类图将在这里渲染 -->
              </div>
              
              <div class="controls">
                <el-form :inline="true" size="small">
                  <el-form-item label="颜色显示">
                    <el-select v-model="plotConfig.colorBy" @change="updatePlot">
                      <el-option label="聚类" value="cluster"></el-option>
                      <el-option label="细胞类型" value="cell_type"></el-option>
                      <el-option label="基因数" value="n_genes_by_counts"></el-option>
                      <el-option label="UMI数" value="total_counts"></el-option>
                    </el-select>
                  </el-form-item>
                  
                  <el-form-item label="基因表达" v-if="availableGenes.length > 0">
                    <el-select v-model="plotConfig.gene" @change="updatePlot" filterable>
                      <el-option 
                        v-for="gene in availableGenes" 
                        :key="gene" 
                        :label="gene" 
                        :value="gene"
                      ></el-option>
                    </el-select>
                  </el-form-item>
                </el-form>
              </div>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="分析报告" name="report">
            <div class="report-container">
              <iframe 
                v-if="reportUrl" 
                :src="reportUrl" 
                class="report-frame" 
                frameborder="0"
              ></iframe>
              <div v-else class="no-report">
                <p>分析报告不可用或正在生成中...</p>
              </div>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="大模型解释" name="llm_explanation" v-if="llmExplanationAvailable">
            <div class="llm-explanation">
              <div class="explanation-header">
                <h4>大模型数据解释</h4>
                <el-button size="mini" @click="refreshLLMExplanation">刷新解释</el-button>
              </div>
              
              <div class="explanation-content" v-html="llmExplanation"></div>
              
              <div class="explanation-feedback">
                <h4>反馈</h4>
                <div class="feedback-buttons">
                  <el-button size="mini" type="success" icon="el-icon-check" @click="sendFeedback('positive')">有帮助</el-button>
                  <el-button size="mini" type="danger" icon="el-icon-close" @click="sendFeedback('negative')">需改进</el-button>
                </div>
              </div>
              
              <div class="ask-container">
                <h4>询问大模型</h4>
                <el-input
                  type="textarea"
                  v-model="askLLMInput"
                  placeholder="输入您对分析结果的问题，如'请解释为什么T细胞亚群有如此明显的分离?'"
                  :rows="3"
                ></el-input>
                <el-button type="primary" @click="askLLM" class="ask-button" :loading="askLLMLoading">询问</el-button>
                
                <div v-if="llmAnswer" class="llm-answer">
                  <h4>回答</h4>
                  <div v-html="llmAnswer"></div>
                </div>
              </div>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="下载数据" name="download">
            <div class="download-container">
              <h4>可下载文件</h4>
              <el-table :data="downloadableFiles" style="width: 100%">
                <el-table-column prop="filename" label="文件名"></el-table-column>
                <el-table-column prop="description" label="描述"></el-table-column>
                <el-table-column prop="size" label="大小">
                  <template slot-scope="scope">
                    {{ formatFileSize(scope.row.size) }}
                  </template>
                </el-table-column>
                <el-table-column label="操作">
                  <template slot-scope="scope">
                    <el-button size="mini" type="primary" @click="downloadFile(scope.row)">下载</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
      
      <div class="step-actions">
        <el-button @click="resetAnalysis">返回首页</el-button>
      </div>
    </div>
  </div>
</template>

<script>
import Plotly from 'plotly.js-dist-min';
import axios from 'axios';
import { getAuthHeader } from '@/utils/auth';

export default {
  name: 'AnalysisTask',
  data() {
    return {
      currentStep: 0,
      loading: false,
      dataList: [],
      selectedData: null,
      
      analysisForm: {
        taskType: '',
        description: '',
        parameters: {
          min_genes: 200,
          min_cells: 3,
          max_mt_percent: 10,
          method: 'harmony',
          batch_key: 'batch',
          model: 'scgpt',
          confidence_threshold: 0.7
        }
      },
      
      useLLM: true,
      llmOptions: {
        model: 'llama3',
        rag_enabled: true
      },
      
      currentTask: null,
      taskLogs: [],
      pollingTimer: null,
      
      activeResultTab: 'visualization',
      plotConfig: {
        colorBy: 'cluster',
        gene: null
      },
      availableGenes: [],
      plotData: null,
      reportUrl: null,
      
      llmExplanationAvailable: false,
      llmExplanation: '',
      askLLMInput: '',
      askLLMLoading: false,
      llmAnswer: '',
      
      downloadableFiles: []
    };
  },
  computed: {
    isTaskRunning() {
      return this.currentTask && this.currentTask.status === 'running';
    },
    
    isTaskCompleted() {
      return this.currentTask && this.currentTask.status === 'completed';
    }
  },
  mounted() {
    this.fetchDataList();
  },
  beforeDestroy() {
    this.clearPolling();
  },
  methods: {
    async fetchDataList() {
      try {
        this.loading = true;
        const response = await axios.get('/api/v1/data', {
          headers: getAuthHeader()
        });
        this.dataList = response.data;
      } catch (error) {
        console.error('获取数据列表失败:', error);
        this.$message.error('获取数据列表失败');
      } finally {
        this.loading = false;
      }
    },
    
    handleDataSelectionChange(selection) {
      this.selectedData = selection.length > 0 ? selection[0] : null;
    },
    
    prevStep() {
      if (this.currentStep > 0) {
        this.currentStep--;
      }
    },
    
    nextStep() {
      if (this.currentStep < 3) {
        this.currentStep++;
        
        if (this.currentStep === 3 && this.isTaskCompleted) {
          this.loadResults();
        }
      }
    },
    
    async submitAnalysis() {
      try {
        this.loading = true;
        
        const payload = {
          task_type: this.analysisForm.taskType,
          description: this.analysisForm.description,
          parameters: this.analysisForm.parameters,
          data_id: this.selectedData.id,
          use_llm: this.useLLM,
          llm_options: this.llmOptions
        };
        
        const response = await axios.post('/api/v1/analysis/submit', payload, {
          headers: getAuthHeader()
        });
        
        this.currentTask = {
          taskId: response.data.task_id,
          status: response.data.status,
          taskType: this.analysisForm.taskType,
          description: this.analysisForm.description,
          submitTime: new Date().toLocaleString(),
          progress: 0
        };
        
        this.$message.success('分析任务提交成功');
        this.nextStep();
        this.startPolling(response.data.task_id);
      } catch (error) {
        console.error('提交分析任务失败:', error);
        this.$message.error('提交分析任务失败');
      } finally {
        this.loading = false;
      }
    },
    
    startPolling(taskId) {
      this.clearPolling();
      
      this.pollingTimer = setInterval(async () => {
        try {
          const response = await axios.get(`/api/v1/analysis/status/${taskId}`, {
            headers: getAuthHeader()
          });
          
          this.currentTask = {
            ...this.currentTask,
            status: response.data.status,
            progress: response.data.progress,
            result: response.data.result,
            error: response.data.error
          };
          
          // 如果任务完成或失败，停止轮询
          if (['completed', 'failed', 'cancelled'].includes(response.data.status)) {
            this.clearPolling();
            
            if (response.data.status === 'completed') {
              this.$message.success('分析任务已完成');
            } else if (response.data.status === 'failed') {
              this.$message.error(`分析任务失败: ${response.data.error || '未知错误'}`);
            }
          }
          
          // 加载任务日志
          this.fetchTaskLogs(taskId);
        } catch (error) {
          console.error('获取任务状态失败:', error);
        }
      }, 5000); // 每5秒轮询一次
    },
    
    clearPolling() {
      if (this.pollingTimer) {
        clearInterval(this.pollingTimer);
        this.pollingTimer = null;
      }
    },
    
    async fetchTaskLogs(taskId) {
      try {
        const response = await axios.get(`/api/v1/analysis/logs/${taskId}`, {
          headers: getAuthHeader()
        });
        
        this.taskLogs = response.data.logs || [];
      } catch (error) {
        console.error('获取任务日志失败:', error);
      }
    },
    
    getStatusLabel(status) {
      const statusMap = {
        'pending': '等待中',
        'running': '运行中',
        'completed': '已完成',
        'failed': '失败',
        'cancelled': '已取消'
      };
      
      return statusMap[status] || status;
    },
    
    getProgressStatus(task) {
      if (task.status === 'failed') return 'exception';
      if (task.status === 'completed') return 'success';
      return '';
    },
    
    formatTaskType(taskType) {
      const typeMap = {
        'cell_annotation': '细胞注释',
        'gene_perturbation': '基因扰动分析',
        'pathway_analysis': '通路富集分析',
        'batch_correction': '批次效应校正',
        'differential_expression': '差异表达分析'
      };
      
      return typeMap[taskType] || taskType;
    },
    
    async loadResults() {
      if (!this.currentTask || !this.currentTask.result) return;
      
      try {
        this.loading = true;
        
        // 获取可视化数据
        const visResponse = await axios.get(`/api/v1/analysis/visualization/${this.currentTask.taskId}`, {
          headers: getAuthHeader()
        });
        
        this.plotData = visResponse.data;
        this.availableGenes = visResponse.data.genes || [];
        
        // 渲染Plotly图表
        this.renderPlot();
        
        // 获取报告URL
        this.reportUrl = `/api/v1/analysis/report/${this.currentTask.taskId}`;
        
        // 检查是否有LLM解释
        this.checkLLMExplanation();
        
        // 获取可下载文件列表
        const filesResponse = await axios.get(`/api/v1/analysis/files/${this.currentTask.taskId}`, {
          headers: getAuthHeader()
        });
        
        this.downloadableFiles = filesResponse.data;
      } catch (error) {
        console.error('加载结果失败:', error);
        this.$message.error('加载结果失败');
      } finally {
        this.loading = false;
      }
    },
    
    renderPlot() {
      if (!this.plotData) return;
      
      const plotlyContainer = this.$refs.plotlyContainer;
      if (!plotlyContainer) return;
      
      const data = [];
      const layout = {
        title: 'UMAP聚类可视化',
        xaxis: { title: 'UMAP1' },
        yaxis: { title: 'UMAP2' },
        hovermode: 'closest',
        height: 500
      };
      
      // 根据选择的颜色方式进行绘制
      if (this.plotConfig.colorBy === 'gene' && this.plotConfig.gene) {
        // 基因表达图
        if (this.plotData.geneExpressions && this.plotData.geneExpressions[this.plotConfig.gene]) {
          const trace = {
            type: 'scatter',
            mode: 'markers',
            x: this.plotData.umap_coords.x,
            y: this.plotData.umap_coords.y,
            text: this.plotData.cell_ids,
            marker: {
              size: 5,
              color: this.plotData.geneExpressions[this.plotConfig.gene],
              colorscale: 'Viridis',
              colorbar: { title: this.plotConfig.gene }
            },
            hoverinfo: 'text+x+y'
          };
          
          data.push(trace);
        }
      } else {
        // 聚类或细胞类型图
        const colorField = this.plotConfig.colorBy === 'cluster' ? 'clusters' : 
          this.plotConfig.colorBy === 'cell_type' ? 'cell_types' : this.plotConfig.colorBy;
        
        if (this.plotData[colorField]) {
          const uniqueValues = [...new Set(this.plotData[colorField])];
          
          uniqueValues.forEach(value => {
            const indices = this.plotData[colorField].map((v, i) => v === value ? i : -1).filter(i => i !== -1);
            
            const trace = {
              type: 'scatter',
              mode: 'markers',
              x: indices.map(i => this.plotData.umap_coords.x[i]),
              y: indices.map(i => this.plotData.umap_coords.y[i]),
              text: indices.map(i => this.plotData.cell_ids[i]),
              name: value,
              marker: { size: 5 },
              hoverinfo: 'text+x+y+name'
            };
            
            data.push(trace);
          });
        }
      }
      
      Plotly.newPlot(plotlyContainer, data, layout);
    },
    
    updatePlot() {
      this.renderPlot();
    },
    
    async checkLLMExplanation() {
      if (!this.useLLM) return;
      
      try {
        const response = await axios.get(`/api/v1/analysis/llm_explanation/${this.currentTask.taskId}`, {
          headers: getAuthHeader()
        });
        
        if (response.data && response.data.explanation) {
          this.llmExplanation = response.data.explanation;
          this.llmExplanationAvailable = true;
        }
      } catch (error) {
        console.error('获取LLM解释失败:', error);
        this.llmExplanationAvailable = false;
      }
    },
    
    async refreshLLMExplanation() {
      try {
        this.loading = true;
        
        const response = await axios.post(`/api/v1/analysis/llm_explanation/${this.currentTask.taskId}`, {}, {
          headers: getAuthHeader()
        });
        
        if (response.data && response.data.explanation) {
          this.llmExplanation = response.data.explanation;
          this.$message.success('解释已更新');
        }
      } catch (error) {
        console.error('刷新LLM解释失败:', error);
        this.$message.error('刷新解释失败');
      } finally {
        this.loading = false;
      }
    },
    
    async askLLM() {
      if (!this.askLLMInput) return;
      
      try {
        this.askLLMLoading = true;
        
        const response = await axios.post(`/api/v1/analysis/ask_llm/${this.currentTask.taskId}`, {
          question: this.askLLMInput
        }, {
          headers: getAuthHeader()
        });
        
        if (response.data && response.data.answer) {
          this.llmAnswer = response.data.answer;
        }
      } catch (error) {
        console.error('询问LLM失败:', error);
        this.$message.error('询问失败');
      } finally {
        this.askLLMLoading = false;
      }
    },
    
    async sendFeedback(type) {
      try {
        await axios.post(`/api/v1/analysis/llm_feedback/${this.currentTask.taskId}`, {
          feedback_type: type
        }, {
          headers: getAuthHeader()
        });
        
        this.$message.success('感谢您的反馈');
      } catch (error) {
        console.error('发送反馈失败:', error);
        this.$message.error('发送反馈失败');
      }
    },
    
    async downloadFile(file) {
      try {
        const response = await axios.get(`/api/v1/analysis/download/${this.currentTask.taskId}/${file.id}`, {
          headers: getAuthHeader(),
          responseType: 'blob'
        });
        
        // 创建下载链接
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', file.filename);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } catch (error) {
        console.error('下载文件失败:', error);
        this.$message.error('下载文件失败');
      }
    },
    
    resetAnalysis() {
      this.currentStep = 0;
      this.selectedData = null;
      this.currentTask = null;
      this.analysisForm = {
        taskType: '',
        description: '',
        parameters: {
          min_genes: 200,
          min_cells: 3,
          max_mt_percent: 10,
          method: 'harmony',
          batch_key: 'batch',
          model: 'scgpt',
          confidence_threshold: 0.7
        }
      };
      
      this.clearPolling();
    },
    
    getDataTypeTag(type) {
      const tagMap = {
        'sc_rnaseq': 'success',
        'bulk_rnaseq': 'primary',
        'atac_seq': 'warning',
        'spatial': 'danger'
      };
      
      return tagMap[type] || 'info';
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
    
    formatFileSize(size) {
      if (size < 1024) {
        return size + ' B';
      } else if (size < 1024 * 1024) {
        return (size / 1024).toFixed(2) + ' KB';
      } else if (size < 1024 * 1024 * 1024) {
        return (size / 1024 / 1024).toFixed(2) + ' MB';
      } else {
        return (size / 1024 / 1024 / 1024).toFixed(2) + ' GB';
      }
    }
  }
};
</script>

<style scoped>
.analysis-panel {
  padding: 20px;
}

.analysis-steps {
  margin-bottom: 30px;
}

.step-content {
  margin-top: 20px;
  margin-bottom: 30px;
}

.step-actions {
  margin-top: 20px;
  text-align: right;
}

.task-status-card {
  margin-bottom: 20px;
}

.status-info {
  margin-bottom: 20px;
}

.progress-wrapper {
  margin-bottom: 20px;
}

.task-logs {
  margin-top: 20px;
  border-top: 1px solid #EBEEF5;
  padding-top: 10px;
}

.log-container {
  max-height: 200px;
  overflow-y: auto;
  background-color: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
}

.log-entry {
  margin: 0;
  padding: 2px 0;
  font-family: monospace;
  font-size: 12px;
}

.results-tabs {
  margin-bottom: 20px;
}

.visualization-container {
  padding: 10px;
}

.plotly-chart {
  width: 100%;
  height: 500px;
  margin-bottom: 20px;
}

.controls {
  margin-top: 20px;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.report-container {
  width: 100%;
  height: 600px;
}

.report-frame {
  width: 100%;
  height: 100%;
  border: none;
}

.no-report {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 300px;
  background-color: #f5f7fa;
  color: #909399;
}

.llm-explanation {
  padding: 10px;
}

.explanation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.explanation-content {
  background-color: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.explanation-feedback {
  margin-bottom: 20px;
}

.feedback-buttons {
  margin-top: 10px;
}

.ask-container {
  margin-top: 20px;
  border-top: 1px solid #EBEEF5;
  padding-top: 15px;
}

.ask-button {
  margin-top: 10px;
}

.llm-answer {
  margin-top: 15px;
  background-color: #f0f9eb;
  padding: 15px;
  border-radius: 4px;
}

.download-container {
  padding: 10px;
}

.parameters {
  margin-top: 15px;
  padding: 15px;
  border: 1px solid #EBEEF5;
  border-radius: 4px;
  background-color: #fafafa;
}

.preprocessing-params {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px dashed #EBEEF5;
}

.llm-enhanced {
  margin-top: 20px;
  padding: 15px;
  border: 1px solid #EBEEF5;
  border-radius: 4px;
  background-color: #f0f9eb;
}

.llm-options {
  margin-top: 15px;
  padding-left: 20px;
}
</style> 