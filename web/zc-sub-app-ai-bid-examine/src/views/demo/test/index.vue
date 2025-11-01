<template>
    <div class="document-editor-wrapper">
        <div class="document-editor-container">
            <DocumentEditor
                v-if="isComponentReady"
                id="docEditor"
                document-server-url="http://172.16.0.198:9066/"
                :config="config"
                :events="config.events"
                :on-load-component-error="onLoadComponentError"
            />
            <div v-else class="loading">
                正在加载文档编辑器...
                <!-- 9066自动化，9070社区版 -->
            </div>
        </div>
        <div class="suggestion-panel"> 
            <div class="suggestion-list">
                <a-button type="primary" @click="testJumpPage(10)">跳转页码</a-button>
                <a-button type="primary" @click="testHighlight(
                    {
                    page:2,position:[{
                    page: 3,
                    x1: 77, y1: 249, x2: 536, y2: 279
                }]})">跳转2页，第4页有高亮选区</a-button>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue';
import { DocumentEditor } from '@onlyoffice/document-editor-vue';
import { message } from 'ant-design-vue';
import CryptoJS from 'crypto-js'; 
const isComponentReady = ref(false);
const docEditorInstance = ref<any>(null);
// onlyoffice配置
const config = reactive({
    document: {
        fileType: 'docx',
        key: 'demo_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
        title: '测试文件.docx',
        // url: 'https://sppgpttest.gcycloud.cn/sftp/file/test/default/20250721/1947172506146705408/测试文件.docx',
        url:'http://172.16.0.116:8090/files/test.docx',
        permissions: {
            edit: true,
            download: true,
            print: true,
            review: true,
            comment: true
        }
    },
    documentType: 'word',
    token: '' as string, // JWT token
    editorConfig: {
        mode: 'edit',
        lang: 'zh-CN',
        customization: {
            autosave: false,
            forcesave: true,
            features: {
                spellcheck: false,
                ruler: true,
                pageNavigation: false,
                leftMenu: false,
                rightMenu: false,
                header: true,
                footer: true
            }
        },
        user: {
            id: 'user_' + Date.now(),
            name: '测试用户'
        },
        // 添加回调URL
        callbackUrl: "http://172.16.0.198:18000/callback"
    },
    events: {
        onAppReady: (event: any) => { 
        },
        onDocumentReady: (event: any) => {
            console.log('文档加载成功', event);
            // 获取文档编辑器实例
            if (event && event.target) {
                docEditorInstance.value = event.target;
                console.log('文档编辑器实例已获取:', docEditorInstance.value);
            } else {
                console.error('无法获取文档编辑器实例');
            }
        },
        onError: (event: any) => {
            console.error('OnlyOffice错误:', event);
        },
        onInfo: (event: any) => {
            // console.log('OnlyOffice信息:', event);
        }
    }
}); 

const onLoadComponentError = (errorCode: number, errorDescription: string) => {
    console.error('OnlyOffice错误:', errorCode, errorDescription);
    
    if (errorCode === -2) {
        message.error('文档服务器连接失败，请检查服务器地址');
    } else if (errorCode === -3) {
        message.error('文档安全令牌错误，请联系管理员');
    } else {
        message.error(`文档编辑器错误: ${errorDescription}`);
    }
};
// 测试页码跳转功能
const testJumpPage = async (page: number) => {
    console.log(`跳转到第${page}页`); 
};

// 测试高亮功能
const testHighlight = async (data: any) => {
    console.log(`跳转到第${data.page}页并高亮选区`, data); 
};


// JWT令牌生成
const setupJWT = () => {
    const payload = {
        document: config.document,
        documentType: config.documentType,
        editorConfig: config.editorConfig,
        height: "100%",
        width: "100%"
    };
    
    // 使用与docs/index.html相同的密钥
    const secret = 'jwt@bos6688';
    config.token = createJWT(payload, secret);
};

/**
 * 生成 ONLYOFFICE 需要的 JWT（HS256）
 * @param {object} payload  ONLYOFFICE 配置对象
 * @param {string} secret   与 ONLYOFFICE 服务端一致的密钥
 * @returns {string} 标准 JWT
 */
