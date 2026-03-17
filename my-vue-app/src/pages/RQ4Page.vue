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
            <span>All Player Scatter</span>
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

// Waiting one browser frame avoids rendering Plotly before the container is ready.
function waitForFrame() {
  return new Promise((resolve) => {
    requestAnimationFrame(() => resolve());
  });
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
    throw new Error("RQ4 comparison chart expected leaderboard data, but none was found.");
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

// Creates the default scatter annotation.
// It belongs to the red point and shows the overall average across all displayed players.
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

// Builds the scatter plot that compares each player's away and home rating.
function buildScatterFigure() {
  if (scatterRows.length === 0) {
    throw new Error("RQ4 scatter chart expected eligible player data, but none was found.");
  }

  // These values are reused for the red average point and the axis limits.
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
  const allRatings = scatterRows.flatMap((row) => [
    row.away_avg_overall_rating,
    row.home_avg_overall_rating,
  ]);
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
    return `This chart shows ${scatterRows.length} players. The bottom axis shows each player's away rating. The left axis shows each player's home rating. The red point shows the average of all shown players. You can move your mouse over a blue point to see that player's details.`;
  }

  const leaderboard = getLeaderboard(selectedViewMode.value, topN.value);
  const selectionSummary = buildSelectionSummaryText(
    leaderboard,
    `Across the ${leaderboard.length} displayed players, average`,
  );

  return `This view highlights the ${MODE_LABELS[selectedViewMode.value]}. ${selectionSummary}`.trim();
});

const researchQuestionAnswer = computed(() => buildResearchQuestionAnswer());

// Stops the timer that would show the default scatter annotation again.
function clearScatterAnnotationRestoreTimer() {
  if (scatterAnnotationRestoreTimer !== null) {
    window.clearTimeout(scatterAnnotationRestoreTimer);
    scatterAnnotationRestoreTimer = null;
  }
}

// Shows the default scatter annotation.
// That default annotation is the average label for the red overall-average point, not a single player.
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

// Hides the default scatter annotation while the user is hovering player points.
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

// Schedules the default scatter annotation to appear again after hover ends.
function scheduleDefaultScatterAnnotation() {
  clearScatterAnnotationRestoreTimer();
  scatterAnnotationRestoreTimer = window.setTimeout(() => {
    scatterAnnotationRestoreTimer = null;
    showDefaultScatterAnnotation();
  }, 0);
}

// Decides whether the default scatter annotation should be shown or hidden on hover.
function handleScatterHover(event) {
  const hoveredTraceName = event?.points?.[0]?.data?.name;
  clearScatterAnnotationRestoreTimer();

  if (hoveredTraceName === "Players") {
    hideDefaultScatterAnnotation();
    return;
  }

  showDefaultScatterAnnotation();
}

// Restores the default scatter annotation after the mouse leaves a point.
function handleScatterUnhover() {
  scheduleDefaultScatterAnnotation();
}

// Connects Plotly hover events that control the default scatter annotation.
function bindScatterHoverEvents() {
  if (!chartRef.value?.on) {
    return;
  }

  chartRef.value.removeListener?.("plotly_hover", handleScatterHover);
  chartRef.value.removeListener?.("plotly_unhover", handleScatterUnhover);
  chartRef.value.on("plotly_hover", handleScatterHover);
  chartRef.value.on("plotly_unhover", handleScatterUnhover);
}

// Removes the Plotly hover events used for the default scatter annotation.
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
    displayModeBar: true,
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
