<template>
  <div class="page">
    <section class="hero">
      <h1 class="page-title">
        How do weather conditions influence total goals scored?
      </h1>
      <p class="page-subtitle">
        Bundesliga matches are grouped into simplified weather categories. The
        dashboard compares total goals by weather condition and shows how many
        matches belong to each group.
      </p>
    </section>

    <section class="description-box">
      Explore whether different weather groups are linked to changes in scoring.
      Use the filter to narrow the sample and switch between average goals,
      median goals, and match count.
    </section>

    <section class="summary-grid">
      <div class="summary-card">
        <span class="summary-label">Matches in selection</span>
        <strong class="summary-value">{{ filteredMatches.length }}</strong>
      </div>

      <div class="summary-card">
        <span class="summary-label">Weather filter</span>
        <strong class="summary-value summary-value-small">
          {{ selectedWeather }}
        </strong>
      </div>

      <div class="summary-card">
        <span class="summary-label">Selected metric</span>
        <strong class="summary-value summary-value-small">
          {{ metricButtonLabel }}
        </strong>
      </div>

      <div class="summary-card">
        <span class="summary-label">{{ metricSummaryLabel }}</span>
        <strong class="summary-value">{{ metricSummaryValue }}</strong>
      </div>
    </section>

    <section class="controls-card">
      <div class="toolbar">
        <div class="control-block control-block-compact">
          <label class="control-label" for="weatherFilter">
            Weather filter
          </label>
          <select
            id="weatherFilter"
            v-model="selectedWeather"
            class="select-control"
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

        <div class="control-block">
          <span class="control-label">Metric</span>
          <div class="button-group">
            <button
              type="button"
              class="toggle-button"
              :class="{ 'toggle-button-active': selectedMetric === 'avg' }"
              @click="selectedMetric = 'avg'"
            >
              Average goals
            </button>
            <button
              type="button"
              class="toggle-button"
              :class="{ 'toggle-button-active': selectedMetric === 'median' }"
              @click="selectedMetric = 'median'"
            >
              Median goals
            </button>
            <button
              type="button"
              class="toggle-button"
              :class="{ 'toggle-button-active': selectedMetric === 'count' }"
              @click="selectedMetric = 'count'"
            >
              Match count
            </button>
          </div>
        </div>
      </div>

      <p class="selection-summary">
        Current selection: <strong>{{ selectedWeather }}</strong
        >. Matches: <strong>{{ filteredMatches.length }}</strong
        >. {{ metricSummaryLabel }}: <strong>{{ metricSummaryValue }}</strong
        >.
      </p>
    </section>

    <section v-if="error" class="status-box error-box">
      {{ error }}
    </section>

    <template v-else>
      <section class="chart-card">
        <h2 class="section-title">{{ metricTitle }}</h2>
        <p class="chart-note">
          This chart compares the selected weather groups using the current
          metric.
        </p>
        <div ref="mainChartRef" class="chart"></div>
      </section>

      <section class="chart-card">
        <h2 class="section-title">Distribution of total goals</h2>
        <p class="chart-note">
          The histogram shows how many matches ended with a given total number
          of goals in the current selection.
        </p>
        <div ref="distributionChartRef" class="chart"></div>
      </section>

      <section class="table-card">
        <h2 class="section-title">Summary table</h2>

        <div class="table-wrapper">
          <table class="summary-table">
            <thead>
              <tr>
                <th>Weather group</th>
                <th>Average goals</th>
                <th>Median goals</th>
                <th>Matches</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in summaryRows" :key="row.weatherGroup">
                <td>{{ row.weatherGroup }}</td>
                <td>{{ row.averageGoals.toFixed(2) }}</td>
                <td>{{ row.medianGoals.toFixed(2) }}</td>
                <td>{{ row.matchCount }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
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
import weatherDataUrl from "../../data/combined_matches_weather.json?url";

type Metric = "avg" | "median" | "count";

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
  weatherGroup: string;
  averageGoals: number;
  medianGoals: number;
  matchCount: number;
};

const WEATHER_ORDER = ["Clear", "Cloudy", "Rain", "Snow", "Other"] as const;

const error = ref("");
const allMatches = ref<MatchItem[]>([]);
const selectedWeather = ref("All");
const selectedMetric = ref<Metric>("avg");

const mainChartRef = ref<HTMLDivElement | null>(null);
const distributionChartRef = ref<HTMLDivElement | null>(null);

function classifyWeather(condition?: string): string {
  if (!condition) {
    return "Other";
  }

  const normalized = condition.toLowerCase();

  if (normalized.includes("snow")) return "Snow";
  if (
    normalized.includes("rain") ||
    normalized.includes("drizzle") ||
    normalized.includes("showers")
  ) {
    return "Rain";
  }
  if (normalized.includes("overcast") || normalized.includes("cloud")) {
    return "Cloudy";
  }
  if (normalized.includes("clear")) return "Clear";

  return "Other";
}

function getTotalGoals(match: MatchItem): number {
  const homeGoals = Number(match.score?.fullTime?.home ?? 0);
  const awayGoals = Number(match.score?.fullTime?.away ?? 0);
  return homeGoals + awayGoals;
}

function getMedian(values: number[]): number {
  if (values.length === 0) {
    return 0;
  }

  const sorted = [...values].sort((left, right) => left - right);
  const middleIndex = Math.floor(sorted.length / 2);

  return sorted.length % 2 === 0
    ? (sorted[middleIndex - 1] + sorted[middleIndex]) / 2
    : sorted[middleIndex];
}

