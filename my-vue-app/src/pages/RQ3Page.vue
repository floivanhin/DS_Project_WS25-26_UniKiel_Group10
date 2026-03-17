<template>
  <div class="rq1-page">
    <section class="rq1-hero">
      <h1 class="rq1-page-title">
        How does the time between winning possession in your own half and the
        first shot correlate with the probability of scoring (per shot)?
      </h1>
      <p class="rq1-page-subtitle">
        How the time between possession wins in the own half and a subsequent
        shot correlates with the probability of scoring a goal
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
import { ref, onMounted, watch, computed, nextTick } from "vue";
import Plotly from "plotly.js-dist-min";
import "../assets/style.css";

// --- 1. STATE ---
const df_RQ3 = ref([]);
const selection = ref("bar");
const selectedMetric = ref("Boxplot");

const loading = ref(true);
const error = ref("");
const mainChartRef = ref(null);

// Definitions matching your Python code
const labels = [
  "0-10s",
  "10-15s",
  "15-20s",
  "20-25s",
  "25-30s",
  "30-35s",
  "35-40s",
  "40-45s",
  "45-50s",
  "50s+",
];
const bins = [0, 10, 15, 20, 25, 30, 35, 40, 45, 50, Infinity];

// --- 2. THE CALCULATION ENGINE ---
const getAggregatedData = (data) => {
  const goals = new Array(labels.length).fill(0);
  const noGoals = new Array(labels.length).fill(0);

  data.forEach((item) => {
    const time = Number(String(item.time_delta).trim());

    if (!Number.isFinite(time)) return;

    // for 0 ≤ t < 10
    
    const binIndex = bins.findIndex(
      (edge, i) => i < bins.length - 1 && time > edge && time <= bins[i + 1],
    );
    

    // for 0 < t ≤ 10

    //const binIndex = bins.findIndex(
    //  (edge, i) => i < bins.length - 1 && time >= edge && time < bins[i + 1],
    //);

    if (binIndex !== -1) {
      const goalValue = String(item.is_goal).trim().toLowerCase();

      const isGoal =
        goalValue === "true" ||
        goalValue === "1" ||
        goalValue === "yes" ||
        goalValue === "goal";

      if (isGoal) {
        goals[binIndex]++;
      } else {
        noGoals[binIndex]++;
      }
    }
  });

  const percentages = goals.map((g, i) => {
    const total = g + noGoals[i];
    return total > 0 ? (g / total) * 100 : 0;
  });

  return { goals, noGoals, percentages };
};

// --- 3. THE GRAPHING FUNCTION ---
const updateGraph = async () => {
  await nextTick();

  const gd = mainChartRef.value;
  if (!gd || df_RQ3.value.length === 0) return;

  const { goals, noGoals, percentages } = getAggregatedData(df_RQ3.value);
  let traces = [];
  let layout = {
    template: "plotly_white",
    xaxis: {
      title: selection.value === "line" ? "Seconds after possession win" : "",
      categoryorder: "array",
      categoryarray: labels,
    },
    yaxis: {
      title: selection.value === "line" ? "Conversion Rate (%)" : "Count",
      gridcolor: "LightGray",
    },
    margin: { l: 60, r: 40, t: 80, b: 60 },
  };

  if (selection.value === "bar") {
    traces = [
      {
        x: labels,
        y: noGoals,
        name: "No Goal",
        type: "bar",
        marker: { color: "#FF0000" },
      },
      {
        x: labels,
        y: goals,
        name: "Goal",
        type: "bar",
        marker: { color: "#27ae60" },
      },
    ];
    layout.barmode = "stack";
    layout.title = "Shots and Goals by Transition Time";
  } else {
    traces = [
      {
        x: labels,
        y: percentages,
        mode: "lines+markers",
        line: { color: "#27ae60", width: 2 },
        marker: { size: 8 },
        name: "Conversion Rate",
      },
    ];
    layout.title = "Goal Conversion Rate per Time Interval";
  }

  Plotly.react(gd, traces, layout, { responsive: true });
};

// --- 4. REACTIVITY & DATA LOAD ---
const description = computed(() => {
  return selection.value === "bar"
    ? "Amount of shots and goals that happened after a team gained possession in its own half based on the time it took between winning possession and shooting."
    : "Percentage of shots that turned into goals based on the time it took for a team between winning possession in its own half and shooting";
});

watch(selectedMetric, (value) => {
  selection.value = value === "Boxplot" ? "bar" : "line";
});

watch([selection, df_RQ3], updateGraph);

function parseCSV(text) {
  const lines = text
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0);

  if (lines.length < 2) return [];

  const headers = lines[0].split(",").map((h) => h.trim().replace(/\r/g, ""));

  return lines.slice(1).map((line) => {
    const values = line.split(",").map((v) => v.trim().replace(/\r/g, ""));
    const obj = {};

    headers.forEach((header, index) => {
      obj[header] = values[index] ?? "";
    });

    return obj;
  });
}

onMounted(async () => {
  try {
    const res = await fetch("/data/RQ3.csv");

    if (!res.ok) {
      throw new Error(`Failed to load CSV: ${res.status}`);
    }

    const csvText = await res.text();
    df_RQ3.value = parseCSV(csvText);

    loading.value = false;
    await nextTick();
    await updateGraph();
  } catch (e) {
    console.error("Failed to load RQ3 data", e);
    error.value = "Failed to load RQ3 data.";
    loading.value = false;
  }
});
</script>
