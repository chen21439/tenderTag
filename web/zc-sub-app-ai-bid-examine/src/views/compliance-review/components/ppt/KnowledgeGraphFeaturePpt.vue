<template>
  <div class="knowledge-graph-feature-ppt">
    <PptSlideBase>
      <div class="ppt-content">
        <!-- 顶部标题居中 -->
        <div class="header">
          <h1 class="title">业务本体与项目知识图谱平台</h1>
        </div>

        <!-- 内容区域 -->
        <div class="content-area">
          <!-- 左侧三个功能示例 -->
          <div class="left-section">
            <div class="feature-list">
              <div class="feature-item">
                <div class="feature-icon">🔍</div>
                <div class="feature-text">
                  <h3>典型业务问题</h3>
                  <ul>
                    <li>是否有类似的招标项目？</li>
                    <li>有哪些相同的技术参数？是否需要更新技术参数？</li>
                    <li>那些项目，那些供应商的合同即将到期，需要重新招标？</li>
                  </ul>
                </div>
              </div>

              <div class="feature-item">
                <div class="feature-icon">🔗</div>
                <div class="feature-text">
                  <h3>图谱怎么看清关系</h3>
                  <ul>
                    <li>自动把项目、标段、设备品类、技术参数、合同、供应商、质量事件等节点连成网络</li>
                    <li>从技术参数出发，一键找到历史上所有“技术参数相似”的招标项目及对应供应商</li>
                    <li>结合合同起止日期，定位哪些项目和供应商的合同即将到期、需要安排续签或重招</li>
                  </ul>
                </div>
              </div>

              <div class="feature-item">
                <div class="feature-icon">⚡</div>
                <div class="feature-text">
                  <h3>决策效率提升</h3>
                  <ul>
                    <li>不再逐个系统、逐份文档翻找拼接，图谱秒级给出参考案例</li>
                    <li>类似项目、可复用或需更新的技术参数、即将到期的合同由系统自动聚合与预警</li>
                    <li>将时间从整理，查找数据转移到决策本身</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          <!-- 右侧图示区域（占位） -->
          <div class="right-section">
            <div class="graph-container" ref="graphContainer"></div>
          </div>
        </div>
      </div>
    </PptSlideBase>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import cytoscape from 'cytoscape'
import PptSlideBase from './PptSlideBase.vue'

defineOptions({
  name: 'KnowledgeGraphFeaturePpt'
})

const graphContainer = ref<HTMLElement | null>(null)
let cy: any = null

onMounted(() => {
  if (!graphContainer.value) return

  // 构建简单的关联关系示意图
  const elements = [
    // 中心节点 - 项目
    { data: { id: 'project', label: '目标项目', type: 'center' } },

    // 关联节点
    { data: { id: 'supplier1', label: '供应商A', type: 'supplier' } },
    { data: { id: 'supplier2', label: '供应商B', type: 'supplier' } },
    { data: { id: 'contract1', label: '合同1', type: 'contract' } },
    { data: { id: 'contract2', label: '合同2', type: 'contract' } },
    { data: { id: 'related_project', label: '关联项目', type: 'related' } },
    { data: { id: 'document', label: '相关文档', type: 'document' } }
  ]

  const edges = [
    { data: { source: 'project', target: 'supplier1' } },
    { data: { source: 'project', target: 'supplier2' } },
    { data: { source: 'project', target: 'contract1' } },
    { data: { source: 'project', target: 'contract2' } },
    { data: { source: 'project', target: 'related_project' } },
    { data: { source: 'project', target: 'document' } },
    { data: { source: 'supplier1', target: 'contract1' } },
    { data: { source: 'supplier2', target: 'contract2' } },
    { data: { source: 'related_project', target: 'supplier1' } }
  ]

  const styles = [
    {
      selector: 'node',
      style: {
        label: 'data(label)',
        'text-valign': 'center',
        'text-halign': 'center',
        'font-size': '14px',
        'border-width': 2
      }
    },
    {
      selector: 'node[type="center"]',
      style: {
        'background-color': '#1890ff',
        'border-color': '#096dd9',
        width: 80,
        height: 80,
        shape: 'ellipse',
        color: '#fff',
        'font-weight': 'bold',
        'font-size': '16px'
      }
    },
    {
      selector: 'node[type="supplier"]',
      style: {
        'background-color': '#52c41a',
        'border-color': '#389e0d',
        width: 60,
        height: 60,
        shape: 'ellipse',
        color: '#fff'
      }
    },
    {
      selector: 'node[type="contract"]',
      style: {
        'background-color': '#fa8c16',
        'border-color': '#d46b08',
        width: 60,
        height: 60,
        shape: 'roundrectangle',
        color: '#fff'
      }
    },
    {
      selector: 'node[type="related"]',
      style: {
        'background-color': '#722ed1',
        'border-color': '#531dab',
        width: 60,
        height: 60,
        shape: 'ellipse',
        color: '#fff'
      }
    },
    {
      selector: 'node[type="document"]',
      style: {
        'background-color': '#eb2f96',
        'border-color': '#c41d7f',
        width: 60,
        height: 60,
        shape: 'rectangle',
        color: '#fff'
      }
    },
    {
      selector: 'edge',
      style: {
        width: 2,
        'line-color': '#1890ff',
        'curve-style': 'bezier',
        'target-arrow-shape': 'triangle',
        'target-arrow-color': '#1890ff',
        opacity: 0.6
      }
    }
  ]

  cy = cytoscape({
    container: graphContainer.value,
    elements: [...elements, ...edges],
    style: styles,
    layout: {
      name: 'cose',
      animate: false,
      padding: 60,
      nodeRepulsion: 8000,
      idealEdgeLength: 80,
      edgeElasticity: 100,
      nestingFactor: 1.2,
      gravity: 80,
      numIter: 1000,
      initialTemp: 200,
      coolingFactor: 0.95,
      minTemp: 1.0
    }
  })
})

