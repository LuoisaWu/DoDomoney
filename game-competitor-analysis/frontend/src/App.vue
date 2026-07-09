<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { chatAnalysis, getGames } from './api'

const navItems = [
  { icon: '✦', label: '智能分析', target: 'analysis' },
  { icon: '▦', label: '游戏数据', target: 'game-data' },
  { icon: '◫', label: '竞品对标', target: 'competitors' },
  { icon: '◇', label: 'SWOT 分析', target: 'swot' },
  { icon: '▥', label: '数据图表', target: 'charts' },
]
const examples = [
  '分析 Stardew Valley 的竞品',
  '分析 Hades 的竞品',
  '分析 Hollow Knight 的竞品',
  '分析 Slay the Spire 的竞品',
]
const chartColors = ['#5b6ff9', '#825cf5', '#2cc7a0', '#4aa8ff', '#f59b58', '#ec668a']

const games = ref([])
const query = ref('')
const result = ref(null)
const loading = ref(false)
const serviceConnected = ref(false)
const activeNav = ref('analysis')
const similarityChart = ref(null)
const ratingChart = ref(null)
const positiveChart = ref(null)
const platformChart = ref(null)
const chartInstances = []

const platformCount = computed(() => {
  const platforms = new Set()
  games.value.forEach((game) => splitPlatforms(game.platform).forEach((item) => platforms.add(item)))
  return platforms.size
})

function splitPlatforms(platform) {
  return platform.split('/').map((item) => item.trim()).filter(Boolean)
}

