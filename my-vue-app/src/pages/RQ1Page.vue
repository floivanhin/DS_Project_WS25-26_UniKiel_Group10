<template>
  <div class="rq1-page">
    <section class="rq1-hero">
      <h1 class="rq1-page-title">
        How do weather conditions influence total goals scored?
      </h1>
      <p class="rq1-page-subtitle">
        Bundesliga matches are grouped by simplified weather categories. The
        dashboard compares total goals by weather condition and shows how many
        matches belong to each group.
      </p>
    </section>

    <section class="rq1-controls">
      <div class="rq1-control-block">
        <label class="rq1-control-label" for="weatherFilter"
          >Weather filter</label
        >
        <select
          id="weatherFilter"
          v-model="selectedWeather"
          class="rq1-select-control"
        >
          <option value="All">All</option>
          <option
            v-for="group in availableWeatherGroups"
            :key="group"
            :value="group"
          >
            {{ group }}
          </option>
        </select>
      </div>

      <div class="rq1-control-block">
        <span class="rq1-control-label">Metric</span>
        <div class="rq1-radio-group">
          <label class="rq1-radio-option">
            <input v-model="selectedMetric" type="radio" value="avg" />
            <span>Average goals</span>
          </label>

          <label class="rq1-radio-option">
            <input v-model="selectedMetric" type="radio" value="median" />
            <span>Median goals</span>
          </label>

          <label class="rq1-radio-option">
            <input v-model="selectedMetric" type="radio" value="count" />
            <span>Match count</span>
          </label>
        </div>
      </div>
    </section>

    <section class="rq1-selection-summary">
      <strong>Current selection:</strong>
      {{ selectedWeather }}. <strong>Matches:</strong>
      {{ filteredMatches.length }}. <strong>{{ metricSummaryLabel }}:</strong>
      {{ metricSummaryValue }}.
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

      <section class="rq1-chart-section">
        <div ref="distributionChartRef" class="rq1-chart"></div>
      </section>

      <section class="rq1-table-section">
        <h2 class="rq1-section-title">Summary table</h2>

        <div class="rq1-table-wrapper">
          <table class="rq1-summary-table">
            <thead>
              <tr>
                <th>Weather group</th>
                <th>Average goals</th>
                <th>Median goals</th>
                <th>Matches</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in summaryRows" :key="row.weather_group">
                <td>{{ row.weather_group }}</td>
                <td>{{ row.avg_goals.toFixed(2) }}</td>
                <td>{{ row.median_goals.toFixed(2) }}</td>
                <td>{{ row.match_count }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";
import Plotly from "plotly.js-dist-min";
import "../assets/style.css";

type MatchItem = {
  weather?: {
    conditions?: string;
  };
  score?: {
    fullTime?: {
      home?: number | null;
      away?: number | null;
    };
  };
};

type JsonData = {
  matches?: MatchItem[];
};

type SummaryRow = {
  weather_group: string;
  avg_goals: number;
  median_goals: number;
  match_count: number;
};

const loading = ref(true);
const error = ref("");
const allMatches = ref<MatchItem[]>([]);

const selectedWeather = ref("All");
const selectedMetric = ref<"avg" | "median" | "count">("avg");

const mainChartRef = ref<HTMLDivElement | null>(null);
const distributionChartRef = ref<HTMLDivElement | null>(null);

function classifyWeather(condition?: string): string {
  if (!condition || typeof condition !== "string") return "Other";

  const c = condition.toLowerCase();

  if (c.includes("snow")) return "Snow";
  if (c.includes("rain") || c.includes("drizzle") || c.includes("showers"))
    return "Rain";
  if (c.includes("overcast")) return "Cloudy";
  if (c.includes("cloud")) return "Cloudy";
  if (c.includes("clear")) return "Clear";

  return "Other";
}

function getTotalGoals(match: MatchItem): number {
  const homeGoals = Number(match.score?.fullTime?.home ?? 0);
  const awayGoals = Number(match.score?.fullTime?.away ?? 0);
  return homeGoals + awayGoals;
}

function median(values: number[]): number {
  if (values.length === 0) return 0;

  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);

  return sorted.length % 2 === 0
    ? (sorted[middle - 1] + sorted[middle]) / 2
    : sorted[middle];
}

function waitForFrame(): Promise<void> {
  return new Promise((resolve) => {
    requestAnimationFrame(() => resolve());
  });
}

const availableWeatherGroups = computed(() => {
  const groups = new Set<string>();

  for (const match of allMatches.value) {
    groups.add(classifyWeather(match.weather?.conditions));
  }

  return ["Clear", "Cloudy", "Rain", "Snow", "Other"].filter((group) =>
    groups.has(group),
  );
});

const filteredMatches = computed(() => {
  if (selectedWeather.value === "All") {
    return allMatches.value;
  }

  return allMatches.value.filter(
    (match) =>
      classifyWeather(match.weather?.conditions) === selectedWeather.value,
  );
});

