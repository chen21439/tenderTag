import express from 'express'
import { readFileSync, readdirSync } from 'fs'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'
import cors from 'cors'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const app = express()
const PORT = 3001

// 启用 CORS
app.use(cors())

const FILE_ID = '1978018096320905217'
const TASK_DIR = join(__dirname, `../../pdf/task/${FILE_ID}`)
const TASK_ROOT = join(__dirname, '../../../docxServer/pdf/task') // task 根目录

// 静态文件服务：提供 PDF 文件访问
app.use('/pdf', express.static(join(__dirname, '../../pdf')))

// 获取目录中所有 step 文件的信息
app.get('/api/files-info', (req, res) => {
  try {
    const files = readdirSync(TASK_DIR)

    // 匹配 step 文件：{fileId}_step{N}_{timestamp}.json
    const stepFilePattern = new RegExp(`^${FILE_ID}_step(\\d+)_(\\d{8}_\\d{6})\\.json$`)

    const stepFiles = files
      .filter(file => stepFilePattern.test(file))
      .map(file => {
        const match = file.match(stepFilePattern)
        return {
          filename: file,
          step: parseInt(match[1]),
          timestamp: match[2]
        }
      })

    // 按 step 分组，找出每个 step 的最新文件
    const stepMap = {}
    stepFiles.forEach(file => {
      if (!stepMap[file.step] || file.timestamp > stepMap[file.step].timestamp) {
        stepMap[file.step] = file
      }
    })

    // 转换为数组并排序
    const latestFiles = Object.values(stepMap).sort((a, b) => a.step - b.step)

    res.json({
      fileId: FILE_ID,
      totalSteps: latestFiles.length,
      files: latestFiles
    })
  } catch (error) {
    console.error('Error reading directory:', error)
    res.status(500).json({ error: 'Failed to read directory', message: error.message })
  }
})

// 获取指定 step 的数据（最新时间戳）
app.get('/api/step-data/:step', (req, res) => {
  try {
    const step = parseInt(req.params.step)

    // 获取该 step 的所有文件
    const files = readdirSync(TASK_DIR)
    const stepFilePattern = new RegExp(`^${FILE_ID}_step${step}_(\\d{8}_\\d{6})\\.json$`)

    const stepFiles = files
      .filter(file => stepFilePattern.test(file))
      .map(file => {
        const match = file.match(stepFilePattern)
        return {
          filename: file,
          timestamp: match[1]
        }
      })
      .sort((a, b) => b.timestamp.localeCompare(a.timestamp))

    if (stepFiles.length === 0) {
      return res.status(404).json({ error: `Step ${step} not found` })
    }

    // 读取最新的文件
    const latestFile = stepFiles[0]
    const jsonPath = join(TASK_DIR, latestFile.filename)
    const jsonData = readFileSync(jsonPath, 'utf-8')
    const data = JSON.parse(jsonData)

    res.json({
      ...data,
      _meta: {
        step,
        filename: latestFile.filename,
        timestamp: latestFile.timestamp
      }
    })
  } catch (error) {
    console.error('Error reading JSON file:', error)
    res.status(500).json({ error: 'Failed to load data', message: error.message })
  }
})

// 获取目录下的任意文件（PDF、JSON 等）
app.get('/api/pdf/:filename', (req, res) => {
  try {
    const filename = req.params.filename
    const filePath = join(TASK_DIR, filename)

    console.log('Requesting file:', filePath)

    // 根据文件扩展名设置 Content-Type
    const ext = filename.split('.').pop().toLowerCase()
    const contentTypeMap = {
      'pdf': 'application/pdf',
      'json': 'application/json',
      'txt': 'text/plain',
      'html': 'text/html',
      'xml': 'application/xml'
    }

    const contentType = contentTypeMap[ext] || 'application/octet-stream'
    res.setHeader('Content-Type', contentType)
    res.setHeader('Access-Control-Allow-Origin', '*')

    // 直接发送文件
    res.sendFile(filePath, (err) => {
      if (err) {
        console.error('Error sending file:', err)
        res.status(404).json({ error: 'File not found', filename })
      }
    })
  } catch (error) {
    console.error('Error loading file:', error)
    res.status(500).json({ error: 'Failed to load file', message: error.message })
  }
})

