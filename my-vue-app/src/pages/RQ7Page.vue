<template>
  <div class="page">
    <section class="hero">
      <h1 class="page-title">
        How do substitutions affect the number of shots on goal in the second
        half?
      </h1>
      <p class="page-subtitle">
        We approach this question in three different ways. The first chart shows
        the average number of shots taken by a team in the second half depending
        on the number of substitutions made. The second chart compares the
        change in second-half shot rate before and after the average
        substitution minute in a match. The third chart shows how the total
        minutes played by substituted players relate to the average number of
        second-half shots.
      </p>
    </section>

    <section class="description-box">
      Use the metric switch to compare substitution count, substitution timing,
      and total minutes played by substituted players. When the minutes view is
      selected, you can adjust the smoothing window with the slider.
    </section>

    <section class="controls-card">
      <div class="control-block">
        <span class="control-label">Metric</span>

        <div class="button-group">
          <button
            type="button"
            class="toggle-button"
            :class="{ 'toggle-button-active': selectedMetric === 'subCount' }"
            @click="selectedMetric = 'subCount'"
          >
            Number of substitutions
          </button>

          <button
            type="button"
            class="toggle-button"
            :class="{ 'toggle-button-active': selectedMetric === 'timing' }"
            @click="selectedMetric = 'timing'"
          >
            Substitution timing
          </button>

          <button
            type="button"
            class="toggle-button"
            :class="{ 'toggle-button-active': selectedMetric === 'minutes' }"
            @click="selectedMetric = 'minutes'"
          >
            Number of minutes
          </button>
        </div>
      </div>

      <div v-if="selectedMetric === 'subCount'" class="control-block">
        <span class="control-label">Display mode</span>

        <div class="button-group">
          <button
            type="button"
            class="toggle-button"
            :class="{ 'toggle-button-active': !showGroupedBars }"
            @click="showGroupedBars = false"
          >
            Box plot
          </button>

          <button
            type="button"
            class="toggle-button"
            :class="{ 'toggle-button-active': showGroupedBars }"
            @click="showGroupedBars = true"
          >
            Grouped mean
          </button>
        </div>
      </div>

      <div
        v-if="selectedMetric === 'minutes'"
        class="control-block slider-block"
      >
        <label class="control-label" for="windowSizeRange">
          Smoothing window:
          <span class="accent-value">{{ windowSize }}</span>
        </label>

        <input
          id="windowSizeRange"
          v-model.number="windowSize"
          class="range-control"
          type="range"
          min="2"
          max="20"
          step="1"
        />

        <div class="range-hints">
          <span>2</span>
          <span>20</span>
        </div>
      </div>

      <p class="selection-summary">
        Current selection:
        <strong>{{ currentMetricLabel }}</strong>
        <span v-if="selectedMetric === 'subCount'">
          - <strong>{{ showGroupedBars ? "Grouped mean" : "Box plot" }}</strong>
        </span>
        <span v-if="selectedMetric === 'minutes'">
          - smoothing window: <strong>{{ windowSize }}</strong>
        </span>
      </p>
    </section>

    <section v-if="!rows.length" class="status-box error-box">
      No rows were found in the RQ7 dataset.
    </section>

    <section v-else class="chart-card">
      <h2 class="section-title">{{ chartTitle }}</h2>
      <p class="chart-note">{{ chartDescription }}</p>
      <div ref="mainChartRef" class="chart"></div>
    </section>
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
import rq7Data from "../../data/RQ8.json";

type Metric = "subCount" | "timing" | "minutes";

type RQ7Row = {
  sub_count: number;
  total_shots_secondHalf: number;
  avg_sub: number;
  spm_diff: number;
  total_sub_time: number;
};

const rows = ref<RQ7Row[]>(Array.isArray(rq7Data) ? rq7Data : []);
const selectedMetric = ref<Metric>("subCount");
const showGroupedBars = ref(false);
const windowSize = ref(10);
const mainChartRef = ref<HTMLDivElement | null>(null);

const currentMetricLabel = computed(() => {
  if (selectedMetric.value === "subCount") return "Number of substitutions";
  if (selectedMetric.value === "timing") return "Substitution timing";
  return "Number of minutes";
});

const chartTitle = computed(() => {
  if (selectedMetric.value === "subCount") {
    return showGroupedBars.value
      ? "Number of substitutions vs average shots in the second half"
      : "Distribution of second-half shots by number of substitutions";
  }

  if (selectedMetric.value === "timing") {
    return "Substitution timing vs change in second-half shot rate";
  }

  return `Minutes played by substitutes vs second-half shots (window: ${windowSize.value})`;
});

const chartDescription = computed(() => {
  if (selectedMetric.value === "subCount") {
    return showGroupedBars.value
      ? "This chart shows the grouped mean of second-half shots for teams making 2 to 5 substitutions."
      : "This chart shows the distribution of second-half shots for teams making 2 to 5 substitutions.";
  }

  if (selectedMetric.value === "timing") {
    return "This chart shows how the change in shots per minute varies with the average substitution timing in a match.";
  }

  return "This chart shows the smoothed relationship between total minutes played by substituted players and the average number of second-half shots.";
});

