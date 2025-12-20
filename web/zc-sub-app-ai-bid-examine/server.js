const express = require('express')
const path = require('path')
const cors = require('cors')
const fs = require('fs')

const app = express()
const PORT = process.env.PORT || 3000

// PDF文件目录
const PDF_DIR = 'E:\\models\\data\\Section\\tender_document\\pdf'
// JSON文件目录
const JSON_DIR = 'E:\\models\\data\\Section\\tender_document\\json'
// Runs目录（存放时间戳文件夹）
const RUNS_DIR = 'E:\\models\\data\\Section\\tender_document\\runs'

// 启用CORS
app.use(cors())

// 静态文件服务 - 提供PDF访问
app.use('/pdf', express.static(PDF_DIR, {
  setHeaders: (res, filePath) => {
    if (filePath.endsWith('.pdf')) {
      res.set('Content-Type', 'application/pdf')
      res.set('Content-Disposition', 'inline')
    }
  }
}))

// 健康检查
app.get('/health', (req, res) => {
  res.json({ status: 'ok', pdfDir: PDF_DIR })
})

// 列出所有PDF文件（可选）
app.get('/api/pdf/list', (req, res) => {
  fs.readdir(PDF_DIR, (err, files) => {
    if (err) {
      return res.status(500).json({ error: err.message })
    }
    const pdfFiles = files.filter(f => f.endsWith('.pdf'))
    res.json({ files: pdfFiles })
  })
})

// 根据文件名获取对应的JSON数据
app.get('/api/json/:filename', (req, res) => {
  const requestedFileName = req.params.filename

  // 如果请求的是 .pdf 文件，将其转换为 .json
  const jsonFileName = requestedFileName.replace(/\.pdf$/i, '.json')

  // 直接尝试读取JSON文件
  const jsonPath = path.join(JSON_DIR, jsonFileName)

  fs.readFile(jsonPath, 'utf8', (err, data) => {
    if (err) {
      // 如果直接匹配失败，尝试模糊匹配
      fs.readdir(JSON_DIR, (err, files) => {
        if (err) {
          return res.status(500).json({ error: err.message })
        }

        // 移除扩展名用于模糊匹配
        const baseName = jsonFileName.replace(/\.json$/i, '')

        // 查找匹配的JSON文件（支持带前缀的文件名，如 [GMCG2025000093-A]）
        const jsonFile = files.find(f => {
          if (!f.endsWith('.json')) return false
          // 尝试多种匹配方式
          const fileBaseName = f.replace(/\.json$/i, '')
          // 1. 精确匹配
          if (fileBaseName === baseName) return true
          // 2. 移除方括号前缀后匹配
          const cleanName = f.replace(/^\[.*?\]/, '').replace(/\.json$/i, '')
          if (cleanName === baseName) return true
          // 3. 包含匹配
          if (f.includes(baseName)) return true
          return false
        })

        if (!jsonFile) {
          return res.status(404).json({
            error: 'JSON文件未找到',
            requestedFileName,
            jsonFileName,
            baseName,
            availableFiles: files.filter(f => f.endsWith('.json')).slice(0, 10)
          })
        }

        const matchedJsonPath = path.join(JSON_DIR, jsonFile)
        fs.readFile(matchedJsonPath, 'utf8', (err, data) => {
          if (err) {
            return res.status(500).json({ error: err.message })
          }
          try {
            const jsonData = JSON.parse(data)
            res.json({
              fileName: jsonFile,
              data: jsonData,
              total: jsonData.length || 0
            })
          } catch (parseErr) {
            res.status(500).json({ error: 'JSON解析失败', details: parseErr.message })
          }
        })
      })
      return
    }

    // 直接匹配成功
    try {
      const jsonData = JSON.parse(data)
      res.json({
        fileName: jsonFileName,
        data: jsonData,
        total: jsonData.length || 0
      })
    } catch (parseErr) {
      res.status(500).json({ error: 'JSON解析失败', details: parseErr.message })
    }
  })
})

// 列出所有JSON文件
app.get('/api/json/list', (req, res) => {
  fs.readdir(JSON_DIR, (err, files) => {
    if (err) {
      return res.status(500).json({ error: err.message })
    }
    const jsonFiles = files.filter(f => f.endsWith('.json'))
    res.json({ files: jsonFiles })
  })
})

