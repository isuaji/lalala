import{_ as i,r as p,o as m,u as b,c as f,a as o,w as r,v as s,b as v,d as w,e as g}from"./index-fSWgsSel.js";const c={class:"admin-container"},x={class:"form-group"},y={class:"form-group"},B={class:"form-group"},k={class:"form-group"},V={__name:"WarnPage",setup(I){const u=b(),n=p({userId:"",count:"",reason:"",proof:""});m(()=>{var l;if((l=window.Telegram)!=null&&l.WebApp){const e=window.Telegram.WebApp;e.setBackButtonHandler(()=>{u.back()}),e.enableClosingConfirmation(),e.BackButton.show(),e.expand(),e.ready()}});const d=()=>{console.log("Форма варна:",n.value)},a=l=>{l.key==="Enter"&&l.target.blur()};return(l,e)=>(g(),f("div",c,[o("form",{class:"warn-form",onSubmit:w(d,["prevent"])},[o("div",x,[e[4]||(e[4]=o("label",null,"ID пользователя",-1)),r(o("input",{type:"text","onUpdate:modelValue":e[0]||(e[0]=t=>n.value.userId=t),placeholder:"Например: 123456789",required:"",onKeydown:a},null,544),[[s,n.value.userId]])]),o("div",y,[e[5]||(e[5]=o("label",null,"Количество предупреждений",-1)),r(o("input",{type:"number","onUpdate:modelValue":e[1]||(e[1]=t=>n.value.count=t),placeholder:"От 1 до 3",min:"1",max:"3",required:"",onKeydown:a},null,544),[[s,n.value.count]])]),o("div",B,[e[6]||(e[6]=o("label",null,"Причина предупреждения",-1)),r(o("textarea",{"onUpdate:modelValue":e[2]||(e[2]=t=>n.value.reason=t),placeholder:"Опишите причину выдачи предупреждения",required:"",onKeydown:a},null,544),[[s,n.value.reason]])]),o("div",k,[e[7]||(e[7]=o("label",null,"Доказательство",-1)),r(o("textarea",{"onUpdate:modelValue":e[3]||(e[3]=t=>n.value.proof=t),placeholder:"Предоставьте доказательства нарушения (ссылки на сообщения, скриншоты и т.д.)",required:"",onKeydown:a},null,544),[[s,n.value.proof]])]),e[8]||(e[8]=o("button",{type:"submit",class:"submit-button"},[o("span",{class:"warn-icon"},"⚠️"),v(" Выдать предупреждение ")],-1))],32)]))}},_=i(V,[["__scopeId","data-v-9a26e484"]]);export{_ as default};
