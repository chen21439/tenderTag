<template>
  <div
    class="ppt-root"
    :style="rootStyle"
    @keydown.left.prevent="prev"
    @keydown.right.prevent="next"
    tabindex="0"
  >
    <!-- 左右点击热区 -->
    <div class="nav-zone left" @click="prev" aria-label="上一页"></div>
    <div class="nav-zone right" @click="next" aria-label="下一页"></div>

    <!-- 幻灯片容器 -->
    <div
      class="slides-wrapper"
      ref="slidesWrapper"
      @touchstart="onTouchStart"
      @touchmove="onTouchMove"
      @touchend="onTouchEnd"
    >
      <transition :name="direction > 0 ? 'slide-next' : 'slide-prev'" mode="out-in">
        <section class="slide" :key="index">
          <!-- 0 封面 -->
          <div v-if="index === 0" class="slide-inner cover-inner">
            <div class="logo">LOGO</div>
            <h1 class="title">工作总结及未来展望</h1>
            <p class="subtitle">工作进展回顾 · 亮点与不足 · 未来规划</p>
            <p class="meta">2025 Q4 汇报</p>
            <div class="bg-decor">
              <span class="c c1"></span>
              <span class="c c2"></span>
              <span class="c c3"></span>
              <span class="c c4"></span>
              <span class="c c5"></span>
            </div>
          </div>

          <!-- 1 目录 -->
          <div v-else-if="index === 1" class="slide-inner toc-inner">
            <div class="toc-badge">目录</div>
            <ol class="toc-list">
              <li class="toc-item">
                <span class="num">1</span><span class="text">基本工作概况</span>
              </li>
              <li class="toc-item">
                <span class="num">2</span><span class="text">重点成果</span>
              </li>
              <li class="toc-item">
                <span class="num">3</span><span class="text">存在问题与不足</span>
              </li>
              <li class="toc-item">
                <span class="num">4</span><span class="text">未来规划与展望</span>
              </li>
            </ol>
            <div class="bg-decor">
              <span class="c c1"></span>
              <span class="c c2"></span>
              <span class="c c3"></span>
              <span class="c c4"></span>
              <span class="c c5"></span>
            </div>
          </div>

          <!-- 2 章节标题 -->
          <div v-else-if="index === 2" class="slide-inner section-title-inner">
            <div class="section-no">1</div>
            <h2 class="section-title-text">基本工作概况</h2>
            <div class="bg-decor">
              <span class="c c1"></span>
              <span class="c c2"></span>
              <span class="c c3"></span>
              <span class="c c4"></span>
              <span class="c c5"></span>
            </div>
          </div>

          <!-- 3 三列要点 -->
          <div v-else-if="index === 3" class="slide-inner trio-inner">
            <div class="card">
              <div class="badge">Part 1</div>
              <div class="card-title">重点工作A</div>
              <div class="card-desc">详细说明占位文本，可替换为具体数据与案例。</div>
            </div>
            <div class="card">
              <div class="badge">Part 2</div>
              <div class="card-title">亮点工作B</div>
              <div class="card-desc">详细说明占位文本，可替换为具体数据与案例。</div>
            </div>
            <div class="card">
              <div class="badge">Part 3</div>
              <div class="card-title">优化方向C</div>
              <div class="card-desc">详细说明占位文本，可替换为具体数据与案例。</div>
            </div>
            <div class="bg-decor">
              <span class="c c1"></span>
              <span class="c c2"></span>
              <span class="c c3"></span>
              <span class="c c4"></span>
              <span class="c c5"></span>
            </div>
          </div>

          <!-- 4 图文页 -->
          <div v-else-if="index === 4" class="slide-inner imgtext-inner">
            <div class="img-wrap">
              <img
                class="photo"
                alt="示例图片"
                src="https://images.unsplash.com/photo-1511379938547-c1f69419868d?q=80&w=1200&auto=format&fit=crop"
              />
            </div>
            <div class="text-wrap">
              <h3>请结合实际业务内容阐述阶段成果</h3>
              <p>可放关键项目进展、量化指标或示意图等。</p>
              <button class="primary" @click="onMore">了解更多</button>
            </div>
            <div class="bg-decor">
              <span class="c c1"></span>
              <span class="c c2"></span>
              <span class="c c3"></span>
              <span class="c c4"></span>
              <span class="c c5"></span>
            </div>
          </div>

          <!-- 5 总结环形 -->
          <div v-else class="slide-inner summary-inner">
            <div class="ring">
              <div class="ring-item">
                <div class="ring-title">阶段成果复盘</div>
                <div class="ring-desc">巩固存量，突破增量</div>
              </div>
              <div class="ring-item">
                <div class="ring-title">问题与改进</div>
                <div class="ring-desc">流程梳理，工具提效</div>
              </div>
              <div class="ring-item">
                <div class="ring-title">未来规划</div>
                <div class="ring-desc">目标拆解，节奏推进</div>
              </div>
            </div>
            <div class="bg-decor">
              <span class="c c1"></span>
              <span class="c c2"></span>
              <span class="c c3"></span>
              <span class="c c4"></span>
              <span class="c c5"></span>
            </div>
          </div>
        </section>
      </transition>
    </div>

    <!-- 底部进度与控制 -->
    <div class="footer">
      <div class="dots">
        <button
          v-for="(_, i) in slidesCount"
          :key="i"
          :class="['dot', { active: i === index }]"
          @click="go(i)"
          :aria-label="`跳转到第 ${i + 1} 页`"
        ></button>
      </div>
      <div class="controls">
        <button class="ctrl" @click="prev">上一页</button>
        <span class="progress">{{ index + 1 }} / {{ slidesCount }}</span>
        <button class="ctrl" @click="next">下一页</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'

