<template>
  <div class="rq4-page">
    <section class="rq4-hero">
      <h1 class="rq4-page-title">
        How does playing at home vs away affect player ratings?
      </h1>
      <p class="rq4-page-subtitle">{{ researchQuestionAnswer }}</p>
    </section>

    <section class="rq4-controls">
      <div class="rq4-control-block">
        <span class="rq4-control-label">Chart view</span>

        <div class="rq4-radio-group">
          <label class="rq4-radio-option">
            <input v-model="selectedChart" type="radio" value="compare" />
            <span>Comparison</span>
          </label>

          <label class="rq4-radio-option">
            <input v-model="selectedChart" type="radio" value="scatter" />
            <span>Scatter</span>
          </label>
        </div>
      </div>

      <div v-if="selectedChart === 'compare'" class="rq4-control-grid">
        <div class="rq4-control-block">
          <label class="rq4-control-label" for="rq4ViewMode">Mode</label>
          <select
            id="rq4ViewMode"
            v-model="selectedViewMode"
            class="rq4-select-control"
          >
            <option value="abs_delta">Biggest gaps</option>
            <option value="home_specialists">Better at home</option>
            <option value="away_specialists">Better away</option>
          </select>
        </div>

        <div class="rq4-control-block">
          <label class="rq4-control-label" for="rq4TopN">Top players</label>
          <input
            id="rq4TopN"
            v-model.number="topN"
            class="rq4-range-control"
            type="range"
            min="5"
            max="20"
            step="1"
          />
          <div class="rq4-range-meta">{{ topN }} players</div>
        </div>
      </div>
    </section>

    <section class="rq4-description">{{ plotDescription }}</section>

    <section class="rq4-chart-card">
      <div ref="chartRef" class="rq4-chart"></div>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import Plotly from "plotly.js-dist-min";
import deltaCsv from "../../data/rq4/rq4_player_home_away_delta.csv?raw";

// load the rq4 csv data
// labels for the chart modes
const modeLabels = {
  abs_delta: "biggest home-away gaps",
  home_specialists: "players who do better at home",
  away_specialists: "players who do better away",
};

// reactive ui state
const chartRef = ref(null);
const selectedChart = ref("compare");
const selectedViewMode = ref("abs_delta");
const topN = ref(10);