const summaryRows = computed<SummaryRow[]>(() => {
  const grouped: Record<string, number[]> = {};

  for (const match of filteredMatches.value) {
    const weatherGroup = classifyWeather(match.weather?.conditions);
    const totalGoals = getTotalGoals(match);

    if (!grouped[weatherGroup]) {
      grouped[weatherGroup] = [];
    }

    grouped[weatherGroup].push(totalGoals);
  }

  const orderedGroups = ["Clear", "Cloudy", "Rain", "Snow", "Other"];

  return orderedGroups
    .filter((group) => grouped[group] && grouped[group].length > 0)
    .map((group) => {
      const goals = grouped[group];
      const sum = goals.reduce((acc, value) => acc + value, 0);

      return {
        weather_group: group,
        avg_goals: sum / goals.length,
        median_goals: median(goals),
        match_count: goals.length,
      };
    });
});

const metricSummaryLabel = computed(() => {
  if (selectedMetric.value === "avg") return "Average total goals";
  if (selectedMetric.value === "median") return "Median total goals";
  return "Match count";
});

const metricSummaryValue = computed(() => {
  if (filteredMatches.value.length === 0) return "0.00";

  const goals = filteredMatches.value.map(getTotalGoals);

  if (selectedMetric.value === "avg") {
    const avg = goals.reduce((acc, value) => acc + value, 0) / goals.length;
    return avg.toFixed(2);
  }

  if (selectedMetric.value === "median") {
    return median(goals).toFixed(2);
  }

  return String(filteredMatches.value.length);
});

function getMetricValue(row: SummaryRow): number {
  if (selectedMetric.value === "avg") return row.avg_goals;
  if (selectedMetric.value === "median") return row.median_goals;
  return row.match_count;
}

function getMetricTitle(): string {
  if (selectedMetric.value === "avg")
    return "Average total goals by weather condition";
  if (selectedMetric.value === "median")
    return "Median total goals by weather condition";
  return "Number of matches by weather condition";
}

function getMetricYAxis(): string {
  if (selectedMetric.value === "avg") return "Average total goals";
  if (selectedMetric.value === "median") return "Median total goals";
  return "Number of matches";
}

async function renderCharts() {
  await nextTick();
  await waitForFrame();

  if (!mainChartRef.value || !distributionChartRef.value) return;

  const rows = summaryRows.value;
  const goals = filteredMatches.value.map(getTotalGoals);

  await Plotly.newPlot(
    mainChartRef.value,
    [
      {
        type: "bar",
        x: rows.map((row) => row.weather_group),
        y: rows.map((row) => getMetricValue(row)),
        text: rows.map((row) =>
          selectedMetric.value === "count"
            ? String(getMetricValue(row))
            : getMetricValue(row).toFixed(2),
        ),
        textposition: "outside",
        hovertemplate:
          selectedMetric.value === "count"
            ? "Weather: %{x}<br>Number of matches: %{y}<extra></extra>"
            : `Weather: %{x}<br>${getMetricYAxis()}: %{y:.2f}<extra></extra>`,
      },
    ],
    {
      title: getMetricTitle(),
      xaxis: { title: "Weather condition" },
      yaxis: { title: getMetricYAxis() },
      margin: { t: 60, r: 20, b: 60, l: 70 },
      paper_bgcolor: "#ffffff",
      plot_bgcolor: "#ffffff",
    },
    {
      responsive: true,
      displayModeBar: false,
    },
  );

  await Plotly.newPlot(
    distributionChartRef.value,
    [
      {
        type: "histogram",
        x: goals,
        hovertemplate:
          "Total goals: %{x}<br>Number of matches: %{y}<extra></extra>",
      },
    ],
    {
      title: "Distribution of total goals",
      xaxis: { title: "Total goals in a match" },
      yaxis: { title: "Number of matches" },
      margin: { t: 60, r: 20, b: 60, l: 70 },
      paper_bgcolor: "#ffffff",
      plot_bgcolor: "#ffffff",
    },
    {
      responsive: true,
      displayModeBar: false,
    },
  );

  Plotly.Plots.resize(mainChartRef.value);
  Plotly.Plots.resize(distributionChartRef.value);
}

async function loadData() {
  try {
    loading.value = true;
    error.value = "";

    const response = await fetch("/data/combined_matches_weather.json");

    if (!response.ok) {
      throw new Error(`Could not load JSON: ${response.status}`);
    }

    const data: JsonData = await response.json();
    allMatches.value = data.matches ?? [];

    if (allMatches.value.length === 0) {
      throw new Error("No matches found in JSON");
    }

    loading.value = false;
    await renderCharts();
  } catch (e) {
    loading.value = false;
    error.value = e instanceof Error ? e.message : "Unknown error";
  }
}

watch([selectedWeather, selectedMetric], async () => {
  if (!loading.value && !error.value) {
    await renderCharts();
  }
});

onMounted(async () => {
  await loadData();
});
</script>
