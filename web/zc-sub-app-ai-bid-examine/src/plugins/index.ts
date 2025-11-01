import '@/assets/css/plugins/tailwind.css'
/** Tailwind's Preflight Style Override */
export  function naiveStyleOverride() {
  const meta = document.createElement('meta')
  meta.name = 'antd-style'
  document.head.appendChild(meta)
}
