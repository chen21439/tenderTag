<template>
  <a-modal
    v-model:open = "visible"
    v-bind="$attrs"
    destroy-on-close
    :class="['base-dialog', { 'has-no-title': !showHeader }]"
    :width="computedWidth"
    :wrap-style="{ overflow: 'hidden' }"
    @after-close="onClose"
  >
  <template v-if="showHeader" #title>
      <div ref="modalMoveRef" class="base-dialog-header" :class="{'is-drag': isDrag }">
          <slot name="header">
            <div v-if="title" class="header-title">
              {{ title }}
              <slot name="titleTip">
                <span v-if="titleTip" class="header-title-tip">{{ titleTip }}</span>
              </slot>
            </div>
          </slot>
          <div v-if="headerSuffixTip" class="header-suffix-tip">{{ headerSuffixTip }}</div>
          <slot name="headerSuffix"></slot>
        </div>
        <slot name="prefix"></slot>
    </template>
    <!-- content -->
    <a-spin :spinning="contentLoading">
      <div class="base-dialog-content base-dialog-scroller" :style="{ 'max-height': scrollHeight }">
        <slot></slot>
      </div>
    </a-spin>
    <!-- footer -->
    <template #footer>
      <div class="base-dialog-footer">
        <slot name="footer">
          <a-button v-if="showCancelButton" class="btn-confirm"  @click="onClickCancel">{{ cancelText }}</a-button>
          <a-button v-if="showConfirmButton" class="btn-cancel" :disabled="loading" type="primary" @click="onClickConfirm">{{ confirmText }}</a-button>
        </slot>
      </div>
    </template>
    <template v-if="isDrag" #modalRender="{ originVNode }">
      <div :style="transformStyle">
        <component :is="originVNode" />
      </div>
    </template>
  </a-modal>
</template>
<script lang="ts" setup>
import { ref, computed, CSSProperties, watch, watchEffect } from 'vue'
import { useDraggable } from '@vueuse/core'
defineOptions({ name: 'BaseDialog' })
interface Props {
  modelValue?: boolean;
  loading?: boolean;
  contentLoading?: boolean;
  width?: string; // 宽度
  showHeader?: boolean; // 显示header
  title?: string; // title
  titleTip?: string; // title后面的tip
  headerSuffixTip?: string; // headerSuffixTip
  scrollHeight?: string;
  showCancelButton?: boolean;
  showConfirmButton?: boolean;
  cancelText?: string;
  confirmText?: string;
  isDrag?:boolean;
}
const props = withDefaults(defineProps<Props>(), {
  modelValue: false,
  loading: false,
  contentLoading: false,
  width: 'middle',
  showHeader: true,
  title: '',
  titleTip: '',
  headerSuffixTip: '',
  scrollHeight: '500px',
  showCancelButton: true,
  showConfirmButton: true,
  cancelText: '取消',
  confirmText: '确定',
  isDrag: false
});
const sizeMap: Record<string, any> = ref({
  xs: '400px',
  small: '532px',
  middle: '576px',
  large: '900px' // 弹框大小
});
const emits = defineEmits(['confirm', 'cancel', 'close', 'update:model-value'])

const visible = computed({
  get: () => props.modelValue,
  set: (val: boolean) => emits('update:model-value', val)
});

const computedWidth = computed(() => {
  const w = props.width
  return w && sizeMap.value[w] ? sizeMap.value[w] : w
})

const onClickConfirm = () => {
  if (props.loading) return
  emits('confirm')
};
const onClickCancel = () => {
  if (props.loading) return;
  emits('update:model-value', false)
  emits('cancel')
}
const onClose = () => {
  emits('close')
}
// 拖拽
const modalMoveRef = ref<HTMLElement>()
const { x, y, isDragging } = useDraggable(modalMoveRef)
const startX = ref<number>(0)
const startY = ref<number>(0)
const startedDrag = ref(false)
const transformX = ref(0)
const transformY = ref(0)
const preTransformX = ref(0)
const preTransformY = ref(0)
const dragRect = ref({ left: 0, right: 0, top: 0, bottom: 0 })
const transformStyle = computed<CSSProperties>(() => {
  return {
    transform: `translate(${transformX.value}px, ${transformY.value}px)`
  }
})
watch([x, y], () => {
  if (!startedDrag.value) {
    startX.value = x.value
    startY.value = y.value
    const bodyRect = document.body.getBoundingClientRect()
    const titleRect = modalMoveRef.value?.getBoundingClientRect()
    dragRect.value.right = bodyRect.width - (titleRect?.width || 0)
    dragRect.value.bottom = bodyRect.height - (titleRect?.height || 0)
    preTransformX.value = transformX.value
    preTransformY.value = transformY.value
  }
  startedDrag.value = true
})
watch(isDragging, () => {
  if (!isDragging) {
    startedDrag.value = false
  }
})

watchEffect(() => {
  if (startedDrag.value) {
    transformX.value =
      preTransformX.value +
      Math.min(Math.max(dragRect.value.left, x.value), dragRect.value.right) -
      startX.value;
    transformY.value =
      preTransformY.value +
      Math.min(Math.max(dragRect.value.top, y.value), dragRect.value.bottom) -
      startY.value
  }
})

</script>

<style lang="scss"  scoped>
.base-dialog{
  .base-dialog-header{
    position: relative;
    box-sizing: border-box;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 24px;
    padding: 0 64px 8px 0;
    box-sizing: border-box;
    .header-title {
      font-weight: 500;
      font-size: var(--font-22);
    }
    .header-title-tip,.header-suffix-tip {
      margin-left: 8px;
      font-size: var(--font-14);
      font-weight: 400;
      color: var(--text-2);
    }
    &.is-drag {
      cursor: move;
    }
  }
  .base-dialog-scroller {
    overflow-y: scroll;
  }
}
</style>
