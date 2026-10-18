function numeric(value,name,low,high){
  if(typeof value!=='string'||!value.trim())throw Error(`Потрібне значення: ${name}`);
  const result=Number(value);
  if(!Number.isFinite(result)||result<low||result>high)throw Error(`Недопустиме значення: ${name}`);
  return result;
}
export function cents(value){
  const amount=numeric(value,'CHF',0,1000000);
  if(Math.abs(amount*100-Math.round(amount*100))>.00001)throw Error('CHF: не більше двох знаків після коми');
  return Math.round(amount*100);
}
export function towerParams(setup,auto){
  if(typeof auto!=='boolean')throw Error('INVALID_BOOLEAN');
  return {setup_cents:cents(setup),auto_deduct_setup:auto};
}
export function expenseRule({id,title,amount,multiplier='',bio=''}){
  if(typeof title!=='string'||!title.trim()||title.length>160)throw Error('Вкажи назву витрати (до 160 символів)');
  const modifiers={};
  if(multiplier.trim())modifiers.revenue_multiplier=numeric(multiplier,'множник доходу',0,5);
  if(bio.trim())modifiers.Bio_RAM=numeric(bio,'Bio_RAM',0,100);
  return {schema:'sovereign.rule.v1',id,format:'json',origin:'operator',
    assumptions:['Synthetic scenario; operator-entered values are not a causal prediction.',title.trim()],
    operations:[{op:'expense',amount_cents:cents(amount),kpi_modifiers:modifiers}]};
}