function scrollTo(target) {
  activeNav.value = target
  document.getElementById(target)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function loadGames() {
  try {
    const data = await getGames()
    games.value = data.games || []
    serviceConnected.value = true
  } catch (error) {
    serviceConnected.value = false
    ElMessage.error(error.message)
  }
}

async function analyze(value = query.value) {
  const content = value.trim()
  if (!content) {
    ElMessage.warning('请输入要分析的游戏名称或问题。')
    return
  }
  query.value = content
  loading.value = true
  try {
    result.value = await chatAnalysis(content)
    serviceConnected.value = true
    ElMessage.success(result.value.message || '分析完成')
    await nextTick()
    document.getElementById('game-data')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  } catch (error) {
    serviceConnected.value = false
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

function commonAxis() {
  return {
    axisLine: { lineStyle: { color: '#dfe4f2' } },
    axisLabel: { color: '#75809a', fontSize: 11 },
    splitLine: { lineStyle: { color: '#edf0f7' } },
  }
}

function makeBarOption(title, names, values, suffix = '', includeTarget = false) {
  const colors = includeTarget ? ['#825cf5', ...values.slice(1).map(() => '#5b8ff9')] : values.map((_, i) => chartColors[i % chartColors.length])
  return {
    title: { text: title, left: 4, textStyle: { color: '#28324a', fontSize: 17, fontWeight: 650 } },
    tooltip: { trigger: 'axis', valueFormatter: (value) => `${value}${suffix}` },
    grid: { left: 46, right: 18, top: 64, bottom: 76 },
    xAxis: { type: 'category', data: names, axisLabel: { ...commonAxis().axisLabel, rotate: 24, interval: 0, overflow: 'truncate', width: 86 }, axisLine: commonAxis().axisLine },
    yAxis: { type: 'value', ...commonAxis(), min: 0 },
    series: [{
      type: 'bar', data: values.map((value, index) => ({ value, itemStyle: { color: colors[index], borderRadius: [7, 7, 0, 0] } })),
      barMaxWidth: 38,
      label: { show: true, position: 'top', color: '#59647c', formatter: `{c}${suffix}` },
    }],
  }
}

function renderCharts() {
  if (!result.value) return
  chartInstances.splice(0).forEach((chart) => chart.dispose())
  const target = result.value.target_game
  const competitors = result.value.competitors
  const allGames = [target, ...competitors]

  const similarity = echarts.init(similarityChart.value)
  similarity.setOption(makeBarOption('竞品相似度排行', competitors.map((item) => item.name), competitors.map((item) => item.similarity_score), ' 分'))

  const rating = echarts.init(ratingChart.value)
  rating.setOption(makeBarOption('游戏评分对比', allGames.map((item) => item.name), allGames.map((item) => item.rating), ' 分', true))

  const positive = echarts.init(positiveChart.value)
  positive.setOption(makeBarOption('用户好评率对比', allGames.map((item) => item.name), allGames.map((item) => item.positive_rate), '%', true))

  const counts = {}
  allGames.forEach((game) => splitPlatforms(game.platform).forEach((platform) => { counts[platform] = (counts[platform] || 0) + 1 }))
  const platform = echarts.init(platformChart.value)
  platform.setOption({
    color: chartColors,
    title: { text: '平台分布', left: 4, textStyle: { color: '#28324a', fontSize: 17, fontWeight: 650 } },
    tooltip: { trigger: 'item', formatter: '{b}<br/>收录游戏：{c}（{d}%）' },
    legend: { bottom: 6, icon: 'circle', textStyle: { color: '#75809a' } },
    series: [{ type: 'pie', radius: ['42%', '67%'], center: ['50%', '50%'], padAngle: 3, itemStyle: { borderRadius: 7 }, label: { color: '#59647c', formatter: '{b}  {c}' }, data: Object.entries(counts).map(([name, value]) => ({ name, value })) }],
  })
  chartInstances.push(similarity, rating, positive, platform)
}

function resizeCharts() {
  chartInstances.forEach((chart) => chart.resize())
}

watch(result, async () => {
  await nextTick()
  renderCharts()
})

onMounted(() => {
  loadGames()
  window.addEventListener('resize', resizeCharts)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)
  chartInstances.splice(0).forEach((chart) => chart.dispose())
})
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">GS</div>
        <div><strong>GameScope</strong><span>智能对标分析</span></div>
      </div>
      <nav class="side-nav">
        <button v-for="item in navItems" :key="item.target" :class="['nav-item', { active: activeNav === item.target }]" @click="scrollTo(item.target)">
          <span class="nav-icon">{{ item.icon }}</span>{{ item.label }}
        </button>
      </nav>
      <div class="sidebar-note">
        <span class="note-kicker">AI INSIGHT</span>
        <strong>让竞品决策更清晰</strong>
        <p>聚合多维数据，快速识别市场位置与增长机会。</p>
      </div>
      <div class="sidebar-version">GameScope · Phase 02</div>
    </aside>

    <main class="main-panel">
      <header class="topbar">
        <div>
          <div class="eyebrow">MULTI-PLATFORM GAME INTELLIGENCE</div>
          <h1>基于 AI 辅助的多平台游戏竞品动态追踪与智能对标分析系统</h1>
          <p>面向 Steam、Switch 等平台，提供游戏竞品匹配、SWOT 分析与智能对标能力。</p>
        </div>
        <div :class="['service-status', { offline: !serviceConnected }]">
          <span class="status-dot"></span>{{ serviceConnected ? '数据服务已连接' : '数据服务未连接' }}
        </div>
      </header>

      <div class="content-wrap">
        <section class="stats-grid" aria-label="数据概览">
          <el-card class="stat-card stat-blue" shadow="never"><div class="stat-icon">▦</div><div><span>已收录游戏数量</span><strong>{{ games.length }}</strong><small>覆盖经典与热门产品</small></div></el-card>
          <el-card class="stat-card stat-purple" shadow="never"><div class="stat-icon">◎</div><div><span>支持平台数量</span><strong>{{ platformCount }}</strong><small>Steam / Switch</small></div></el-card>
          <el-card class="stat-card stat-cyan" shadow="never"><div class="stat-icon">✦</div><div><span>可分析维度数量</span><strong>6</strong><small>从数据到策略建议</small></div></el-card>
        </section>

        <section id="analysis" class="section-card assistant-card">
          <div class="section-heading compact"><div><span class="section-index">01</span><h2>智能竞品分析</h2><p>输入游戏名称或自然语言需求，即刻生成结构化分析结果。</p></div><span class="ai-badge">✦ AI ANALYST</span></div>
          <div class="assistant-input">
            <div class="input-avatar">AI</div>
            <el-input v-model="query" type="textarea" :autosize="{ minRows: 3, maxRows: 6 }" resize="none" placeholder="请输入游戏名称或分析需求，例如：分析 Stardew Valley 的竞品" @keydown.ctrl.enter="analyze()" />
            <el-button class="analyze-button" type="primary" :loading="loading" @click="analyze()">{{ loading ? '正在分析' : '开始分析' }}<span v-if="!loading">→</span></el-button>
          </div>
          <div class="quick-queries"><span>快捷提问</span><el-button v-for="example in examples" :key="example" round @click="analyze(example)">{{ example }}</el-button></div>
        </section>

        <div v-if="!result" class="empty-state">
          <div class="empty-orbit"><span>✦</span></div>
          <h3>准备开始智能分析</h3><p>选择上方示例问题，或输入你关心的游戏名称。</p>
        </div>

        <template v-else>
          <section id="game-data" class="section-block">
            <div class="section-heading"><div><span class="section-index">02</span><h2>目标游戏画像</h2><p>{{ result.message }}</p></div><el-tag :type="result.matched ? 'success' : 'warning'" effect="light">{{ result.matched ? '精准匹配' : '智能推荐' }}</el-tag></div>
            <el-card class="game-profile" shadow="never">
              <div class="game-hero">
                <div class="game-monogram">{{ result.target_game.name.slice(0, 1) }}</div>
                <div class="game-title"><span class="micro-label">TARGET GAME</span><h3>{{ result.target_game.name }}</h3><div><el-tag>{{ result.target_game.platform }}</el-tag><el-tag type="info">{{ result.target_game.genre }}</el-tag></div></div>
                <div class="score-cluster"><div><strong>{{ result.target_game.rating }}</strong><span>综合评分</span></div><div><strong>{{ result.target_game.positive_rate }}%</strong><span>用户好评率</span></div></div>
              </div>
              <el-descriptions :column="4" border class="game-descriptions">
                <el-descriptions-item label="开发商">{{ result.target_game.developer }}</el-descriptions-item><el-descriptions-item label="发行商">{{ result.target_game.publisher }}</el-descriptions-item>
                <el-descriptions-item label="发行时间">{{ result.target_game.release_date }}</el-descriptions-item><el-descriptions-item label="价格">$ {{ result.target_game.price.toFixed(2) }}</el-descriptions-item>
                <el-descriptions-item label="评论数量">{{ result.target_game.review_count.toLocaleString() }}</el-descriptions-item><el-descriptions-item label="标签" :span="3"><el-tag v-for="tag in result.target_game.tags" :key="tag" class="data-tag" size="small" effect="plain">{{ tag }}</el-tag></el-descriptions-item>
              </el-descriptions>
              <div class="game-description"><span>游戏简介</span><p>{{ result.target_game.description }}</p></div>
            </el-card>
          </section>

          <section id="competitors" class="section-block">
            <div class="section-heading"><div><span class="section-index">03</span><h2>竞品推荐矩阵</h2><p>基于类型、标签、平台、价格与用户口碑综合计算。</p></div><span class="result-count">TOP {{ result.competitors.length }}</span></div>
            <el-card class="table-card" shadow="never">
              <el-table :data="result.competitors" stripe table-layout="fixed">
                <el-table-column type="index" label="排名" width="65" align="center"><template #default="scope"><span class="rank-badge">{{ scope.$index + 1 }}</span></template></el-table-column>
                <el-table-column prop="name" label="游戏名称" min-width="180"><template #default="scope"><strong class="game-cell-name">{{ scope.row.name }}</strong></template></el-table-column>
                <el-table-column label="平台" width="130"><template #default="scope"><el-tag size="small">{{ scope.row.platform }}</el-tag></template></el-table-column>
                <el-table-column label="类型" width="155"><template #default="scope"><el-tag type="info" size="small">{{ scope.row.genre }}</el-tag></template></el-table-column>
                <el-table-column label="价格" width="85" align="center"><template #default="scope">${{ scope.row.price.toFixed(2) }}</template></el-table-column>
                <el-table-column prop="rating" label="评分" width="70" align="center" />
                <el-table-column label="好评率" width="85" align="center"><template #default="scope"><span class="positive-rate">{{ scope.row.positive_rate }}%</span></template></el-table-column>
                <el-table-column label="相似度" min-width="150"><template #default="scope"><el-progress :percentage="Math.min(scope.row.similarity_score, 100)" :stroke-width="9" :format="() => `${scope.row.similarity_score} 分`" /></template></el-table-column>
                <el-table-column label="匹配原因" min-width="280"><template #default="scope"><el-tag v-for="reason in scope.row.match_reasons" :key="reason" class="reason-tag" size="small" effect="plain">{{ reason }}</el-tag></template></el-table-column>
              </el-table>
            </el-card>
          </section>

          <section class="section-block insight-section">
            <div class="section-heading"><div><span class="section-index">04</span><h2>智能分析洞察</h2><p>从产品特征、竞品格局与市场位置三个层面提炼结论。</p></div></div>
            <div class="insight-grid"><article><span class="insight-icon">◈</span><h3>游戏概况</h3><p>{{ result.summary }}</p></article><article><span class="insight-icon">⌁</span><h3>竞品对比分析</h3><p>{{ result.comparison }}</p></article><article><span class="insight-icon">◎</span><h3>市场定位分析</h3><p>{{ result.market_position }}</p></article></div>
          </section>

          <section id="charts" class="section-block">
            <div class="section-heading"><div><span class="section-index">05</span><h2>数据可视化</h2><p>关键指标横向对比，快速识别市场格局与产品差异。</p></div></div>
            <div class="charts-grid"><el-card shadow="never"><div ref="similarityChart" class="chart"></div></el-card><el-card shadow="never"><div ref="ratingChart" class="chart"></div></el-card><el-card shadow="never"><div ref="positiveChart" class="chart"></div></el-card><el-card shadow="never"><div ref="platformChart" class="chart"></div></el-card></div>
          </section>

          <section id="swot" class="section-block">
            <div class="section-heading"><div><span class="section-index">06</span><h2>SWOT 四象限分析</h2><p>综合内外部因素，识别优势、短板、机会与潜在风险。</p></div></div>
            <div class="swot-grid">
              <article class="swot-card strengths"><div class="swot-letter">S</div><div><h3>Strengths <span>优势</span></h3><ul><li v-for="item in result.swot.strengths" :key="item">{{ item }}</li></ul></div></article>
              <article class="swot-card weaknesses"><div class="swot-letter">W</div><div><h3>Weaknesses <span>劣势</span></h3><ul><li v-for="item in result.swot.weaknesses" :key="item">{{ item }}</li></ul></div></article>
              <article class="swot-card opportunities"><div class="swot-letter">O</div><div><h3>Opportunities <span>机会</span></h3><ul><li v-for="item in result.swot.opportunities" :key="item">{{ item }}</li></ul></div></article>
              <article class="swot-card threats"><div class="swot-letter">T</div><div><h3>Threats <span>威胁</span></h3><ul><li v-for="item in result.swot.threats" :key="item">{{ item }}</li></ul></div></article>
            </div>
          </section>

          <section class="section-card strategy-section">
            <div class="section-heading compact"><div><span class="section-index">07</span><h2>策略建议</h2><p>将分析结论转化为可执行的产品与市场动作。</p></div></div>
            <el-timeline><el-timeline-item v-for="(suggestion, index) in result.suggestions" :key="suggestion" :timestamp="`策略 0${index + 1}`" placement="top" color="#665cf6"><div class="strategy-item"><span>{{ String(index + 1).padStart(2, '0') }}</span><p>{{ suggestion }}</p></div></el-timeline-item></el-timeline>
          </section>
        </template>
        <footer>GameScope · 多平台游戏竞品智能分析系统 <span>数据驱动洞察，智能辅助决策</span></footer>
      </div>
    </main>
  </div>
</template>
