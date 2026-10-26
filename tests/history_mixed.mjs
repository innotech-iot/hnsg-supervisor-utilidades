import assert from 'node:assert/strict';
const {historyGapLimit}=await import('../static/charts.js');
assert.equal(historyGapLimit({ts:0,interval_end:3600,aggregation:'hourly',resolution_seconds:3600},
    {ts:3600,aggregation:'raw',resolution_seconds:10},10000),3645);
assert.equal(historyGapLimit({ts:0,interval_end:3600,aggregation:'hourly',resolution_seconds:3600},
    {ts:7200,aggregation:'hourly',resolution_seconds:3600},10000),6480);
assert.equal(historyGapLimit({ts:0,aggregation:'raw',resolution_seconds:10},
    {ts:300,aggregation:'raw',resolution_seconds:10},10000),45);
assert.equal(historyGapLimit({ts:0},{ts:300},100),100);

// Exercise the actual canvas draw: the min/max band must begin at its interval,
// not shade the preceding missing hour.
globalThis.window={devicePixelRatio:1};globalThis.document={documentElement:{}};
globalThis.getComputedStyle=()=>({getPropertyValue:()=> '#000'});
const {TimeChart}=await import('../static/charts.js');
const bands=[];const context=new Proxy({fillRect:(...rect)=>bands.push(rect)},
    {get:(target,key)=>key in target?target[key]:(()=>{})});
const chart=Object.create(TimeChart.prototype);
Object.assign(chart,{canvas:{isConnected:true,width:800,height:300,getBoundingClientRect:()=>({width:800,height:300})},
    ctx:context,tip:{hidden:true},options:{series:[{key:'temperature'}],aggregation:'mixed'},
    rows:[{ts:0,interval_end:3600,resolution_seconds:3600,aggregation:'hourly',data:{temperature:22},
        quality:'good',extrema:{temperature:{min:20,max:24}}},
        {ts:7200,resolution_seconds:10,aggregation:'raw',quality:'good',data:{temperature:23}}]});
chart.draw();assert.equal(bands.length,1);
assert.equal(bands[0][0],55);assert.equal(bands[0][2],364.5);
// A bucket containing only a sample at the inclusive query endpoint has no
// interval width; its value may remain, but it must not shade invented time.
bands.length=0;
Object.assign(chart.rows[1],{aggregation:'bucketed',interval_end:7200,
    extrema:{temperature:{min:23,max:23}}});
chart.draw();assert.equal(bands.length,1);