function getRollingAverage(
  data: Array<{ x: number; y: number }>,
  window: number,
) {
  return data.map((point, index, source) => {
    const offset = Math.floor(window / 2);
    const startIndex = Math.max(0, index - offset);
    const endIndex = Math.min(source.length, index + offset + 1);
    const slice = source.slice(startIndex, endIndex);
    const total = slice.reduce((sum, value) => sum + value.y, 0);

    return {
      x: point.x,
      y: total / slice.length,
    };
  });
}

function getGroupedMean(
  data: RQ7Row[],
  key: keyof RQ7Row,
  valueKey: keyof RQ7Row,
) {
  const groups = new Map<number, number[]>();

  for (const row of data) {
    const groupKey = Math.round(Number(row[key]));
    const currentValues = groups.get(groupKey) ?? [];
    currentValues.push(Number(row[valueKey]));
    groups.set(groupKey, currentValues);
  }

  return Array.from(groups.entries())
    .map(([x, values]) => ({
      x,
      y: values.reduce((sum, value) => sum + value, 0) / values.length,
    }))
    .sort((left, right) => left.x - right.x);
}

async function waitForChartReady(): Promise<void> {
  await nextTick();
  await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()));
}

async function renderChart() {
  await waitForChartReady();

  if (!mainChartRef.value || rows.value.length === 0) {
    return;
  }

  const layout: Record<string, any> = {
    title: chartTitle.value,
    paper_bgcolor: "#ffffff",
    plot_bgcolor: "#ffffff",
    margin: { l: 60, r: 40, t: 60, b: 60 },
    xaxis: { showgrid: true, gridcolor: "#e5e7eb" },
    yaxis: { showgrid: true, gridcolor: "#e5e7eb" },
    legend: { orientation: "h", y: 1.08 },
  };

  let traces: Record<string, any>[] = [];

  if (selectedMetric.value === "subCount") {
    const filtered = rows.value.filter((row) =>
      [2, 3, 4, 5].includes(row.sub_count),
    );

    if (showGroupedBars.value) {
      const grouped = getGroupedMean(
        filtered,
        "sub_count",
        "total_shots_secondHalf",
      );

      traces = [
        {
          x: grouped.map((row) => row.x),
          y: grouped.map((row) => row.y),
          type: "bar",
          marker: { color: "#16a34a" },
          hovertemplate:
            "<b>Substitutions:</b> %{x}<br><b>Average shots:</b> %{y:.2f}<extra></extra>",
        },
      ];

      layout.xaxis = { ...layout.xaxis, title: "Number of substitutions" };
      layout.yaxis = { ...layout.yaxis, title: "Average shots in second half" };
    } else {
      traces = [2, 3, 4, 5].map((count) => ({
        y: filtered
          .filter((row) => row.sub_count === count)
          .map((row) => row.total_shots_secondHalf),
        type: "box",
        name: `${count} subs`,
        marker: { color: "#eab308" },
        hovertemplate:
          "<b>%{fullData.name}</b><br><b>Shots in second half:</b> %{y}<extra></extra>",
      }));

      layout.yaxis = { ...layout.yaxis, title: "Shots in second half" };
    }
  } else if (selectedMetric.value === "timing") {
    const filtered = rows.value.filter(
      (row) => row.avg_sub > 55 && row.avg_sub < 80,
    );
    const grouped = getGroupedMean(filtered, "avg_sub", "spm_diff");

    traces = [
      {
        x: grouped.map((row) => row.x),
        y: grouped.map((row) => row.y),
        mode: "lines+markers",
        type: "scatter",
        line: { color: "#2563eb", width: 2 },
        marker: { size: 8 },
        hovertemplate:
          "<b>Average substitution minute:</b> %{x}<br><b>Change in shots/min:</b> %{y:.3f}<extra></extra>",
      },
    ];

    layout.xaxis = { ...layout.xaxis, title: "Average substitution minute" };
    layout.yaxis = { ...layout.yaxis, title: "Change in shots per minute" };
    layout.shapes = [
      {
        type: "line",
        x0: 55,
        x1: 80,
        y0: 0,
        y1: 0,
        line: { color: "#111827", dash: "dash", width: 1 },
      },
    ];
  } else {
    const grouped = getGroupedMean(
      rows.value,
      "total_sub_time",
      "total_shots_secondHalf",
    );
    const smoothed = getRollingAverage(grouped, windowSize.value);

    traces = [
      {
        x: smoothed.map((row) => row.x),
        y: smoothed.map((row) => row.y),
        mode: "lines+markers",
        type: "scatter",
        line: { color: "#2563eb", width: 2 },
        marker: { size: 6 },
        hovertemplate:
          "<b>Total substitute minutes:</b> %{x}<br><b>Average shots:</b> %{y:.2f}<extra></extra>",
      },
    ];

    layout.xaxis = {
      ...layout.xaxis,
      title: "Total minutes played by substitutes",
    };
    layout.yaxis = { ...layout.yaxis, title: "Average shots in second half" };
  }

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

watch([selectedMetric, showGroupedBars, windowSize], async () => {
  await renderChart();
});

onMounted(async () => {
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
