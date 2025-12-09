/**
 * 知识图谱PPT模拟数据
 * 用于演示"从信息孤岛到知识图谱"的渐进式构建过程
 */

// 文档数据 - 3个项目 × 3种文件 = 9个文档
export const documents = [
  // 项目1：LED显示屏框架协议采购（2024-2025年度）
  {
    id: 'doc_p1_tender',
    label: 'LED显示屏\n招标文件',
    projectName: 'LED显示屏',
    docType: '招标文件',
    project: 'proj_led_screen',
    supplier: 'sup_deyun',
    year: '2025'
  },
  {
    id: 'doc_p1_bid',
    label: 'LED显示屏\n投标文件',
    projectName: 'LED显示屏',
    docType: '投标文件',
    project: 'proj_led_screen',
    supplier: 'sup_deyun',
    year: '2025'
  },
  {
    id: 'doc_p1_contract',
    label: 'LED显示屏\n合同',
    projectName: 'LED显示屏',
    docType: '合同',
    project: 'proj_led_screen',
    supplier: 'sup_deyun',
    year: '2025'
  },

  // 项目2：扫描仪框架协议采购（2025-2026年度）
  { id: 'doc_p2_tender', label: '扫描仪\n招标文件', projectName: '扫描仪', docType: '招标文件', project: 'proj_scanner', supplier: 'sup_deyun', year: '2025-2026' },
  {
    id: 'doc_p2_bid',
    label: '扫描仪\n投标文件',
    projectName: '扫描仪',
    docType: '投标文件',
    project: 'proj_scanner',
    supplier: 'sup_tech_future',
    year: '2025'
  },
  {
    id: 'doc_p2_contract',
    label: '扫描仪\n合同',
    projectName: '扫描仪',
    docType: '合同',
    project: 'proj_scanner',
    supplier: 'sup_tech_future',
    year: '2025'
  },

  // 项目3：空调机框架协议采购（2025年）
  {
    id: 'doc_p3_tender',
    label: '空调机\n招标文件',
    projectName: '空调机',
    docType: '招标文件',
    project: 'proj_air_conditioner',
    supplier: 'sup_deyun',
    year: '2024'
  },
  {
    id: 'doc_p3_bid',
    label: '空调机\n投标文件',
    projectName: '空调机',
    docType: '投标文件',
    project: 'proj_air_conditioner',
    supplier: 'sup_local_supplier',
    year: '2024'
  },
  {
    id: 'doc_p3_contract',
    label: '空调机\n合同',
    projectName: '空调机',
    docType: '合同',
    project: 'proj_air_conditioner',
    supplier: 'sup_local_supplier',
    year: '2024'
  }
]

// 项目数据
export const projects = [
  { id: 'proj_led_screen', label: 'LED显示屏框架协议\n采购项目\n(2024-2025年度)', framework: 'fa_equipment_2024' },
  { id: 'proj_scanner', label: '扫描仪框架协议\n采购项目\n(2025-2026年度)', framework: 'fa_equipment_2025' },
  { id: 'proj_air_conditioner', label: '空调机框架协议\n采购项目\n(2025年)', framework: 'fa_equipment_2025' }
]

// 供应商数据
export const suppliers = [
  { id: 'sup_deyun', label: '德云天科技' },
  { id: 'sup_tech_future', label: '未来科技' },
  { id: 'sup_local_supplier', label: '本地供应商' }
]

// 框架协议数据
export const frameworks = [
  { id: 'fa_equipment_2024', label: '2024年设备框架协议', org: 'org_sz_hc' },
  { id: 'fa_equipment_2025', label: '2025年设备框架协议', org: 'org_sz_hc' }
]

// 组织单位数据
export const organizations = [{ id: 'org_sz_hc', label: '某市政府采购中心' }]

// 履约记录数据
export const performances = [
  { id: 'perf_p1_deyun', label: 'LED-德云天履约', project: 'proj_led_screen', supplier: 'sup_deyun' },
  { id: 'perf_p2_deyun', label: '扫描仪-德云天履约', project: 'proj_scanner', supplier: 'sup_deyun' },
  { id: 'perf_p2_future', label: '扫描仪-未来科技履约', project: 'proj_scanner', supplier: 'sup_tech_future' },
  { id: 'perf_p3_local', label: '空调-本地供应商履约', project: 'proj_air_conditioner', supplier: 'sup_local_supplier' }
]

