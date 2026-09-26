const root=document.documentElement;
const toggle=document.getElementById('themeToggle');
function labelTheme(){toggle.setAttribute('aria-label',root.dataset.theme==='dark'?'Switch to light theme':'Switch to dark theme');}
labelTheme();
toggle.addEventListener('click',()=>{root.dataset.theme=root.dataset.theme==='dark'?'light':'dark';try{localStorage.setItem('wystone-theme',root.dataset.theme)}catch(e){}labelTheme()});
