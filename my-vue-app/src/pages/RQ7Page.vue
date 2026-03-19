<template>
  <div class="rq1-page">
    <section class="rq1-hero">
      <h1 class="rq1-page-title">
        How do substitutions affect the number of shots on goal in the second half?
      </h1>
      <p class="rq1-page-subtitle">
        We tried to answer this question in three different ways. Our first graph shows the average number
        of shots taken by a team based on the number of substitutions they took.
        Our second graph shows how the amount of shots in the second half changes when comparing the time
        before and after the minute of the average substitution by that team during that game based on 
        the minute of the average substitution.
        Our third graph shows how the total number of minutes played by substituted players affects the average amount 
        of shots taken in the second half. The resulting graph was smoothed, using a rolling average. 
        The window size for the rolling average calculation can be adjusted manually using a slider.
      </p>
    </section>

    <section class="rq1-controls">
      <div class="rq1-control-block">
        <span class="rq1-control-label">Metric</span>
        <div class="rq1-radio-group">
          <label class="rq1-radio-option">
            <input v-model="selectedMetric" type="radio" value="NumOfSubs" />
            <span>Number of substitutions</span>
          </label>

          <label class="rq1-radio-option">
            <input v-model="selectedMetric" type="radio" value="Timing" />
            <span>Substitution timing</span>
          </label>

          <label class="rq1-radio-option">
            <input v-model="selectedMetric" type="radio" value="Minutes" />
            <span>Number of minutes</span>
          </label>
        </div>
      </div>
      <div v-if="selectedMetric === 'Minutes'" class="rq1-slider-container">
        <label class="rq1-control-label">
        Smoothing Window: <span style="color: #441AEE; font-weight: bold;">{{ windowSize }}</span>
        </label>
        <input 
          type="range" 
          min="2" 
          max="20" 
          step="1"
          v-model.number="windowSize" 
          class="rq1-slider"
        />
        <div class="slider-hints">
          <span>2</span>
          <span>20</span>
        </div>
      </div>
    </section>

    <section v-if="loading" class="rq1-status-box">
      Loading dashboard...
    </section>

    <section v-else-if="error" class="rq1-status-box rq1-error-box">
      {{ error }}
    </section>

    <template v-else>
      <section class="rq1-chart-section">
        <div ref="mainChartRef" class="rq1-chart"></div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed, nextTick } from "vue";
import Plotly from "plotly.js-dist-min";
import "../assets/style.css";

// --- 1. TYPES & STATE ---
interface RQ8Data {
  sub_count: number;
  total_shots_secondHalf: number;
  avg_sub: number;
  spm_diff: number;
  total_sub_time: number;
}

const df_RQ8 = ref<RQ8Data[]>([]);
const selectedMetric = ref('NumOfSubs');
const toggleBarBox = ref(false); // Replacement for daq.BooleanSwitch
const windowSize = ref(10);     // Replacement for dcc.Slider
const loading = ref(true);
const error = ref<string | null>(null);
const mainChartRef = ref<HTMLElement | null>(null);

// --- 2. MATHEMATICAL WORKAROUNDS (The "Pandas" logic in JS) ---

// Replicates pandas .rolling(window=n, center=True).mean()
const getRollingAverage = (data: {x: number, y: number}[], window: number) => {
  return data.map((val, idx, arr) => {
    const offset = Math.floor(window / 2);
    const start = Math.max(0, idx - offset);
    const end = Math.min(arr.length, idx + offset + 1);
    const slice = arr.slice(start, end);
    const sum = slice.reduce((acc, curr) => acc + curr.y, 0);
    return { x: val.x, y: sum / slice.length };
  });
};

// Replicates pandas .groupby().mean()
const getGroupedMean = (data: RQ8Data[], key: keyof RQ8Data, valueKey: keyof RQ8Data) => {
  const groups: Record<number, number[]> = {};
  data.forEach(item => {
    const k = Math.round(item[key] as number);
    if (!groups[k]) groups[k] = [];
    groups[k].push(item[valueKey] as number);
  });
  
  return Object.keys(groups).map(k => ({
    x: Number(k),
    y: groups[Number(k)].reduce((a, b) => a + b, 0) / groups[Number(k)].length
  })).sort((a, b) => a.x - b.x);
};

// --- 3. GRAPHING ENGINE ---
const updateGraph = async () => {
  await nextTick();
  if (!mainChartRef.value || df_RQ8.value.length === 0) return;

  // Sync with your style.css variables if needed
  const style = getComputedStyle(document.documentElement);
  const gridColor = "LightGray";

  let traces: any[] = [];
  let layout: any = {
    template: "plotly_white",
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    margin: { l: 60, r: 40, t: 80, b: 60 },
    xaxis: { showgrid: true, gridcolor: gridColor },
    yaxis: { showgrid: true, gridcolor: gridColor }
  };

  if (selectedMetric.value === 'NumOfSubs') {
    const filtered = df_RQ8.value.filter(d => [2, 3, 4, 5].includes(d.sub_count));
    
    if (toggleBarBox.value) {
      // Bar Chart (Grouped Mean)
      const grouped = getGroupedMean(filtered, 'sub_count', 'total_shots_secondHalf');
      traces = [{
        x: grouped.map(d => d.x),
        y: grouped.map(d => d.y),
        type: 'bar',
        marker: { color: '#02A508' }
      }];
    } else {
      // Box Plot
      traces = [2, 3, 4, 5].map(count => ({
        y: filtered.filter(d => d.sub_count === count).map(d => d.total_shots_secondHalf),
        type: 'box',
        name: `${count} Subs`,
        marker: { color: '#DED11D' }
      }));
    }
    layout.title = "Number of Substitutions vs Shots in 2nd Half";
  } 
  
  else if (selectedMetric.value === 'Timing') {
    const filtered = df_RQ8.value.filter(d => d.avg_sub > 55 && d.avg_sub < 80);
    const grouped = getGroupedMean(filtered, 'avg_sub', 'spm_diff');
    
    traces = [{
      x: grouped.map(d => d.x),
      y: grouped.map(d => d.y),
      mode: 'lines+markers',
      line: { color: '#441AEE', width: 2 },
      marker: { size: 8 }
    }];
    layout.title = "Sub Timing vs Change in Shots Per Min";
    layout.shapes = [{
      type: 'line', x0: 55, x1: 80, y0: 0, y1: 0,
      line: { color: 'black', dash: 'dash', width: 1 }
    }];
  } 
  
  else {
    // Minutes Played (Rolling Average)
    const rawGrouped = getGroupedMean(df_RQ8.value, 'total_sub_time', 'total_shots_secondHalf');
    const smoothed = getRollingAverage(rawGrouped, windowSize.value);
    
    traces = [{
      x: smoothed.map(d => d.x),
      y: smoothed.map(d => d.y),
      mode: 'lines+markers',
      line: { color: '#441AEE', width: 2 }
    }];
    layout.title = `Minutes Played vs Shots (Window: ${windowSize.value})`;
  }

  Plotly.react(mainChartRef.value, traces, layout);
};

// --- 4. LIFECYCLE & WATCHERS ---
watch([selectedMetric, toggleBarBox, windowSize], updateGraph);

onMounted(async () => {
  try {
    const res = await fetch("/data/RQ8.json"); // Ensure this is JSON now
    if (!res.ok) throw new Error("Could not fetch data");
    df_RQ8.value = await res.json();
    loading.value = false;
    updateGraph();
  } catch (e: any) {
    error.value = e.message;
    loading.value = false;
  }
});
</script>