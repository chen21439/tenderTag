import { createRouter, createWebHashHistory } from 'vue-router'
import PdfContentViewer from '../views/pdf/PdfContentViewer.vue'
import PdfViewer from '../views/pdf/PdfViewer.vue'
import SectionsViewer from '../views/SectionsViewer.vue'
import SectionHeaderPreview from '../views/sectionHeaderPreview/index.vue'
import PaperTreeViewer from '../views/tree/index.vue'

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'PdfContentViewer',
      component: PdfContentViewer
    },
    {
      path: '/pdf-viewer',
      name: 'PdfViewer',
      component: PdfViewer
    },
    {
      path: '/sections',
      name: 'SectionsViewer',
      component: SectionsViewer
    },
    {
      path: '/section-header-preview',
      name: 'SectionHeaderPreview',
      component: SectionHeaderPreview
    },
    {
      path: '/tree',
      name: 'PaperTreeViewer',
      component: PaperTreeViewer
    },
    { path: '/:pathMatch(.*)*', redirect: '/' }
  ],
})

export default router
