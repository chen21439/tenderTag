import path from 'path'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { createSvgIconsPlugin } from 'vite-plugin-svg-icons'
import Components from 'unplugin-vue-components/vite'
import { AntDesignVueResolver } from 'unplugin-vue-components/resolvers'
import type { ImportMetaEnv } from './src/typings/env'
import topLevelAwait from 'vite-plugin-top-level-await'
import htmlPlugin from 'vite-plugin-index-html'
import dayjs from 'dayjs'
function setupPlugins(env: ImportMetaEnv): any[] {
  const plugins =  [
    vue(),
    topLevelAwait(),// env.VITE_ENV !== 'dev' &&
    htmlPlugin({
      input: './src/main.ts',
      preserveEntrySignatures: 'exports-only'
    }),
    Components({
      resolvers: [
        AntDesignVueResolver({
          importStyle: false // css in js
        })
      ]
    }),
    createSvgIconsPlugin({
      iconDirs: [path.resolve(process.cwd(), 'src/assets/svgs')], // svg 图标保存的位置
      symbolId: 'icon-[name]', // 指定symbolId格式
      svgoOptions: {
        plugins: [
          // {
          //   name: 'removeAttrs',
          //   params: { attrs: ['class', 'data-name', 'fill', 'stroke'] }
          // }
        ]
      }
    })
  ]
  return plugins
}

export default defineConfig(env => {
  const viteEnv = loadEnv(env.mode, process.cwd()) as unknown as ImportMetaEnv
  const version = `V6.1.EXAMINE.1_${dayjs().format('YYYYMMDD_HH_mm')}`
  return {
    resolve: {
      alias: {
        '@': path.resolve(process.cwd(), 'src')
      }
    },
    plugins: setupPlugins(viteEnv),
    base: viteEnv.VITE_APP_PUBLIC_URL,
    header: {
      'Access-Control-Allow-Origin': '*'
    },
    server: {
      host: '0.0.0.0',
      port: 9801,
      // origin: viteEnv.VITE_ENV === 'dev' ? viteEnv.VITE_SUB_APP_AI_CHAT : '',
      open: false,
      hmr: true,
      proxy: {
        // '/to_sub_app_bid_examine': {
        //   target: 'https://sppgpttest.gcycloud.cn/to_sub_app_bid_examine/',
        //   changeOrigin: true
        // },
        '/api': {
          target: 'https://sppgpttest.gcycloud.cn',
          changeOrigin: true
        },
        '/compliance': {
          target: 'https://sppgpttest.gcycloud.cn',
          changeOrigin: true
        },
        '/bid': {
          target: 'https://sppgpttest.gcycloud.cn',
          changeOrigin: true
        },
        '/auth': {
          target: 'https://sppgpttest.gcycloud.cn',
          changeOrigin: true
        },
        '/file': {
          target: 'https://sppgpttest.gcycloud.cn',
          changeOrigin: true
        },
        '/sftp': {
          target: 'https://sppgpttest.gcycloud.cn',
          changeOrigin: true
        },
        '/static-resources': {
          target: 'https://sppgpttest.gcycloud.cn',
          changeOrigin: true
        }
      }
    },
    build: {
      reportCompressedSize: false,
      sourcemap: false,
      commonjsOptions: {
        ignoreTryCatch: false
      },
      minify : 'terser' ,
      terserOptions : {
        compress : {
            // test 环境保留 console 以便调试
            drop_console : viteEnv.VITE_ENV !== 'test',
            drop_debugger : true
        }
      },
      rollupOptions: {
        output: {
          chunkFileNames: 'assets/js/[name]-[hash].js',
          entryFileNames: 'assets/js/[name]-[hash].js',
          assetFileNames: 'assets/[ext]/[name]-[hash].[ext]',
          manualChunks(id: string) {
            const independentChunks = ['tailwindcss','ant-design-vue','echarts']
            const chunkVue = ['@vue', 'vue-router', 'pinia', 'axios']
            if (id.includes('node_modules')) {
              const moduleName = id?.toString()?.split('node_modules/')[1]?.split('/')[0]?.toString()
              if (chunkVue.includes(moduleName)) {
                return 'chunk-vue'
              }else if (independentChunks.includes(moduleName)) {
                return 'chunk-' + moduleName
              } else {
                return 'vendor-' + version
              }
            }
          }
        }
      }
    }
  }
})