onUnmounted(() => {
  if (cy) {
    cy.destroy()
  }
})
</script>

<style lang="scss" scoped>
.knowledge-graph-feature-ppt {
  width: 100%;
  height: 100%;
  background: #f5faff;

  .ppt-content {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    background: #f5faff;

    .header {
      text-align: center;
      padding: 40px 60px 20px;

      .title {
        font-size: 48px;
        font-weight: bold;
        color: #1a1a2e;
        margin: 0;
        position: relative;
        display: inline-block;
        padding-bottom: 20px;

        &::after {
          content: '';
          position: absolute;
          bottom: 0;
          left: 50%;
          transform: translateX(-50%);
          width: 80px;
          height: 4px;
          background: #1890ff;
          border-radius: 2px;
        }
      }
    }

    .content-area {
      flex: 1;
      display: flex;
      padding: 20px 40px 40px;
      gap: 60px;
      background: #f5faff;

      .left-section {
        flex: 1.4;
        display: flex;
        align-items: center;
        justify-content: center;

        .feature-list {
          display: flex;
          flex-direction: column;
          gap: 28px;
          width: 100%;

          .feature-item {
            display: flex;
            align-items: flex-start;
            gap: 16px;
            padding: 20px;
            background: #fff;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            transition: all 0.3s ease;

            &:hover {
              box-shadow: 0 4px 16px rgba(24, 144, 255, 0.15);
              transform: translateY(-2px);
            }

            .feature-icon {
              font-size: 28px;
              flex-shrink: 0;
              width: 40px;
              height: 40px;
              display: flex;
              align-items: center;
              justify-content: center;
            }

            .feature-text {
              flex: 1;

              h3 {
                font-size: 18px;
                font-weight: bold;
                color: #1890ff;
                margin: 0 0 10px 0;
              }

              .subtitle {
                font-size: 14px;
                color: #999;
                margin: 0 0 12px 0;
              }

              ul {
                margin: 0;
                padding-left: 18px;

                li {
                  font-size: 14px;
                  line-height: 1.6;
                  color: #666;
                  margin-bottom: 4px;

                  &:last-child {
                    margin-bottom: 0;
                  }
                }
              }

              p {
                font-size: 16px;
                line-height: 1.6;
                color: #666;
                margin: 0;
              }
            }
          }
        }
      }

      .right-section {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;

        .graph-container {
          width: 85%;
          height: 85%;
          background: #fff;
          border-radius: 12px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        }
      }
    }
  }
}
</style>
