<template>
  <div class="rq6-page">
    <section class="rq6-hero">
      <p class="rq6-kicker">RQ6</p>
      <h1 class="rq6-page-title">
        What is the relationship between arena capacity and the number of cards
        issued?
      </h1>
      <p class="rq6-page-subtitle">
        This page analyses all 308 Bundesliga matches from the 2024 season. The
        data is aggregated by stadium, so each point in the chart represents one
        stadium instead of one individual match.
      </p>
    </section>

    <section class="rq6-description">
      Arena capacity is operationalized as the home team's stadium capacity.
      Switch between total, yellow, and red cards to compare how the trend
      changes across metrics. Click a point or a table row to inspect one
      stadium in detail.
    </section>

    <section class="rq6-summary-grid">
      <div class="rq6-summary-card">
        <span class="rq6-summary-label">Matches analysed</span>
        <strong class="rq6-summary-value">{{ totalMatches }}</strong>
      </div>

      <div class="rq6-summary-card">
        <span class="rq6-summary-label">Stadiums analysed</span>
        <strong class="rq6-summary-value">{{ totalStadiums }}</strong>
      </div>

      <div class="rq6-summary-card">
        <span class="rq6-summary-label">Selected metric</span>
        <strong class="rq6-summary-value rq6-summary-value-small">{{
          metricLabel
        }}</strong>
      </div>

      <div class="rq6-summary-card">
        <span class="rq6-summary-label">Pearson correlation</span>
        <strong class="rq6-summary-value">{{
          stadiumCorrelation.toFixed(3)
        }}</strong>
      </div>
    </section>

    <section class="rq6-chart-card">
      <div class="rq6-toolbar">
        <div class="rq6-toolbar-group">
          <span class="rq6-toolbar-label">Metric</span>
          <div class="rq6-button-group">
            <button
              class="rq6-toggle-button"
              :class="{
                'rq6-toggle-button-active': selectedMetric === 'avg_cards',
              }"
              type="button"
              @click="selectedMetric = 'avg_cards'"
            >
              Total cards
            </button>
            <button
              class="rq6-toggle-button"
              :class="{
                'rq6-toggle-button-active': selectedMetric === 'avg_yellow',
              }"
              type="button"
              @click="selectedMetric = 'avg_yellow'"
            >
              Yellow cards
            </button>
            <button
              class="rq6-toggle-button"
              :class="{
                'rq6-toggle-button-active': selectedMetric === 'avg_red',
              }"
              type="button"
              @click="selectedMetric = 'avg_red'"
            >
              Red cards
            </button>
          </div>
        </div>

        <div class="rq6-toolbar-group rq6-toolbar-group-compact">
          <span class="rq6-toolbar-label">Current reading</span>
          <p class="rq6-toolbar-summary">
            {{ correlationStrengthLabel }} correlation, r =
            {{ stadiumCorrelation.toFixed(3) }}
          </p>
        </div>
      </div>

      <h2 class="rq6-section-title">
        Arena capacity vs {{ metricAxisLabel.toLowerCase() }}
      </h2>
      <p class="rq6-chart-note">
        Marker size reflects the number of home matches in the dataset. The red
        line shows the linear trend.
      </p>

      <div ref="chartRef" class="rq6-chart"></div>
    </section>

    <section v-if="selectedStadium" class="rq6-detail-card">
      <h2 class="rq6-section-title">Selected stadium</h2>
      <div class="rq6-detail-grid">
        <div class="rq6-detail-item">
          <span class="rq6-detail-label">Team</span>
          <strong class="rq6-detail-value">{{
            selectedStadium.home_team_name
          }}</strong>
        </div>
        <div class="rq6-detail-item">
          <span class="rq6-detail-label">Venue</span>
          <strong class="rq6-detail-value">{{
            selectedStadium.venue_name
          }}</strong>
        </div>
        <div class="rq6-detail-item">
          <span class="rq6-detail-label">City</span>
          <strong class="rq6-detail-value">{{ selectedStadium.city }}</strong>
        </div>
        <div class="rq6-detail-item">
          <span class="rq6-detail-label">Capacity</span>
          <strong class="rq6-detail-value">{{
            selectedStadium.capacity.toLocaleString()
          }}</strong>
        </div>
        <div class="rq6-detail-item">
          <span class="rq6-detail-label">Home matches</span>
          <strong class="rq6-detail-value">{{
            selectedStadium.match_count
          }}</strong>
        </div>
        <div class="rq6-detail-item">
          <span class="rq6-detail-label">Average total cards</span>
          <strong class="rq6-detail-value">{{
            selectedStadium.avg_cards.toFixed(2)
          }}</strong>
        </div>
        <div class="rq6-detail-item">
          <span class="rq6-detail-label">Average yellow cards</span>
          <strong class="rq6-detail-value">{{
            selectedStadium.avg_yellow.toFixed(2)
          }}</strong>
        </div>
        <div class="rq6-detail-item">
          <span class="rq6-detail-label">Average red cards</span>
          <strong class="rq6-detail-value">{{
            selectedStadium.avg_red.toFixed(2)
          }}</strong>
        </div>
      </div>
    </section>

    <section class="rq6-insight-card">
      <h2 class="rq6-section-title">Interpretation</h2>
      <p class="rq6-insight-text">{{ interpretationText }}</p>
    </section>

    <section class="rq6-table-card">
      <div class="rq6-table-header">
        <h2 class="rq6-section-title">Stadium overview</h2>
        <p class="rq6-chart-note">
          Select a row to highlight the same stadium in the scatter plot.
        </p>
      </div>

      <div class="rq6-table-wrapper">
        <table class="rq6-table">
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
              :key="`${stadium.home_team_name}-${stadium.venue_name}`"
              :class="{
                'rq6-table-row-active':
                  selectedStadium &&
                  selectedStadium.home_team_name === stadium.home_team_name &&
                  selectedStadium.venue_name === stadium.venue_name,
              }"
              @click="selectedStadium = stadium"
            >
              <td>{{ stadium.home_team_name }}</td>
              <td>{{ stadium.venue_name }}</td>
              <td>{{ stadium.city }}</td>
              <td>{{ stadium.capacity.toLocaleString() }}</td>
              <td>{{ stadium.match_count }}</td>
              <td>{{ stadium[selectedMetric].toFixed(2) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import Plotly from "plotly.js-dist-min";
import relationData from "../../data/capacity_cards_relation.json";

const chartRef = ref(null);
const selectedMetric = ref("avg_cards");
const selectedStadium = ref(null);

const matches = computed(() => {
  const raw = relationData?.matches ?? [];

  return raw.filter(
    (item) =>
      Number.isFinite(item?.capacity) && Number.isFinite(item?.cards_total),
  );
});

const totalMatches = computed(() => matches.value.length);

const stadiumData = computed(() => {
  const grouped = new Map();

  for (const match of matches.value) {
    const key = `${match.home_team_name}__${match.team_capacity_venue_name}`;

    if (!grouped.has(key)) {
      grouped.set(key, {
        home_team_name: match.home_team_name,
        venue_name: match.team_capacity_venue_name,
        city: match.team_capacity_city,
        capacity: match.capacity,
        match_count: 0,
        total_cards_sum: 0,
        yellow_sum: 0,
        red_sum: 0,
      });
    }

    const entry = grouped.get(key);
    entry.match_count += 1;
    entry.total_cards_sum += match.cards_total ?? 0;
    entry.yellow_sum += match.yellow_total ?? 0;
    entry.red_sum += match.red_total ?? 0;
  }

  return Array.from(grouped.values())
    .map((entry) => ({
      ...entry,
      avg_cards: entry.match_count ? entry.total_cards_sum / entry.match_count : 0,
      avg_yellow: entry.match_count ? entry.yellow_sum / entry.match_count : 0,
      avg_red: entry.match_count ? entry.red_sum / entry.match_count : 0,
    }))
    .sort((left, right) => right.capacity - left.capacity);
});

const totalStadiums = computed(() => stadiumData.value.length);

const metricLabelMap = {
  avg_cards: "Average total cards",
  avg_yellow: "Average yellow cards",
  avg_red: "Average red cards",
};

const metricAxisLabelMap = {
  avg_cards: "Average cards per match",
  avg_yellow: "Average yellow cards per match",
  avg_red: "Average red cards per match",
};

const metricLabel = computed(() => metricLabelMap[selectedMetric.value]);
const metricAxisLabel = computed(() => metricAxisLabelMap[selectedMetric.value]);

function pearsonCorrelation(data, xKey, yKey) {
  const n = data.length;
  if (n === 0) return 0;

  const xs = data.map((d) => d[xKey]);
  const ys = data.map((d) => d[yKey]);
  const meanX = xs.reduce((sum, value) => sum + value, 0) / n;
  const meanY = ys.reduce((sum, value) => sum + value, 0) / n;

  let numerator = 0;
  let denomX = 0;
  let denomY = 0;

  for (let i = 0; i < n; i += 1) {
    const dx = xs[i] - meanX;
    const dy = ys[i] - meanY;
    numerator += dx * dy;
    denomX += dx * dx;
    denomY += dy * dy;
  }

  if (denomX === 0 || denomY === 0) return 0;
  return numerator / Math.sqrt(denomX * denomY);
}

function linearRegression(data, xKey, yKey) {
  const n = data.length;
  if (n === 0) return { slope: 0, intercept: 0 };

  const xs = data.map((d) => d[xKey]);
  const ys = data.map((d) => d[yKey]);
  const meanX = xs.reduce((sum, value) => sum + value, 0) / n;
  const meanY = ys.reduce((sum, value) => sum + value, 0) / n;

  let numerator = 0;
  let denominator = 0;

  for (let i = 0; i < n; i += 1) {
    numerator += (xs[i] - meanX) * (ys[i] - meanY);
    denominator += (xs[i] - meanX) ** 2;
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
  if (!stadiumData.value.length) return { x: [], y: [] };

  const capacities = stadiumData.value.map((stadium) => stadium.capacity);
  const minX = Math.min(...capacities);
  const maxX = Math.max(...capacities);
  const { slope, intercept } = regression.value;

  return {
    x: [minX, maxX],
    y: [slope * minX + intercept, slope * maxX + intercept],
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
  const r = stadiumCorrelation.value;
  const metricText = metricAxisLabel.value.toLowerCase();

  if (r > 0.3) {
    return `The correlation is positive (${r.toFixed(
      3,
    )}), which suggests that larger stadiums tend to be associated with higher ${metricText}. This is still a broad tendency rather than a strong effect.`;
  }

  if (r > 0.1) {
    return `The correlation is weakly positive (${r.toFixed(
      3,
    )}), so larger stadiums show only a small tendency toward higher ${metricText}.`;
  }

  if (r >= -0.1) {
    return `The correlation is very close to zero (${r.toFixed(
      3,
    )}), which means stadium capacity has little to no clear linear relationship with ${metricText}.`;
  }

  if (r >= -0.3) {
    return `The correlation is weakly negative (${r.toFixed(
      3,
    )}), so larger stadiums show only a small tendency toward lower ${metricText}.`;
  }

  return `The correlation is negative (${r.toFixed(
    3,
  )}), which suggests that larger stadiums tend to be associated with lower ${metricText}. This should be interpreted carefully and not as causation.`;
});

function getSelectedStadiumIndex() {
  if (!selectedStadium.value) return -1;

  return stadiumData.value.findIndex(
    (stadium) =>
      stadium.home_team_name === selectedStadium.value.home_team_name &&
      stadium.venue_name === selectedStadium.value.venue_name,
  );
}

function renderChart() {
  if (!chartRef.value || !stadiumData.value.length) return;

  const selectedIndex = getSelectedStadiumIndex();

  const scatterTrace = {
    x: stadiumData.value.map((stadium) => stadium.capacity),
    y: stadiumData.value.map((stadium) =>
      Number(stadium[selectedMetric.value].toFixed(2)),
    ),
    text: stadiumData.value.map(
      (stadium) =>
        `${stadium.home_team_name}<br>` +
        `Venue: ${stadium.venue_name}<br>` +
        `Capacity: ${stadium.capacity.toLocaleString()}<br>` +
        `Matches: ${stadium.match_count}<br>` +
        `${metricLabel.value}: ${stadium[selectedMetric.value].toFixed(2)}`,
    ),
    type: "scatter",
    mode: "markers",
    name: "Stadiums",
    hovertemplate: "%{text}<extra></extra>",
    marker: {
      size: stadiumData.value.map((stadium) => 12 + stadium.match_count * 0.18),
      color: stadiumData.value.map((_, index) =>
        index === selectedIndex ? "#b91c1c" : "#2563eb",
      ),
      opacity: 0.82,
      line: {
        color: "#ffffff",
        width: 1.5,
      },
    },
  };

  const trendTrace = {
    x: trendLinePoints.value.x,
    y: trendLinePoints.value.y,
    type: "scatter",
    mode: "lines",
    name: "Trend line",
    hoverinfo: "skip",
    line: {
      color: "#b91c1c",
      width: 3,
      dash: "solid",
    },
  };

  const layout = {
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
  };

  const config = {
    responsive: true,
    displayModeBar: false,
  };

  Plotly.react(chartRef.value, [scatterTrace, trendTrace], layout, config).then(
    () => {
      const pointElements = chartRef.value?.querySelectorAll(
        ".scatterlayer .trace .points path",
      );

      pointElements?.forEach((element) => {
        element.style.cursor = "pointer";
      });
    },
  );

  chartRef.value.removeAllListeners?.("plotly_click");
  chartRef.value.on?.("plotly_click", (event) => {
    const pointIndex = event?.points?.[0]?.pointIndex;
    if (typeof pointIndex !== "number") return;
    selectedStadium.value = stadiumData.value[pointIndex] ?? null;
  });
}

onMounted(async () => {
  await nextTick();
  renderChart();
});

watch([stadiumData, selectedMetric, selectedStadium], async () => {
  await nextTick();
  renderChart();
});

onBeforeUnmount(() => {
  if (chartRef.value) {
    chartRef.value.removeAllListeners?.("plotly_click");
    Plotly.purge(chartRef.value);
  }
});
</script>