// 获取 runs 目录下的所有文件夹（时间戳列表）
app.get('/api/runs/list', (req, res) => {
  fs.readdir(RUNS_DIR, { withFileTypes: true }, (err, entries) => {
    if (err) {
      return res.status(500).json({
        error: err.message,
        path: RUNS_DIR
      })
    }

    // 筛选出文件夹，并提取时间戳
    const folders = entries
      .filter(entry => entry.isDirectory())
      .map(entry => {
        const folderName = entry.name

        // 尝试从文件夹名称中提取时间戳
        // 支持多种格式：
        // 1. 纯数字时间戳：1234567890
        // 2. 日期时间格式：20251218_095825_checkpoint-3000_9a0124
        let timestamp = null
        let dateStr = null

        // 尝试匹配 YYYYMMDD_HHMMSS 格式
        const dateMatch = folderName.match(/^(\d{8})_(\d{6})/)
        if (dateMatch) {
          const [_, datePart, timePart] = dateMatch
          // 解析为 Date 对象
          const year = datePart.substring(0, 4)
          const month = datePart.substring(4, 6)
          const day = datePart.substring(6, 8)
          const hour = timePart.substring(0, 2)
          const minute = timePart.substring(2, 4)
          const second = timePart.substring(4, 6)

          const dateObj = new Date(`${year}-${month}-${day}T${hour}:${minute}:${second}`)
          timestamp = dateObj.getTime()
          dateStr = dateObj.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
          })
        } else {
          // 尝试解析纯数字时间戳
          const numTimestamp = parseInt(folderName)
          if (!isNaN(numTimestamp) && numTimestamp > 1000000000) {
            timestamp = numTimestamp
            dateStr = new Date(numTimestamp).toLocaleString('zh-CN', {
              year: 'numeric',
              month: '2-digit',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit'
            })
          }
        }

        return {
          name: folderName,
          timestamp: timestamp,
          date: dateStr
        }
      })
      // 按时间戳降序排序（最新的在前）
      .sort((a, b) => {
        if (a.timestamp && b.timestamp) {
          return b.timestamp - a.timestamp
        }
        // 没有时间戳的按名称排序
        return b.name.localeCompare(a.name)
      })

    res.json({
      total: folders.length,
      folders: folders,
      runsDir: RUNS_DIR
    })
  })
})

// 获取指定 run 文件夹下的文件列表（支持子目录）
app.get('/api/runs/:timestamp/files', (req, res) => {
  const timestamp = req.params.timestamp
  const subPath = req.query.subPath || '' // 支持查询子目录
  const runDir = path.join(RUNS_DIR, timestamp, subPath)

  // 检查文件夹是否存在
  if (!fs.existsSync(runDir)) {
    return res.status(404).json({
      error: '文件夹不存在',
      path: runDir
    })
  }

  fs.readdir(runDir, (err, files) => {
    if (err) {
      return res.status(500).json({ error: err.message })
    }

    // 返回文件列表及其详细信息
    const fileList = files.map(fileName => {
      const filePath = path.join(runDir, fileName)
      const stats = fs.statSync(filePath)

      return {
        name: fileName,
        size: stats.size,
        isDirectory: stats.isDirectory(),
        modified: stats.mtime,
        ext: path.extname(fileName)
      }
    })

    res.json({
      timestamp,
      subPath,
      path: runDir,
      total: fileList.length,
      files: fileList
    })
  })
})

// 读取指定 run 文件夹下的 JSON 文件
// 使用查询参数支持子目录: /api/runs/:timestamp/json?file=enriched/xxx.json
app.get('/api/runs/:timestamp/json', (req, res) => {
  const timestamp = req.params.timestamp
  const filename = req.query.file || ''

  if (!filename) {
    return res.status(400).json({
      error: '缺少 file 参数',
      example: '/api/runs/:timestamp/json?file=enriched/xxx.json'
    })
  }

  const filePath = path.join(RUNS_DIR, timestamp, filename)

  fs.readFile(filePath, 'utf8', (err, data) => {
    if (err) {
      return res.status(404).json({
        error: '文件未找到',
        path: filePath
      })
    }

    try {
      const jsonData = JSON.parse(data)
      res.json({
        timestamp,
        filename,
        data: jsonData
      })
    } catch (parseErr) {
      res.status(500).json({
        error: 'JSON解析失败',
        details: parseErr.message
      })
    }
  })
})

