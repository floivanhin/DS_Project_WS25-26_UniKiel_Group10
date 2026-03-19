<template>
  <div class="page">
    <section class="hero">
      <p class="kicker">RQ4</p>
      <h1 class="page-title">
        Which players perform particularly well in home matches and which in
        away matches?
      </h1>
      <p class="page-subtitle">{{ researchQuestionAnswer }}</p>
    </section>

    <section class="controls-card">
      <div class="control-block">
        <span class="control-label">Chart view</span>

        <div class="radio-group">
          <label class="radio-option">
            <input v-model="selectedChart" type="radio" value="compare" />
            <span>Comparison</span>
          </label>

          <label class="radio-option">
            <input v-model="selectedChart" type="radio" value="scatter" />
            <span>Scatter</span>
          </label>
        </div>
      </div>

      <div v-if="selectedChart === 'compare'" class="control-grid">
        <div class="control-block">
          <label class="control-label" for="rq4ViewMode">Mode</label>
          <select
            id="rq4ViewMode"
            v-model="selectedViewMode"
            class="select-control"
          >
            <option value="abs_delta">Biggest gaps</option>
            <option value="home_specialists">Better at home</option>
            <option value="away_specialists">Better away</option>
          </select>
        </div>

        <div class="control-block">
          <label class="control-label" for="rq4TopN">Top players</label>
          <input
            id="rq4TopN"
            v-model.number="topN"
            class="range-control"
            type="range"
            min="5"
            max="20"
            step="1"
          />
          <div class="range-meta">{{ clampedTopN }} players</div>
        </div>
      </div>
    </section>

    <section class="description-box">{{ plotDescription }}</section>

    <section v-if="!rows.length" class="status-box error-box">
      No eligible player rows were found in the RQ4 dataset.
    </section>

    <section v-else class="chart-card">
      <div ref="chartRef" class="chart"></div>
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
import deltaCsv from "../../data/rq4/rq4_player_home_away_delta.csv?raw";

type ViewMode = "abs_delta" | "home_specialists" | "away_specialists";
type ChartMode = "compare" | "scatter";

type PlayerRow = {
  player: string;
  home: number;
  away: number;
  delta: number;
  absDelta: number;
  homeMatches: number;
  awayMatches: number;
};

const chartRef = ref<HTMLDivElement | null>(null);
const selectedChart = ref<ChartMode>("compare");
const selectedViewMode = ref<ViewMode>("abs_delta");
const topN = ref(10);

function parseCsv(text: string): Record<string, string>[] {
  const lines = text.replace(/^\uFEFF/, "").trim().split(/\r?\n/).filter(Boolean);

  if (lines.length < 2) {
    return [];
  }

  const headers = lines[0].split(",").map((value) => value.trim());

  return lines.slice(1).map((line) => {
    const values = line.split(",");
    const row: Record<string, string> = {};

    headers.forEach((header, index) => {
      row[header] = values[index]?.trim() ?? "";
    });

    return row;
  });
}

