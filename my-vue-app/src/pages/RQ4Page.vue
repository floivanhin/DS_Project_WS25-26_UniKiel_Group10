<template>
  <div class="rq4-page">
    <section class="rq4-hero">
      <h1 class="rq4-page-title">
        How does playing at home compared to away affect player performance
        ratings?
      </h1>
      <p class="rq4-page-subtitle">
        {{ researchQuestionAnswer }}
      </p>
    </section>

    <section class="rq4-controls">
      <div class="rq4-control-block">
        <span class="rq4-control-label">Chart view</span>

        <div class="rq4-radio-group">
          <label class="rq4-radio-option">
            <input v-model="selectedChart" type="radio" value="compare" />
            <span>Leaderboard comparison</span>
          </label>

          <label class="rq4-radio-option">
            <input v-model="selectedChart" type="radio" value="scatter" />
            <span>Eligible-player scatter</span>
          </label>
        </div>
      </div>

      <div v-if="selectedChart !== 'scatter'" class="rq4-control-grid">
        <div class="rq4-control-block">
          <label class="rq4-control-label" for="rq4ViewMode"
            >Leaderboard mode</label
          >
          <select
            id="rq4ViewMode"
            v-model="selectedViewMode"
            class="rq4-select-control"
          >
            <option value="abs_delta">Largest gaps</option>
            <option value="home_specialists">Home specialists</option>
            <option value="away_specialists">Away specialists</option>
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
          <div class="rq4-range-meta">Showing {{ topN }} players</div>
        </div>
      </div>
    </section>

    <section class="rq4-description">
      {{ plotDescription }}
    </section>

    <section class="rq4-chart-card">
      <div class="rq4-chart-toolbar">
        <button
          type="button"
          class="rq4-download-button"
          :disabled="isDownloading"
          @click="downloadChartAsPng"
        >
          {{ isDownloading ? "Preparing PNG..." : "Download PNG" }}
        </button>
        <button
          type="button"
          class="rq4-download-button rq4-download-button-secondary"
          :disabled="isExportingCsv"
          @click="downloadChartAsCsv"
        >
          {{ isExportingCsv ? "Preparing CSV..." : "Download CSV" }}
        </button>
      </div>
      <div ref="chartRef" class="rq4-chart"></div>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import Plotly from "plotly.js-dist-min";
import deltaCsv from "../../data/rq4/rq4_player_home_away_delta.csv?raw";

// Labels used in the UI and in the explanation text below the controls.
const MODE_LABELS = {
  abs_delta: "largest home-away gaps",
  home_specialists: "strongest home specialists",
  away_specialists: "strongest away specialists",
};

const DEFAULT_CHART = "compare";
const DEFAULT_VIEW_MODE = "abs_delta";
const DEFAULT_TOP_N = 10;

// Reads CSV text into an array of objects while handling quoted values safely.
function parseCsv(text) {
  const normalizedText = text.replace(/^\uFEFF/, "");
  const rows = [];
  let currentRow = [];
  let currentValue = "";
  let insideQuotes = false;

  for (let index = 0; index < normalizedText.length; index += 1) {
    const char = normalizedText[index];

    if (char === '"') {
      if (insideQuotes && normalizedText[index + 1] === '"') {
        currentValue += '"';
        index += 1;
      } else {
        insideQuotes = !insideQuotes;
      }
      continue;
    }

    if (char === "," && !insideQuotes) {
      currentRow.push(currentValue);
      currentValue = "";
      continue;
    }

    if ((char === "\n" || char === "\r") && !insideQuotes) {
      if (char === "\r" && normalizedText[index + 1] === "\n") {
        index += 1;
      }

      currentRow.push(currentValue);
      if (currentRow.some((value) => value !== "")) {
        rows.push(currentRow);
      }
      currentRow = [];
      currentValue = "";
      continue;
    }

    currentValue += char;
  }

  if (currentValue !== "" || currentRow.length > 0) {
    currentRow.push(currentValue);
    if (currentRow.some((value) => value !== "")) {
      rows.push(currentRow);
    }
  }

  if (rows.length === 0) {
    return [];
  }

  const [headerRow, ...dataRows] = rows;
  const headers = headerRow.map((header) => header.trim());

  return dataRows.map((row) =>
    Object.fromEntries(
      headers.map((header, headerIndex) => [header, row[headerIndex] ?? ""]),
    ),
  );
}