// 获取 taskList.json（任务列表）
app.get('/api/task-list', (req, res) => {
  try {
    const taskListPath = join(TASK_ROOT, 'taskList.json')
    console.log('Reading taskList.json from:', taskListPath)

    const jsonData = readFileSync(taskListPath, 'utf-8')
    const data = JSON.parse(jsonData)

    res.json(data)
  } catch (error) {
    console.error('Error reading taskList.json:', error)
    res.status(500).json({ error: 'Failed to load task list', message: error.message })
  }
})

// 获取指定任务的文件（支持访问 task/{taskId}/ 下的任意文件）
app.get('/api/task/:taskId/:filename', (req, res) => {
  try {
    const { taskId, filename } = req.params
    const filePath = join(TASK_ROOT, taskId, filename)

    console.log('Requesting task file:', filePath)

    // 根据文件扩展名设置 Content-Type
    const ext = filename.split('.').pop().toLowerCase()
    const contentTypeMap = {
      'pdf': 'application/pdf',
      'json': 'application/json',
      'txt': 'text/plain',
      'html': 'text/html',
      'xml': 'application/xml'
    }

    const contentType = contentTypeMap[ext] || 'application/octet-stream'
    res.setHeader('Content-Type', contentType)
    res.setHeader('Access-Control-Allow-Origin', '*')

    // 直接发送文件
    res.sendFile(filePath, (err) => {
      if (err) {
        console.error('Error sending file:', err)
        res.status(404).json({ error: 'File not found', taskId, filename })
      }
    })
  } catch (error) {
    console.error('Error loading file:', error)
    res.status(500).json({ error: 'Failed to load file', message: error.message })
  }
})

// 专用路由：读取"国土空间规划实施监测网络建设项目"目录的 table.json 和 paragraph.json
const PROJECT_DIR = join(TASK_ROOT, '鄂尔多斯市政府网站群集约化平台升级改造项目')

// 获取所有 table.json 文件列表（按时间戳排序）
app.get('/api/content/table/list', (req, res) => {
  try {
    const files = readdirSync(PROJECT_DIR)
    const tableFilePattern = /_table(_\d{8}_\d{6})?\.json$/

    const tableFiles = files
      .filter(file => tableFilePattern.test(file))
      .map(file => {
        const timestampMatch = file.match(/_table_(\d{8}_\d{6})\.json$/)
        return {
          filename: file,
          timestamp: timestampMatch ? timestampMatch[1] : '00000000_000000'
        }
      })
      .sort((a, b) => b.timestamp.localeCompare(a.timestamp))

    res.json({
      files: tableFiles,
      total: tableFiles.length
    })
  } catch (error) {
    console.error('Error listing table files:', error)
    res.status(500).json({ error: 'Failed to list table files', message: error.message })
  }
})

// 获取指定时间戳的 table.json
app.get('/api/content/table/:timestamp', (req, res) => {
  try {
    const timestamp = req.params.timestamp
    const files = readdirSync(PROJECT_DIR)

    // 查找匹配的文件
    const targetFile = files.find(file => file.includes(`_table_${timestamp}.json`))

    if (!targetFile) {
      return res.status(404).json({ error: 'Table file not found for timestamp', timestamp })
    }

    const filePath = join(PROJECT_DIR, targetFile)
    console.log(`Requesting table.json with timestamp: ${timestamp}`)

    res.setHeader('Content-Type', 'application/json; charset=utf-8')
    res.setHeader('Access-Control-Allow-Origin', '*')

    const jsonData = readFileSync(filePath, 'utf-8')
    const data = JSON.parse(jsonData)
    data._meta = {
      filename: targetFile,
      timestamp: timestamp
    }
    res.json(data)
  } catch (error) {
    console.error('Error loading table.json:', error)
    res.status(500).json({ error: 'Failed to load table.json', message: error.message })
  }
})

