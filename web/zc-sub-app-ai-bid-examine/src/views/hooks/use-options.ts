// 评审状态 1:评审中，2：评审结束 3：评审失败
export const statusMap : Record<number|string,string>= {
  1: '评审中',
  2: '评审完成',
  3: '评审失败'
}
// 表格表头
export const tableColumns = [
  {
    title: '项目名称',
    dataIndex: 'projectName',
    align: 'left',
    width: '30%',
    ellipsis: true
  },
  {
    title: '包号',
    dataIndex: 'packageId',
    align: 'left',
    width: '20%',
    ellipsis: true
  },
  {
    title: '状态',
    dataIndex: 'status',
    align: 'left',
    width: '15%',
    ellipsis: true 
  },
  {
    title: '开始时间',
    dataIndex: 'startTime',
    align: 'left',
    width: '20%',
    ellipsis: true
  },
  {
      title: '操作',
      dataIndex: 'operation',
      fixed: 'right',
      width: '15%'
  }
]

// 是否启用状态
export const checkPointStatusMap: Record<number|string,any> = {
  0: {
    label: '否',
    color: 'var(--error-6)'
  },
  1: {
    label: '是',
    color:'var(--success-6)'
  }
}