// 修改JSON文件中的元素（本地 JSON 目录）
app.post('/api/json/update', express.json(), (req, res) => {
  const { fileName, lineId, updates } = req.body

  if (!fileName || !lineId || !updates) {
    return res.status(400).json({
      success: false,
      error: '缺少必要参数：fileName, lineId, updates'
    })
  }

  const jsonPath = path.join(JSON_DIR, fileName)

  // 读取文件
  fs.readFile(jsonPath, 'utf8', (err, data) => {
    if (err) {
      return res.status(404).json({
        success: false,
        error: `文件未找到: ${fileName}`
      })
    }

    try {
      const jsonData = JSON.parse(data)

      // 查找并更新对应的元素
      let found = false
      for (let i = 0; i < jsonData.length; i++) {
        if (jsonData[i].line_id === lineId) {
          // 更新字段
          Object.assign(jsonData[i], updates)
          found = true
          console.log(`✅ 更新元素 ${lineId}:`, updates)
          break
        }
      }

      if (!found) {
        return res.status(404).json({
          success: false,
          error: `未找到 line_id=${lineId} 的元素`
        })
      }

      // 写回文件
      fs.writeFile(jsonPath, JSON.stringify(jsonData, null, 2), 'utf8', (err) => {
        if (err) {
          return res.status(500).json({
            success: false,
            error: '写入文件失败'
          })
        }

        res.json({
          success: true,
          message: '更新成功',
          lineId,
          updates
        })
      })
    } catch (parseErr) {
      res.status(500).json({
        success: false,
        error: 'JSON解析失败'
      })
    }
  })
})

// 修改 runs 目录下的 JSON 文件中的元素
app.post('/api/runs/update', express.json(), (req, res) => {
  const { runName, fileName, id, updates } = req.body

  console.log('📝 [Runs] 收到更新请求:', { runName, fileName, id, updates })

  if (!runName || !fileName || (id === undefined && id !== 0) || !updates) {
    console.error('❌ [Runs] 缺少必要参数:', { runName, fileName, id, updates })
    return res.status(400).json({
      success: false,
      error: '缺少必要参数：runName, fileName, id, updates'
    })
  }

  const jsonPath = path.join(RUNS_DIR, runName, 'enriched', fileName)

  console.log('📂 [Runs] 读取文件:', jsonPath)

  // 读取文件
  fs.readFile(jsonPath, 'utf8', (err, data) => {
    if (err) {
      console.error('❌ [Runs] 文件读取失败:', err.message)
      return res.status(404).json({
        success: false,
        error: `文件未找到: ${jsonPath}`
      })
    }

    try {
      const jsonData = JSON.parse(data)

      // 查找并更新对应的元素（使用 id 字段）
      let found = false
      for (let i = 0; i < jsonData.length; i++) {
        if (jsonData[i].id === id) {
          // 更新字段
          Object.assign(jsonData[i], updates)
          found = true
          console.log(`✅ [Runs] 更新元素 id=${id}:`, updates)
          break
        }
      }

      if (!found) {
        console.error(`❌ [Runs] 未找到 id=${id} 的元素`)
        return res.status(404).json({
          success: false,
          error: `未找到 id=${id} 的元素`
        })
      }

      // 写回文件
      fs.writeFile(jsonPath, JSON.stringify(jsonData, null, 2), 'utf8', (err) => {
        if (err) {
          console.error('❌ [Runs] 文件写入失败:', err.message)
          return res.status(500).json({
            success: false,
            error: '写入文件失败'
          })
        }

        console.log('✅ [Runs] 文件更新成功:', jsonPath)
        res.json({
          success: true,
          message: '更新成功',
          runName,
          fileName,
          id,
          updates
        })
      })
    } catch (parseErr) {
      console.error('❌ [Runs] JSON解析失败:', parseErr.message)
      res.status(500).json({
        success: false,
        error: 'JSON解析失败'
      })
    }
  })
})

