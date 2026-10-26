import assert from 'node:assert/strict';
const nodes=new Map();const buttons={profile:{dataset:{profile:'1'}},tag:{dataset:{tag:'1'}}};
function element(selector){if(!nodes.has(selector))nodes.set(selector,{innerHTML:'',textContent:'',value:'',
    elements:new Proxy({}, {get:()=>({value:'',checked:false})}),classList:{toggle(){},add(){},remove(){}},
    addEventListener(){},focus(){}});return nodes.get(selector);}
globalThis.document={querySelector:s=>s.startsWith('#')?element(s):null,
    querySelectorAll:s=>s==='[data-profile]'?[buttons.profile]:s==='[data-tag]'?[buttons.tag]:[]};
globalThis.window={};globalThis.location={hash:''};
globalThis.fetch=async path=>({ok:true,json:async()=>path==='/api/tags'?{tags:[{id:1,controller_id:1,
    asset_id:1,symbol:'Fixture',description:'Fixture',address:0,area:'holding',unit:'boolean',
    poll_seconds:2,alarm_priority:'warning',revision:1}]}:{}});
const core=await import('../static/core.js');
core.ctx.session={user:{role:'admin'}};core.ctx.state={assets:[{id:1,kind:'uta',name:'UTA 01',
    controller_id:1,profile:{validated:false},revision:1}],controllers:[{id:1,name:'CLP 1'}]};
const configuration=await import('../static/configuration.js');
if(process.argv[2]==='tag'){
    await configuration.configView('points');buttons.tag.onclick();
    assert.ok(!element('#dialog-body').innerHTML.includes('name="fan_confirmation_validated"'));
}else{
    await configuration.configView('profiles');buttons.profile.onclick();
    assert.ok(element('#dialog-body').innerHTML.includes('name="fan_confirmation_validated"'));
}
