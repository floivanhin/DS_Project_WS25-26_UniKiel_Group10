<template>
<<<<<<< HEAD
  <div class="rq1-page">
    <section class="rq1-hero">
      <p class="rq1-kicker">RQ3</p>
      <h1 class="rq1-page-title">
        How does transition time correlate with goal probability?
      </h1>
      <p class="rq1-page-subtitle">
        To answer this research question we scraped raw event data and
        filtered out all the events, where a team won possession in their own half and then shot on the 
        opposing team's goal, without losing possession before the shot event.
      </p>
    </section>

    <section class="rq1-description">
      The graphs show how many shots were taken and goals were scored based on how long it took a team to shoot
      after they have won possession in their own half (transition time).
    </section>

    <section class="rq1-controls">
      <div class="rq1-control-block">
        <span class="rq1-control-label">Metric</span>
          <div class="rq1-button-group">
            <button
              class="rq1-toggle-button"
              :class="{ 'rq1-toggle-button-active': selectedMetric === 'Absolute' }"
              type="button"
              @click="selectedMetric = 'Absolute'"
            >
              Absolute Numbers
            </button>
            <button
              class="rq1-toggle-button"
              :class="{
                'rq1-toggle-button-active': selectedMetric === 'Efficiency',
              }"
              type="button"
              @click="selectedMetric = 'Efficiency'"
            >
              Shot Efficiency
            </button>
      </div>
    </div> 
=======
  <div class="page">
    <section class="hero">
      <h1 class="page-title">
        How does transition time correlate with goal probability?
      </h1>
      <p class="page-subtitle">
        To answer this question, we filtered all situations in which a team won
        possession in its own half and then produced a shot before losing
        possession again. The first view shows counts of shots and goals by
        transition-time interval, and the second view shows the corresponding
        conversion rate.
      </p>
    </section>

    <section class="description-box">
      Use the metric switch to compare absolute numbers of shots and goals with
      the conversion rate across transition-time intervals.
    </section>

    <section class="controls-card">
      <div class="control-block">
        <span class="control-label">Metric</span>
        <div class="button-group">
          <button
            type="button"
            class="toggle-button"
            :class="{ 'toggle-button-active': selectedMetric === 'absolute' }"
            @click="selectedMetric = 'absolute'"
          >
            Absolute numbers
          </button>

          <button
            type="button"
            class="toggle-button"
            :class="{ 'toggle-button-active': selectedMetric === 'conversion' }"
            @click="selectedMetric = 'conversion'"
          >
            Shot efficiency
          </button>
        </div>
      </div>

      <p class="selection-summary">
        Current selection:
        <strong>
          {{
            selectedMetric === "absolute"
              ? "Absolute numbers"
              : "Shot efficiency"
          }}
        </strong>
      </p>
>>>>>>> 7dcd9249fa0c4bba5535e68902e259c44a7c292d
    </section>

    <section v-if="error" class="status-box error-box">
      {{ error }}
    </section>

<<<<<<< HEAD
    <template v-else>
      <section class="rq1-chart-section">
        <h2 class="rq1-section-title">{{ getMetricTitle() }}</h2>
        <div ref="mainChartRef" class="rq1-chart"></div>
      </section>
    </template>
=======
    <section v-else class="chart-card">
      <h2 class="section-title">
        {{
          selectedMetric === "absolute"
            ? "Shots and goals by transition time"
            : "Goal conversion rate by transition time"
        }}
      </h2>

      <p class="chart-note">
        {{
          selectedMetric === "absolute"
            ? "This chart compares how many possessions ended without a goal and how many resulted in a goal across transition-time intervals."
            : "This chart shows the percentage of shots that turned into goals in each transition-time interval."
        }}
      </p>

      <div ref="mainChartRef" class="chart"></div>
    </section>
>>>>>>> 7dcd9249fa0c4bba5535e68902e259c44a7c292d
  </div>
</template>

<script setup lang="ts">
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from "vue";
import Plotly from "plotly.js-dist-min";
import rq3Csv from "../../data/RQ3.csv?raw";

<<<<<<< HEAD
// Setting up the data transformation
const df_RQ3 = ref([]);
const selectedMetric = ref("Absolute");
=======
type Metric = "absolute" | "conversion";
>>>>>>> 7dcd9249fa0c4bba5535e68902e259c44a7c292d

type RQ3Row = {
  is_goal: string;
  time_delta: string;
};

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
] as const;

const intervalStarts = [0, 10, 15, 20, 25, 30, 35, 40, 45, 50] as const;

const selectedMetric = ref<Metric>("absolute");
const mainChartRef = ref<HTMLDivElement | null>(null);
const error = ref("");