function waitForFrame(): Promise<void> {
  return new Promise((resolve) => requestAnimationFrame(() => resolve()));
}

const availableWeatherGroups = computed(() => {
  const groups = new Set(
    allMatches.value.map((match) => classifyWeather(match.weather?.conditions)),
  );

  return WEATHER_ORDER.filter((group) => groups.has(group));
});

const filteredMatches = computed(() => {
  if (selectedWeather.value === "All") {
    return allMatches.value;
  }

  return allMatches.value.filter((match) => {
    return classifyWeather(match.weather?.conditions) === selectedWeather.value;
  });
});

const summaryRows = computed<SummaryRow[]>(() => {
  const grouped = new Map<string, number[]>();

  for (const match of filteredMatches.value) {
    const weatherGroup = classifyWeather(match.weather?.conditions);
    const totalGoals = getTotalGoals(match);
    const values = grouped.get(weatherGroup) ?? [];
    values.push(totalGoals);
    grouped.set(weatherGroup, values);
  }

  return WEATHER_ORDER.filter((group) => grouped.has(group)).map((group) => {
    const values = grouped.get(group) ?? [];
    const totalGoals = values.reduce((sum, value) => sum + value, 0);

    return {
      weatherGroup: group,
      averageGoals: values.length ? totalGoals / values.length : 0,
      medianGoals: getMedian(values),
      matchCount: values.length,
    };
  });
});

const metricSummaryLabel = computed(() => {
  if (selectedMetric.value === "avg") return "Average total goals";
  if (selectedMetric.value === "median") return "Median total goals";
  return "Match count";
});

const metricButtonLabel = computed(() => {
  if (selectedMetric.value === "avg") return "Average goals";
  if (selectedMetric.value === "median") return "Median goals";
  return "Match count";
});

const metricTitle = computed(() => {
  if (selectedMetric.value === "avg") {
    return "Average total goals by weather condition";
  }
  if (selectedMetric.value === "median") {
    return "Median total goals by weather condition";
  }
  return "Number of matches by weather condition";
});

const metricYAxisLabel = computed(() => {
  if (selectedMetric.value === "avg") return "Average total goals";
  if (selectedMetric.value === "median") return "Median total goals";
  return "Number of matches";
});

const metricSummaryValue = computed(() => {
  if (filteredMatches.value.length === 0) {
    return selectedMetric.value === "count" ? "0" : "0.00";
  }

  const goals = filteredMatches.value.map(getTotalGoals);

  if (selectedMetric.value === "avg") {
    const average = goals.reduce((sum, value) => sum + value, 0) / goals.length;
    return average.toFixed(2);
  }

  if (selectedMetric.value === "median") {
    return getMedian(goals).toFixed(2);
  }

  return String(filteredMatches.value.length);
});

function getMetricValue(row: SummaryRow): number {
  if (selectedMetric.value === "avg") return row.averageGoals;
  if (selectedMetric.value === "median") return row.medianGoals;
  return row.matchCount;
}

async function renderCharts() {
  await nextTick();
  await waitForFrame();

  if (!mainChartRef.value || !distributionChartRef.value) {
    return;
  }

  const rows = summaryRows.value;
  const goals = filteredMatches.value.map(getTotalGoals);

  await Plotly.react(
    mainChartRef.value,
    [
      {
        type: "bar",
        x: rows.map((row) => row.weatherGroup),
        y: rows.map(getMetricValue),
        text: rows.map((row) =>
          selectedMetric.value === "count"
            ? String(getMetricValue(row))
            : getMetricValue(row).toFixed(2),
        ),
        textposition: "outside",
        hovertemplate:
          selectedMetric.value === "count"
            ? "Weather: %{x}<br>Number of matches: %{y}<extra></extra>"
            : `Weather: %{x}<br>${metricYAxisLabel.value}: %{y:.2f}<extra></extra>`,
        marker: {
          color: "#2563eb",
        },
      },
    ],
    {
      title: metricTitle.value,
      xaxis: { title: "Weather condition" },
      yaxis: { title: metricYAxisLabel.value },
      margin: { t: 60, r: 20, b: 60, l: 70 },
      paper_bgcolor: "#ffffff",
      plot_bgcolor: "#ffffff",
    },
    {
      responsive: true,
      displayModeBar: false,
    },
  );

  await Plotly.react(
    distributionChartRef.value,
    [
      {
        type: "histogram",
        x: goals,
        marker: {
          color: "#16a34a",
        },
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
}

function handleResize() {
  if (mainChartRef.value) {
    Plotly.Plots.resize(mainChartRef.value);
  }
  if (distributionChartRef.value) {
    Plotly.Plots.resize(distributionChartRef.value);
  }
}

async function loadData() {
  try {
    const response = await fetch(weatherDataUrl);

    if (!response.ok) {
      throw new Error(`Could not load JSON: ${response.status}`);
    }

    const data = (await response.json()) as JsonData;
    const matches = data.matches ?? [];

    if (matches.length === 0) {
      throw new Error("No matches found in the JSON dataset.");
    }

    allMatches.value = matches;
    await renderCharts();
  } catch (loadError) {
    error.value =
      loadError instanceof Error ? loadError.message : "Unknown error";
  }
}

watch([selectedWeather, selectedMetric], async () => {
  if (!error.value) {
    await renderCharts();
  }
});

onMounted(async () => {
  window.addEventListener("resize", handleResize);
  await loadData();
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);

  if (mainChartRef.value) {
    Plotly.purge(mainChartRef.value);
  }

  if (distributionChartRef.value) {
    Plotly.purge(distributionChartRef.value);
  }
});
</script>
