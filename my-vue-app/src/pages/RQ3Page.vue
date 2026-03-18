<template>
  <div class="rq1-page">
    <section class="rq1-hero">
      <h1 class="rq1-page-title">
        How does transition time correlate with goal probability?
      </h1>
      <p class="rq1-page-subtitle">
        To answer this research question we scraped raw event data and
        filtered out all the events, where a team won possession in their own half and then shot on the 
        opposing team's goal, before they lost possession. 
        Our first graph shows how many shots were taken and how many
        goals were scored after a team won possession in their half. The results are partitioned based on how much time
        passed between the possession win and the subsequent shot or goal (transition time).
        Our second graph shows the percentage of shots that resulted in a goal based on the transition time.
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

// Setting up the data transformation
const df_RQ3 = ref([]);
const selection = ref("bar");
const selectedMetric = ref("Boxplot");

const loading = ref(true);
const error = ref("");
const mainChartRef = ref(null);

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

// Ordering goals and non-goals by time intervall
const getAggregatedData = (data) => {
  const goals = new Array(labels.length).fill(0);
  const noGoals = new Array(labels.length).fill(0);

  data.forEach((item) => {
    const time = Number(String(item.time_delta).trim());

    if (!Number.isFinite(time)) return;

    const binIndex = bins.findIndex(
      (edge, i) => i < bins.length - 1 && time > edge && time <= bins[i + 1],
    );
    

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

// Creating the graphs
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

// Loading the data
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
