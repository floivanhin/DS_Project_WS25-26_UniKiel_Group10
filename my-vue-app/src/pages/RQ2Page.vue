<template>
  <div class="page">
    <section class="hero">
      <p class="kicker">RQ2</p>
      <h1 class="page-title">
        How does the matchday affect the amount of goals?
      </h1>
      <p class="page-subtitle">
        This page compares total goals across Bundesliga matchdays for multiple
        seasons. You can switch between stacked bars, a line chart, and an area
        chart to inspect the pattern from different angles.
      </p>
    </section>

    <section class="description-box">
      The visualization shows how many total goals were scored on each matchday
      in different seasons. The chart modes are based on the same aggregated
      dataset and avoid using an actual histogram for already grouped values.
    </section>

    <section class="summary-grid">
      <div class="summary-card">
        <span class="summary-label">Minimum amount of goals scored on a matchday in 2024/25</span>
        <strong class="summary-value">19</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">Maximum amount of goals scored on a matchday in 2024/25</span>
        <strong class="summary-value">37</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">Median amount of goals scored on a matchday in 2024/25</span>
        <strong class="summary-value">30</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">Total amount of goals scored in 2024/25</span>
        <strong class="summary-value">959</strong>
      </div>
      
    </section>

    <section class="controls-card">
      <div class="control-block">
        <span class="control-label">Chart view</span>
        <div class="button-group">
          <button
            v-for="mode in chartModes"
            :key="mode"
            type="button"
            class="toggle-button"
            :class="{ 'toggle-button-active': chartMode === mode }"
            @click="chartMode = mode"
          >
            {{ formatChartModeLabel(mode) }}
          </button>
        </div>
      </div>

      <p class="selection-summary">
        Current selection: <strong>{{ formatChartModeLabel(chartMode) }}</strong
        >. Seasons included: <strong>{{ availableColumns.length }}</strong
        >.
      </p>
    </section>

    <section v-if="error" class="status-box error-box">
      {{ error }}
    </section>

    <section v-else class="chart-card">
      <h2 class="section-title">Goals by matchday</h2>
      <p class="chart-note">
        The chart displays total goals per matchday for each available season.
      </p>

      <div ref="plotRef" class="chart"></div>
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
import rq2Csv from "../../data/RQ2.csv?raw";

type ChartMode = "bar" | "line" | "area";
type CsvRow = Record<string, number | string>;

const chartModes: ChartMode[] = ["bar", "line", "area"];
const chartMode = ref<ChartMode>("bar");
const plotRef = ref<HTMLDivElement | null>(null);
const error = ref("");

const yColumns = [
  "total_goals_2020-2021",
  "total_goals_2021-2022",
  "total_goals_2022-2023",
  "total_goals_2023-2024",
  "total_goals_2024-2025",
] as const;

function parseCSV(text: string): CsvRow[] {
  const lines = text.trim().split(/\r?\n/);
  if (lines.length < 2) {
    return [];
  }

  const headers = lines[0].split(",").map((value) => value.trim());

  return lines.slice(1).map((line) => {
    const values = line.split(",").map((value) => value.trim());
    const row: CsvRow = {};

    headers.forEach((header, index) => {
      const rawValue = values[index] ?? "";
      const numericValue = Number(rawValue);
      row[header] =
        rawValue !== "" && !Number.isNaN(numericValue)
          ? numericValue
          : rawValue;
    });

    return row;
  });
}

const rows = parseCSV(rq2Csv);

const availableColumns = computed(() => {
  if (rows.length === 0) {
    return [];
  }

  return yColumns.filter((column) => column in rows[0]);
});

function formatChartModeLabel(mode: ChartMode): string {
  if (mode === "bar") return "Stacked bars";
  if (mode === "line") return "Line chart";
  return "Area chart";
}

function formatSeasonLabel(columnName: string): string {
  return columnName.replace("total_goals_", "");
}

async function waitForChartReady(): Promise<void> {
  await nextTick();
  await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()));
}

async function renderChart() {
  await waitForChartReady();

  if (
    !plotRef.value ||
    rows.length === 0 ||
    availableColumns.value.length === 0
  ) {
    return;
  }

  const x = rows.map((row) => Number(row.matchday));

  const traces = availableColumns.value.map((column) => {
    const name = formatSeasonLabel(column);
    const y = rows.map((row) => Number(row[column]));

    if (chartMode.value === "bar") {
      return {
        type: "bar",
        x,
        y,
        name,
        hovertemplate:
          "<b>Season:</b> " +
          name +
          "<br><b>Matchday:</b> %{x}<br><b>Goals:</b> %{y}<extra></extra>",
      };
    }

    return {
      type: "scatter",
      mode: "lines+markers",
      stackgroup: chartMode.value === "area" ? "goals" : undefined,
      x,
      y,
      name,
      line: {
        width: 2,
      },
      hovertemplate:
        "<b>Season:</b> " +
        name +
        "<br><b>Matchday:</b> %{x}<br><b>Goals:</b> %{y}<extra></extra>",
    };
  });

  await Plotly.react(
    plotRef.value,
    traces,
    {
      title: "Total goals by matchday",
      xaxis: { title: "Matchday" },
      yaxis: { title: "Goals" },
      barmode: chartMode.value === "bar" ? "stack" : undefined,
      margin: { t: 60, r: 20, l: 60, b: 60 },
      legend: { orientation: "h", y: -0.2 },
      paper_bgcolor: "#ffffff",
      plot_bgcolor: "#ffffff",
    },
    {
      responsive: true,
      displayModeBar: false,
    },
  );
}

function handleResize() {
  if (plotRef.value) {
    Plotly.Plots.resize(plotRef.value);
  }
}

watch(chartMode, async () => {
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

  if (plotRef.value) {
    Plotly.purge(plotRef.value);
  }
});
</script>
