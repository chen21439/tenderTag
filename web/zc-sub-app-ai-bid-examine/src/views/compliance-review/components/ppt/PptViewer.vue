<template>
  <div class="ppt-viewer">
    <!-- 左侧悬停区域 -->
    <div
      v-if="slides.length > 1 && currentSlide > 0"
      class="ppt-hover-area ppt-hover-left"
      @mouseenter="showLeftNav = true"
      @mouseleave="showLeftNav = false"
    >
      <!-- 左侧翻页按钮 -->
      <div v-show="showLeftNav" class="ppt-nav ppt-nav-prev" @click="prevSlide">
        <LeftOutlined />
      </div>
    </div>

    <!-- PPT 内容区 -->
    <div class="ppt-content">
      <Transition name="slide" mode="out-in">
        <component :is="currentSlideComponent" :key="currentSlide" />
      </Transition>
    </div>

    <!-- 右侧悬停区域 -->
    <div
      v-if="slides.length > 1 && currentSlide < slides.length - 1"
      class="ppt-hover-area ppt-hover-right"
      @mouseenter="showRightNav = true"
      @mouseleave="showRightNav = false"
    >
      <!-- 右侧翻页按钮 -->
      <div v-show="showRightNav" class="ppt-nav ppt-nav-next" @click="nextSlide">
        <RightOutlined />
      </div>
    </div>

    <!-- 页码指示器 -->
    <div v-if="slides.length > 1" v-show="showLeftNav || showRightNav" class="ppt-indicator">
      <span class="current">{{ currentSlide + 1 }}</span>
      <span class="divider">/</span>
      <span class="total">{{ slides.length }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h } from 'vue'
import { LeftOutlined, RightOutlined } from '@ant-design/icons-vue'
import DataSiloPpt from './DataSiloPpt.vue'
import DataFabricPpt from './DataFabricPpt.vue'
import KnowledgeGraphFeaturePpt from './KnowledgeGraphFeaturePpt.vue'
import KnowledgeGraphStepPpt from './KnowledgeGraphStepPpt.vue'
import SupplierAnalysisPpt from './SupplierAnalysisPpt.vue'
import CrossProjectInsightPpt from './CrossProjectInsightPpt.vue'

defineOptions({
  name: 'PptViewer'
})

// Props
interface Props {
  pptUrl?: string
}

const props = withDefaults(defineProps<Props>(), {
  pptUrl: ''
})

// PPT 幻灯片列表
const slides = [
  DataSiloPpt, // 第1页：数据孤岛问题
  DataFabricPpt, // 第2页：三层架构的数据织网图
  KnowledgeGraphFeaturePpt, // 第3页：知识图谱的核心能力
  // () => h(KnowledgeGraphStepPpt, { step: 0, graphWidth: '70%', graphHeight: '420px' }),  // 第3页：信息孤岛
  () => h(KnowledgeGraphStepPpt, { step: 1, graphWidth: '75%', graphHeight: '500px' }), // 第4页：按项目聚合
  () => h(KnowledgeGraphStepPpt, { step: 2, graphWidth: '75%', graphHeight: '520px' }), // 第5页：按年份聚合
  SupplierAnalysisPpt, // 第6页：供应商履约分析
  CrossProjectInsightPpt // 第7页：跨项目数据洞察
]

// 当前幻灯片索引
const currentSlide = ref(0)

// 控制左右翻页按钮显示
const showLeftNav = ref(false)
const showRightNav = ref(false)

// 当前幻灯片组件
const currentSlideComponent = computed(() => {
  const slide = slides[currentSlide.value]
  // 如果是函数，执行它以获取组件
  return typeof slide === 'function' ? slide() : slide
})

// 上一页
const prevSlide = () => {
  if (currentSlide.value > 0) {
    currentSlide.value--
  }
}

// 下一页
const nextSlide = () => {
  if (currentSlide.value < slides.length - 1) {
    currentSlide.value++
  }
}
</script>

<style lang="scss" scoped>
.ppt-viewer {
  width: 100%;
  height: 100%;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;

  .ppt-content {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .ppt-hover-area {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 120px;
    z-index: 10;
    display: flex;
    align-items: center;

    &.ppt-hover-left {
      left: 0;
      justify-content: flex-start;
      padding-left: 20px;
    }

    &.ppt-hover-right {
      right: 0;
      justify-content: flex-end;
      padding-right: 20px;
    }
  }

  .ppt-nav {
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.9);
    border-radius: 50%;
    cursor: pointer;
    transition: all 0.3s;
    font-size: 20px;
    color: #1890ff;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);

    &:hover {
      background: #fff;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
      transform: scale(1.1);
    }

    &:active {
      transform: scale(0.95);
    }
  }

  .ppt-indicator {
    position: absolute;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    padding: 8px 16px;
    background: rgba(0, 0, 0, 0.6);
    color: #fff;
    border-radius: 20px;
    font-size: 14px;
    z-index: 10;

    .current {
      font-weight: bold;
    }

    .divider {
      margin: 0 4px;
      opacity: 0.7;
    }

    .total {
      opacity: 0.8;
    }
  }
}

// 过渡动画
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.slide-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}
</style>
