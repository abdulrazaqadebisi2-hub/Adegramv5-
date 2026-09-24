from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json, time
from datetime import datetime

app = FastAPI()
users = {} # name -> {ws, last_seen, online}
msgs = []
pinned_id = None

HTML = """
<!DOCTYPE html><html><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Adegram Ultimate</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:system-ui,-apple-system}
body{display:flex;height:100vh;background:#0e1621;color:#fff;overflow:hidden}
.side{width:380px;background:#17212b;display:flex;flex-direction:column;border-right:1px solid #2b5278}
@media(max-width:700px){.side{width:100%}.chat{display:none}.chat.on{display:flex;width:100%}.side.hide{display:none}}
.top{padding:12px;background:#17212b;display:flex;gap:8px;align-items:center}
.top b{color:#5288c1;font-size:18px}
.top input{flex:1;padding:9px 14px;border-radius:20px;border:none;background:#242f3d;color:#fff;outline:none}
.list{flex:1;overflow-y:auto}
.item{padding:10px 12px;display:flex;gap:10px;align-items:center;cursor:pointer}
.item:hover,.item.act{background:#2b5278}
.ava{width:48px;height:48px;border-radius:50%;background:linear-gradient(135deg,#5288c1,#3ca1ff);display:grid;place-items:center;font-weight:700}
.chat{flex:1;display:flex;flex-direction:column;background:#0e1621;position:relative}
.head{height:54px;background:#17212b;display:flex;align-items:center;padding:0 10px;gap:10px;border-bottom:1px solid #242f3d}
.pin{padding:6px 12px;background:#182533;border-bottom:1px solid #2b5278;font-size:12px;display:none;align-items:center;gap:8px}
.pin.on{display:flex}
.mbox{flex:1;overflow-y:auto;padding:10px 10%;display:flex;flex-direction:column;gap:2px}
@media(max-width:700px){.mbox{padding:8px}}
.bub{max-width:68%;padding:6px 10px;border-radius:12px;font-size:14px;position:relative;cursor:pointer;word-break:break-word}
.bub.me{align-self:flex-end;background:#2b5278;border-bottom-right-radius:3px}
.bub.you{align-self:flex-start;background:#182533;border-bottom-left-radius:3px}
.bub.deleted{opacity:.5;font-style:italic}
.rep{border-left:2px solid #5288c1;background:#0003;padding:4px 6px;border-radius:4px;font-size:12px;margin-bottom:4px}
.bub img{max-width:200px;border-radius:8px;display:block;margin:4px 0}
.bub audio,.bub video{width:220px;margin:4px 0}
.meta{font-size:10px;color:#7d8b99;display:flex;justify-content:flex-end;gap:6px;margin-top:4px;align-items:center}
.react{font-size:11px;background:#242f3d;border-radius:10px;padding:1px 6px;display:inline-block;margin-top:3px}
.actMenu{position:fixed;background:#17212b;border-radius:8px;box-shadow:0 4px 20px #0008;z-index:200;overflow:hidden;display:none;min-width:160px}
.actMenu div{padding:10px 14px;font-size:13px;cursor:pointer}
.actMenu div:hover{background:#2b5278}
.input{padding:8px;background:#17212b;display:flex;align-items:flex-end;gap:6px}
.replyBar{display:none;background:#182533;padding:6px 12px;border-left:2px solid #5288c1;margin:0 8px;font-size:12px;justify-content:space-between}
.replyBar.on{display:flex}
.input textarea{flex:1;background:#242f3d;border:none;border-radius:20px;padding:10px 14px;color:#fff;outline:none;resize:none;max-height:110px}
.icon{width:42px;height:42px;border-radius:50%;border:none;background:#242f3d;color:#aaa;display:grid;place-items:center;cursor:pointer;font-size:16px}
.send{background:#5288c1;color:#fff}
.typ{font-size:11px;color:#7d8b99;height:16px;padding:0 12px}
.login{position:fixed;inset:0;background:#17212b;z-index:99;display:flex;align-items:center;justify-content:center}
.lbox{background:#0e1621;padding:26px;border-radius:12px;width:92%;max-width:340px;text-align:center}
.lbox input{width:100%;padding:11px;margin:8px 0;border-radius:8px;border:none;background:#242f3d;color:#fff;outline:none}
.lbox button{width:100%;padding:11px;background:#5288c1;border:none;border-radius:8px;color:#fff;font-weight:700;cursor:pointer}
#fileIn{display:none}
</style>
</head><body>
<div class="login" id="log"><div class="lbox"><h2 style="color:#5288c1">ADEGRAM</h2><p style="color:#7d8b99;font-size:12px;margin:6px 0 14px">Ultimate Telegram Clone</p><input id="n" placeholder="Your name"><input id="u" placeholder="@username (optional)"><button onclick="join()">START</button></div></div>

<div class="side" id="side"><div class="top"><b>Adegram</b><input id="s" placeholder="Search" oninput="filt()"></div><div class="list" id="list"></div></div>

<div class="chat" id="chat">
<div class="head"><span id="back" style="display:none;cursor:pointer;font-size:22px" onclick="showSide()">←</span><div class="ava" id="cAva">G</div><div style="flex:1"><div id="cName" style="font-weight:600">General</div><div id="cStat" style="font-size:11px;color:#7d8b99">real-time</div></div><div style="display:flex;gap:8px"><button class="icon" onclick="clearChat()" title="Clear">🗑️</button><button class="icon" id="oCnt"></button></div></div>
<div class="pin" id="pinBar"><span>📌</span><span id="pinTxt" style="flex:1"></span><span style="cursor:pointer" onclick="unpin()">✕</span></div>
<div class="mbox" id="mbox"></div>
<div class="typ" id="typ"></div>
<div class="replyBar" id="rBar"><div><div id="rWho" style="color:#5288c1;font-weight:600"></div><div id="rTxt"></div></div><span style="cursor:pointer" onclick="cancelReply()">✕</span></div>
<div class="input">
<button class="icon" onclick="document.getElementById('fileIn').click()">📎</button>
<input type="file" id="fileIn" onchange="sendFile(this)" accept="image/*,video/*,audio/*,.pdf,.zip,.doc">
<button class="icon" id="rec" onmousedown="sRec()" onmouseup="eRec()" ontouchstart="sRec()" ontouchend="eRec()">🎤</button>
<textarea id="t" rows="1" placeholder="Message" oninput="grow(this);typing()" onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();send()}"></textarea>
<button class="icon send" onclick="send()">➤</button>
</div>
</div>

<div class="actMenu" id="menu">
<div onclick="doReply()">↩️ Reply</div>
<div onclick="doReact('❤️')">❤️ Love</div>
<div onclick="doReact('😂')">😂 Haha</div>
<div onclick="doReact('🔥')">🔥 Fire</div>
<div onclick="doPin()">📌 Pin</div>
<div onclick="doForward()">➡️ Forward</div>
<div onclick="doEdit()">✏️ Edit</div>
<div onclick="doDel()" style="color:#ff5a5a">🗑️ Delete</div>
</div>

<script>
let ws, myName, cur='General', curType='group', allUsers=[], allMsgs=[], replyTo=null, selMsg=null, mRec, aChunks=[];
function join(){
 myName=document.getElementById('n').value.trim(); if(!myName)return alert('Enter name');
 document.getElementById('log').style.display='none';
 if(innerWidth<=700) document.getElementById('back').style.display='block';
 let pr=location.protocol==='https:'?'wss://':'ws://';
 ws=new WebSocket(pr+location.host+'/ws/'+encodeURIComponent(myName));
 ws.onmessage=e=>{
  let d=JSON.parse(e.data);
  if(d.type==='init'){allUsers=d.users; allMsgs=d.msgs; renderList(); allMsgs.forEach(m=>{if(showable(m)) draw(m)}); updCount(d.users); if(d.pinned) showPin(d.pinned)}
  else if(d.type==='msg'){allMsgs.push(d); if(showable(d)) draw(d)}
  else if(d.type==='users'){allUsers=d.users; renderList(); updCount(d.users)}
  else if(d.type==='typing'){if(d.from!==myName && (d.to===cur||d.to==='General')){document.getElementById('typ').innerText=d.from+' typing...'; setTimeout(()=>document.getElementById('typ').innerText='',1500)}}
  else if(d.type==='delete'){allMsgs=allMsgs.filter(m=>m.id!==d.id); document.getElementById('mbox').innerHTML=''; allMsgs.forEach(m=>{if(showable(m)) draw(m)})}
  else if(d.type==='edit'){let m=allMsgs.find(x=>x.id===d.id); if(m){m.text=d.text; m.edited=true; document.getElementById('mbox').innerHTML=''; allMsgs.forEach(x=>{if(showable(x)) draw(x)})}}
  else if(d.type==='react'){let m=allMsgs.find(x=>x.id===d.id); if(m){m.reacts=m.reacts||{}; m.reacts[d.from]=d.emoji; document.getElementById('mbox').innerHTML=''; allMsgs.forEach(x=>{if(showable(x)) draw(x)})}}
  else if(d.type==='pin'){showPin(d.msg)} else if(d.type==='unpin'){document.getElementById('pinBar').classList.remove('on')}
 };
}
function showable(m){
 if(curType==='group') return m.to==='General' || m.to===cur;
 return (m.sender===myName&&m.to===cur)||(m.sender===cur&&m.to===myName)||(m.sender===myName&&m.to===myName);
}
function updCount(u){document.getElementById('oCnt').innerText=u.length}
function renderList(f=''){
 let l=document.getElementById('list'); l.innerHTML='';
 let add=(name,sub,ico)=>{
  if(f&&!name.toLowerCase().includes(f))return;
  let d=document.createElement('div'); d.className='item'+(cur===name?' act':'');
  d.innerHTML=`<div class="ava">${ico}</div><div style="flex:1;min-width:0"><div style="font-weight:500">${name}</div><div style="font-size:12px;color:#7d8b99;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${sub}</div></div>`;
  d.onclick=()=>openChat(name); l.appendChild(d);
 };
 add('General','Group - everyone','G');
 allUsers.forEach(u=>{if(u.name!==myName) add(u.name, u.online?'online • '+u.last_seen:'offline • '+u.last_seen, u.name[0].toUpperCase())});
}
function openChat(name){
 cur=name; curType=name==='General'?'group':'private';
 document.getElementById('cName').innerText=name; document.getElementById('cAva').innerText=name[0].toUpperCase();
 document.getElementById('cStat').innerText=curType==='private'?'private • tap and hold message for actions':'group • real-time • hold message';
 document.getElementById('mbox').innerHTML=''; allMsgs.forEach(m=>{if(showable(m)) draw(m)});
 if(innerWidth<=700){document.getElementById('side').classList.add('hide');document.getElementById('chat').classList.add('on')}
}
function showSide(){document.getElementById('side').classList.remove('hide');document.getElementById('chat').classList.remove('on')}
function draw(m){
 let b=document.getElementById('mbox'); let div=document.createElement('div'); div.className='bub '+(m.sender===myName?'me':'you')+(m.deleted?' deleted':'');
 let rep=''; if(m.replyTo){let rm=allMsgs.find(x=>x.id===m.replyTo); if(rm) rep=`<div class="rep"><b>${rm.sender}</b><br>${esc((rm.text||'media').slice(0,40))}</div>`;}
 let cont=rep;
 if(m.sender!==myName && curType==='group') cont+=`<div style="font-size:11px;color:#7fc0ff;font-weight:600">${m.sender}</div>`;
 if(m.deleted) cont+='<i>deleted</i>';
 else if(m.mtype==='text') cont+=`<div>${esc(m.text)}${m.edited?' <small style="color:#7d8b99">(edited)</small>':''}</div>`;
 else if(m.mtype==='image') cont+=`<img src="${m.data}"><div>${esc(m.text||'')}</div>`;
 else if(m.mtype==='video') cont+=`<video controls src="${m.data}"></video>`;
 else if(m.mtype==='audio') cont+=`<audio controls src="${m.data}"></audio>`;
 else if(m.mtype==='file') cont+=`📄 <a href="${m.data}" download="${m.fname}" style="color:#7fc0ff">${esc(m.fname)}</a>`;
 if(m.reacts && Object.keys(m.reacts).length){let r=Object.values(m.reacts).join(' '); cont+=`<div class="react">${r}</div>`}
 cont+=`<div class="meta"><span>${m.time}</span><span>${m.sender===myName?'✓✓':''}</span></div>`;
 div.innerHTML=cont;
 div.oncontextmenu=e=>{e.preventDefault(); openMenu(e,m)}; let press;
 div.ontouchstart=e=>{press=setTimeout(()=>openMenu(e,m),600)}; div.ontouchend=()=>clearTimeout(press);
 div.onclick=()=>{if(replyTo) document.getElementById('t').focus()};
 b.appendChild(div); b.scrollTop=b.scrollHeight;
}
function esc(s){let d=document.createElement('div');d.textContent=s||'';return d.innerHTML}
function grow(el){el.style.height='';el.style.height=Math.min(el.scrollHeight,110)+'px'}
function typing(){ws.send(JSON.stringify({type:'typing',to:cur}))}
function send(){
 let el=document.getElementById('t'); let txt=el.value.trim(); if(!txt)return;
 if(selMsg && selMsg._edit){ws.send(JSON.stringify({type:'edit',id:selMsg.id,text:txt})); selMsg=null; el.value=''; document.getElementById('rBar').classList.remove('on'); return;}
 ws.send(JSON.stringify({type:'msg',mtype:'text',text:txt,to:cur,replyTo:replyTo})); el.value=''; cancelReply();
}
function sendFile(inp){
 let f=inp.files[0]; if(!f)return; if(f.size>8*1024*1024) return alert('Max 8MB');
 let r=new FileReader(); r.onload=e=>{
  let mt=f.type.startsWith('image/')?'image':f.type.startsWith('video/')?'video':f.type.startsWith('audio/')?'audio':'file';
  ws.send(JSON.stringify({type:'msg',mtype:mt,data:e.target.result,fname:f.name,text:'',to:cur,replyTo:replyTo}));
  cancelReply();
 }; r.readAsDataURL(f); inp.value='';
}
function openMenu(e,m){selMsg=m; let menu=document.getElementById('menu'); menu.style.left=(e.touches?e.touches[0].clientX:e.clientX)+'px'; menu.style.top=(e.touches?e.touches[0].clientY:e.clientY)+'px'; menu.style.display='block';}
document.addEventListener('click',()=>document.getElementById('menu').style.display='none');
function doReply(){replyTo=selMsg.id; document.getElementById('rBar').classList.add('on'); document.getElementById('rWho').innerText=selMsg.sender; document.getElementById('rTxt').innerText=(selMsg.text||'media').slice(0,40);}
function cancelReply(){replyTo=null; document.getElementById('rBar').classList.remove('on');}
function doDel(){ws.send(JSON.stringify({type:'delete',id:selMsg.id}));}
function doEdit(){if(selMsg.sender!==myName)return alert('Only your message'); selMsg._edit=true; document.getElementById('t').value=selMsg.text; document.getElementById('rBar').classList.add('on'); document.getElementById('rWho').innerText='Editing'; document.getElementById('rTxt').innerText=selMsg.text.slice(0,40);}
function doReact(em){ws.send(JSON.stringify({type:'react',id:selMsg.id,emoji:em}));}
function doPin(){ws.send(JSON.stringify({type:'pin',id:selMsg.id}));}
function unpin(){ws.send(JSON.stringify({type:'unpin'}));}
function doForward(){let to=prompt('Forward to who? Type name or General'); if(to) ws.send(JSON.stringify({type:'msg',mtype:selMsg.mtype,text:selMsg.text,data:selMsg.data,fname:selMsg.fname,to:to}));}
function showPin(m){document.getElementById('pinBar').classList.add('on'); document.getElementById('pinTxt').innerText=(m?m.sender+': '+(m.text||'media'):'Pinned');}
function clearChat(){if(confirm('Clear your view?')) document.getElementById('mbox').innerHTML='';}
function filt(){renderList(document.getElementById('s').value.toLowerCase())}
async function sRec(){
 try{let st=await navigator.mediaDevices.getUserMedia({audio:true}); mRec=new MediaRecorder(st); aChunks=[]; mRec.ondataavailable=e=>aChunks.push(e.data);
 mRec.onstop=()=>{let bl=new Blob(aChunks,{type:'audio/webm'}); let r=new FileReader(); r.onload=e=>ws.send(JSON.stringify({type:'msg',mtype:'audio',data:e.target.result,to:cur})); r.readAsDataURL(bl); st.getTracks().forEach(t=>t.stop())};
 mRec.start(); document.getElementById('rec').style.background='#ff3b30';
 }catch{}
}
function eRec(){if(mRec&&mRec.state==='recording'){mRec.stop(); document.getElementById('rec').style.background='#242f3d'}}
</script>
</body></html>
"""

