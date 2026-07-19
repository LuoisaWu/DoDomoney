<script setup lang="ts">
import { Calculator, CircleAlert, RotateCcw } from "lucide-vue-next";
import { computed, reactive } from "vue";

const form = reactive({ annualIncome: 180000, socialInsurance: 24000, specialDeductions: 12000, otherDeductions: 0, prepaidTax: 6000 });
const brackets = [
  { ceiling: 36000, rate: 0.03, deduction: 0 }, { ceiling: 144000, rate: 0.1, deduction: 2520 },
  { ceiling: 300000, rate: 0.2, deduction: 16920 }, { ceiling: 420000, rate: 0.25, deduction: 31920 },
  { ceiling: 660000, rate: 0.3, deduction: 52920 }, { ceiling: 960000, rate: 0.35, deduction: 85920 },
  { ceiling: Infinity, rate: 0.45, deduction: 181920 }
];
const taxableIncome = computed(() => Math.max(0, Number(form.annualIncome) - 60000 - Number(form.socialInsurance) - Number(form.specialDeductions) - Number(form.otherDeductions)));
const bracket = computed(() => brackets.find(item => taxableIncome.value <= item.ceiling) ?? brackets[brackets.length - 1]);
const annualTax = computed(() => Math.max(0, taxableIncome.value * bracket.value.rate - bracket.value.deduction));
const settlement = computed(() => annualTax.value - Number(form.prepaidTax));
const effectiveRate = computed(() => Number(form.annualIncome) ? annualTax.value / Number(form.annualIncome) * 100 : 0);
const money = (value: number) => value.toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
function reset() { Object.assign(form, { annualIncome: 180000, socialInsurance: 24000, specialDeductions: 12000, otherDeductions: 0, prepaidTax: 6000 }); }
</script>

<template>
  <section class="work-area tax-page">
    <header class="page-header">
      <div><p class="eyebrow">个人所得税计算</p><h1>年度综合所得税测算</h1><p class="subtle">独立计算，不写入账本，也不依赖 AI 对话。</p></div>
      <button class="secondary-button tax-reset" @click="reset"><RotateCcw :size="16" /> 重置示例</button>
    </header>
    <div class="tax-layout">
      <div class="section-block tax-form-card">
        <div class="section-heading"><div><h2><Calculator :size="18" /> 输入年度数据</h2><span>单位：人民币元</span></div></div>
        <div class="tax-form-grid">
          <label>年度综合所得<input v-model.number="form.annualIncome" min="0" step="100" type="number" /></label>
          <label>专项扣除（社保、公积金等）<input v-model.number="form.socialInsurance" min="0" step="100" type="number" /></label>
          <label>专项附加扣除<input v-model.number="form.specialDeductions" min="0" step="100" type="number" /></label>
          <label>其他依法扣除及捐赠<input v-model.number="form.otherDeductions" min="0" step="100" type="number" /></label>
          <label class="wide">年度已预缴税额<input v-model.number="form.prepaidTax" min="0" step="100" type="number" /></label>
        </div>
        <div class="tax-formula">应纳税所得额 = 综合所得 − 60,000 元基本减除费用 − 各项扣除</div>
      </div>
      <div class="section-block tax-result-card">
        <p>预计年度应纳税额</p><strong>¥ {{ money(annualTax) }}</strong>
        <dl>
          <div><dt>应纳税所得额</dt><dd>¥ {{ money(taxableIncome) }}</dd></div>
          <div><dt>适用税率</dt><dd>{{ bracket.rate * 100 }}%</dd></div>
          <div><dt>速算扣除数</dt><dd>¥ {{ money(bracket.deduction) }}</dd></div>
          <div><dt>综合税负率</dt><dd>{{ effectiveRate.toFixed(2) }}%</dd></div>
        </dl>
        <div :class="['settlement-result', settlement > 0 ? 'tax-due' : 'tax-refund']">
          <span>{{ settlement > 0 ? "预计需补税" : settlement < 0 ? "预计可退税" : "预计无需补退" }}</span>
          <strong>¥ {{ money(Math.abs(settlement)) }}</strong>
        </div>
      </div>
    </div>
    <div class="tax-notice"><CircleAlert :size="17" /><span>本工具按中国居民个人年度综合所得的通用公式估算，仅供参考；劳务报酬、稿酬等收入额换算、减免税及特殊情形请以税务机关最终核定为准。</span></div>
  </section>
</template>