// 项目-供应商关系（中标关系）
export const projectSupplierRelations = [
  { project: 'proj_led_screen', supplier: 'sup_deyun' },
  { project: 'proj_scanner', supplier: 'sup_deyun' },
  { project: 'proj_scanner', supplier: 'sup_tech_future' },
  { project: 'proj_air_conditioner', supplier: 'sup_local_supplier' }
]

// 完整的Cytoscape元素数据（用于第二页PPT）
export const getFullGraphElements = () => {
  return [
    // 1. 组织单位
    { data: { id: 'org_sz_hc', label: '某市住建局', type: 'org', layer: 0 } },

    // 2. 框架协议
    {
      data: { id: 'fa_led_2025', label: '2025年LED城市照明框架协议', type: 'framework', layer: 1, parent: 'org_sz_hc' }
    },

    // 3. 项目
    { data: { id: 'proj_road_001', label: '市主干道智慧照明项目', type: 'project', layer: 2, parent: 'fa_led_2025' } },
    { data: { id: 'proj_square_002', label: '市政广场亮化项目', type: 'project', layer: 2, parent: 'fa_led_2025' } },

    // 4. 项目1文档
    {
      data: {
        id: 'doc_p1_tender',
        label: 'P1-招标文件',
        type: 'doc',
        docType: 'tender',
        layer: 3,
        parent: 'proj_road_001'
      }
    },
    {
      data: {
        id: 'doc_p1_eval',
        label: 'P1-评标报告',
        type: 'doc',
        docType: 'evaluation',
        layer: 3,
        parent: 'proj_road_001'
      }
    },
    {
      data: {
        id: 'doc_p1_contract',
        label: 'P1-合同文本',
        type: 'doc',
        docType: 'contract',
        layer: 3,
        parent: 'proj_road_001'
      }
    },
    {
      data: {
        id: 'doc_p1_accept',
        label: 'P1-验收报告',
        type: 'doc',
        docType: 'acceptance',
        layer: 3,
        parent: 'proj_road_001'
      }
    },

    // 5. 项目2文档
    {
      data: {
        id: 'doc_p2_tender',
        label: 'P2-招标文件',
        type: 'doc',
        docType: 'tender',
        layer: 3,
        parent: 'proj_square_002'
      }
    },
    {
      data: {
        id: 'doc_p2_eval',
        label: 'P2-评标报告',
        type: 'doc',
        docType: 'evaluation',
        layer: 3,
        parent: 'proj_square_002'
      }
    },
    {
      data: {
        id: 'doc_p2_contract',
        label: 'P2-合同文本',
        type: 'doc',
        docType: 'contract',
        layer: 3,
        parent: 'proj_square_002'
      }
    },
    {
      data: {
        id: 'doc_p2_accept',
        label: 'P2-验收报告',
        type: 'doc',
        docType: 'acceptance',
        layer: 3,
        parent: 'proj_square_002'
      }
    },

    // 6. 供应商（跨项目）
    { data: { id: 'sup_star_light', label: '星辰光电', type: 'supplier', layer: 2 } },
    { data: { id: 'sup_local_led', label: '本地照明科技', type: 'supplier', layer: 2 } },

    // 7. 履约记录
    { data: { id: 'perf_p1_star', label: 'P1-星辰光电履约', type: 'performance', layer: 3, parent: 'proj_road_001' } },
    {
      data: { id: 'perf_p2_star', label: 'P2-星辰光电履约', type: 'performance', layer: 3, parent: 'proj_square_002' }
    },
    {
      data: { id: 'perf_p2_local', label: 'P2-本地照明履约', type: 'performance', layer: 3, parent: 'proj_square_002' }
    },

    // 8. 关系边 - 项目与供应商（中标关系，关键：星辰光电跨两个项目）
    { data: { source: 'proj_road_001', target: 'sup_star_light', type: 'awardedTo' } },
    { data: { source: 'proj_square_002', target: 'sup_star_light', type: 'awardedTo' } },
    { data: { source: 'proj_square_002', target: 'sup_local_led', type: 'awardedTo' } },

    // 9. 关系边 - 履约记录与供应商
    { data: { source: 'perf_p1_star', target: 'sup_star_light', type: 'performanceOf' } },
    { data: { source: 'perf_p2_star', target: 'sup_star_light', type: 'performanceOf' } },
    { data: { source: 'perf_p2_local', target: 'sup_local_led', type: 'performanceOf' } }
  ]
}

