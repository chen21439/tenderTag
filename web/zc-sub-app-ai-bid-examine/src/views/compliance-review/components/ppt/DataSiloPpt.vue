<template>
  <div class="data-silo-ppt">
    <PptSlideBase>
      <!-- 左侧内容区 -->
      <div class="left-content">
        <h1 class="title">打破数据孤岛</h1>

        <div class="description">
          <p class="paragraph">
            在传统模式下，业主单位的项目决策严重依赖分散在多个文档中的信息：
            招标采购，合同执行、进度与质保等大量关键资料文件在不同人电脑中零散存放，缺乏统一的结构和命名规范，
            项目管理人员往往需要反复查看、拼接和核对数据，既费时费力，又难以保证信息的完整性与准确性，一旦遗漏关键信息，就可能影响项目决策和风险控制。
          </p>

          <p class="paragraph">
            基于业务本体和知识图谱的项目生命周期管理有效解决了上述问题
            通过对从各类文档中抽取的项目、合同、供应商等数据进行智能分析与统计， 从语义层面将分散信息统一关联起来：
            将“项目”与“年度计划、标段、框架协议、合同、变更、验收记录、付款信息、供应商履约情况”等实体等实体从不同文档中识别出来并统一纳入项目知识图谱，
            在统一的业务本体之上，系统对这些结构化数据开展智能分析与统计，无论关键信息隐藏在哪一份文档中，项目经理和决策层都可以通过一张项目知识图谱，
            全面掌握项目从立项、招标、合同的全生命周期状态和风险，实现基于文档资源的一体化管理与辅助决策。
          </p>
        </div>
      </div>

      <!-- 右侧图谱展示区 -->
      <div class="right-content">
        <div class="graph-container">
          <img
            src="https://www.stardog.com/img/home-data-fabric.gif?_cchid=ddebc27da836963d74e47565864b6e69"
            alt="数据孤岛示意图"
            class="graph-image"
            @error="handleImageError"
          />
        </div>
      </div>
    </PptSlideBase>
  </div>
</template>

<script setup lang="ts">
import PptSlideBase from './PptSlideBase.vue'

defineOptions({
  name: 'DataSiloPpt'
})

const handleImageError = (e: Event) => {
  console.warn('图片加载失败:', e)
}
</script>

<style lang="scss" scoped>
.data-silo-ppt {
  width: 100%;
  height: 100%;
  background: #fff;
  display: flex;

  .left-content {
    flex: 1;
    padding: 60px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    background: #f5f5f5;

    .title {
      font-size: 48px;
      font-weight: bold;
      color: #1a1a2e;
      margin-bottom: 40px;
      position: relative;
      padding-bottom: 20px;

      &::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 80px;
        height: 4px;
        background: #1890ff;
        border-radius: 2px;
      }
    }

    .description {
      .paragraph {
        font-size: 18px;
        line-height: 1.8;
        color: #333;
        margin-bottom: 24px;
        text-align: justify;

        &:last-child {
          margin-bottom: 0;
        }
      }
    }
  }

  .right-content {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 40px;
    background: #fff;

    .graph-container {
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;

      .graph-image {
        width: 100%;
        height: 100%;
        object-fit: contain;
      }
    }
  }
}

// 响应式调整
@media (max-width: 1200px) {
  .data-silo-ppt {
    .left-content {
      padding: 40px;

      .title {
        font-size: 36px;
        margin-bottom: 24px;
      }

      .description .paragraph {
        font-size: 16px;
      }
    }

    .right-content {
      padding: 20px;
    }
  }
}
</style>