const theme = {
  bg: '#eef7ef',
  text: '#224433',
  accent: '#6bc38a',
  accent2: '#f2d385',
  muted: '#a6c9b2'
}

const index = ref(0)
const slidesCount = 6
const direction = ref(1) // 1: forward, -1: backward
const slidesWrapper = ref(null)

const touchStartX = ref(0)
const touchDeltaX = ref(0)

const rootStyle = computed(() => ({
  '--bg': theme.bg,
  '--text': theme.text,
  '--accent': theme.accent,
  '--accent2': theme.accent2,
  '--muted': theme.muted
}))

function go(target) {
  if (target < 0 || target >= slidesCount || target === index.value) return
  direction.value = target > index.value ? 1 : -1
  index.value = target
  focusRoot()
}
function next() {
  if (index.value < slidesCount - 1) {
    direction.value = 1
    index.value++
    focusRoot()
  }
}
function prev() {
  if (index.value > 0) {
    direction.value = -1
    index.value--
    focusRoot()
  }
}
function focusRoot() {
  // 让键盘事件可持续触发
  requestAnimationFrame(() => {
    const el = slidesWrapper.value?.parentElement
    el?.focus?.()
  })
}

function onTouchStart(e) {
  touchStartX.value = e.touches[0].clientX
  touchDeltaX.value = 0
}
function onTouchMove(e) {
  touchDeltaX.value = e.touches[0].clientX - touchStartX.value
}
function onTouchEnd() {
  const threshold = 60
  if (touchDeltaX.value > threshold) {
    prev()
  } else if (touchDeltaX.value < -threshold) {
    next()
  }
  touchDeltaX.value = 0
}

function onKey(e) {
  if (e.key === 'ArrowRight' || e.key === 'PageDown') next()
  if (e.key === 'ArrowLeft' || e.key === 'PageUp') prev()
}

function onMore() {
  window.alert('可绑定跳转/更多详情')
}

onMounted(() => {
  window.addEventListener('keydown', onKey)
  focusRoot()
})
onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
})
</script>