// 移动节点（更新 parent_id）
app.post('/api/runs/:timestamp/move-node', express.json(), (req, res) => {
  const timestamp = req.params.timestamp
  const { fileName, id, newParentId } = req.body

  if (!fileName || (id === undefined && id !== 0)) {
    return res.status(400).json({
      success: false,
      error: '缺少必要参数：fileName, id'
    })
  }

  const jsonPath = path.join(RUNS_DIR, timestamp, 'enriched', fileName)

  console.log(`🔄 移动节点请求:`, {
    timestamp,
    fileName,
    id,
    newParentId: newParentId || 'null (根节点)'
  })

  // 读取文件
  fs.readFile(jsonPath, 'utf8', (err, data) => {
    if (err) {
      return res.status(404).json({
        success: false,
        error: `文件未找到: ${jsonPath}`
      })
    }

    try {
      const jsonData = JSON.parse(data)

      // 查找并更新对应的元素（使用 id 字段）
      let found = false
      for (let i = 0; i < jsonData.length; i++) {
        if (jsonData[i].id === id) {
          // 更新 parent_id
          jsonData[i].parent_id = newParentId === null ? null : newParentId
          found = true
          console.log(`✅ 更新节点 id=${id} 的 parent_id: ${newParentId || 'null'}`)
          break
        }
      }

      if (!found) {
        return res.status(404).json({
          success: false,
          error: `未找到 id=${id} 的元素`
        })
      }

      // 写回文件
      fs.writeFile(jsonPath, JSON.stringify(jsonData, null, 2), 'utf8', (err) => {
        if (err) {
          return res.status(500).json({
            success: false,
            error: '写入文件失败'
          })
        }

        res.json({
          success: true,
          message: '节点移动成功',
          timestamp,
          fileName,
          id,
          newParentId
        })
      })
    } catch (parseErr) {
      res.status(500).json({
        success: false,
        error: 'JSON解析失败',
        details: parseErr.message
      })
    }
  })
})

// 批量移动节点
app.post('/api/runs/:timestamp/move-nodes', express.json(), (req, res) => {
  const timestamp = req.params.timestamp
  const { fileName, lineIds, newParentId } = req.body

  if (!fileName || !lineIds || !Array.isArray(lineIds) || lineIds.length === 0) {
    return res.status(400).json({
      success: false,
      error: '缺少必要参数：fileName, lineIds (数组)'
    })
  }

  const jsonPath = path.join(RUNS_DIR, timestamp, 'enriched', fileName)

  console.log(`🔄 批量移动节点请求:`, {
    timestamp,
    fileName,
    lineIds,
    count: lineIds.length,
    newParentId: newParentId || 'null (根节点)'
  })

  // 读取文件
  fs.readFile(jsonPath, 'utf8', (err, data) => {
    if (err) {
      return res.status(404).json({
        success: false,
        error: `文件未找到: ${jsonPath}`
      })
    }

    try {
      const jsonData = JSON.parse(data)
      let updatedCount = 0

      // 查找并更新所有匹配的元素
      for (let i = 0; i < jsonData.length; i++) {
        if (lineIds.includes(jsonData[i].line_id)) {
          jsonData[i].parent_id = newParentId === null ? null : newParentId
          updatedCount++
          console.log(`✅ 更新节点 ${jsonData[i].line_id} 的 parent_id: ${newParentId || 'null'}`)
        }
      }

      if (updatedCount === 0) {
        return res.status(404).json({
          success: false,
          error: `未找到任何匹配的节点`
        })
      }

      // 写回文件
      fs.writeFile(jsonPath, JSON.stringify(jsonData, null, 2), 'utf8', (err) => {
        if (err) {
          return res.status(500).json({
            success: false,
            error: '写入文件失败'
          })
        }

        res.json({
          success: true,
          message: `成功移动 ${updatedCount} 个节点`,
          timestamp,
          fileName,
          updatedCount,
          totalRequested: lineIds.length,
          newParentId
        })
      })
    } catch (parseErr) {
      res.status(500).json({
        success: false,
        error: 'JSON解析失败',
        details: parseErr.message
      })
    }
  })
})

app.listen(PORT, () => {
  console.log(`PDF服务器运行在 http://localhost:${PORT}`)
  console.log(`PDF目录: ${PDF_DIR}`)
  console.log(`JSON目录: ${JSON_DIR}`)
  console.log(`Runs目录: ${RUNS_DIR}`)
  console.log(`访问PDF: http://localhost:${PORT}/pdf/<filename.pdf>`)
  console.log(`访问JSON: http://localhost:${PORT}/api/json/<filename.pdf>`)
  console.log(`访问Runs列表: http://localhost:${PORT}/api/runs/list`)
  console.log(`访问Run文件: http://localhost:${PORT}/api/runs/<timestamp>/files`)
})
