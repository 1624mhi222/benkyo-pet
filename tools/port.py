"""Artifact版 benkyo-pet.html → GitHub Pages + Firebase 版 index.html に変換する。
使い方: python3 port.py ../benkyo-pet.html site/index.html
Artifact版が更新されたら、もう一度これを実行するだけで移植できる。"""
import sys

src, dst = sys.argv[1], sys.argv[2]
h = open(src, encoding='utf-8').read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} of {old[:60]!r}, found {n}'
    h = h.replace(old, new)

FB = 'https://www.gstatic.com/firebasejs/10.14.1/'
head = f'''<!doctype html>
<html lang="ja"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#23845f">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icon-192.png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="べんきょうペット">
<script src="{FB}firebase-app-compat.js"></script>
<script src="{FB}firebase-auth-compat.js"></script>
<script src="{FB}firebase-firestore-compat.js"></script>
<script src="firebase-config.js"></script>
'''
rep('<meta name="claude:viewport-fit-sides" content="cover">\n', '')
h = head + h
rep('<style>\n/* Layout:', '''<style>
:root{box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
body{margin:0}
textarea{box-sizing:border-box}
#gate{position:fixed;inset:0;z-index:50;display:flex;align-items:center;justify-content:center;padding:16px;background:color-mix(in srgb,var(--paper) 88%,transparent);backdrop-filter:blur(3px)}
#gate .card{max-width:360px;width:100%;text-align:center;align-items:center}
#acct{display:flex;gap:8px;justify-content:center;align-items:center;flex-wrap:wrap;color:var(--muted);font-size:.8rem;margin-top:-8px}
/* Layout:''')
rep('''<footer id="footer">読み込み中…</footer>
</div>''', '''<footer id="footer">読み込み中…</footer>
  <div id="acct"></div>
</div>
<div id="gate" hidden><div class="card"><h2>べんきょうペット</h2>
  <p class="small muted" style="margin:0">Googleでログインすると、スマホとPCで同じ記録とペットが使えます。</p>
  <button class="big-btn primary" id="gateLogin">Googleでログイン</button>
  <button class="ghost" id="gateLocal">ログインせずに使う（この端末だけに保存）</button>
  <div class="msg" id="gateMsg"></div></div></div>''')

# storage: Claude db → Firebase (compat API is the same shape: doc().get/set, collection().get)
rep('''    if(window.claude&&window.claude.use){
      const [db,user]=await Promise.all([window.claude.use('db'),window.claude.use('user')]);
      const uid=user?await user.id():null;
      if(db&&uid){store.db=db;store.uid=uid;store.mode='cloud';return}
    }''', '''    const cfg=window.FIREBASE_CONFIG;
    if(window.firebase&&cfg&&cfg.apiKey){
      if(!firebase.apps.length)firebase.initializeApp(cfg);
      const auth=firebase.auth();
      const user=await new Promise(res=>{
        const off=auth.onAuthStateChanged(u=>{if(u){off();$('gate').hidden=true;res(u)}else showGate(auth,res)});
      });
      if(user){
        store.db=firebase.firestore();store.uid=user.uid;store.mode='cloud';
        $('acct').innerHTML='<span>'+esc(user.email||user.displayName||'')+'</span><button class="ghost" id="logout">ログアウト</button>';
        $('logout').onclick=()=>auth.signOut().then(()=>location.reload());
        return;
      }
    }''')
rep('async function initStore(){', '''function showGate(auth,res){
  const g=$('gate');g.hidden=false;
  $('gateLogin').onclick=async()=>{
    const p=new firebase.auth.GoogleAuthProvider();$('gateMsg').textContent='';
    try{await auth.signInWithPopup(p)}
    catch(e){console.error(e);
      if(e&&(e.code==='auth/popup-blocked'||e.code==='auth/operation-not-supported-in-this-environment')){try{await auth.signInWithRedirect(p);return}catch(e2){console.error(e2)}}
      if(!(e&&e.code==='auth/popup-closed-by-user'))$('gateMsg').textContent='ログインできませんでした。もう一度お試しください。'}
  };
  $('gateLocal').onclick=()=>{g.hidden=true;res(null)};
}
async function initStore(){''')
rep("'記録はあなたのアカウントに保存されます。スマホとPCで同じ記録が見られます。'",
    "'記録はGoogleアカウントに保存されます。スマホとPCで同じ記録が見られます。'")

# export: plain browser download
rep("let dl=null;try{dl=window.claude&&window.claude.use?await window.claude.use('downloads'):null}catch(e){}",
    "const dl={save:async o=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([o.data],{type:'application/json'}));a.download=o.filename;document.body.appendChild(a);a.click();a.remove()}};")

# import (moving in from the Artifact version)
rep('''esc(S.exportNote||'')+'</div>':'');
}''', '''esc(S.exportNote||'')+'</div>':'')+
    '<div class="divider"></div><h2>データの読み込み</h2><p class="small muted" style="margin:0">前のアプリで書き出したファイルを選ぶか、文字を貼りつけてください。今のこのアプリの記録は上書きされます。</p>'+
    '<input type="file" id="importFile" accept=".json,application/json">'+
    '<textarea id="importBox" rows="3" placeholder="ここに貼りつけてもOK" style="width:100%;font:12px/1.4 monospace;border:1px solid var(--line);border-radius:10px;padding:8px;background:var(--surface);color:var(--ink)"></textarea>'+
    '<div class="row"><button class="primary" data-act="import">読み込む</button></div>';
}''')
rep("  }else if(act==='view'){", '''  }else if(act==='import'){
    let data;try{data=JSON.parse(($('importBox').value||'').trim())}catch(e){toast('読み込めませんでした。書き出した文字をそのまま貼りつけてください。');return}
    if(!data||data.app!=='benkyo-pet'||!data.settings||typeof data.weeks!=='object'){toast('べんきょうペットのデータではないようです。');return}
    if(!confirm('今の記録を、読み込んだデータで上書きします。よろしいですか？'))return;
    await Promise.all(Object.keys(data.weeks).map(w=>sset('w-'+w,data.weeks[w])));
    await sset('settings',data.settings);
    await refresh();toast('読み込みました！（週の記録 '+Object.keys(data.weeks).length+'件）');
  }else if(act==='view'){''')
rep("  }else if(ev.target.id==='timerSubj'){S.lastSubj=ev.target.value}", '''  }else if(ev.target.id==='timerSubj'){S.lastSubj=ev.target.value}
  else if(ev.target.id==='importFile'){const f=ev.target.files&&ev.target.files[0];if(f){$('importBox').value=await f.text()}}''')

h += '\n</body></html>\n'
open(dst, 'w', encoding='utf-8').write(h)
print('wrote', dst, len(h))
