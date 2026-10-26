// Behavioral rendering/navigation checks with a minimal DOM; no browser layout claims.
import assert from 'node:assert/strict';
const nodes=new Map();
function node(){return {innerHTML:'',textContent:'',value:'',hidden:false,isConnected:false,
    classList:{toggle(){},add(){},remove(){}},addEventListener(){},removeEventListener(){},setAttribute(){},
    parentElement:{append(){}},getContext(){return {};},remove(){}};}
function element(selector){if(!nodes.has(selector))nodes.set(selector,node());return nodes.get(selector);}
globalThis.document={querySelector:selector=>selector.startsWith('#')?element(selector):null,
    querySelectorAll:()=>[],createElement:()=>node()};
globalThis.window={addEventListener(){},dispatchEvent(){}};
globalThis.location={hash:''};
globalThis.ResizeObserver=class {observe(){} disconnect(){}};
globalThis.fetch=async()=>({ok:true,json:async()=>({rows:[],aggregation:'raw',tags:[]})});
const core=await import('../static/core.js');
const views=await import('../static/views.js');
core.ctx.session={user:{role:'admin'}};
core.ctx.state={mode:'demo',health:{},assets:[...Array.from({length:14},(_,i)=>({id:i+1,kind:'uta',name:`UTA ${String(i+1).padStart(2,'0')}`,
    controller_id:i===0?1:2,sector:'Fixture',data:{},quality:'unknown',status:'unknown',trend:[],alarms:[],alarm_count:0,profile:{}})),
    ...[{id:15,kind:'cag',name:'CAG <fixture>',controller_id:2},{id:16,kind:'caq',name:'CAQ',controller_id:3}].map(a=>({...a,
        sector:'Fixture',data:{},quality:'unknown',status:'unknown',trend:[],alarms:[],alarm_count:0,profile:{},coverage:[]}))],
    controllers:[1,2,3].map(id=>({id,name:`CLP ${id}`,status:'unconfigured'}))};
if(process.argv[2]==='dashboard'){
    await views.dashboard();
    const html=element('#content').innerHTML;
    assert.equal((html.match(/class="asset-card /g)||[]).length,14);
    assert.equal((html.match(/class="central-card /g)||[]).length,2);
    assert.ok(html.includes('href="#central/16"'));
    assert.ok(html.includes('CAG &lt;fixture&gt;'));
    assert.ok(html.includes('<option value="3">CLP 3</option>'));
    assert.equal(core.adjacentAsset(14,1),'central/15');
    assert.equal(core.adjacentAsset(16,1),'uta/1');
    assert.equal(core.adjacentAsset(1,-1),'central/16');
    assert.ok(!views.statusBadge(core.ctx.state.assets.at(-1)).includes('Parada'));
    assert.ok(!views.statusBadge({...core.ctx.state.assets.at(-1),quality:'good'}).includes('Em operação'));
    core.ctx.state.assets.at(-1).quality='good';
    await views.dashboard();
    const missing=element('#dashboard-kpis').innerHTML.match(/Sem dados válidos[\s\S]*?<div class="kpi-number [^"]*">(\d+)</);
    assert.equal(Number(missing?.[1]),15);
}else if(process.argv[2]==='central'){
    assert.equal(typeof views.centralDetail,'function');
    await views.centralDetail(16);
    const html=element('#content').innerHTML;
    assert.ok(html.includes('Central de água quente'));
    assert.ok(html.includes('supply_temperature')&&html.includes('return_temperature'));
    assert.ok(!html.includes('fan-device')&&!html.includes('adjust-button')&&!html.includes('Umidade'));
    assert.ok(!html.includes('Referência'));
    assert.ok(html.includes('Ida da água')&&html.includes('Retorno da água'));
    assert.equal(core.ctx.charts.length,2);
    assert.equal(core.ctx.charts[0].metric,'supply_temperature');
    assert.equal(core.ctx.charts[0].live,true);
    assert.equal(core.ctx.charts[1].live,false);
    assert.ok(element('#central-quality').textContent.includes('Desconhecida'));
    core.ctx.state.assets.at(-1).data={supply_temperature:48,return_temperature:43,pump_command:1,pump_feedback:1};
    core.ctx.state.assets.at(-1).source='demo';
    core.ctx.state.assets.at(-1).quality='good';
    await views.centralDetail(16);
    assert.ok(element('#content').innerHTML.includes('Valores sintéticos de demonstração'));
    assert.ok(!element('#content').innerHTML.includes('não têm simulação'));
}else{
    const configuration=await import('../static/configuration.js');
    globalThis.fetch=async path=>({ok:true,json:async()=>path==='/api/tags'?{tags:[{
        id:1,controller_id:2,asset_id:15,symbol:'EX_CENTRAL',description:'Fixture',address:100,
        area:'holding',access:'RO',scale:.1,offset:0,unit:'°C',data_type:'int16',map_revision:1,
        semantic:'supply_temperature',validated:false,reading:null}]}:{}});
    await configuration.configView('points');
    const table=element('#tag-table').innerHTML;
    assert.ok(table.includes('CAG &lt;fixture&gt;'));
    assert.ok(!table.includes('CAG <fixture>'));
}
console.log('central frontend '+process.argv[2]+': passed');
