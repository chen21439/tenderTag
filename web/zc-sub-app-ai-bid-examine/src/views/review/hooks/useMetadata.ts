import { ref } from 'vue'

export interface Metadata {
  filename: string
  stage1_gt_status: boolean
  stage2_gt_status: boolean
  stage3_gt_status: boolean
  infer_range?: number[]
  infer_completed?: boolean
}

export const useMetadata = () => {
  const loading = ref(false)

  /**
   * 获取文件的 metadata
   */
  const getMetadata = async (runName: string, filename: string): Promise<Metadata | null> => {
    try {
      loading.value = true
      const timestamp = Date.now()
      const response = await fetch(
        `http://localhost:3000/api/runs/metadata?runName=${runName}&filename=${filename}&t=${timestamp}`
      )
      const result = await response.json()

      if (result.success && result.metadata) {
        return result.metadata
      }
      return null
    } catch (error) {
      console.error('❌ 获取 metadata 失败:', error)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 检查文件是否有推理后版本
   */
  const hasInferVersion = (metadata: Metadata | null): boolean => {
    return metadata?.infer_completed === true
  }

  /**
   * 检查所有 stage 是否都已完成
   */
  const isAllStagesCompleted = (metadata: Metadata | null): boolean => {
    if (!metadata) return false
    return (
      metadata.stage1_gt_status === true &&
      metadata.stage2_gt_status === true &&
      metadata.stage3_gt_status === true
    )
  }

  /**
   * 获取未完成的 stages
   */
  const getMissingStages = (metadata: Metadata | null): string[] => {
    if (!metadata) return []

    const missing: string[] = []
    if (!metadata.stage1_gt_status) missing.push('Stage1')
    if (!metadata.stage2_gt_status) missing.push('Stage2')
    if (!metadata.stage3_gt_status) missing.push('Stage3')

    return missing
  }

  return {
    loading,
    getMetadata,
    hasInferVersion,
    isAllStagesCompleted,
    getMissingStages
  }
}