const createJWT = (payload: any, secret: string): string => {
    if (!secret) return '';

    const header = { alg: 'HS256', typ: 'JWT' };
    const headerEnc = base64url(JSON.stringify(header));
    const payloadEnc = base64url(JSON.stringify(payload));

    const signature = CryptoJS.HmacSHA256(`${headerEnc}.${payloadEnc}`, secret);
    const signatureEnc = signature.toString(CryptoJS.enc.Base64)
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=/g, '');

    return `${headerEnc}.${payloadEnc}.${signatureEnc}`;
};

/**
 * Base64URL编码
 * @param {string} data 要编码的数据
 * @returns {string} Base64URL编码后的字符串
 */
const base64url = (data: string): string => {
    // 使用CryptoJS进行Base64编码
    const base64 = CryptoJS.enc.Base64.stringify(
        CryptoJS.enc.Utf8.parse(data)
    );
    
    // 转换为Base64URL格式
    return base64
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=/g, '');
}; 

onMounted(async () => {
    // 生成JWT令牌
    setupJWT(); 
    nextTick(() => {
        isComponentReady.value = true;
    });
});

// 组件卸载时清理监听器
onUnmounted(() => { 
});
</script>

<style scoped>
.document-editor-wrapper {
    display: flex;
    width: 100%;
    height: 100vh;
}

.document-editor-container {
    flex: 1;
    height: 100vh;
    position: relative;
    border-right: 1px solid #e8e8e8;
}

.loading {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    font-size: 16px;
    color: #666;
}

#docEditor {
    width: 100%;
    height: 100%;
}

.suggestion-panel {
    width: 350px;
    height: 100vh;
    overflow-y: auto;
    background-color: #f9f9f9;
    padding: 16px;
    box-sizing: border-box;
}

.suggestion-panel h3 {
    margin-top: 0;
    margin-bottom: 16px;
    font-size: 18px;
    color: #333;
    border-bottom: 1px solid #e8e8e8;
    padding-bottom: 8px;
} 

.suggestion-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.suggestion-item {
    background-color: white;
    border-radius: 4px;
    padding: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    cursor: pointer;
    transition: all 0.3s;
    border: 1px solid #e8e8e8;
}

.suggestion-item:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.suggestion-item.active {
    border-color: #1890ff;
    background-color: #e6f7ff;
}

.suggestion-content {
    margin-bottom: 12px;
}

.suggestion-title {
    font-weight: bold;
    margin-bottom: 8px;
    color: #333;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.suggestion-status {
    font-size: 12px;
    padding: 2px 8px;
    border-radius: 12px;
    font-weight: normal;
}

.suggestion-status.pending {
    background-color: #fff7e6;
    color: #fa8c16;
    border: 1px solid #ffd591;
}

.suggestion-status.accepted {
    background-color: #f6ffed;
    color: #52c41a;
    border: 1px solid #b7eb8f;
}

.suggestion-status.rejected {
    background-color: #fff2f0;
    color: #ff4d4f;
    border: 1px solid #ffccc7;
}

.suggestion-text {
    font-size: 14px;
    color: #666;
}

.original-text, .suggested-text {
    margin-bottom: 4px;
    word-break: break-all;
}

.original-text {
    color: #ff4d4f;
    text-decoration: line-through;
}

.suggested-text {
    color: #52c41a;
}

.location {
    font-size: 12px;
    color: #999;
    margin-top: 8px;
    line-height: 1.4;
}

.location > div {
    margin-bottom: 2px;
}

.suggestion-actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
}

.accept-btn, .reject-btn {
    padding: 4px 12px;
    border-radius: 4px;
    border: none;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.3s;
}

.accept-btn {
    background-color: #52c41a;
    color: white;
}

.accept-btn:hover {
    background-color: #73d13d;
}

.reject-btn {
    background-color: #f5f5f5;
    color: #666;
}

.reject-btn:hover {
    background-color: #e8e8e8;
}
</style>

