import assert from 'node:assert/strict';
const nodes=new Map();
function el(key){if(!nodes.has(key))nodes.set(key,{innerHTML:'',textContent:'',onclick:null,click(){this.clicked=true;}});return nodes.get(key);}
globalThis.document={querySelector:el,querySelectorAll:()=>[]};
let requests=[];
globalThis.fetch=async url=>{requests.push(url);throw Error('Unexpected account lookup');};
const {ctx}=await import('../static/core.js');
const {configView}=await import('../static/configuration.js');
for(const role of ['viewer','operator']){
    ctx.session={user:{id:2,username:'own_fixture',name:'Conta propria',role}};
    await configView('account');
    const html=el('#content').innerHTML;
    assert.ok(html.includes('own_fixture'));
    assert.ok(!html.includes('href="#config/users"'));
    assert.ok(html.includes('Alterar minha senha'));
    el('#own-password').onclick();
    assert.equal(el('#account-button').clicked,true);
    await configView('users');
    assert.ok(!el('#content').innerHTML.includes('href="#config/users"'));
}
assert.deepEqual(requests,[]);
const {passwordChangePayload}=await import('../static/account.js');
assert.throws(()=>passwordChangePayload({current:'old',password:'new-long-password',confirmation:'different'}));
assert.deepEqual(passwordChangePayload({current:'old',password:'new-long-password',confirmation:'new-long-password',user_id:99}),
    {current:'old',password:'new-long-password'});
console.log('Own account accessible; restricted accounts neither requested nor linked');
