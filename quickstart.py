#!/usr/bin/env python3
"""
AI 写作卡壳救援助手 - 单文件快速体验版
只需要这一个文件，安装 openai 后即可运行。

用法:
  export OPENAI_API_KEY="你的API Key"
  export OPENAI_BASE_URL="https://api.deepseek.com/v1"
  export OPENAI_MODEL="deepseek-chat"
  python3 quickstart.py

然后打开浏览器访问 http://localhost:8080
"""

import os
import sys
import json
import uuid
import re
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# ==================== 配置 ====================
API_KEY = os.environ.get("OPENAI_API_KEY", "")
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
MODEL = os.environ.get("OPENAI_MODEL", "deepseek-chat")

# ==================== 核心引擎（内联） ====================

class TaskMode:
    TOPIC_ANALYSIS = "TOPIC_ANALYSIS"
    STUCK_RESCUE = "STUCK_RESCUE"
    ENDING_GUIDE = "ENDING_GUIDE"
    COMPLETE = "COMPLETE"

class GuideLevel:
    L1_DIRECTION = 1
    L2_STRUCTURE = 2
    L3_KEYWORDS = 3
    L4_EXAMPLES = 4

class StuckType:
    TYPE_1_PLOT = "情节推进卡"
    TYPE_2_DETAIL = "细节展开卡"
    TYPE_3_TRANSITION = "过渡衔接卡"
    TYPE_4_EMOTION = "情感表达卡"
    TYPE_5_PARAGRAPH = "段落结构卡"
    TYPE_6_PSYCHOLOGY = "心理描写卡"

class SessionState:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.topic = ""
        self.task_mode = TaskMode.TOPIC_ANALYSIS
        self.current_level = GuideLevel.L1_DIRECTION
        self.current_stuck_type = None
        self.stuck_count = 0
        self.written_content = ""
        self.has_introduction = False
        self.has_body = False
        self.has_ending = False
        self.conversation_history = []
    
    def add_message(self, role, content):
        self.conversation_history.append({"role": role, "content": content, "timestamp": datetime.now().isoformat()})
    
    def advance_level(self):
        self.stuck_count += 1
        if self.current_level < GuideLevel.L4_EXAMPLES:
            self.current_level += 1
    
    def reset_level(self):
        self.current_level = GuideLevel.L1_DIRECTION
        self.stuck_count = 0
        self.current_stuck_type = None
    
    def should_cool_down(self):
        return self.stuck_count >= 3
    
    def complete_topic_analysis(self):
        self.task_mode = TaskMode.STUCK_RESCUE
        self.reset_level()
    
    def start_ending_guide(self):
        self.task_mode = TaskMode.ENDING_GUIDE
        self.reset_level()
    
    def complete_writing(self):
        self.task_mode = TaskMode.COMPLETE
    
    def update_written_content(self, content):
        self.written_content = content
        paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
        total_chars = len(content.replace('\n', '').replace(' ', ''))
        if len(paragraphs) >= 1 or total_chars > 30:
            self.has_introduction = True
        if len(paragraphs) >= 2 or total_chars > 80:
            self.has_body = True
        if len(paragraphs) >= 3 or total_chars > 150:
            self.has_ending = True

