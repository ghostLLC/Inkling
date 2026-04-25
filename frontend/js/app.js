/**
 * Inkling 前端 - API 对接层
 * 
 * API 端点（FastAPI 版）:
 *   POST /api/sessions             创建会话 { topic: str }
 *   POST /api/sessions/{id}/messages 发送消息 { session_id: str, message: str }
 *   GET  /api/sessions/{id}        获取会话信息
 *   GET  /health                   健康检查
 */
const API_BASE = window.location.origin;
let sessionId = null;
let currentMode = '审题';

async function startSession() {
    const topic = document.getElementById('topicInput').value.trim();
    if (!topic) {
        document.getElementById('setupError').textContent = '请输入作文题目';
        return;
    }
    
    try {
        const res = await fetch(`${API_BASE}/api/sessions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic })
        });
        const data = await res.json();
        
        if (data.session_id) {
            sessionId = data.session_id;
            document.getElementById('setupPanel').style.display = 'none';
            document.getElementById('chatPanel').style.display = 'block';
            document.getElementById('sessionInfo').textContent = `题目: ${topic}`;
            
            // 自动发送题目
            await sendMessageInternal(`题目是《${topic}》`);
        }
    } catch (e) {
        document.getElementById('setupError').textContent = '连接失败，请检查服务器是否运行';
    }
}

async function sendQuick(text) {
    if (!sessionId) return;
    document.getElementById('messageInput').value = text;
    await sendMessage();
}

async function sendMessage() {
    const input = document.getElementById('messageInput');
    const text = input.value.trim();
    if (!text || !sessionId) return;
    
    input.value = '';
    addMessage(text, 'user');
    
    await sendMessageInternal(text);
}

async function sendMessageInternal(text) {
    const typing = document.getElementById('typingIndicator');
    typing.classList.add('active');
    document.getElementById('sendBtn').disabled = true;
    
    try {
        const res = await fetch(`${API_BASE}/api/sessions/${sessionId}/messages`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, message: text })
        });
        
        const data = await res.json();
        
        typing.classList.remove('active');
        
        // 显示 AI 回复
        const modeMap = {
            'TOPIC_ANALYSIS': '审题',
            'STUCK_RESCUE': '卡壳救援',
            'ENDING_GUIDE': '结尾收束',
            'COMPLETE': '完成'
        };
        currentMode = modeMap[data.task_mode] || data.task_mode;
        document.getElementById('modeInfo').textContent = `模式: ${currentMode}`;
        
        // 状态标签
        let meta = '';
        if (data.stuck_type) meta += `卡壳: ${data.stuck_type} | `;
        if (data.current_level) meta += `层级: L${data.current_level} | `;
        if (data.cool_down) meta += '💡冷却中';
        
        addMessage(data.ai_response, 'ai', meta);
        
        // 更新快捷按钮
        updateChips(data.task_mode, data.cool_down);
        
    } catch (e) {
        typing.classList.remove('active');
        addMessage('抱歉，连接出错了。请刷新页面重试。', 'ai');
    } finally {
        document.getElementById('sendBtn').disabled = false;
    }
}

function addMessage(text, role, meta = '') {
    const chatArea = document.getElementById('chatArea');
    const div = document.createElement('div');
    div.className = `message ${role}`;
    
    const metaHtml = meta ? `<div class="meta">${meta}</div>` : '';
    div.innerHTML = `<div class="bubble">${escapeHtml(text).replace(/\n/g, '<br>')}${metaHtml}</div>`;
    
    chatArea.insertBefore(div, document.getElementById('typingIndicator'));
    chatArea.scrollTop = chatArea.scrollHeight;
}

function updateChips(mode, coolDown) {
    const chips = document.getElementById('suggestionChips');
    
    if (coolDown) {
        chips.innerHTML = '<span class="chip" onclick="sendQuick(\'我写好了\')">我写好了</span>';
        return;
    }
    
    if (mode === 'TOPIC_ANALYSIS') {
        chips.innerHTML = `
            <span class="chip" onclick="sendQuick('开始写了')">开始写了</span>
            <span class="chip" onclick="sendQuick('我想写帮妈妈洗碗')">帮妈妈洗碗</span>
        `;
    } else if (mode === 'STUCK_RESCUE') {
        chips.innerHTML = `
            <span class="chip" onclick="sendQuick('还是不会')">还是不会</span>
            <span class="chip" onclick="sendQuick('还是不懂')">还是不懂</span>
            <span class="chip" onclick="sendQuick('正文写完了，不会结尾')">不会结尾</span>
        `;
    } else if (mode === 'ENDING_GUIDE') {
        chips.innerHTML = `
            <span class="chip" onclick="sendQuick('我选感悟式')">感悟式</span>
            <span class="chip" onclick="sendQuick('我选呼应式')">呼应式</span>
            <span class="chip" onclick="sendQuick('写完了')">写完了</span>
        `;
    } else {
        chips.innerHTML = '';
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
