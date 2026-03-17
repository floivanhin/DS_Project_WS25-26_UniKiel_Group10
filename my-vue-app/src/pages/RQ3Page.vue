<template>
  <div class="rq1-page">
    <section class="rq1-hero">
      <h1 class="rq1-page-title">
        How does the time between winning possession in your own half and the first shot 
        correlate with the probability of scoring (per shot)?
      </h1>
      <p class="rq1-page-subtitle">
        How the time between possession wins in the own half and a subsequent shot correlates with 
        the probability of scoring a goal
      </p>
    </section>

    <section class="rq1-controls">
      <div class="rq1-control-block">
        <span class="rq1-control-label">Metric</span>
        <div class="rq1-radio-group">
          <label class="rq1-radio-option">
            <input v-model="selectedMetric" type="radio" value="Boxplot" />
            <span>Absolute numbers</span>
          </label>

          <label class="rq1-radio-option">
            <input v-model="selectedMetric" type="radio" value="Barplot" />
            <span>Shot efficiency</span>
          </label>

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


<script setup>
import { ref, onMounted, watch, computed } from 'vue';
import Plotly from 'plotly.js-dist-min';
import "../assets/style.css";

// --- 1. STATE ---
const df_RQ3 = ref([]); 
const selection = ref('bar');

// Definitions matching your Python code
const labels = ["0-10s", "10-15s", "15-20s", "20-25s", "25-30s", "30-35s", "35-40s", "40-45s", "45-50s", "50s+"];
const bins = [0, 10, 15, 20, 25, 30, 35, 40, 45, 50, Infinity];

// --- 2. THE CALCULATION ENGINE ---

const getAggregatedData = (data) => {
  // Initialize counts
  const goals = new Array(labels.length).fill(0);
  const noGoals = new Array(labels.length).fill(0);

  data.forEach(item => {
    const time = item.time_delta;
    // Find which bin the time falls into (logic of pd.cut)
    const binIndex = bins.findIndex((edge, i) => time >= edge && time < bins[i + 1]);
    
    if (binIndex !== -1) {
      if (item.is_goal === true || item.is_goal === 1) {
        goals[binIndex]++;
      } else {
        noGoals[binIndex]++;
      }
    }
  });

  // Calculate percentages (Conversion Rate)
  const percentages = goals.map((g, i) => {
    const total = g + noGoals[i];
    return total > 0 ? Math.round((g / total) * 100) : 0;
  });

  return { goals, noGoals, percentages };
};

// --- 3. THE GRAPHING FUNCTION ---
const updateGraph = () => {
  const gd = document.getElementById('main-graph-div');
  if (!gd || df_RQ3.value.length === 0) return;

  const { goals, noGoals, percentages } = getAggregatedData(df_RQ3.value);
  let traces = [];
  let layout = {
    template: 'plotly_white',
    xaxis: { 
        title: selection.value === 'line' ? "Seconds after possession win" : "",
        categoryorder: "array", 
        categoryarray: labels 
    },
    yaxis: { 
        title: selection.value === 'line' ? "Conversion Rate (%)" : "Count",
        gridcolor: 'LightGray' 
    },
    margin: { l: 60, r: 40, t: 80, b: 60 }
  };

  if (selection.value === 'bar') {
    // Stacked Bar Plot
    traces = [
      {
        x: labels,
        y: noGoals,
        name: 'No Goal',
        type: 'bar',
        marker: { color: '#FF0000' }
      },
      {
        x: labels,
        y: goals,
        name: 'Goal',
        type: 'bar',
        marker: { color: '#27ae60' }
      }
    ];
    layout.barmode = 'stack';
    layout.title = "Shots and Goals by Transition Time";
  } else {
    // Line Plot
    traces = [{
      x: labels,
      y: percentages,
      mode: 'lines+markers',
      line: { color: '#27ae60', width: 2 },
      marker: { size: 8 },
      name: 'Conversion Rate'
    }];
    layout.title = "Goal Conversion Rate per Time Interval";
  }

  Plotly.react(gd, traces, layout);
};

// --- 4. REACTIVITY & DATA LOAD ---
const description = computed(() => {
  return selection.value === 'bar' 
    ? "Amount of shots and goals that happened after a team gained possession in its own half based on the time it took between winning possession and shooting."
    : "Percentage of shots that turned into goals based on the time it took for a team between winning possession in its own half and shooting";
});

watch([selection, df_RQ3], updateGraph);

onMounted(async () => {
  try {
    const res = await fetch('/data/RQ3.json');
    df_RQ3.value = await res.json();
  } catch (e) {
    console.error("Failed to load RQ3 data", e);
  }
});
</script>