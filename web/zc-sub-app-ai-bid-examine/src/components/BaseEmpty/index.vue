<template>
  <div class="base-empty" :style="{ height }">
    <div :class="['base-empty-main', direction === 'row' && 'row']">
      <slot>
        <img src="@/assets/images/common/empty-default.png" />
      </slot>
      <div class="base-empty-main__desc">{{ description }}</div>
    </div>
    <slot name="footer" />
  </div>
</template>
<script setup lang="ts">
defineOptions({ name: 'BaseEmpty' });
interface Props {
  height?: string;
  direction?: 'row' | 'column';
  description?: string;
}
const props = withDefaults(defineProps<Props>(), {
  height: '100%',
  direction: 'column',
  description: '暂无数据'
});
</script>

<style lang="scss" scoped>
.base-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%; 
  &-main {
    display: flex;
    flex-direction: column;
    align-items: center;

    img {
      width: 184px;
      height: 184px;
    }

    &__desc {
      font-family: Source Han Sans;
      font-size: var(--font-12);
      font-weight: normal;
      line-height: 18px;
      text-align: center;
      color:var(--fill-6);
    }

    &.row {
      flex-direction: row;

      .base-empty-main__desc {
        margin: 0 0 0 4px;
      }
    }
  }
}
</style>