// Cytoscape通用样式配置
export const cytoscapeStyles = [
  {
    selector: 'node',
    style: {
      label: 'data(label)',
      'text-valign': 'center',
      'text-halign': 'center',
      'text-wrap': 'wrap',
      'text-max-width': '100px',
      'font-size': '11px',
      color: '#fff',
      'background-color': '#666',
      'border-width': 2,
      'border-color': '#333'
    }
  },
  {
    selector: 'node[type="doc"]',
    style: {
      'background-color': '#fa8c16',
      'border-color': '#d46b08',
      width: 60,
      height: 60,
      'font-size': '10px',
      shape: 'rectangle'
    }
  },
  {
    selector: 'node[type="placeholder"]',
    style: {
      'background-color': '#fff',
      'border-color': '#d9d9d9',
      'border-width': 2,
      'border-style': 'solid',
      width: 60,
      height: 60,
      opacity: 1,
      shape: 'rectangle'
    }
  },
  {
    selector: 'node[type="project"]',
    style: {
      'background-color': 'rgba(114, 46, 209, 0.08)',  // 更淡的半透明背景
      'border-color': '#722ed1',
      'border-width': 2,
      'border-style': 'dashed',  // 虚线边框
      'padding': '45px',  // 恢复原来的内边距
      'text-valign': 'top',  // 标签在顶部
      'text-margin-y': -15,
      'font-size': '16px',  // 增大字体
      'font-weight': 'bold',
      'color': '#722ed1',
      shape: 'roundrectangle',
      'min-width': '160px',  // 恢复原来的最小宽度
      'min-height': '270px'  // 恢复原来的高度
    }
  },
  {
    selector: 'node[type="year"]',
    style: {
      'background-color': '#13c2c2',
      'border-color': '#08979c',
      'border-width': 2,
      width: 120,
      height: 80,
      'font-size': '14px',
      'font-weight': 'bold',
      'color': '#fff',
      shape: 'roundrectangle'
    }
  },
  {
    selector: 'node[type="org"]',
    style: {
      'background-color': '#1890ff',
      'border-color': '#096dd9',
      width: 140,
      height: 140,
      'font-size': '16px',
      'font-weight': 'bold',
      shape: 'roundrectangle'
    }
  },
  {
    selector: 'node[type="framework"]',
    style: {
      'background-color': '#52c41a',
      'border-color': '#389e0d',
      width: 120,
      height: 120,
      'font-size': '12px',
      shape: 'roundrectangle'
    }
  },
  {
    selector: 'node[type="performance"]',
    style: {
      'background-color': '#13c2c2',
      'border-color': '#08979c',
      width: 45,
      height: 45,
      'font-size': '9px',
      shape: 'triangle'
    }
  },
  {
    selector: 'edge',
    style: {
      width: 3,
      'line-color': '#d9d9d9',
      'target-arrow-color': '#d9d9d9',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier',
      'arrow-scale': 1.5
    }
  },
  {
    selector: 'edge[type="awardedTo"]',
    style: {
      'line-color': '#eb2f96',
      'target-arrow-color': '#eb2f96',
      width: 5,
      'line-style': 'solid'
    }
  },
  {
    selector: 'edge[type="performanceOf"]',
    style: {
      'line-color': '#13c2c2',
      'target-arrow-color': '#13c2c2',
      width: 3,
      'line-style': 'dashed'
    }
  },
  {
    selector: '.doc-flow',
    style: {
      'line-color': '#52c41a',
      'target-arrow-color': '#52c41a',
      'target-arrow-shape': 'triangle',
      width: 2,
      'curve-style': 'bezier',
      'line-style': 'solid',
      'arrow-scale': 1,
      'target-arrow-fill': 'filled'
    }
  },
  {
    selector: '.year-edge',
    style: {
      'line-color': '#13c2c2',
      'target-arrow-color': '#13c2c2',
      'target-arrow-shape': 'triangle',
      width: 3,
      'curve-style': 'bezier',
      'line-style': 'solid'
    }
  },
  {
    selector: '.hidden',
    style: {
      opacity: 0,
      display: 'none'
    }
  },
  {
    selector: '.visible',
    style: {
      opacity: 1
    }
  },
  {
    selector: ':parent',
    style: {
      'background-opacity': 0.1,
      'border-width': 3,
      'border-style': 'dashed',
      padding: 20
    }
  }
]