function parseCSV(text: string): RQ3Row[] {
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

<<<<<<< HEAD
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
      title: selectedMetric.value === "line" ? "Seconds after possession win" : "",
      categoryorder: "array",
      categoryarray: labels,
    },
    yaxis: {
      title: selectedMetric.value === "line" ? "Conversion Rate (%)" : "Count",
      gridcolor: "LightGray",
    },
    margin: { l: 60, r: 40, t: 80, b: 60 },
  };

  if (selectedMetric.value === "Absolute") {
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

function getMetricTitle(){
  if (selectedMetric.value === "Absolute"){
    return "Absolute number of shots and goals by transition time";
  }
  if (selectedMetric.value === "Efficiency") {
    return "Percentage of shots that resulted in a goal by transition time";
  }
}

// Loading the data

watch([selectedMetric, df_RQ3], updateGraph);

function parseCSV(text) {
  const lines = text
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0);

  if (lines.length < 2) return [];

  const headers = lines[0].split(",").map((h) => h.trim().replace(/\r/g, ""));
=======
  if (lines.length < 2) {
    return [];
  }

  const headers = lines[0].split(",").map((value) => value.trim());
>>>>>>> 7dcd9249fa0c4bba5535e68902e259c44a7c292d

  return lines.slice(1).map((line) => {
    const values = line.split(",").map((value) => value.trim());
    const row = {} as RQ3Row;

    headers.forEach((header, index) => {
      row[header as keyof RQ3Row] = values[index] ?? "";
    });

    return row;
  });
}

function isGoal(value: string): boolean {
  const normalized = value.trim().toLowerCase();
  return ["true", "1", "yes", "goal"].includes(normalized);
}

function getBinIndex(time: number): number {
  if (time < 0) {
    return -1;
  }

  for (let index = 0; index < intervalStarts.length - 1; index += 1) {
    if (time >= intervalStarts[index] && time < intervalStarts[index + 1]) {
      return index;
    }
  }

  return intervalStarts.length - 1;
}

const rows = parseCSV(rq3Csv);

const aggregatedData = computed(() => {
  const goals = new Array(labels.length).fill(0);
  const noGoals = new Array(labels.length).fill(0);

  for (const row of rows) {
    const time = Number(row.time_delta);
    if (!Number.isFinite(time)) {
      continue;
    }

    const binIndex = getBinIndex(time);
    if (binIndex < 0) {
      continue;
    }

    if (isGoal(row.is_goal)) {
      goals[binIndex] += 1;
    } else {
      noGoals[binIndex] += 1;
    }
  }

  const percentages = goals.map((goalCount, index) => {
    const total = goalCount + noGoals[index];
    return total > 0 ? (goalCount / total) * 100 : 0;
  });

  return { goals, noGoals, percentages };
});

async function waitForChartReady(): Promise<void> {
  await nextTick();
  await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()));
}

async function renderChart() {
  await waitForChartReady();

  if (!mainChartRef.value) {
    return;
  }

  const { goals, noGoals, percentages } = aggregatedData.value;

  const layout = {
    title:
      selectedMetric.value === "absolute"
        ? "Shots and goals by transition time"
        : "Goal conversion rate per time interval",
    xaxis: {
      title:
        selectedMetric.value === "absolute"
          ? "Transition time interval"
          : "Seconds after possession win",
      categoryorder: "array" as const,
      categoryarray: [...labels],
    },
    yaxis: {
      title:
        selectedMetric.value === "absolute" ? "Count" : "Conversion rate (%)",
      gridcolor: "#e5e7eb",
    },
    margin: { l: 60, r: 24, t: 60, b: 60 },
    paper_bgcolor: "#ffffff",
    plot_bgcolor: "#ffffff",
    legend: { orientation: "h" as const, y: 1.08 },
    barmode: "stack" as const,
  };

  const traces =
    selectedMetric.value === "absolute"
      ? [
          {
            type: "bar",
            name: "No goal",
            x: labels,
            y: noGoals,
            marker: { color: "#dc2626" },
            hovertemplate:
              "<b>Interval:</b> %{x}<br><b>No-goal shots:</b> %{y}<extra></extra>",
          },
          {
            type: "bar",
            name: "Goal",
            x: labels,
            y: goals,
            marker: { color: "#16a34a" },
            hovertemplate:
              "<b>Interval:</b> %{x}<br><b>Goals:</b> %{y}<extra></extra>",
          },
        ]
      : [
          {
            type: "scatter",
            mode: "lines+markers",
            name: "Conversion rate",
            x: labels,
            y: percentages,
            line: { color: "#2563eb", width: 2 },
            marker: { size: 8 },
            hovertemplate:
              "<b>Interval:</b> %{x}<br><b>Conversion rate:</b> %{y:.2f}%<extra></extra>",
          },
        ];

  await Plotly.react(mainChartRef.value, traces, layout, {
    responsive: true,
    displayModeBar: false,
  });
}

function handleResize() {
  if (mainChartRef.value) {
    Plotly.Plots.resize(mainChartRef.value);
  }
}

watch(selectedMetric, async () => {
  await renderChart();
});

onMounted(async () => {
  if (rows.length === 0) {
    error.value = "No rows found in the CSV dataset.";
    return;
  }

  window.addEventListener("resize", handleResize);
  await renderChart();
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);

  if (mainChartRef.value) {
    Plotly.purge(mainChartRef.value);
  }
});
</script>
