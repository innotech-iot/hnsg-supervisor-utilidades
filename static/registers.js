// Historian keys correspond to explicitly associated functional points.
export const registers={
 temperature:{label:'Temperatura',unit:'°C'},temp_sp:{label:'Referência de temperatura',unit:'°C'},
 humidity:{label:'Umidade',unit:'% UR'},humidity_sp:{label:'Referência de umidade',unit:'% UR'},
 airflow:{label:'Vazão de ar',unit:'m³/h'},airflow_sp:{label:'Referência de vazão',unit:'m³/h'},
 pressure:{label:'Pressão diferencial',unit:'Pa'},cooling:{label:'Comando de resfriamento',unit:'%'},
 heating:{label:'Comando de reaquecimento',unit:'%'},fan_speed:{label:'Velocidade do ventilador',unit:'%'}
};
export function selectedSeries(keys,unit){return [...new Set(keys)].filter(k=>registers[k]?.unit===unit).map((key,i)=>({key,label:`${registers[key].label} (${unit})`,color:['cyan','orange','lime','purple'][i%4],dashed:key.endsWith('_sp')}));}