// simple csv parser for our data
function parseCsv(text) {
  const lines = text.replace(/^\uFEFF/, "").trim().split(/\r?\n/).filter(Boolean);
  if (!lines.length) {
    return [];
  }

  const headers = lines[0].split(",").map((value) => value.trim());
  return lines.slice(1).map((line) => {
    const values = line
      .split(/,(?=(?:[^"]*"[^"]*")*[^"]*$)/)
      .map((value) => value.replace(/^"|"$/g, "").replace(/""/g, '"'));

    return Object.fromEntries(
      headers.map((header, index) => [header, values[index] ?? ""]),
    );
  });
}

// convert text values to numbers
const num = (value) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
};

// helper for average values
const average = (values) =>
  values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;

// wait so plotly sees the right size
const waitForFrame = () =>
  new Promise((resolve) => {
    requestAnimationFrame(() => resolve());
  });

// keep only valid player rows
const rows = parseCsv(deltaCsv)
  .map((row) => ({
    player: row.player,
    home: num(row.home_avg_overall_rating),
    away: num(row.away_avg_overall_rating),
    delta: num(row.avg_rating_delta_home_minus_away),
    absDelta: num(row.abs_avg_rating_delta),
    homeMatches: num(row.home_matches),
    awayMatches: num(row.away_matches),
    eligible: String(row.eligible_both_sides).trim().toLowerCase() === "true",
  }))
  .filter(
    (row) =>
      row.player &&
      row.eligible &&
      row.home !== null &&
      row.away !== null &&
      row.delta !== null &&
      row.absDelta !== null &&
      row.homeMatches !== null &&
      row.awayMatches !== null,
  );

// summary values for the page text
const overallHome = average(rows.map((row) => row.home));
const overallAway = average(rows.map((row) => row.away));
const homeBetterCount = rows.filter((row) => row.delta > 0).length;

// short answer for the title
const researchQuestionAnswer =
  rows.length && overallHome !== null && overallAway !== null
    ? `Players are a bit better at home in this dataset. Mean home rating is ${overallHome.toFixed(3)} and away is ${overallAway.toFixed(3)}. ${homeBetterCount} of ${rows.length} eligible players rate higher at home.`
    : "Not enough usable RQ4 data was found.";

// rows used in the bar chart
const leaderboardRows = computed(() => {
  let list = rows.slice();

  // sort rows based on selected mode
  if (selectedViewMode.value === "home_specialists") {
    list = list
      .filter((row) => row.delta > 0)
      .sort((a, b) => b.delta - a.delta || a.player.localeCompare(b.player));
  } else if (selectedViewMode.value === "away_specialists") {
    list = list
      .filter((row) => row.delta < 0)
      .sort((a, b) => a.delta - b.delta || a.player.localeCompare(b.player));
  } else {
    list = list.sort((a, b) => b.absDelta - a.absDelta || a.player.localeCompare(b.player));
  }

  return list.slice(0, Number(topN.value));
});

const plotDescription = computed(() => {
  // text shown under the controls
  if (selectedChart.value === "scatter") {
    return `Each blue point is one player. The x-axis is away rating, the y-axis is home rating, and the red point is the overall average.`;
  }

  const list = leaderboardRows.value;
  if (!list.length) {
    return "No players match this selection.";
  }

  const home = average(list.map((row) => row.home));
  const away = average(list.map((row) => row.away));

  return `This view shows the ${modeLabels[selectedViewMode.value]}. For these ${list.length} players, home averages ${home.toFixed(3)} and away averages ${away.toFixed(3)}.`;
});

function buildCompareFigure() {
  const list = leaderboardRows.value;

  // bar chart with home and away ratings
  return {
    data: [
      {
        type: "bar",
        name: "Home",
        x: list.map((row) => row.player),
        y: list.map((row) => row.home),
        marker: { color: "#2E8B57" },
        hovertemplate: "<b>%{x}</b><br>Home average rating: %{y:.3f}<extra></extra>",
      },
      {
        type: "bar",
        name: "Away",
        x: list.map((row) => row.player),
        y: list.map((row) => row.away),
        marker: { color: "#1F77B4" },
        hovertemplate: "<b>%{x}</b><br>Away average rating: %{y:.3f}<extra></extra>",
      },
    ],
    layout: {
      title: "Leaderboard comparison by player",
      barmode: "group",
      margin: { t: 64, r: 24, b: 110, l: 72 },
      paper_bgcolor: "#ffffff",
      plot_bgcolor: "#ffffff",
      legend: { orientation: "h", y: 1.12 },
      xaxis: {
        title: "Player",
        tickangle: 50,
        automargin: true,
      },
      yaxis: {
        title: "Average Overall Rating",
      },
    },
  };
}

function buildScatterFigure() {
  // scatter plot for all players
  const allRatings = rows.flatMap((row) => [row.away, row.home]);
  // add some space around the axes
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
        customdata: rows.map((row) => [row.homeMatches, row.awayMatches, row.delta]),
        marker: {
          color: "#1F77B4",
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
          color: "#DC2626",
          size: 16,
          opacity: 0.98,
          line: { color: "#ffffff", width: 1.5 },
        },
        hovertemplate: "Overall average<br>Away: %{x:.3f}<br>Home: %{y:.3f}<extra></extra>",
        },
      ],
      layout: {
        title: "Home vs away average rating",
      margin: { t: 64, r: 24, b: 72, l: 72 },
      paper_bgcolor: "#ffffff",
      plot_bgcolor: "#ffffff",
      hovermode: "closest",
      legend: { orientation: "h", y: 1.12 },
        annotations: [
          {
            // label the overall average point
            x: overallAway,
            y: overallHome,
            xref: "x",
            yref: "y",
          showarrow: false,
          xanchor: "left",
          xshift: 14,
          bgcolor: "#ffffff",
          bordercolor: "#DC2626",
          borderwidth: 1,
          borderpad: 4,
          text: `Average<br>Away: ${overallAway.toFixed(3)}<br>Home: ${overallHome.toFixed(3)}`,
        },
      ],
      xaxis: {
        title: "Away Average Overall Rating",
        range: [axisMin, axisMax],
      },
      yaxis: {
        title: "Home Average Overall Rating",
        range: [axisMin, axisMax],
        scaleanchor: "x",
        scaleratio: 1,
      },
    },
  };
}

// choose which chart to show
const figure = computed(() =>
  selectedChart.value === "scatter" ? buildScatterFigure() : buildCompareFigure(),
);

async function renderChart() {
  if (!chartRef.value) {
    return;
  }

  // wait until the chart container is ready
  await nextTick();
  await waitForFrame();

  await Plotly.react(chartRef.value, figure.value.data, figure.value.layout, {
    responsive: true,
    displayModeBar: true,
  });

  Plotly.Plots.resize(chartRef.value);
}

function handleResize() {
  // resize the chart with the window
  if (chartRef.value) {
    Plotly.Plots.resize(chartRef.value);
  }
}

// redraw when controls change
watch([selectedChart, selectedViewMode, topN], renderChart);

onMounted(async () => {
  // draw the chart on page load
  window.addEventListener("resize", handleResize);
  await renderChart();
});

onBeforeUnmount(() => {
  // clean up before leaving the page
  window.removeEventListener("resize", handleResize);

  if (chartRef.value) {
    Plotly.purge(chartRef.value);
  }
});
</script>