class StuckClassifier:
    KEYWORDS = {
        StuckType.TYPE_1_PLOT: ["不知道写什么了", "后面怎么写", "接下来呢", "接下来", "接下来写什么", "不知道该怎么继续", "写不下去了", "没思路了", "不知道怎么发展", "故事怎么继续", "情节怎么推进", "不知道发生什么", "然后怎么办"],
        StuckType.TYPE_2_DETAIL: ["不知道怎么描写", "太笼统了", "怎么写细一点", "怎么写具体", "怎么展开", "不够详细", "细节怎么写", "画面感", "描写", "怎么写得生动", "怎么加细节", "不知道怎么描述", "不够具体"],
        StuckType.TYPE_3_TRANSITION: ["不知道怎么接", "两段之间", "过渡", "衔接", "接不上", "怎么转", "跳转", "上下文", "连接起来", "连贯"],
        StuckType.TYPE_4_EMOTION: ["不知道怎么表达感情", "情感", "感受", "情绪", "感动", "不知道怎么写感受", "心情怎么写", "表达不出", "感情不够"],
        StuckType.TYPE_5_PARAGRAPH: ["段落", "结构", "这一段", "不知道怎么分段", "段落结构", "层次", "条理", "逻辑", "组织"],
        StuckType.TYPE_6_PSYCHOLOGY: ["心理", "内心", "想法", "脑子", "心里", "不知道怎么写心理", "心理活动", "思绪", "心情变化"],
    }
    ENDING_KEYWORDS = ["结尾", "不会结尾", "结尾怎么写", "怎么收束", "怎么结束", "不会收", "结尾卡了"]
    
    def classify(self, user_input, written_content=""):
        user_lower = user_input.lower()
        for stuck_type, keywords in self.KEYWORDS.items():
            if self._contains_any(user_lower, keywords):
                return stuck_type, 0.8
        return StuckType.TYPE_1_PLOT, 0.3
    
    def _contains_any(self, text, keywords):
        return any(kw in text for kw in keywords)

SYSTEM_PROMPT = """你是初中生的写作陪练助手，名字叫"写作小救星"。

## 核心使命
在学生写作卡壳时，通过分层引导帮助其恢复思路、继续独立完成作文。

## 绝对禁止（底线）
1. 不得输出可被学生直接复制粘贴提交的完整句子或段落
2. 不得直接续写学生的正文（不可以把学生的文章接着写下去）
3. 不得在第一轮直接给出完整答案或完整提纲
4. 不得使用专业写作术语（如"铺垫"、"高潮"、"叙事结构"等），改用初中生能懂的说法

## 必须遵守的分层原则
每次回复只能暴露一个层级，学生追问后才解锁下一层：

- L1 方向引导：只给 2-3 个展开方向，用问句或选项呈现。不给结构、不给关键词、不给示例句。
- L2 结构提示：在学生确定方向后，给出段落内部的功能安排。不给具体词语。
- L3 关键词启发：只给零散的词语或短词组（2-4个字）。不要组成完整句子，不要给句式模板。
- L4 示例句：最多给 1 个不完整的句式骨架（如："那一刻，我才明白，原来____"）。必须注明"这是骨架，用你的内容填空"。

## 冷却机制（强制）
如果同一卡壳点学生已经求助了 3 次以上（当前层级达到 L4），必须停止提供任何新内容，只回复：
"💡 我们已经把这一步拆解得比较细了。建议你先根据刚才的提示，自己试着写2-3句话。写完之后如果还觉得不对，我们再一起看。写作不是一次就写对的，是先写出来再改对的。"

## 交互风格
- 称呼学生为"你"，自称"我"
- 语气：鼓励但不纵容，有帮助但不代劳
- 每次回复末尾可加一句轻量鼓励
- 不啰嗦，不教育人

## 输出格式
- 不输出 markdown 表格
- 用自然段落、短句、项目符号（→）呈现选项
- 关键提示用 📌 标记"""

class LLMProvider:
    def chat(self, system_prompt, user_prompt):
        raise NotImplementedError
    @property
    def name(self):
        return "Base"

class MockProvider(LLMProvider):
    @property
    def name(self):
        return "Mock"
    def chat(self, system_prompt, user_prompt):
        if "审题立意" in system_prompt or "审题" in user_prompt:
            return "这个题目有两个关键词值得关注：\n\n1. \"那一刻\" —— 提示你需要聚焦到一个具体的瞬间\n2. \"长大了\" —— 提示这件事要体现你的某种转变或领悟\n\n现在，你有没有一个具体的瞬间可以写？"
        elif "冷却" in system_prompt or ("stuck_count" in system_prompt and "3" in system_prompt):
            return "💡 我们已经把这一步拆解得比较细了。建议你先根据刚才的提示，自己试着写2-3句话。写完之后如果还觉得不对，我们再一起看。写作不是一次就写对的，是先写出来再改对的。✍️"
        elif "结尾" in system_prompt:
            return "我读了你的正文，故事已经很完整了。结尾有几种常见的收束方式：\n\n1. 【感悟式】—— 直接说出这件事让你明白了什么\n2. 【呼应式】—— 回到开头写的那个场景/物件，形成对照\n3. 【行动式】—— 结尾不写感悟，而是写你接下来做的一个具体动作\n\n你倾向哪一种？"
        else:
            return "别着急，卡住很正常。你现在卡在哪个部分了？是不知道写什么，还是不知道怎么写细？告诉我，我帮你一步步来。"