app.get('/api/content/table', (req, res) => {
  try {
    // 读取目录中所有 table 相关的 JSON 文件
    const files = readdirSync(PROJECT_DIR)

    // 匹配模式：*_table.json 或 *_table_*.json（带时间戳）
    const tableFilePattern = /_table(_\d{8}_\d{6})?\.json$/

    const tableFiles = files
      .filter(file => tableFilePattern.test(file))
      .map(file => {
        // 提取时间戳（如果有）
        const timestampMatch = file.match(/_table_(\d{8}_\d{6})\.json$/)
        return {
          filename: file,
          timestamp: timestampMatch ? timestampMatch[1] : '00000000_000000'
        }
      })
      .sort((a, b) => b.timestamp.localeCompare(a.timestamp)) // 降序排序，最新的在前

    if (tableFiles.length === 0) {
      console.error('No table JSON files found in:', PROJECT_DIR)
      return res.status(404).json({ error: 'No table JSON files found' })
    }

    // 使用最新的文件
    const latestFile = tableFiles[0]
    const filePath = join(PROJECT_DIR, latestFile.filename)

    console.log(`Requesting latest table.json: ${latestFile.filename} (timestamp: ${latestFile.timestamp})`)

    res.setHeader('Content-Type', 'application/json; charset=utf-8')
    res.setHeader('Access-Control-Allow-Origin', '*')

    // 读取JSON并添加时间戳元数据
    const jsonData = readFileSync(filePath, 'utf-8')
    const data = JSON.parse(jsonData)
    data._meta = {
      filename: latestFile.filename,
      timestamp: latestFile.timestamp
    }
    res.json(data)
  } catch (error) {
    console.error('Error loading table.json:', error)
    res.status(500).json({ error: 'Failed to load table.json', message: error.message })
  }
})

app.get('/api/content/paragraph', (req, res) => {
  try {
    // 读取目录中所有 paragraph 相关的 JSON 文件
    const files = readdirSync(PROJECT_DIR)

    // 匹配模式：*_paragraph.json 或 *_paragraph_*.json（带时间戳）
    const paragraphFilePattern = /_paragraph(_\d{8}_\d{6})?\.json$/

    const paragraphFiles = files
      .filter(file => paragraphFilePattern.test(file))
      .map(file => {
        // 提取时间戳（如果有）
        const timestampMatch = file.match(/_paragraph_(\d{8}_\d{6})\.json$/)
        return {
          filename: file,
          timestamp: timestampMatch ? timestampMatch[1] : '00000000_000000'
        }
      })
      .sort((a, b) => b.timestamp.localeCompare(a.timestamp)) // 降序排序，最新的在前

    if (paragraphFiles.length === 0) {
      console.error('No paragraph JSON files found in:', PROJECT_DIR)
      return res.status(404).json({ error: 'No paragraph JSON files found' })
    }

    // 使用最新的文件
    const latestFile = paragraphFiles[0]
    const filePath = join(PROJECT_DIR, latestFile.filename)

    console.log(`Requesting latest paragraph.json: ${latestFile.filename} (timestamp: ${latestFile.timestamp})`)

    res.setHeader('Content-Type', 'application/json; charset=utf-8')
    res.setHeader('Access-Control-Allow-Origin', '*')

    // 读取JSON并添加时间戳元数据
    const jsonData = readFileSync(filePath, 'utf-8')
    const data = JSON.parse(jsonData)
    data._meta = {
      filename: latestFile.filename,
      timestamp: latestFile.timestamp
    }
    res.json(data)
  } catch (error) {
    console.error('Error loading paragraph.json:', error)
    res.status(500).json({ error: 'Failed to load paragraph.json', message: error.message })
  }
})

// 获取 section headers 数据
app.get('/api/section-headers', (req, res) => {
  try {
    const sectionHeaderPath = join(__dirname, '../../modelTrain/transformers/examples/pytorch/text-classification/Docling/docling_output/output_20251107_112226_sectionHeader.json')
    console.log('Reading section headers from:', sectionHeaderPath)

    res.setHeader('Content-Type', 'application/json; charset=utf-8')
    res.setHeader('Access-Control-Allow-Origin', '*')

    const jsonData = readFileSync(sectionHeaderPath, 'utf-8')
    const data = JSON.parse(jsonData)

    res.json(data)
  } catch (error) {
    console.error('Error loading section headers:', error)
    res.status(500).json({ error: 'Failed to load section headers', message: error.message })
  }
})

// 兼容旧接口
app.get('/api/step2-data', (req, res) => {
  req.params.step = '2'
  return app._router.handle(req, res)
})


app.listen(PORT, () => {
  console.log(`API Server running at http://localhost:${PORT}`)
  console.log(`Step API: http://localhost:${PORT}/api/step2-data`)
  console.log(`Task List: http://localhost:${PORT}/api/task-list`)
  console.log(`Task File: http://localhost:${PORT}/api/task/{taskId}/{filename}`)
  console.log(`Content Table: http://localhost:${PORT}/api/content/table`)
  console.log(`Content Paragraph: http://localhost:${PORT}/api/content/paragraph`)
  console.log(`Section Headers: http://localhost:${PORT}/api/section-headers`)
  console.log(`PDF (legacy): http://localhost:${PORT}/api/pdf/1978018096320905217_highlighted.pdf`)
})
