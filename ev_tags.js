// Outlier games page: capture EV+ tags for ML / spread / total (run on https://app.outlier.bet/NBA/games)
(() => { const out=[]; const t=document.querySelector('main').innerText.split('TODAY').slice(1);
 for (const s of t){ const toks=s.split('\n').map(x=>x.trim()).filter(Boolean); const game=toks.slice(1,5).join(' ');
  toks.forEach((x,i)=>{ if(x==='EV+') out.push(game+' | EV+ on: '+toks.slice(i+1,i+3).join(' ')); }); }
 return out.join('\n'); })()