<style scoped>
.ppt-root {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 100vh;
  background: var(--bg);
  color: var(--text);
  overflow: hidden;
  outline: none;
  display: flex;
  flex-direction: column;
}

.slides-wrapper {
  position: relative;
  flex: 1 1 auto;
  display: grid;
  place-items: center;
  overflow: hidden;
}

.slides-stage {
  position: relative;
  width: min(1080px, 96vw);
  height: min(620px, 70vh);
}

.slide {
  position: relative;
  width: min(1080px, 96vw);
  height: min(620px, 70vh);
  background: transparent;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 12px 38px rgba(0,0,0,0.08);
  backdrop-filter: blur(0.5px);
}

.slide .slide-inner {
  position: relative;
  width: 100%;
  height: 100%;
  background: linear-gradient(180deg, #f7fbf8 0%, #eef7ef 100%);
}

/* 过渡动画：前进与后退方向 */
.slide-next-enter-active,
.slide-next-leave-active,
.slide-prev-enter-active,
.slide-prev-leave-active {
  transition: transform 380ms cubic-bezier(.2,.8,.2,1), opacity 380ms ease;
}
.slide-next-enter-from { opacity: 0; transform: translateX(40px); }
.slide-next-leave-to   { opacity: 0; transform: translateX(-40px); }
.slide-prev-enter-from { opacity: 0; transform: translateX(-40px); }
.slide-prev-leave-to   { opacity: 0; transform: translateX(40px); }

/* 点击导航热区 */
.nav-zone {
  position: absolute;
  top: 0;
  bottom: 68px; /* 给底部控制区留空间 */
  width: 28%;
  z-index: 5;
  cursor: pointer;
}
.nav-zone.left { left: 0; }
.nav-zone.right { right: 0; }

/* 底部控制栏 */
.footer {
  height: 68px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 16px;
}
.dots {
  display: flex;
  align-items: center;
  gap: 10px;
}
.dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #cfe6d8;
  border: none;
  cursor: pointer;
}
.dot.active {
  background: var(--accent);
  box-shadow: 0 0 0 4px rgba(107,195,138,0.18);
}
.controls {
  display: flex;
  align-items: center;
  gap: 10px;
}
.ctrl {
  height: 36px;
  padding: 0 14px;
  border-radius: 8px;
  border: 1px solid #d2e5d8;
  background: white;
  color: var(--text);
  cursor: pointer;
}
.ctrl:hover { border-color: var(--accent); }
.progress { color: #537b66; }

/* 背景圆形装饰 */
.bg-decor .c {
  position: absolute;
  display: block;
  border-radius: 999px;
  background: radial-gradient(circle at 30% 30%, rgba(107,195,138,0.18), transparent 60%);
}
.bg-decor .c1 { width: 220px; height: 220px; left: -40px; top: -40px; }
.bg-decor .c2 { width: 160px; height: 160px; right: -30px; top: 20px; background: radial-gradient(circle at 30% 30%, rgba(242,211,133,0.28), transparent 60%); }
.bg-decor .c3 { width: 120px; height: 120px; left: 40px; bottom: 60px; }
.bg-decor .c4 { width: 180px; height: 180px; right: 60px; bottom: -40px; }
.bg-decor .c5 { width: 80px; height: 80px; left: 50%; top: 20%; transform: translateX(-50%); }

/* 各页面局部样式 */
.cover-inner {
  display: grid;
  grid-template-rows: 1fr auto auto auto 1fr;
  justify-items: center;
  align-items: center;
}
.cover-inner .logo {
  place-self: start start;
  margin: 22px;
  font-weight: 700;
  color: #89c9a3;
}
.cover-inner .title {
  font-size: clamp(24px, 4.6vw, 54px);
  letter-spacing: 1px;
  margin: 0;
}
.cover-inner .subtitle {
  color: #6d8f7f;
  margin: 0;
}
.cover-inner .meta {
  color: #7aa58c;
}

.toc-inner {
  padding: 28px 36px;
  display: grid;
  grid-template-columns: 180px 1fr;
  gap: 24px;
  align-items: center;
}
.toc-badge {
  width: 120px;
  height: 120px;
  border-radius: 20px;
  background: white;
  display: grid;
  place-items: center;
  color: var(--text);
  box-shadow: 0 8px 24px rgba(0,0,0,0.06);
  border: 1px solid #d8eadf;
}
.toc-list {
  list-style: none;
  display: grid;
  grid-template-columns: repeat(2, minmax(0,1fr));
  gap: 16px 24px;
  margin: 0;
  padding: 0;
}
.toc-item {
  background: white;
  border-radius: 12px;
  border: 1px solid #dbece2;
  padding: 14px 16px;
  display: flex;
  gap: 10px;
  align-items: center;
}
.toc-item .num {
  width: 26px;
  height: 26px;
  border-radius: 999px;
  background: var(--accent);
  color: white;
  display: grid;
  place-items: center;
  font-weight: 600;
}
.toc-item .text { color: #3f5f52; }

.section-title-inner {
  display: grid;
  place-items: center;
  text-align: center;
  padding: 24px;
}
.section-no {
  font-size: clamp(28px, 6vw, 64px);
  color: #3a5d4d;
  margin-bottom: 8px;
}
.section-title-text {
  font-size: clamp(22px, 4.5vw, 42px);
  margin: 0;
  color: #27493c;
}

.trio-inner {
  height: 100%;
  padding: 24px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
  align-items: stretch;
}
.trio-inner .card {
  background: white;
  border: 1px solid #dbece2;
  border-radius: 12px;
  padding: 16px;
  display: grid;
  gap: 10px;
}
.trio-inner .badge {
  width: max-content;
  padding: 4px 10px;
  border-radius: 999px;
  background: #eaf7ef;
  color: #2d5847;
  border: 1px solid #cfe7d8;
  font-size: 12px;
}
.trio-inner .card-title {
  font-weight: 700;
  color: #2c4c40;
}
.trio-inner .card-desc { color: #597a6b; }

.imgtext-inner {
  height: 100%;
  padding: 24px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  align-items: center;
}
.img-wrap {
  background: white;
  border: 1px solid #dbece2;
  border-radius: 16px;
  padding: 12px;
}
.photo {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  border-radius: 12px;
}
.text-wrap h3 { margin: 0 0 8px 0; color: #2b4d40; }
.text-wrap p { margin: 0 0 12px 0; color: #557a68; }
.primary {
  height: 36px;
  padding: 0 14px;
  border-radius: 8px;
  border: none;
  background: var(--accent);
  color: white;
  cursor: pointer;
}
.primary:hover { filter: brightness(0.95); }

.summary-inner {
  height: 100%;
  display: grid;
  place-items: center;
}
.ring {
  width: min(540px, 82%);
  aspect-ratio: 1 / 1;
  border-radius: 999px;
  border: 10px solid #e3f3e9;
  display: grid;
  place-items: center;
  position: relative;
}
.ring-item {
  width: 58%;
  margin: 8px 0;
  text-align: center;
  background: white;
  border: 1px solid #dbece2;
  border-radius: 12px;
  padding: 10px;
  color: #335b49;
  box-shadow: 0 6px 16px rgba(0,0,0,0.04);
}
.ring-title { font-weight: 700; }
.ring-desc { color: #5a7f6d; }

/* 响应式 */
@media (max-width: 900px) {
  .slide {
    width: 96vw;
    height: auto;
    aspect-ratio: 16/10;
  }
  .toc-inner {
    grid-template-columns: 1fr;
  }
  .imgtext-inner {
    grid-template-columns: 1fr;
  }
  .trio-inner {
    grid-template-columns: 1fr;
  }
  .nav-zone {
    bottom: 88px;
  }
}
</style>