class DeepSeekProvider(LLMProvider):
    def __init__(self, api_key, model, base_url):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
    
    @property
    def name(self):
        return f"DeepSeek-{self.model}"
    
    def chat(self, system_prompt, user_prompt):
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=600
            )
            return response.choices[0].message.content
        except ImportError:
            return "[缺少 openai SDK，请运行：pip install openai]"
        except Exception as e:
            return f"[API 调用失败: {str(e)}]"

def create_provider():
    if API_KEY and BASE_URL:
        return DeepSeekProvider(API_KEY, MODEL, BASE_URL)
    return MockProvider()

# ==================== 会话管理器 ====================

class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.classifier = StuckClassifier()
        self.llm = create_provider()
    
    def create_session(self, topic=None):
        sid = str(uuid.uuid4())[:8]
        session = SessionState(sid)
        if topic:
            session.topic = topic
        self.sessions[sid] = session
        return sid
    
    def process(self, sid, user_input):
        session = self.sessions.get(sid)
        if not session:
            return {"status": "error", "ai_response": "会话不存在"}
        
        session.add_message("user", user_input)
        
        if session.task_mode == TaskMode.TOPIC_ANALYSIS:
            result = self._handle_topic(session, user_input)
        elif session.task_mode == TaskMode.STUCK_RESCUE:
            result = self._handle_stuck(session, user_input)
        elif session.task_mode == TaskMode.ENDING_GUIDE:
            result = self._handle_ending(session, user_input)
        else:
            result = {"ai_response": "你已经写完啦！很棒。下次卡壳了再叫我。✍️", "status": "ok"}
        
        session.add_message("assistant", result["ai_response"])
        result.update({
            "session_id": sid,
            "task_mode": session.task_mode,
            "current_level": session.current_level,
            "stuck_type": session.current_stuck_type,
            "cool_down": session.should_cool_down(),
        })
        return result
    
    def _handle_topic(self, session, user_input):
        completion_signals = ["开始写了", "我知道了", "明白了", "懂了", "开始写", "动笔了"]
        if any(s in user_input for s in completion_signals) and len(session.conversation_history) >= 2:
            session.complete_topic_analysis()
            return {"ai_response": "好的，开始写吧！记住：先写出自己的想法，卡住了随时叫我。我在旁边陪写。✍️", "status": "ok"}
        
        system = SYSTEM_PROMPT + "\n\n## 当前模式：审题立意辅助\n你正在帮助学生理解作文题目，找到写作方向。通过提问引导学生思考，不要直接给完整立意。"
        context = f"作文题目：{session.topic}\n" if session.topic else ""
        prompt = f"{context}学生当前输入：{user_input}\n\n请根据审题立意策略回复。"
        return {"ai_response": self.llm.chat(system, prompt), "status": "ok"}
    
    def _handle_stuck(self, session, user_input):
        if self.classifier._contains_any(user_input.lower(), self.classifier.ENDING_KEYWORDS):
            if session.has_body:
                session.start_ending_guide()
                return self._handle_ending(session, user_input)
            return {"ai_response": "正文好像还没写完？先把中间的故事写完，我们再一起看结尾。需要我帮你推进情节吗？", "status": "ok"}
        
        if any(s in user_input for s in ["写完了", "完成了", "搞定了"]) and "不会" not in user_input:
            session.complete_writing()
            return {"ai_response": "写完了？不错。先自己读一遍，看看通不通顺。如果还有时间，可以想想：开头和结尾有没有呼应？题目有没有点到位？\n\n这次写作就到这里。下次卡壳了，我还在。✍️🔥", "status": "ok"}
        
        if len(user_input) > 50 and "题目" not in user_input:
            session.update_written_content(user_input)
        
        if session.stuck_count == 0 or session.current_stuck_type is None:
            stuck_type, _ = self.classifier.classify(user_input, session.written_content)
            session.current_stuck_type = stuck_type
            session.current_level = GuideLevel.L1_DIRECTION
            session.stuck_count = 0
        
        if session.should_cool_down():
            session.reset_level()
            return {"ai_response": "💡 我们已经把这一步拆解得比较细了。建议你先根据刚才的提示，自己试着写2-3句话。写完之后如果还觉得不对，我们再一起看。写作不是一次就写对的，是先写出来再改对的。✍️", "status": "ok"}
        
        if any(s in user_input for s in ["还是不会", "还是不懂", "还是不知道", "还是卡"]):
            session.advance_level()
        
        system = SYSTEM_PROMPT + f"\n\n## 当前模式：写作中途卡壳救援\n\n### 当前状态\n- 卡壳类型：{session.current_stuck_type}\n- 当前引导层级：L{session.current_level}（共4层）\n- 当前卡壳点已求助次数：{session.stuck_count}\n- 冷却状态：{'已激活' if session.should_cool_down() else '未激活'}\n\n### 引导层级规则\nL1：只给2-3个方向选项\nL2：只给结构安排\nL3：只给零散词语（2-4字）\nL4：最多1个句式骨架\n\n### 冷却机制\n{'已激活 - 必须停止给新内容' if session.should_cool_down() else '未激活'}"
        
        context = f"作文题目：{session.topic}\n\n" if session.topic else ""
        if session.written_content:
            context += f"学生已写内容：\n{session.written_content[:500]}\n\n"
        prompt = f"{context}学生卡壳描述：{user_input}\n\n请根据分层引导策略回复。"
        return {"ai_response": self.llm.chat(system, prompt), "status": "ok"}
    
    def _handle_ending(self, session, user_input):
        if any(s in user_input for s in ["写完了", "完成了"]) and "不会" not in user_input and "怎么" not in user_input:
            session.complete_writing()
            return {"ai_response": "写完了？不错。先自己读一遍，看看通不通顺。如果还有时间，可以想想：开头和结尾有没有呼应？题目有没有点到位？\n\n这次写作就到这里。下次卡壳了，我还在。✍️🔥", "status": "ok"}
        
        system = SYSTEM_PROMPT + "\n\n## 当前模式：结尾收束辅助\n学生正文已写完，需要帮助其完成结尾。提供5种结尾策略供选择：感悟式、呼应式、留白式、行动式、对话式。不提供完整结尾段落。"
        context = f"作文题目：{session.topic}\n\n学生已写全文：\n{session.written_content[:600]}\n\n"
        prompt = f"{context}学生当前需求：{user_input}\n\n请帮助选择结尾策略并给出引导。"
        return {"ai_response": self.llm.chat(system, prompt), "status": "ok"}

