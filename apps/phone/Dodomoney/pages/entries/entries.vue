<script setup>
import { reactive, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import { api, showError } from "../../services/api";
import { requireLogin } from "../../services/session";
const entries=ref([]), selected=ref(null), saving=ref(false); const form=reactive({amount:"",category:"",date:"",time:"",description:""});
const money=v=>Number(v).toLocaleString("zh-CN",{minimumFractionDigits:2});
function format(value){return new Date(value).toLocaleString("zh-CN",{month:"numeric",day:"numeric",hour:"2-digit",minute:"2-digit"})}
async function load(){if(!requireLogin())return;try{entries.value=await api.listEntries()}catch(e){showError(e)}}
function open(item){selected.value=item;const d=new Date(item.occurred_at);const local=new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString();Object.assign(form,{amount:item.amount,category:item.category,date:local.slice(0,10),time:local.slice(11,16),description:item.description})}
async function save(){saving.value=true;try{await api.updateEntry(selected.value.id,{amount:String(form.amount),category:form.category.trim(),description:form.description.trim(),occurred_at:new Date(`${form.date}T${form.time}:00`).toISOString()});selected.value=null;await load();uni.showToast({title:"已保存"})}catch(e){showError(e)}finally{saving.value=false}}
function remove(item){uni.showModal({title:"删除账单",content:`确定删除“${item.description}”吗？`,success:async r=>{if(r.confirm){try{await api.deleteEntry(item.id);selected.value=null;await load()}catch(e){showError(e)}}}})}
onShow(load);
</script>
<template><view class="page"><view class="hero"><text class="eyebrow">账单明细</text><text class="title">每一笔都清清楚楚</text><text class="subtle">共 {{ entries.length }} 笔记录，点击可查看和编辑</text></view>
<view v-if="!entries.length" class="card empty">还没有账单，从 AI 记账开始吧。</view>
<view v-for="item in entries" :key="item.id" class="entry card" @click="open(item)"><view class="entry-icon" :class="item.type">{{ item.type==='expense'?'支':'收' }}</view><view class="entry-main"><text class="entry-name">{{ item.description }}</text><text class="muted">{{ item.category }}{{ item.subcategory?` · ${item.subcategory}`:'' }} · {{ format(item.occurred_at) }}</text></view><text :class="['money',item.type]">{{ item.type==='expense'?'-':'+' }}¥{{ money(item.amount) }}</text></view>
<view v-if="selected" class="sheet-mask" @click.self="selected=null"><view class="sheet"><view class="sheet-head"><text>编辑账单 #{{ selected.id }}</text><text @click="selected=null">×</text></view><label class="field">金额<input v-model="form.amount" class="input" type="digit" /></label><label class="field">类别<input v-model="form.category" class="input" /></label><view class="row"><label class="field half">日期<picker mode="date" :value="form.date" @change="form.date=$event.detail.value"><view class="picker">{{form.date}}</view></picker></label><label class="field half">时间<picker mode="time" :value="form.time" @change="form.time=$event.detail.value"><view class="picker">{{form.time}}</view></picker></label></view><label class="field">备注<textarea v-model="form.description" class="textarea" maxlength="500" /></label><view class="row"><button class="btn danger" @click="remove(selected)">删除</button><button class="btn primary grow" :disabled="saving" @click="save">{{saving?'保存中…':'保存修改'}}</button></view></view></view></view></template>
<style scoped>.entry{display:flex;align-items:center;gap:18rpx;padding:24rpx}.entry-icon{width:62rpx;height:62rpx;display:flex;align-items:center;justify-content:center;border-radius:18rpx;background:#fff0e7}.entry-icon.income{background:#e8f5ee}.entry-main{flex:1;min-width:0}.entry-name{display:block;font-weight:750;margin-bottom:7rpx}.muted{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.half{flex:1}.grow{flex:1}</style>


