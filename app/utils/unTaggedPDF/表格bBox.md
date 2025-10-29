  1. 使用的方法

  page.find_tables(table_settings={
      "vertical_strategy": "lines",
      "horizontal_strategy": "lines",
      "intersection_x_tolerance": 3,
      "intersection_y_tolerance": 3
  })

  2. pdfplumber 的实现机制

  调用链：
  page.find_tables()
    ↓
  TableFinder(page, settings)
    ↓
  1. self.edges = self.get_edges()           # 从 page.edges 提取线段
  2. self.intersections = edges_to_intersections()  # 计算交点
  3. self.cells = intersections_to_cells()   # 生成单元格
  4. self.tables = cells_to_tables()         # 分组成表格

  关键步骤：
  - get_edges()：当策略是 "lines" 时，直接使用 page.edges
  - page.edges：从 PDF 底层数据结构中读取的原始线段坐标

  3. 为什么会有跨页坐标？

  根本原因：PDF 文件本身存储的坐标就是跨页的！

  验证结果：
  第4页：96个edges，其中30个跨页坐标
  第5页：48个edges，全部48个都是跨页坐标！
  第15页：96个edges，其中60个跨页坐标

  原因分析：
  1. 这个PDF是从DOCX转换来的
  2. 转换工具（Word或其他）对跨页表格使用了累积坐标系统
  3. PDF规范允许这种坐标变换（通过坐标矩阵）
  4. pdfplumber 忠实地读取了这些原始坐标

  4. 为什么第4-23页是同一个表格却被分开？

  因为 pdfplumber 是按页处理的：
  - 每个 page 对象只能访问当前页的内容
  - page.find_tables() 只在当前页内查找表格
  - 即使PDF底层坐标是跨页的，每一页也会独立检测出一个"表格"

  实际情况：
  - PDF底层：第4-23页是一个整体表格（线段连续，坐标累积）
  - pdfplumber：每一页独立检测，返回20个"表格"对象（每页一个）

  结论

  你的方案是正确的：
  - 保留 raw_bbox：记录PDF原始的跨页坐标（珍贵的几何信息）
  - 生成 bbox：裁剪到当前页面 [x0, max(0, y0), x1, min(842, y1)]
  - 用于文本提取：避免提取到其他页的内容（包括页码标记）


● 理解 pdfplumber 的实现机制

  使用的方法

  page.find_tables(table_settings={
      "vertical_strategy": "lines",
      "horizontal_strategy": "lines",
      ...
  })

  实现流程

  1. find_tables() → TableFinder(page, settings)
  2. TableFinder.__init__() 的步骤：
  self.edges = self.get_edges()          # 1. 提取边缘线段
  self.intersections = edges_to_intersections(...)  # 2. 计算交点
  self.cells = intersections_to_cells(...)  # 3. 生成单元格
  self.tables = cells_to_tables(self.cells)  # 4. 将cells分组成表格
  3. cells_to_tables() 的分组逻辑：
    - 遍历所有cells
    - 如果两个cell 共享至少1个角点，就归为同一个表格
    - 使用贪心算法聚合相邻的cells




  第一个大跨页表格（第4-11页）

  第4页:  跨6.93页 (约第4页 ~ 第10页)
  第5页:  跨6.91页 (约第5页 ~ 第10页)
  第6页:  跨6.91页 (约第5页 ~ 第10页)
  第7页:  跨6.91页 (约第5页 ~ 第10页)
  第8页:  跨6.91页 (约第5页 ~ 第10页)
  第9页:  跨6.91页 (约第5页 ~ 第10页)
  第10页: 跨6.91页 (约第5页 ~ 第10页)
  第11页: 跨10.13页 (约第5页 ~ 第13页) ← 看到的最多！
  实际跨页范围：第4-11页（共8页）

  第二个大跨页表格（第12-18页）

  第12页: 跨3.23页 (约第12页 ~ 第13页)
  第13页: 跨3.23页 (约第12页 ~ 第13页)
  第14页: 跨3.23页 (约第12页 ~ 第14页)
  第15页: 跨6.36页 (约第12页 ~ 第17页) ← 中心页，看到最多！
  第16页: 跨3.14页 (约第16页 ~ 第17页)
  第17页: 跨3.14页 (约第16页 ~ 第17页)
  第18页: 跨3.64页 (约第16页 ~ 第18页)
  实际跨页范围：第12-18页（共7页）

  第三个跨页表格（第24-27页）

  第24页: 跨2.42页 (约第24页 ~ 第25页)
  第25页: 跨1.12页 (约第25页 ~ 第25页)
  第26页: 跨2.77页 (约第25页 ~ 第26页)
  第27页: 跨0.64页 (约第27页 ~ 第27页)
  实际跨页范围：第24-27页（共4页）

  关键发现

  1. 中心页现象：
    - 第11页（在第4-11页表格中）：看到10.13页
    - 第15页（在第12-18页表格中）：看到6.36页
    - 这些"中心页"看到的跨度最大，因为它们在表格的几何中心
  2. 边缘页现象：
    - 表格的起始页和结束页看到的跨度较小
    - 第27页只跨0.64页（接近结束）
  3. pdfplumber的检测机制：
    - 每一页都能检测到表格的线段
    - 线段形成的bbox会累积跨页的y坐标
    - 导致每页都有一个"观察到的跨页范围"