// Converts CSV strings to numbers and keeps invalid values as null.
function toNumber(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

// The derived CSV stores booleans as text, so we normalize them here.
function toBoolean(value) {
  return String(value).trim().toLowerCase() === "true";
}

// Small helper for league-wide averages used in the summary text.
function mean(values) {
  if (values.length === 0) {
    return null;
  }

  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function computeLinearTrend(rows, xSelector, ySelector) {
  if (rows.length < 2) {
    return null;
  }

  let sumX = 0;
  let sumY = 0;
  let sumXY = 0;
  let sumXSquare = 0;

  for (const row of rows) {
    const x = xSelector(row);
    const y = ySelector(row);
    sumX += x;
    sumY += y;
    sumXY += x * y;
    sumXSquare += x * x;
  }

  const denominator = rows.length * sumXSquare - sumX * sumX;
  if (denominator === 0) {
    return null;
  }

  const slope = (rows.length * sumXY - sumX * sumY) / denominator;
  const intercept = (sumY - slope * sumX) / rows.length;
  return { slope, intercept };
}

// Waiting one browser frame avoids rendering Plotly before the container is ready.
function waitForFrame() {
  return new Promise((resolve) => {
    requestAnimationFrame(() => resolve());
  });
}

// Reusable fallback figure for empty or invalid datasets.
function emptyFigure(title) {
  return {
    data: [],
    layout: {
      title,
      margin: { t: 64, r: 24, b: 64, l: 64 },
      paper_bgcolor: "#ffffff",
      plot_bgcolor: "#ffffff",
      xaxis: { visible: false },
      yaxis: { visible: false },
      annotations: [
        {
          text: "No data available",
          showarrow: false,
          xref: "paper",
          yref: "paper",
          x: 0.5,
          y: 0.5,
          font: { size: 16, color: "#475569" },
        },
      ],
    },
  };
}

// Convert the raw CSV text into JavaScript objects with usable field names.
function buildDeltaRows() {
  return parseCsv(deltaCsv).map((row) => ({
    player: row.player,
    home_avg_overall_rating: toNumber(row.home_avg_overall_rating),
    away_avg_overall_rating: toNumber(row.away_avg_overall_rating),
    avg_rating_delta_home_minus_away: toNumber(
      row.avg_rating_delta_home_minus_away,
    ),
    abs_avg_rating_delta: toNumber(row.abs_avg_rating_delta),
    home_matches: toNumber(row.home_matches),
    away_matches: toNumber(row.away_matches),
    eligible_both_sides: toBoolean(row.eligible_both_sides),
  }));
}

// The CSV file does not change while the page is open, so we parse it once here.
const deltaRows = buildDeltaRows();

// Keep only rows that are safe to use in the charts and text summaries.
const eligibleDeltaRows = deltaRows.filter(
  (row) =>
    row.eligible_both_sides &&
    row.player &&
    row.home_avg_overall_rating !== null &&
    row.away_avg_overall_rating !== null &&
    row.avg_rating_delta_home_minus_away !== null &&
    row.abs_avg_rating_delta !== null &&
    row.home_matches !== null &&
    row.away_matches !== null,
);

// Use the same cohort across the headline, scatter, and leaderboard views.
const scatterRows = eligibleDeltaRows;

// `ref(...)` creates reactive state. When one of these values changes, Vue can redraw the chart.
const chartRef = ref(null);
const selectedChart = ref(DEFAULT_CHART);
const selectedViewMode = ref(DEFAULT_VIEW_MODE);
const topN = ref(DEFAULT_TOP_N);
const isDownloading = ref(false);
const isExportingCsv = ref(false);
let scatterAnnotationRestoreTimer = null;

// Produces the short answer shown directly under the page title.
function buildResearchQuestionAnswer() {
  const meanHomeRating = mean(
    eligibleDeltaRows.map((row) => row.home_avg_overall_rating),
  );
  const meanAwayRating = mean(
    eligibleDeltaRows.map((row) => row.away_avg_overall_rating),
  );

  if (
    eligibleDeltaRows.length === 0 ||
    meanHomeRating === null ||
    meanAwayRating === null
  ) {
    return "The derived RQ4 tables do not contain enough data to support a home-versus-away conclusion.";
  }

  // Count how many players are better at home or away to support the written summary.
  const homeBetterCount = eligibleDeltaRows.filter(
    (row) => row.avg_rating_delta_home_minus_away > 0,
  ).length;
  const awayBetterCount = eligibleDeltaRows.filter(
    (row) => row.avg_rating_delta_home_minus_away < 0,
  ).length;
  const delta = meanHomeRating - meanAwayRating;

  return `Players perform slightly better at home overall: average home rating is ${meanHomeRating.toFixed(3)} versus ${meanAwayRating.toFixed(3)} away (${delta >= 0 ? "+" : ""}${delta.toFixed(3)}). The effect is modest, but ${homeBetterCount} of ${eligibleDeltaRows.length} eligible players rate better at home, compared with ${awayBetterCount} who rate better away.`;
}

// Returns the player subset that should appear in the current chart.
function getLeaderboard(viewMode, rankingDepth) {
  // `slice()` makes a copy so sorting below does not change the original full dataset.
  let leaderboard = eligibleDeltaRows.slice();

  if (viewMode === "home_specialists") {
    // Home specialists are players with a positive home-minus-away difference.
    leaderboard = leaderboard
      .filter((row) => row.avg_rating_delta_home_minus_away > 0)
      .sort((left, right) => {
        if (
          right.avg_rating_delta_home_minus_away !==
          left.avg_rating_delta_home_minus_away
        ) {
          return (
            right.avg_rating_delta_home_minus_away -
            left.avg_rating_delta_home_minus_away
          );
        }
        return left.player.localeCompare(right.player);
      });
  } else if (viewMode === "away_specialists") {
    // Away specialists are the same idea, but with a negative delta.
    leaderboard = leaderboard
      .filter((row) => row.avg_rating_delta_home_minus_away < 0)
      .sort((left, right) => {
        if (
          left.avg_rating_delta_home_minus_away !==
          right.avg_rating_delta_home_minus_away
        ) {
          return (
            left.avg_rating_delta_home_minus_away -
            right.avg_rating_delta_home_minus_away
          );
        }
        return left.player.localeCompare(right.player);
      });
  } else {
    // "Largest gaps" ignores direction and sorts by the absolute difference.
    leaderboard = leaderboard.sort((left, right) => {
      if (right.abs_avg_rating_delta !== left.abs_avg_rating_delta) {
        return right.abs_avg_rating_delta - left.abs_avg_rating_delta;
      }
      return left.player.localeCompare(right.player);
    });
  }

  return leaderboard.slice(0, Number(rankingDepth));
}

// Summarizes the averages for the rows currently shown in the active chart.
function buildSelectionSummaryText(rows, prefix) {
  if (rows.length === 0) {
    return "";
  }

  const meanHomeSelectionRating = mean(
    rows
      .map((row) => row.home_avg_overall_rating)
      .filter((value) => value !== null),
  );
  const meanAwaySelectionRating = mean(
    rows
      .map((row) => row.away_avg_overall_rating)
      .filter((value) => value !== null),
  );

  if (meanHomeSelectionRating === null || meanAwaySelectionRating === null) {
    return "";
  }

  const delta = meanHomeSelectionRating - meanAwaySelectionRating;
  const deltaText = `${delta >= 0 ? "+" : ""}${delta.toFixed(3)}`;
  return `${prefix} home rating: ${meanHomeSelectionRating.toFixed(3)}; away rating: ${meanAwaySelectionRating.toFixed(3)}; delta: ${deltaText}.`;
}

// Grouped bar chart for comparing home and away averages per player.
function buildCompareFigure(viewMode, rankingDepth) {
  const leaderboard = getLeaderboard(viewMode, rankingDepth);

  if (leaderboard.length === 0) {
    return emptyFigure("No comparison data available");
  }

  return {
    data: [
      {
        type: "bar",
        name: "Home",
        x: leaderboard.map((row) => row.player),
        y: leaderboard.map((row) => row.home_avg_overall_rating),
        marker: { color: "#2E8B57" },
        hovertemplate:
          "<b>%{x}</b><br>Home average rating: %{y:.3f}<extra></extra>",
      },
      {
        type: "bar",
        name: "Away",
        x: leaderboard.map((row) => row.player),
        y: leaderboard.map((row) => row.away_avg_overall_rating),
        marker: { color: "#1F77B4" },
        hovertemplate:
          "<b>%{x}</b><br>Away average rating: %{y:.3f}<extra></extra>",
      },
    ],
    layout: {
      title: "Leaderboard Comparison by Player",
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

function buildOverallAverageAnnotation(averageAwayRating, averageHomeRating) {
  return {
    x: averageAwayRating,
    y: averageHomeRating,
    xref: "x",
    yref: "y",
    visible: true,
    showarrow: false,
    xanchor: "left",
    yanchor: "middle",
    xshift: 18,
    align: "left",
    bgcolor: "#ffffff",
    bordercolor: "#DC2626",
    borderwidth: 1,
    borderpad: 4,
    font: {
      color: "#111827",
      size: 12,
    },
    text:
      `<b>Overall average</b><br>X (Away average rating): ${averageAwayRating.toFixed(3)}<br>Y (Home average rating): ${averageHomeRating.toFixed(3)}<br>Delta (Home - Away): ${(averageHomeRating - averageAwayRating).toFixed(3)}`,
  };
}

function buildScatterFigure() {
  if (scatterRows.length === 0) {
    return emptyFigure("No scatter data available");
  }

  // These values are reused for the red average point, the trend line, and the axis limits.
  const averageAwayRating =
    scatterRows.reduce(
      (sum, row) => sum + row.away_avg_overall_rating,
      0,
    ) / scatterRows.length;
  const averageHomeRating =
    scatterRows.reduce(
      (sum, row) => sum + row.home_avg_overall_rating,
      0,
    ) / scatterRows.length;
  const trend = computeLinearTrend(
    scatterRows,
    (row) => row.away_avg_overall_rating,
    (row) => row.home_avg_overall_rating,
  );
  const allRatings = scatterRows.flatMap((row) => [
    row.away_avg_overall_rating,
    row.home_avg_overall_rating,
  ]);
  const minAwayRating = Math.min(
    ...scatterRows.map((row) => row.away_avg_overall_rating),
  );
  const maxAwayRating = Math.max(
    ...scatterRows.map((row) => row.away_avg_overall_rating),
  );
  const minRating = Math.min(...allRatings);
  const maxRating = Math.max(...allRatings);
  const padding = Math.max((maxRating - minRating) * 0.05, 0.05);
  const axisMin = minRating - padding;
  const axisMax = maxRating + padding;
  const data = [
    {
      type: "scatter",
      mode: "markers",
      name: "Players",
      x: scatterRows.map((row) => row.away_avg_overall_rating),
      y: scatterRows.map((row) => row.home_avg_overall_rating),
      text: scatterRows.map((row) => row.player),
      customdata: scatterRows.map((row) => [
        row.home_matches,
        row.away_matches,
        row.avg_rating_delta_home_minus_away,
      ]),
      marker: {
        color: "#1F77B4",
        size: 10,
        opacity: 0.72,
        line: { color: "#ffffff", width: 0.8 },
      },
      hovertemplate:
        "<b>%{text}</b><br>Away average rating: %{x:.3f}<br>Home average rating: %{y:.3f}<br>Delta (Home - Away): %{customdata[2]:.3f}<br>Home matches: %{customdata[0]}<br>Away matches: %{customdata[1]}<extra></extra>",
    },
  ];

  if (trend) {
    data.push({
      type: "scatter",
      mode: "lines",
      name: "Trend line",
      x: [minAwayRating, maxAwayRating],
      y: [
        trend.slope * minAwayRating + trend.intercept,
        trend.slope * maxAwayRating + trend.intercept,
      ],
      line: {
        color: "#111827",
        dash: "dash",
        width: 2,
      },
      hoverinfo: "skip",
    });
  }

  data.push({
    type: "scatter",
    mode: "markers",
    name: "Overall average",
    x: [averageAwayRating],
    y: [averageHomeRating],
    text: ["Overall average"],
    marker: {
      color: "#DC2626",
      size: 16,
      opacity: 0.98,
      line: { color: "#ffffff", width: 1.5 },
    },
    hoverinfo: "skip",
  });

  return {
    data,
    layout: {
      title: "Home vs Away Average Rating for Eligible Players",
      margin: { t: 64, r: 24, b: 72, l: 72 },
      paper_bgcolor: "#ffffff",
      plot_bgcolor: "#ffffff",
      hovermode: "closest",
      legend: { orientation: "h", y: 1.12 },
      annotations: [
        buildOverallAverageAnnotation(averageAwayRating, averageHomeRating),
      ],
      shapes: [
        {
          type: "line",
          x0: axisMin,
          y0: axisMin,
          x1: axisMax,
          y1: axisMax,
          line: {
            color: "#94A3B8",
            dash: "dot",
            width: 1.5,
          },
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

// Central switch so all render paths decide the chart type in one place.
function buildFigure() {
  if (selectedChart.value === "scatter") {
    return buildScatterFigure();
  }

  return buildCompareFigure(selectedViewMode.value, topN.value);
}

const plotDescription = computed(() => {
  if (selectedChart.value === "scatter") {
    const scatterSummary = buildSelectionSummaryText(
      scatterRows,
      `Across all ${scatterRows.length} eligible players, average`,
    );

    return `This scatter uses all ${scatterRows.length} eligible players with valid home and away averages on both sides. The x-axis shows each player's away average overall rating, and the y-axis shows the home average overall rating. Points above the dotted parity line indicate better home ratings, the dashed line shows the overall linear trend, and the larger red point marks the overall average across all displayed players. Its callout is visible by default, while the other points only show their details on hover. ${scatterSummary}`.trim();
  }

  const leaderboard = getLeaderboard(selectedViewMode.value, topN.value);
  const selectionSummary = buildSelectionSummaryText(
    leaderboard,
    `Across the ${leaderboard.length} displayed players, average`,
  );

  return `This view highlights the ${MODE_LABELS[selectedViewMode.value]}. ${selectionSummary}`.trim();
});

const researchQuestionAnswer = computed(() => buildResearchQuestionAnswer());

// These helpers control the default red annotation in scatter mode.
// It hides while the user hovers a player and comes back afterward.
function clearScatterAnnotationRestoreTimer() {
  if (scatterAnnotationRestoreTimer !== null) {
    window.clearTimeout(scatterAnnotationRestoreTimer);
    scatterAnnotationRestoreTimer = null;
  }
}

function showDefaultScatterAnnotation() {
  if (!chartRef.value || selectedChart.value !== "scatter") {
    return;
  }

  const annotations = chartRef.value.layout?.annotations;
  if (!Array.isArray(annotations) || annotations.length === 0) {
    return;
  }

  if (annotations[0]?.visible === true) {
    return;
  }

  Plotly.relayout(chartRef.value, {
    "annotations[0].visible": true,
  });
}

function hideDefaultScatterAnnotation() {
  if (!chartRef.value || selectedChart.value !== "scatter") {
    return;
  }

  const annotations = chartRef.value.layout?.annotations;
  if (!Array.isArray(annotations) || annotations.length === 0) {
    return;
  }

  if (annotations[0]?.visible === false) {
    return;
  }

  Plotly.relayout(chartRef.value, {
    "annotations[0].visible": false,
  });
}

function scheduleDefaultScatterAnnotation() {
  clearScatterAnnotationRestoreTimer();
  scatterAnnotationRestoreTimer = window.setTimeout(() => {
    scatterAnnotationRestoreTimer = null;
    showDefaultScatterAnnotation();
  }, 0);
}

function handleScatterHover(event) {
  const hoveredTraceName = event?.points?.[0]?.data?.name;
  clearScatterAnnotationRestoreTimer();

  if (hoveredTraceName === "Players") {
    hideDefaultScatterAnnotation();
    return;
  }

  showDefaultScatterAnnotation();
}

function handleScatterUnhover() {
  scheduleDefaultScatterAnnotation();
}

function bindScatterHoverEvents() {
  if (!chartRef.value?.on) {
    return;
  }

  chartRef.value.removeListener?.("plotly_hover", handleScatterHover);
  chartRef.value.removeListener?.("plotly_unhover", handleScatterUnhover);
  chartRef.value.on("plotly_hover", handleScatterHover);
  chartRef.value.on("plotly_unhover", handleScatterUnhover);
}

function unbindScatterHoverEvents() {
  clearScatterAnnotationRestoreTimer();
  showDefaultScatterAnnotation();

  if (!chartRef.value) {
    return;
  }

  chartRef.value.removeListener?.("plotly_hover", handleScatterHover);
  chartRef.value.removeListener?.("plotly_unhover", handleScatterUnhover);
}

// Renders or updates the Plotly chart whenever state changes.
async function renderChart() {
  if (!chartRef.value) {
    return;
  }

  await nextTick();
  await waitForFrame();

  const figure = buildFigure();

  await Plotly.react(chartRef.value, figure.data, figure.layout, {
    responsive: true,
    displayModeBar: false,
  });

  Plotly.Plots.resize(chartRef.value);

  if (selectedChart.value === "scatter") {
    bindScatterHoverEvents();
    await waitForFrame();
    clearScatterAnnotationRestoreTimer();
    showDefaultScatterAnnotation();
    return;
  }

  unbindScatterHoverEvents();
  Plotly.Fx.unhover(chartRef.value);
}

function buildDownloadFilename() {
  if (selectedChart.value === "scatter") {
    return "rq4-scatter-eligible-players.png";
  }

  return `rq4-${selectedChart.value}-${selectedViewMode.value}-top-${topN.value}.png`;
}

function buildCsvFilename() {
  if (selectedChart.value === "scatter") {
    return "rq4-scatter-eligible-players.csv";
  }

  return `rq4-${selectedChart.value}-${selectedViewMode.value}-top-${topN.value}.csv`;
}

function escapeCsvValue(value) {
  const text = value === null || value === undefined ? "" : String(value);

  if (/[",\n\r]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }

  return text;
}

function rowsToCsv(rows) {
  if (rows.length === 0) {
    return "";
  }

  const headers = Array.from(
    rows.reduce((headerSet, row) => {
      Object.keys(row).forEach((key) => headerSet.add(key));
      return headerSet;
    }, new Set()),
  );

  const csvLines = [
    headers.join(","),
    ...rows.map((row) =>
      headers.map((header) => escapeCsvValue(row[header])).join(","),
    ),
  ];

  return csvLines.join("\r\n");
}

function triggerFileDownload(filename, content, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = objectUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  setTimeout(() => URL.revokeObjectURL(objectUrl), 0);
}

// Export only the rows that belong to the chart the user is currently viewing.
function buildCurrentCsvRows() {
  if (selectedChart.value === "scatter") {
    return scatterRows
      .slice()
      .sort((left, right) => left.player.localeCompare(right.player))
      .map((row) => ({
        player: row.player,
        away_avg_overall_rating: row.away_avg_overall_rating,
        home_avg_overall_rating: row.home_avg_overall_rating,
        avg_rating_delta_home_minus_away: row.avg_rating_delta_home_minus_away,
        away_matches: row.away_matches,
        home_matches: row.home_matches,
        eligible_both_sides: row.eligible_both_sides,
      }));
  }

  const leaderboard = getLeaderboard(selectedViewMode.value, topN.value);

  return leaderboard.flatMap((row) => [
    {
      player: row.player,
      setting: "Home",
      avg_overall_rating: row.home_avg_overall_rating,
    },
    {
      player: row.player,
      setting: "Away",
      avg_overall_rating: row.away_avg_overall_rating,
    },
  ]);
}

async function downloadChartAsPng() {
  if (!chartRef.value || isDownloading.value) {
    return;
  }

  isDownloading.value = true;

  try {
    await nextTick();
    await waitForFrame();

    await Plotly.downloadImage(chartRef.value, {
      format: "png",
      filename: buildDownloadFilename().replace(/\.png$/, ""),
      width: 1600,
      height: 900,
      scale: 2,
    });
  } finally {
    isDownloading.value = false;
  }
}

async function downloadChartAsCsv() {
  if (isExportingCsv.value) {
    return;
  }

  isExportingCsv.value = true;

  try {
    const rows = buildCurrentCsvRows();
    const csvContent = rowsToCsv(rows);

    triggerFileDownload(
      buildCsvFilename(),
      csvContent,
      "text/csv;charset=utf-8;",
    );
  } finally {
    isExportingCsv.value = false;
  }
}

// Plotly needs a manual resize call when the window changes size.
function handleResize() {
  if (chartRef.value) {
    Plotly.Plots.resize(chartRef.value);

    if (selectedChart.value === "scatter") {
      requestAnimationFrame(() => {
        showDefaultScatterAnnotation();
      });
    }
  }
}

// Whenever the controls change, rebuild the chart with the new selection.
watch([selectedChart, selectedViewMode, topN], async () => {
  await renderChart();
});

onMounted(async () => {
  window.addEventListener("resize", handleResize);
  await renderChart();
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  unbindScatterHoverEvents();

  if (chartRef.value) {
    // Clean up Plotly's internal listeners when leaving the page.
    Plotly.purge(chartRef.value);
  }
});
</script>
