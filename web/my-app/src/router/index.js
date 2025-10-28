import { createRouter, createWebHistory } from 'vue-router'
import PdfContentViewer from '../views/pdf/PdfContentViewer.vue'
import PdfViewer from '../views/pdf/PdfViewer.vue'
import SectionsViewer from '../views/SectionsViewer.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
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
    }
  ],
})

export default router