manager = SessionManager()

# ==================== HTTP 服务器 ====================

HTML_PAGE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI 写作卡壳救援助手</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;display:flex;justify-content:center;align-items:center;padding:20px}
.container{width:100%;max-width:600px;background:white;border-radius:20px;box-shadow:0 20px 60px rgba(0,0,0,0.3);overflow:hidden}
.header{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);padding:30px;text-align:center;color:white}
.header h1{font-size:24px;margin-bottom:8px}
.header p{font-size:14px;opacity:.9}
.chat-area{height:400px;overflow-y:auto;padding:20px;background:#f8f9fa}
.message{margin-bottom:16px;animation:fadeIn .3s ease}
@keyframes fadeIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
.message.user{text-align:right}
.message.ai{text-align:left}
.bubble{display:inline-block;max-width:80%;padding:12px 16px;border-radius:18px;font-size:14px;line-height:1.6;word-wrap:break-word}
.message.user .bubble{background:#667eea;color:white;border-bottom-right-radius:4px}
.message.ai .bubble{background:white;color:#333;border-bottom-left-radius:4px;box-shadow:0 2px 8px rgba(0,0,0,.1)}
.bubble .meta{font-size:11px;color:#999;margin-top:6px;text-align:right}
.input-area{padding:20px;background:white;border-top:1px solid #eee;display:flex;gap:10px}
.input-area input{flex:1;padding:12px 16px;border:2px solid #e0e0e0;border-radius:25px;font-size:14px;outline:none}
.input-area input:focus{border-color:#667eea}
.input-area button{padding:12px 24px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:25px;font-size:14px;cursor:pointer}
.input-area button:disabled{opacity:.5;cursor:not-allowed}
.typing{display:none;padding:12px 16px;font-size:14px;color:#999}
.typing.active{display:block}
.setup-panel{padding:30px;text-align:center}
.setup-panel h2{font-size:20px;margin-bottom:20px;color:#333}
.setup-panel input{width:100%;padding:12px 16px;margin-bottom:12px;border:2px solid #e0e0e0;border-radius:10px;font-size:14px}
.setup-panel button{padding:14px 40px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:25px;font-size:16px;cursor:pointer}
.status-bar{padding:8px 20px;background:#f0f0f0;font-size:12px;color:#666;display:flex;justify-content:space-between}
.suggestion-chips{display:flex;gap:8px;flex-wrap:wrap;padding:0 20px 10px}
.chip{padding:6px 14px;background:#f0f0f0;border-radius:15px;font-size:13px;color:#667eea;cursor:pointer}
.chip:hover{background:#e0e0e0}
</style>
</head>
<body>
<div class="container">
<div class="header"><h1>📝 写作小救星</h1><p>AI 写作卡壳救援助手</p></div>
<div id="setupPanel" class="setup-panel">
<h2>开始写作</h2>
<p style="color:#666;margin-bottom:20px;font-size:14px">输入作文题目，AI 会在你卡壳时给你引导</p>
<input type="text" id="topicInput" placeholder="例如：那一刻，我长大了" value="那一刻，我长大了">
<button onclick="startSession()">开始</button>
</div>
<div id="chatPanel" style="display:none">
<div class="status-bar"><span id="sessionInfo">题目: -</span><span id="modeInfo">模式: 审题</span></div>
<div class="chat-area" id="chatArea"><div class="typing" id="typingIndicator">🤖 AI 正在思考...</div></div>
<div class="suggestion-chips" id="suggestionChips">
<span class="chip" onclick="sendQuick(\'开始写了\')">开始写了</span>
<span class="chip" onclick="sendQuick(\'还是不会\')">还是不会</span>
<span class="chip" onclick="sendQuick(\'正文写完了，不会结尾\')">不会结尾</span>
</div>
<div class="input-area">
<input type="text" id="messageInput" placeholder="输入你想说的..." onkeypress="if(event.key===\'Enter\')sendMessage()">
<button id="sendBtn" onclick="sendMessage()">发送</button>
</div>
</div>
</div>
<script>
const API_BASE=window.location.origin;
let sessionId=null;
async function startSession(){
const topic=document.getElementById("topicInput").value.trim();
if(!topic){alert("请输入作文题目");return}
const res=await fetch(API_BASE+"/api/create_session",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({topic})});
const data=await res.json();
if(data.session_id){sessionId=data.session_id;document.getElementById("setupPanel").style.display="none";document.getElementById("chatPanel").style.display="block";document.getElementById("sessionInfo").textContent="题目: "+topic;await sendMessageInternal("题目是《"+topic+"》")}
}
async function sendQuick(text){if(!sessionId)return;document.getElementById("messageInput").value=text;await sendMessage()}
async function sendMessage(){const input=document.getElementById("messageInput");const text=input.value.trim();if(!text||!sessionId)return;input.value="";addMessage(text,"user");await sendMessageInternal(text)}
async function sendMessageInternal(text){
document.getElementById("typingIndicator").classList.add("active");document.getElementById("sendBtn").disabled=true;
try{const res=await fetch(API_BASE+"/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({session_id:sessionId,message:text})});
const data=await res.json();document.getElementById("typingIndicator").classList.remove("active");
const modeMap={"TOPIC_ANALYSIS":"审题","STUCK_RESCUE":"卡壳救援","ENDING_GUIDE":"结尾收束","COMPLETE":"完成"};
document.getElementById("modeInfo").textContent="模式: "+(modeMap[data.task_mode]||data.task_mode);
let meta="";if(data.stuck_type)meta+="卡壳: "+data.stuck_type+" | ";if(data.current_level)meta+="层级: L"+data.current_level+" | ";if(data.cool_down)meta+="💡冷却中";
addMessage(data.ai_response,"ai",meta);updateChips(data.task_mode,data.cool_down);
}catch(e){document.getElementById("typingIndicator").classList.remove("active");addMessage("抱歉，连接出错了。","ai")}
document.getElementById("sendBtn").disabled=false;
}
function addMessage(text,role,meta=""){
const chatArea=document.getElementById("chatArea");const div=document.createElement("div");div.className="message "+role;
const metaHtml=meta?'<div class="meta">'+meta+"</div>":"";
div.innerHTML='<div class="bubble">'+escapeHtml(text).replace(/\\n/g,"<br>")+metaHtml+"</div>";
chatArea.insertBefore(div,document.getElementById("typingIndicator"));chatArea.scrollTop=chatArea.scrollHeight;
}
function updateChips(mode,coolDown){
const chips=document.getElementById("suggestionChips");
if(coolDown){chips.innerHTML='<span class="chip" onclick="sendQuick(\'我写好了\')">我写好了</span>';return}
if(mode==="TOPIC_ANALYSIS"){chips.innerHTML='<span class="chip" onclick="sendQuick(\'开始写了\')">开始写了</span><span class="chip" onclick="sendQuick(\'我想写帮妈妈洗碗\')">帮妈妈洗碗</span>'}
else if(mode==="STUCK_RESCUE"){chips.innerHTML='<span class="chip" onclick="sendQuick(\'还是不会\')">还是不会</span><span class="chip" onclick="sendQuick(\'还是不懂\')">还是不懂</span><span class="chip" onclick="sendQuick(\'正文写完了，不会结尾\')">不会结尾</span>'}
else if(mode==="ENDING_GUIDE"){chips.innerHTML='<span class="chip" onclick="sendQuick(\'我选感悟式\')">感悟式</span><span class="chip" onclick="sendQuick(\'我选呼应式\')">呼应式</span><span class="chip" onclick="sendQuick(\'写完了\')">写完了</span>'}
else{chips.innerHTML=""}
}
function escapeHtml(text){const div=document.createElement("div");div.textContent=text;return div.innerHTML}
</script>
</body>
</html>'''

class APIHandler(BaseHTTPRequestHandler):
    def _set_headers(self, ct="application/json"):
        self.send_response(200)
        self.send_header("Content-type", ct)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def do_OPTIONS(self): self._set_headers()
    
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            self._set_headers()
            self.wfile.write(json.dumps({"status": "ok", "provider": manager.llm.name}).encode())
        elif path == "/":
            self._set_headers("text/html")
            self.wfile.write(HTML_PAGE.encode())
        else:
            self.send_response(404); self.end_headers()
    
    def do_POST(self):
        path = urlparse(self.path).path
        body = self.rfile.read(int(self.headers.get('Content-Length', 0))).decode()
        try:
            data = json.loads(body)
        except:
            self._set_headers(); self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode()); return
        
        if path == "/api/create_session":
            sid = manager.create_session(data.get("topic"))
            self._set_headers()
            self.wfile.write(json.dumps({"session_id": sid, "topic": data.get("topic"), "status": "created"}).encode())
        elif path == "/api/chat":
            result = manager.process(data.get("session_id", ""), data.get("message", ""))
            self._set_headers()
            self.wfile.write(json.dumps(result).encode())
        else:
            self.send_response(404); self.end_headers()
    
    def log_message(self, format, *args): pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("", port), APIHandler)
    print(f"\n🚀 服务器启动: http://localhost:{port}")
    print(f"📖 打开浏览器访问即可体验")
    print(f"🔌 当前 LLM: {manager.llm.name}")
    if manager.llm.name == "Mock":
        print(f"⚠️  当前使用 Mock 模式（无真实 AI），配置环境变量以连接 DeepSeek")
    print(f"\n按 Ctrl+C 停止\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n已停止")