@app.get("/")
async def home():
    return HTMLResponse(HTML)

@app.websocket("/ws/{name}")
async def ws_ep(websocket: WebSocket, name: str):
    await websocket.accept()
    users[name] = {"ws": websocket, "name": name, "online": True, "last_seen": datetime.now().strftime("%H:%M")}

    await websocket.send_text(json.dumps({
        "type": "init",
        "users": [{"name": u, "online": v["online"], "last_seen": v["last_seen"]} for u,v in users.items()],
        "msgs": msgs[-200:],
        "pinned": next((m for m in msgs if m["id"] == pinned_id), None)
    }))

    for u,v in users.items():
        if u!= name:
            try:
                await v["ws"].send_text(json.dumps({"type":"users","users":[{"name":x,"online":y["online"],"last_seen":y["last_seen"]} for x,y in users.items()]}))
            except: pass

    try:
        while True:
            raw = await websocket.receive_text()
            obj = json.loads(raw)
            t = obj.get("type")

            if t == "typing":
                to = obj.get("to","General")
                for uname, udata in users.items():
                    if uname==name: continue
                    if to=="General" or uname==to:
                        try: await udata["ws"].send_text(json.dumps({"type":"typing","from":name,"to":to}))
                        except: pass
                continue

            if t == "delete":
                mid = obj.get("id")
                m = next((x for x in msgs if x["id"]==mid), None)
                if m and m["sender"]==name:
                    m["deleted"]=True
                    m["text"]=""
                    m["data"]=""
                    for ud in users.values():
                        try: await ud["ws"].send_text(json.dumps({"type":"delete","id":mid}))
                        except: pass
                continue

            if t == "edit":
                mid = obj.get("id")
                m = next((x for x in msgs if x["id"]==mid), None)
                if m and m["sender"]==name:
                    m["text"]=obj.get("text","")[:1000]
                    m["edited"]=True
                    for ud in users.values():
                        try: await ud["ws"].send_text(json.dumps({"type":"edit","id":mid,"text":m["text"]}))
                        except: pass
                continue

            if t == "react":
                mid = obj.get("id")
                m = next((x for x in msgs if x["id"]==mid), None)
                if m:
                    m.setdefault("reacts",{})[name]=obj.get("emoji","❤️")
                    for ud in users.values():
                        try: await ud["ws"].send_text(json.dumps({"type":"react","id":mid,"emoji":obj.get("emoji"),"from":name}))
                        except: pass
                continue

            if t == "pin":
                global pinned_id
                pinned_id = obj.get("id")
                pm = next((x for x in msgs if x["id"]==pinned_id), None)
                for ud in users.values():
                    try: await ud["ws"].send_text(json.dumps({"type":"pin","msg":pm}))
                    except: pass
                continue

            if t == "unpin":
                pinned_id = None
                for ud in users.values():
                    try: await ud["ws"].send_text(json.dumps({"type":"unpin"}))
                    except: pass
                continue

            if t == "msg":
                msg = {
                    "id": int(time.time()*1000),
                    "type": "msg",
                    "sender": name,
                    "to": obj.get("to","General"),
                    "mtype": obj.get("mtype","text"),
                    "text": obj.get("text","")[:1000],
                    "data": obj.get("data",""),
                    "fname": obj.get("fname",""),
                    "replyTo": obj.get("replyTo"),
                    "time": datetime.now().strftime("%H:%M"),
                    "reacts": {}
                }
                msgs.append(msg)
                if len(msgs)>500: msgs.pop(0)

                # routing
                if msg["to"]=="General":
                    for ud in users.values():
                        try: await ud["ws"].send_text(json.dumps(msg))
                        except: pass
                else:
                    for target in [msg["to"], name]:
                        if target in users:
                            try: await users[target]["ws"].send_text(json.dumps(msg))
                            except: pass

    except WebSocketDisconnect:
        if name in users:
            users[name]["online"]=False
            users[name]["last_seen"]=datetime.now().strftime("%H:%M")
        for ud in users.values():
            try:
                await ud["ws"].send_text(json.dumps({"type":"users","users":[{"name":x,"online":y["online"],"last_seen":y["last_seen"]} for x,y in users.items()]}))
            except: pass