function toNumber(value: unknown): number | null {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function getAverage(values: number[]): number | null {
  if (values.length === 0) {
    return null;
  }

  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

const rows: PlayerRow[] = parseCsv(deltaCsv)
  .map((row) => {
    const home = toNumber(row.home_avg_overall_rating);
    const away = toNumber(row.away_avg_overall_rating);
    const delta = toNumber(row.avg_rating_delta_home_minus_away);
    const absDelta = toNumber(row.abs_avg_rating_delta);
    const homeMatches = toNumber(row.home_matches);
    const awayMatches = toNumber(row.away_matches);
    const eligible =
      String(row.eligible_both_sides).trim().toLowerCase() === "true";

    if (
      !row.player ||
      !eligible ||
      home === null ||
      away === null ||
      delta === null ||
      absDelta === null ||
      homeMatches === null ||
      awayMatches === null
    ) {
      return null;
    }

    return {
      player: row.player,
      home,
      away,
      delta,
      absDelta,
      homeMatches,
      awayMatches,
    };
  })
  .filter((row): row is PlayerRow => row !== null);

const clampedTopN = computed(() => Math.min(Math.max(topN.value, 5), 20));

const overallHome = getAverage(rows.map((row) => row.home));
const overallAway = getAverage(rows.map((row) => row.away));
const overallDelta =
  overallHome !== null && overallAway !== null ? overallHome - overallAway : null;
const homeBetterCount = rows.filter((row) => row.delta > 0).length;

const researchQuestionAnswer =
  rows.length > 0 &&
  overallHome !== null &&
  overallAway !== null &&
  overallDelta !== null
    ? `Players perform slightly better at home overall. The average home rating is ${overallHome.toFixed(3)}, compared with ${overallAway.toFixed(3)} away, a difference of ${overallDelta.toFixed(3)} rating points. ${homeBetterCount} of ${rows.length} eligible players have a higher home rating.`
    : "Not enough usable RQ4 data was found.";

const leaderboardRows = computed(() => {
  const mode = selectedViewMode.value;
  const filteredRows = rows.filter((row) =>
    mode === "home_specialists"
      ? row.delta > 0
      : mode === "away_specialists"
        ? row.delta < 0
        : true,
  );

  filteredRows.sort((left, right) => {
    if (mode === "home_specialists") {
      return right.delta - left.delta || left.player.localeCompare(right.player);
    }

    if (mode === "away_specialists") {
      return left.delta - right.delta || left.player.localeCompare(right.player);
    }

    return (
      right.absDelta - left.absDelta || left.player.localeCompare(right.player)
    );
  });

  return filteredRows.slice(0, clampedTopN.value);
});

const plotDescription = computed(() => {
  if (selectedChart.value === "scatter") {
    return "Each blue point represents one player. The x-axis shows away ratings, the y-axis shows home ratings, and the red point marks the overall average.";
  }

  if (leaderboardRows.value.length === 0) {
    return "No players match the current selection.";
  }

  const homeAverage = getAverage(leaderboardRows.value.map((row) => row.home));
  const awayAverage = getAverage(leaderboardRows.value.map((row) => row.away));
  const averageDifference = (homeAverage ?? 0) - (awayAverage ?? 0);

  let modeLabel = "biggest home-away gaps";
  if (selectedViewMode.value === "home_specialists") {
    modeLabel = "players who perform better at home";
  } else if (selectedViewMode.value === "away_specialists") {
    modeLabel = "players who perform better away";
  }

  return `This view highlights the ${modeLabel}. Across the shown players, home averages ${homeAverage?.toFixed(3) ?? "0.000"} and away averages ${awayAverage?.toFixed(3) ?? "0.000"}, a difference of ${Math.abs(averageDifference).toFixed(3)}${averageDifference === 0 ? "" : averageDifference > 0 ? " in favor of home" : " in favor of away"}.`;
});

function buildCompareFigure() {
  const labels = leaderboardRows.value.map((row) => row.player);

  return {
    data: [
      {
        type: "bar",
        name: "Home",
        x: labels,
        y: leaderboardRows.value.map((row) => row.home),
        marker: { color: "#16a34a" },
        hovertemplate:
          "<b>%{x}</b><br>Home average rating: %{y:.3f}<extra></extra>",
      },
      {
        type: "bar",
        name: "Away",
        x: labels,
        y: leaderboardRows.value.map((row) => row.away),
        marker: { color: "#2563eb" },
        hovertemplate:
          "<b>%{x}</b><br>Away average rating: %{y:.3f}<extra></extra>",
      },
    ],
    layout: {
      title: "Leaderboard comparison by player",
      barmode: "group" as const,
      margin: { t: 64, r: 24, b: 110, l: 72 },
      paper_bgcolor: "#ffffff",
      plot_bgcolor: "#ffffff",
      legend: { orientation: "h" as const, y: 1.12 },
      xaxis: {
        title: "Player",
        tickangle: 50,
        automargin: true,
      },
      yaxis: {
        title: "Average overall rating",
      },
    },
  };
}

function buildScatterFigure() {
  if (overallHome === null || overallAway === null) {
    return { data: [], layout: {} };
  }

  const allRatings = rows.flatMap((row) => [row.away, row.home]);
  const minRating = Math.min(...allRatings);
  const maxRating = Math.max(...allRatings);
  const padding = Math.max((maxRating - minRating) * 0.05, 0.05);
  const axisMin = minRating - padding;
  const axisMax = maxRating + padding;

  return {
    data: [
      {
        type: "scatter",
        mode: "markers",
        name: "Players",
        x: rows.map((row) => row.away),
        y: rows.map((row) => row.home),
        text: rows.map((row) => row.player),
        customdata: rows.map((row) => [
          row.homeMatches,
          row.awayMatches,
          row.delta,
        ]),
        marker: {
          color: "#2563eb",
          size: 10,
          opacity: 0.72,
          line: { color: "#ffffff", width: 0.8 },
        },
        hovertemplate:
          "<b>%{text}</b><br>Away average rating: %{x:.3f}<br>Home average rating: %{y:.3f}<br>Delta (Home - Away): %{customdata[2]:.3f}<br>Home matches: %{customdata[0]}<br>Away matches: %{customdata[1]}<extra></extra>",
      },
      {
        type: "scatter",
        mode: "markers",
        name: "Overall average",
        x: [overallAway],
        y: [overallHome],
        marker: {
          color: "#dc2626",
          size: 16,
          opacity: 0.98,
          line: { color: "#ffffff", width: 1.5 },
        },
        hovertemplate:
          "Overall average<br>Away: %{x:.3f}<br>Home: %{y:.3f}<extra></extra>",
      },
    ],
    layout: {
      title: "Home vs away average rating",
      margin: { t: 64, r: 24, b: 72, l: 72 },
      paper_bgcolor: "#ffffff",
      plot_bgcolor: "#ffffff",
      hovermode: "closest" as const,
      legend: { orientation: "h" as const, y: 1.12 },
      annotations: [
        {
          x: overallAway,
          y: overallHome,
          xref: "x",
          yref: "y",
          showarrow: false,
          xanchor: "left",
          xshift: 14,
          bgcolor: "#ffffff",
          bordercolor: "#dc2626",
          borderwidth: 1,
          borderpad: 4,
          text: `Average<br>Away: ${overallAway.toFixed(3)}<br>Home: ${overallHome.toFixed(3)}`,
        },
      ],
      xaxis: {
        title: "Away average overall rating",
        range: [axisMin, axisMax],
      },
      yaxis: {
        title: "Home average overall rating",
        range: [axisMin, axisMax],
        scaleanchor: "x",
        scaleratio: 1,
      },
    },
  };
}

async function renderChart() {
  await nextTick();
  await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()));

  if (!chartRef.value || rows.length === 0) {
    return;
  }

  const figure =
    selectedChart.value === "scatter"
      ? buildScatterFigure()
      : buildCompareFigure();

  await Plotly.react(chartRef.value, figure.data, figure.layout, {
    responsive: true,
    displayModeBar: false,
  });
}

function resizeChart() {
  if (chartRef.value) {
    Plotly.Plots.resize(chartRef.value);
  }
}

watch([selectedChart, selectedViewMode, clampedTopN], renderChart);

onMounted(async () => {
  window.addEventListener("resize", resizeChart);
  await renderChart();
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", resizeChart);

  if (chartRef.value) {
    Plotly.purge(chartRef.value);
  }
});
</script>
