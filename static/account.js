import {ctx,$,h,roles,api,showDialog,submitSafely} from './core.js';

export function passwordChangePayload(data){
 if(data.password!==data.confirmation)throw new Error('A confirmação deve ser igual à nova senha.');
 return {current:data.current,password:data.password};
}

export function showAccount({logout,leave}){
 const u=ctx.session.user;
 showDialog('Minha conta e senha',`<div class="notice"><strong>${h(u.name)}</strong> · ${h(roles[u.role])}<br>Usuário ${h(u.username)}.</div><form id="password-form"><label>Senha atual<input name="current" type="password" required maxlength="256" autocomplete="current-password"></label><label class="mt">Nova senha (mínimo 12 caracteres)<input name="password" type="password" minlength="12" maxlength="256" required autocomplete="new-password"></label><label class="mt">Confirme a nova senha<input name="confirmation" type="password" minlength="12" maxlength="256" required autocomplete="new-password"></label><p class="muted small-text mt">Após alterar, todas as suas sessões serão encerradas.</p><div class="form-actions"><button type="button" class="button danger" id="logout-button">Sair da conta</button><button type="submit" class="button primary">Alterar minha senha</button></div></form>`);
 $('#logout-button').onclick=e=>logout(e.currentTarget);
 $('#password-form').onsubmit=e=>{
  e.preventDefault();
  submitSafely(e.target,async data=>{
   await api('/api/auth/password',{method:'POST',body:passwordChangePayload(data)});
   leave();$('#login-error').textContent='Senha alterada. Entre novamente.';
  });
 };
}
