<template>
    <div class="reader-container">
        <div class="reader-content">
            <DocumentReader
                ref="documentReaderRef"
                v-if="documentData"
                :data="documentData"
                :show-toc="false"
                :show-toolbar="true"
                :show-pagination="true"
                :initial-zoom="1"
                @page-change="handlePageChange"
                @zoom-change="handleZoomChange"
            />
            <div v-else class="loading-container">
                <a-spin size="large" tip="加载文档中..." />
            </div>
        </div>
        <div class="other">
            <div class="info-panel">
                <h4>文档信息</h4>
                <div v-if="documentData" class="info-content">
                    <p><strong>文件ID:</strong> {{ documentData.fileId }}</p>
                    <p><strong>总页数:</strong> {{ totalPages }}</p>
                    <p><strong>当前页:</strong> {{ currentPage }}</p>
                    <p><strong>缩放比例:</strong> {{ Math.round(currentZoom * 100) }}%</p>
                </div> 
            </div>
            <!-- 修订建议面板 -->
            <div class="revision-panel">
                <div class="revision-header">
                    <h3>修订建议</h3> 
                </div>
                <div class="revision-list">
                    <div
                        v-for="suggestion in filteredRevisionSuggestions"
                        :key="suggestion.id"
                        class="revision-item"
                        :class="[
                            'type-risk',
                            { active: activeSuggestionId === suggestion.uniqueId }
                        ]"
                        @click="jumpToSuggestion(suggestion)"
                    >
                        <div class="revision-item-header">
                            <a-tag
                                color="orange"
                                size="small"
                            >
                                风险提示
                            </a-tag>
                            <span class="page-info">第{{ suggestion.page }}页</span>
                        </div>

                        <div class="revision-item-content">
                            <div class="review-item-name">
                                <span class="label">检查项：</span>
                                <span class="text">{{ suggestion.reviewItemName }}</span>
                            </div>

                            <div class="scene-desc">
                                <span class="label">场景：</span>
                                <span class="text">{{ suggestion.sceneDesc }}</span>
                            </div>

                            <div class="original-text">
                                <span class="label">原文内容：</span>
                                <span class="text deleted">{{ suggestion.fileText }}</span>
                            </div>

                            <div class="risk-tip">
                                <span class="label">风险提示：</span>
                                <span class="text risk">{{ suggestion.showRiskTip }}</span>
                            </div>
                        </div>

                        <div class="revision-item-actions">
                            <!-- <a-button-group size="small">
                                <a-button
                                    type="primary"
                                    @click.stop="acceptSuggestion(suggestion)"
                                >
                                    处理
                                </a-button>
                                <a-button @click.stop="rejectHighlight()">
                                    取消高亮
                                </a-button>
                            </a-button-group> -->
                        </div>

                        <div class="legal-sources" v-if="suggestion.legalBasicSourceList && suggestion.legalBasicSourceList.length > 0">
                            <div class="label">法规依据：</div>
                            <div
                                v-for="(source, index) in suggestion.legalBasicSourceList"
                                :key="index"
                                class="legal-source-item"
                            >
                                <div class="source-title">{{ source.source }} {{ source.basicNumber }}</div>
                                <div class="source-desc">{{ source.basicDesc }}</div>
                            </div>
                        </div>
                    </div>
                </div> 
            </div>
        </div>
    </div>
</template>

<script setup lang='ts'>
import { ref, computed } from 'vue'
import  DocumentReader from '@/components/DocumentReader/index.vue'
import type { DocumentData, DocumentElement } from '@/components/DocumentReader'
import {taskMarkDownDetail, getTaskReview } from '@/api/examine'

defineOptions({
    name: 'ReaderIndex'
})
const taskId = ref<string>('1955823962696978434')
// 响应式数据
const documentData = ref<DocumentData | null>(null)
const currentPage = ref(1)
const currentZoom = ref(1)
const documentReaderRef = ref<any>(null)
// 计算属性
const totalPages = computed(() => {
    if (!documentData.value) return 0

    try {
        const elements = typeof documentData.value.markDownDetail === 'string'
            ? JSON.parse(documentData.value.markDownDetail)
            : documentData.value.markDownDetail

        return Math.max(...elements.map((el: DocumentElement) => el.page_id))
    } catch {
        return 0
    }
})

// 事件处理函数
const handlePageChange = (page: number) => {
    currentPage.value = page
    console.log('页面切换到:', page)
}

const handleZoomChange = (zoom: number) => {
    currentZoom.value = zoom
    console.log('缩放比例变更为:', zoom)
}


// 修订建议相关 
const revisionSuggestions = ref<any[]>([])

const activeSuggestionId = ref<string>('')
const isJumping = ref<boolean>(false) // 防止重复跳转
// 加载修订建议数据
const loadRevisionSuggestions = async () => { 
    const  {data,err} = await getTaskReview({
        taskId: taskId.value,
        reviewResult: 1
    })
    if(err) return
    revisionSuggestions.value = data.dataList ?? []
}
const filteredRevisionSuggestions = computed(() => {
    // 真实数据中使用 handleStatus 来判断是否已处理
    // 0: 未处理, 1: 已处理
    return revisionSuggestions.value.filter(s => s.handleStatus === 0)
})
// 修订建议相关方法

