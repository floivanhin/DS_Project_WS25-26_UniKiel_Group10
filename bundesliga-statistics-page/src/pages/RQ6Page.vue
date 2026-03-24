<template>
  <div class="page">
    <section class="hero">
      <p class="kicker">RQ6</p>
      <h1 class="page-title">
        What is the relationship between arena capacity and the number of cards
        issued?
      </h1>
      <p class="page-subtitle">
        This page analyzes Bundesliga matches from the 2024 season. The data is
        aggregated by stadium, so each point in the chart represents one venue
        instead of one individual match.
      </p>
    </section>

    <section class="description-box">
      Arena capacity is operationalized as the home team's stadium capacity.
      Switch between total, yellow, and red cards to compare how the pattern
      changes across metrics. Click a point or a table row to inspect one
      stadium in detail.
    </section>

    <section class="summary-grid">
      <div class="summary-card">
        <span class="summary-label">Matches analyzed</span>
        <strong class="summary-value">{{ totalMatches }}</strong>
      </div>

      <div class="summary-card">
        <span class="summary-label">Stadiums analyzed</span>
        <strong class="summary-value">{{ totalStadiums }}</strong>
      </div>

      <div class="summary-card">
        <span class="summary-label">Selected metric</span>
        <strong class="summary-value summary-value-small">
          {{ metricLabel }}
        </strong>
      </div>

      <div class="summary-card">
        <span class="summary-label">Pearson correlation</span>
        <strong class="summary-value">
          {{ stadiumCorrelation.toFixed(3) }}
        </strong>
      </div>
    </section>

    <section class="chart-card">
      <div class="toolbar">
        <div class="control-block">
          <span class="control-label">Metric</span>
          <div class="button-group">
            <button
              type="button"
              class="toggle-button"
              :class="{ 'toggle-button-active': selectedMetric === 'avg_cards' }"
              @click="selectedMetric = 'avg_cards'"
            >
              Total cards
            </button>
            <button
              type="button"
              class="toggle-button"
              :class="{ 'toggle-button-active': selectedMetric === 'avg_yellow' }"
              @click="selectedMetric = 'avg_yellow'"
            >
              Yellow cards
            </button>
            <button
              type="button"
              class="toggle-button"
              :class="{ 'toggle-button-active': selectedMetric === 'avg_red' }"
              @click="selectedMetric = 'avg_red'"
            >
              Red cards
            </button>
          </div>
        </div>

        <div class="control-block control-block-compact">
          <span class="control-label">Current reading</span>
          <p class="selection-summary">
            {{ correlationStrengthLabel }} correlation, r =
            <strong>{{ stadiumCorrelation.toFixed(3) }}</strong>
          </p>
        </div>
      </div>

      <h2 class="section-title">
        Arena capacity vs {{ metricAxisLabel.toLowerCase() }}
      </h2>
      <p class="chart-note">
        Marker size reflects the number of home matches in the dataset. The red
        line shows the linear trend.
      </p>

      <div ref="chartRef" class="chart"></div>
    </section>

    <section v-if="selectedStadium" class="chart-card">
      <h2 class="section-title">Selected stadium</h2>

      <div class="detail-grid">
        <div class="detail-item">
          <span class="detail-label">Team</span>
          <strong class="detail-value">{{ selectedStadium.homeTeamName }}</strong>
        </div>
        <div class="detail-item">
          <span class="detail-label">Venue</span>
          <strong class="detail-value">{{ selectedStadium.venueName }}</strong>
        </div>
        <div class="detail-item">
          <span class="detail-label">City</span>
          <strong class="detail-value">{{ selectedStadium.city }}</strong>
        </div>
        <div class="detail-item">
          <span class="detail-label">Capacity</span>
          <strong class="detail-value">
            {{ selectedStadium.capacity.toLocaleString() }}
          </strong>
        </div>
        <div class="detail-item">
          <span class="detail-label">Home matches</span>
          <strong class="detail-value">{{ selectedStadium.matchCount }}</strong>
        </div>
        <div class="detail-item">
          <span class="detail-label">Average total cards</span>
          <strong class="detail-value">{{ selectedStadium.avg_cards.toFixed(2) }}</strong>
        </div>
        <div class="detail-item">
          <span class="detail-label">Average yellow cards</span>
          <strong class="detail-value">{{ selectedStadium.avg_yellow.toFixed(2) }}</strong>
        </div>
        <div class="detail-item">
          <span class="detail-label">Average red cards</span>
          <strong class="detail-value">{{ selectedStadium.avg_red.toFixed(2) }}</strong>
        </div>
      </div>
    </section>

    <section class="chart-card">
      <h2 class="section-title">Interpretation</h2>
      <p class="selection-summary">{{ interpretationText }}</p>
    </section>

    <section class="table-card">
      <h2 class="section-title">Stadium overview</h2>
      <p class="chart-note">
        Select a row to highlight the same stadium in the scatter plot.
      </p>

      <div class="table-wrapper">
        <table class="summary-table">
          <thead>
            <tr>
              <th>Team</th>
              <th>Venue</th>
              <th>City</th>
              <th>Capacity</th>
              <th>Matches</th>
              <th>{{ metricLabel }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="stadium in stadiumData"
              :key="`${stadium.homeTeamName}-${stadium.venueName}`"
              :class="{
                'table-row-active':
                  selectedStadium?.homeTeamName === stadium.homeTeamName &&
                  selectedStadium?.venueName === stadium.venueName,
              }"
              @click="selectedStadium = stadium"
            >
              <td>{{ stadium.homeTeamName }}</td>
              <td>{{ stadium.venueName }}</td>
              <td>{{ stadium.city }}</td>
              <td>{{ stadium.capacity.toLocaleString() }}</td>
              <td>{{ stadium.matchCount }}</td>
              <td>{{ stadium[selectedMetric].toFixed(2) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import Plotly from "plotly.js-dist-min";
import relationData from "../../data/capacity_cards_relation.json";

type MetricKey = "avg_cards" | "avg_yellow" | "avg_red";

type MatchRow = {
  home_team_name: string;
  team_capacity_venue_name: string;
  team_capacity_city: string;
  capacity: number;
  cards_total: number;
  yellow_total: number;
  red_total: number;
};

type StadiumRow = {
  homeTeamName: string;
  venueName: string;
  city: string;
  capacity: number;
  matchCount: number;
  avg_cards: number;
  avg_yellow: number;
  avg_red: number;
};

const chartRef = ref<HTMLDivElement | null>(null);
const selectedMetric = ref<MetricKey>("avg_cards");
const selectedStadium = ref<StadiumRow | null>(null);

const matches = computed<MatchRow[]>(() => {
  const rawMatches = relationData?.matches ?? [];

  return rawMatches.filter((item: Partial<MatchRow>) => {
    return Number.isFinite(item?.capacity) && Number.isFinite(item?.cards_total);
  }) as MatchRow[];
});

const totalMatches = computed(() => matches.value.length);

const stadiumData = computed<StadiumRow[]>(() => {
  const grouped = new Map<
    string,
    StadiumRow & {
      totalCardsSum: number;
      yellowSum: number;
      redSum: number;
    }
  >();

  for (const match of matches.value) {
    const key = `${match.home_team_name}__${match.team_capacity_venue_name}`;

    if (!grouped.has(key)) {
      grouped.set(key, {
        homeTeamName: match.home_team_name,
        venueName: match.team_capacity_venue_name,
        city: match.team_capacity_city,
        capacity: match.capacity,
        matchCount: 0,
        avg_cards: 0,
        avg_yellow: 0,
        avg_red: 0,
        totalCardsSum: 0,
        yellowSum: 0,
        redSum: 0,
      });
    }

    const entry = grouped.get(key);
    if (!entry) continue;

    entry.matchCount += 1;
    entry.totalCardsSum += match.cards_total ?? 0;
    entry.yellowSum += match.yellow_total ?? 0;
    entry.redSum += match.red_total ?? 0;
  }

  return Array.from(grouped.values())
    .map((entry) => ({
      homeTeamName: entry.homeTeamName,
      venueName: entry.venueName,
      city: entry.city,
      capacity: entry.capacity,
      matchCount: entry.matchCount,
      avg_cards: entry.matchCount ? entry.totalCardsSum / entry.matchCount : 0,
      avg_yellow: entry.matchCount ? entry.yellowSum / entry.matchCount : 0,
      avg_red: entry.matchCount ? entry.redSum / entry.matchCount : 0,
    }))
    .sort((left, right) => right.capacity - left.capacity);
});

const totalStadiums = computed(() => stadiumData.value.length);

const metricLabelMap: Record<MetricKey, string> = {
  avg_cards: "Average total cards",
  avg_yellow: "Average yellow cards",
  avg_red: "Average red cards",
};

const metricAxisLabelMap: Record<MetricKey, string> = {
  avg_cards: "Average cards per match",
  avg_yellow: "Average yellow cards per match",
  avg_red: "Average red cards per match",
};

const metricLabel = computed(() => metricLabelMap[selectedMetric.value]);
const metricAxisLabel = computed(() => metricAxisLabelMap[selectedMetric.value]);

function pearsonCorrelation(data: StadiumRow[], xKey: keyof StadiumRow, yKey: MetricKey) {
  const sampleSize = data.length;
  if (sampleSize === 0) return 0;

  const xs = data.map((row) => Number(row[xKey]));
  const ys = data.map((row) => row[yKey]);
  const meanX = xs.reduce((sum, value) => sum + value, 0) / sampleSize;
  const meanY = ys.reduce((sum, value) => sum + value, 0) / sampleSize;

  let numerator = 0;
  let denominatorX = 0;
  let denominatorY = 0;

  for (let index = 0; index < sampleSize; index += 1) {
    const dx = xs[index] - meanX;
    const dy = ys[index] - meanY;
    numerator += dx * dy;
    denominatorX += dx * dx;
    denominatorY += dy * dy;
  }

  if (denominatorX === 0 || denominatorY === 0) return 0;
  return numerator / Math.sqrt(denominatorX * denominatorY);
}

function linearRegression(data: StadiumRow[], xKey: keyof StadiumRow, yKey: MetricKey) {
  const sampleSize = data.length;
  if (sampleSize === 0) return { slope: 0, intercept: 0 };

  const xs = data.map((row) => Number(row[xKey]));
  const ys = data.map((row) => row[yKey]);
  const meanX = xs.reduce((sum, value) => sum + value, 0) / sampleSize;
  const meanY = ys.reduce((sum, value) => sum + value, 0) / sampleSize;

  let numerator = 0;
  let denominator = 0;

  for (let index = 0; index < sampleSize; index += 1) {
    numerator += (xs[index] - meanX) * (ys[index] - meanY);
    denominator += (xs[index] - meanX) ** 2;
  }

  const slope = denominator === 0 ? 0 : numerator / denominator;
  const intercept = meanY - slope * meanX;
  return { slope, intercept };
}

const stadiumCorrelation = computed(() =>
  pearsonCorrelation(stadiumData.value, "capacity", selectedMetric.value),
);

const regression = computed(() =>
  linearRegression(stadiumData.value, "capacity", selectedMetric.value),
);

const trendLinePoints = computed(() => {
  if (stadiumData.value.length === 0) return { x: [], y: [] };

  const capacities = stadiumData.value.map((stadium) => stadium.capacity);
  const minCapacity = Math.min(...capacities);
  const maxCapacity = Math.max(...capacities);
  const { slope, intercept } = regression.value;

  return {
    x: [minCapacity, maxCapacity],
    y: [slope * minCapacity + intercept, slope * maxCapacity + intercept],
  };
});

const correlationStrengthLabel = computed(() => {
  const absoluteCorrelation = Math.abs(stadiumCorrelation.value);

  if (absoluteCorrelation < 0.1) return "Very weak";
  if (absoluteCorrelation < 0.3) return "Weak";
  if (absoluteCorrelation < 0.5) return "Moderate";
  return "Strong";
});

const interpretationText = computed(() => {
  const correlation = stadiumCorrelation.value;
  const metricText = metricAxisLabel.value.toLowerCase();

  if (correlation > 0.3) {
    return `The correlation is positive (${correlation.toFixed(3)}), which suggests that larger stadiums tend to be associated with higher ${metricText}. This is still a broad tendency rather than a strong effect.`;
  }
  if (correlation > 0.1) {
    return `The correlation is weakly positive (${correlation.toFixed(3)}), so larger stadiums show only a small tendency toward higher ${metricText}.`;
  }
  if (correlation >= -0.1) {
    return `The correlation is very close to zero (${correlation.toFixed(3)}), which means stadium capacity has little to no clear linear relationship with ${metricText}.`;
  }
  if (correlation >= -0.3) {
    return `The correlation is weakly negative (${correlation.toFixed(3)}), so larger stadiums show only a small tendency toward lower ${metricText}.`;
  }

  return `The correlation is negative (${correlation.toFixed(3)}), which suggests that larger stadiums tend to be associated with lower ${metricText}. This should be interpreted carefully and not as causation.`;
});

function getSelectedStadiumIndex(): number {
  if (!selectedStadium.value) return -1;

  return stadiumData.value.findIndex((stadium) => {
    return (
      stadium.homeTeamName === selectedStadium.value?.homeTeamName &&
      stadium.venueName === selectedStadium.value?.venueName
    );
  });
}

async function renderChart() {
  if (!chartRef.value || stadiumData.value.length === 0) return;

  const selectedIndex = getSelectedStadiumIndex();

  await Plotly.react(
    chartRef.value,
    [
      {
        x: stadiumData.value.map((stadium) => stadium.capacity),
        y: stadiumData.value.map((stadium) =>
          Number(stadium[selectedMetric.value].toFixed(2)),
        ),
        text: stadiumData.value.map(
          (stadium) =>
            `${stadium.homeTeamName}<br>` +
            `Venue: ${stadium.venueName}<br>` +
            `Capacity: ${stadium.capacity.toLocaleString()}<br>` +
            `Matches: ${stadium.matchCount}<br>` +
            `${metricLabel.value}: ${stadium[selectedMetric.value].toFixed(2)}`,
        ),
        type: "scatter",
        mode: "markers",
        name: "Stadiums",
        hovertemplate: "%{text}<extra></extra>",
        marker: {
          size: stadiumData.value.map((stadium) => 12 + stadium.matchCount * 0.18),
          color: stadiumData.value.map((_, index) =>
            index === selectedIndex ? "#b91c1c" : "#2563eb",
          ),
          opacity: 0.82,
          line: {
            color: "#ffffff",
            width: 1.5,
          },
        },
      },
      {
        x: trendLinePoints.value.x,
        y: trendLinePoints.value.y,
        type: "scatter",
        mode: "lines",
        name: "Trend line",
        hoverinfo: "skip",
        line: {
          color: "#b91c1c",
          width: 3,
        },
      },
    ],
    {
      autosize: true,
      height: 560,
      paper_bgcolor: "transparent",
      plot_bgcolor: "#f8fafc",
      margin: { t: 24, r: 24, b: 64, l: 72 },
      xaxis: {
        title: "Arena capacity",
        gridcolor: "#dbe4f0",
        zeroline: false,
        tickformat: ",",
      },
      yaxis: {
        title: metricAxisLabel.value,
        gridcolor: "#dbe4f0",
        zeroline: false,
      },
      legend: {
        orientation: "h",
        y: 1.12,
        x: 0,
      },
      hovermode: "closest",
    },
    {
      responsive: true,
      displayModeBar: false,
    },
  );

  chartRef.value.removeAllListeners?.("plotly_click");
  chartRef.value.on?.("plotly_click", (event: { points?: Array<{ pointIndex?: number }> }) => {
    const pointIndex = event?.points?.[0]?.pointIndex;
    if (typeof pointIndex === "number") {
      selectedStadium.value = stadiumData.value[pointIndex] ?? null;
    }
  });
}

function handleResize() {
  if (chartRef.value) {
    Plotly.Plots.resize(chartRef.value);
  }
}

watch([selectedMetric, selectedStadium], async () => {
  await renderChart();
});

onMounted(async () => {
  window.addEventListener("resize", handleResize);
  await renderChart();
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);

  if (chartRef.value) {
    chartRef.value.removeAllListeners?.("plotly_click");
    Plotly.purge(chartRef.value);
  }
});
</script>