// 修订建议操作方法
const jumpToSuggestion = (suggestion: any) => {
    // 防止重复跳转
    if (isJumping.value) {
        return
    }

    // 如果点击的是同一个建议，不重复处理
    if (activeSuggestionId.value === suggestion.uniqueId) {
        return
    }

    isJumping.value = true

    // 清除所有现有高亮
    if (documentReaderRef.value) {
        documentReaderRef.value.clearAllHighlights()
    }

    // 设置当前激活的建议
    activeSuggestionId.value = suggestion.uniqueId

    // 跳转到对应页面并高亮
    if (documentReaderRef.value && suggestion.position && suggestion.position.length > 0) {
        const position = suggestion.position[0] // 取第一个位置
        // 传递fileText参数用于精确定位
        documentReaderRef.value.scrollToHighlight(suggestion.page, position, suggestion.fileText)

        // 添加高亮
        documentReaderRef.value.addHighlight(suggestion.uniqueId, {
            type: 'risk',
            position: position,
            pageId: suggestion.page,
            reviewItemName: suggestion.reviewItemName,
            fileText: suggestion.fileText // 传递原文内容用于文本高亮
        })

        // 延迟重置防抖标志
        setTimeout(() => {
            isJumping.value = false
        }, 1000)
    } else {
        isJumping.value = false
    }
}

const loadData = async () => {
    const {data,err} = await taskMarkDownDetail({taskId:taskId.value})
    if(err) return
    documentData.value = data
}
loadData()
loadRevisionSuggestions()
</script>

<style lang="scss" scoped>
.reader-container {
    display: flex;
    height: 100vh;
    padding: 20px;
    gap: 20px;
    width: 100%;
    background: #f5f5f5;

    .reader-content {
        flex: 1;
        min-width: 0;
        min-height: 0;

        .loading-container {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100%;
            background: #fff;
            border-radius: 8px;
        }
    }

    .other {
        width: 300px;
        overflow-y: auto;
        flex-shrink: 0;
        height: 100%;
        display: flex;
        flex-direction: column;
        .info-panel {
            flex-shrink: 0;
            background: #fff;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

            h4 {
                margin: 0 0 12px 0;
                color: #262626;
                font-size: 16px;
                font-weight: 600;
            }

            .info-content {
                p {
                    margin: 8px 0;
                    font-size: 14px;
                    color: #595959;

                    strong {
                        color: #262626;
                    }
                }
            } 
        }
    }
}
.revision-panel {  
    flex: 1; 
    margin-top: 20px;
    background: white;
    border-left: 1px solid #e8e8e8;
    display: flex;
    flex-direction: column;
    transition: width 0.3s ease; 
    .revision-header {
        padding: 16px;
        border-bottom: 1px solid #e8e8e8; 
    }
    .revision-list {
        padding: 8px;

        .revision-item {
            background: white;
            border: 1px solid #e8e8e8;
            border-radius: 6px;
            margin-bottom: 12px;
            padding: 12px;
            cursor: pointer;
            transition: all 0.2s ease;

            &:hover {
                border-color: #1890ff;
                box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
            }

            &.active {
                border-color: #1890ff;
                background: #e6f7ff;
            }

            &.type-add {
                border-left: 4px solid #52c41a;
            }

            &.type-delete {
                border-left: 4px solid #ff4d4f;
            }

            &.type-modify {
                border-left: 4px solid #fa8c16;
            }

            &.type-risk {
                border-left: 4px solid #ff4d4f;
            }

            .revision-item-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;

                .page-info {
                    font-size: 12px;
                    color: #666;
                }
            }

            .revision-item-content {
                margin-bottom: 12px;

                .label {
                    font-size: 12px;
                    color: #666;
                    font-weight: 500;
                }

                .text {
                    font-size: 13px;
                    line-height: 1.4;
                    margin-left: 4px;

                    &.deleted {
                        background: #fff2f0;
                        color: #cf1322;
                        text-decoration: line-through;
                        padding: 2px 4px;
                        border-radius: 2px;
                    }

                    &.added {
                        background: #f6ffed;
                        color: #389e0d;
                        padding: 2px 4px;
                        border-radius: 2px;
                    }

                    &.risk {
                        background: #fff2f0;
                        color: #cf1322;
                        padding: 2px 4px;
                        border-radius: 2px;
                        font-weight: 500;
                    }
                }

                .original-text,
                .suggested-text,
                .review-item-name,
                .scene-desc,
                .risk-tip {
                    margin-bottom: 6px;
                }
            }

            .revision-item-actions {
                margin-bottom: 8px;
            }

            .legal-sources {
                margin-top: 8px;
                font-size: 12px;

                .label {
                    font-weight: 500;
                    color: #666;
                    margin-bottom: 6px;
                    display: block;
                }

                .legal-source-item {
                    background: #f8f9fa;
                    padding: 8px;
                    border-radius: 4px;
                    margin-bottom: 6px;
                    border-left: 3px solid #1890ff;

                    .source-title {
                        font-weight: 500;
                        color: #1890ff;
                        margin-bottom: 4px;
                        font-size: 12px;
                    }

                    .source-desc {
                        color: #666;
                        line-height: 1.4;
                        font-size: 11px;
                    }
                }
            }
        }
    } 
}
</style>
