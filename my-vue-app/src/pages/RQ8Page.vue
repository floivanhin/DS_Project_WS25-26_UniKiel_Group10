<template>
  <div class="rq8-page">
    <section class="rq8-hero">
      <h1 class="rq8-page-title">
        Is there an ideal player age or average team age for strong shooting
        efficiency?
      </h1>
      <p class="rq8-page-subtitle">
        {{ researchQuestionAnswer }}
      </p>
    </section>

    <section class="rq8-controls">
      <div class="rq8-control-block">
        <span class="rq8-control-label">Chart view</span>

        <div class="rq8-radio-group">
          <label class="rq8-radio-option">
            <input v-model="selectedChart" type="radio" value="team_scatter" />
            <span>Team age vs efficiency</span>
          </label>

          <label class="rq8-radio-option">
            <input v-model="selectedChart" type="radio" value="age_profile" />
            <span>Player age profile</span>
          </label>
        </div>
      </div>

      <div
        v-if="selectedChart === 'age_profile'"
        class="rq8-control-block rq8-compact-block"
      >
        <label class="rq8-control-label" for="rq8MinShots"
          >Minimum shots per age band</label
        >
        <div class="rq8-range-wrap">
          <input
            id="rq8MinShots"
            v-model.number="minShots"
            class="rq8-range-control"
            type="range"
            :min="MIN_SHOTS_MIN"
            :max="MIN_SHOTS_MAX"
            :step="MIN_SHOTS_STEP"
          />
          <div class="rq8-range-markers" aria-hidden="true">
            <span
              v-for="threshold in minShotThresholds"
              :key="threshold"
              class="rq8-range-marker"
              :class="{
                'is-current': threshold === minShots,
                'is-reference': threshold === referenceMinShotsThreshold,
              }"
              :style="{ left: `${getRangePercent(threshold)}%` }"
            >
              <span class="rq8-range-marker-tick"></span>
              <span class="rq8-range-marker-label">{{ threshold }}</span>
            </span>
          </div>
        </div>
        <div class="rq8-range-meta">{{ minShots }} minimum shots</div>
      </div>
    </section>

    <section class="rq8-description">
      {{ plotDescription }}
    </section>

    <section class="rq8-chart-card">
      <div class="rq8-chart-toolbar">
        <button
          type="button"
          class="rq8-download-button"
          :disabled="isDownloading"
          @click="downloadChartAsPng"
        >
          {{ isDownloading ? "Preparing PNG..." : "Download PNG" }}
        </button>
        <button
          type="button"
          class="rq8-download-button rq8-download-button-secondary"
          :disabled="isExportingCsv"
          @click="downloadChartAsCsv"
        >
          {{ isExportingCsv ? "Preparing CSV..." : "Download CSV" }}
        </button>
      </div>
      <div ref="chartRef" class="rq8-chart"></div>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import Plotly from "plotly.js-dist-min";
import teamEfficiencyCsv from "../../data/rq8/rq8_team_age_vs_efficiency.csv?raw";
import optimalAgeCsv from "../../data/rq8/rq8_optimal_age_summary.csv?raw";
import playerAgeProfileCsv from "../../data/rq8/rq8_player_age_profile.csv?raw";
import playerBestAgeCsv from "../../data/rq8/rq8_player_best_age.csv?raw";

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

function toNumber(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function waitForFrame() {
  return new Promise((resolve) => {
    requestAnimationFrame(() => resolve());
  });
}

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

function computeLinearTrend(rows) {
  if (rows.length < 2) {
    return null;
  }

  let sumX = 0;
  let sumY = 0;
  let sumXY = 0;
  let sumXSquare = 0;

  for (const row of rows) {
    sumX += row.avg_age;
    sumY += row.goals_per_shot;
    sumXY += row.avg_age * row.goals_per_shot;
    sumXSquare += row.avg_age * row.avg_age;
  }

  const denominator = rows.length * sumXSquare - sumX * sumX;
  if (denominator === 0) {
    return null;
  }

  const slope = (rows.length * sumXY - sumX * sumY) / denominator;
  const intercept = (sumY - slope * sumX) / rows.length;
  return { slope, intercept };
}

const MIN_SHOTS_MIN = 50;
const MIN_SHOTS_MAX = 800;
const MIN_SHOTS_STEP = 10;

const teamEfficiencyRows = parseCsv(teamEfficiencyCsv).map((row) => ({
  team: row.team,
  avg_age: toNumber(row.avg_age),
  matches: toNumber(row.matches),
  total_goals: toNumber(row.total_goals),
  total_shots: toNumber(row.total_shots),
  goals_per_shot: toNumber(row.goals_per_shot),
}));

const optimalAgeRows = parseCsv(optimalAgeCsv).map((row) => ({
  n_teams: toNumber(row.n_teams),
  pearson_r_age_efficiency: toNumber(row.pearson_r_age_efficiency),
  estimated_peak_age: toNumber(row.estimated_peak_age),
  estimated_peak_goals_per_shot: toNumber(row.estimated_peak_goals_per_shot),
  model_note: row.model_note,
}));

const playerAgeProfileRows = parseCsv(playerAgeProfileCsv).map((row) => ({
  age_int: toNumber(row.age_int),
  players: toNumber(row.players),
  total_goals: toNumber(row.total_goals),
  total_shots: toNumber(row.total_shots),
  goals_per_shot: toNumber(row.goals_per_shot),
})).filter(
  (row) =>
    row.age_int !== null &&
    row.players !== null &&
    row.total_goals !== null &&
    row.total_shots !== null &&
    row.goals_per_shot !== null,
);

const playerBestAgeRows = parseCsv(playerBestAgeCsv).map((row) => ({
  min_total_shots: toNumber(row.min_total_shots),
  best_age_int: toNumber(row.best_age_int),
  goals_per_shot: toNumber(row.goals_per_shot),
  total_shots: toNumber(row.total_shots),
  total_goals: toNumber(row.total_goals),
  players: toNumber(row.players),
}));

const storedBestAge = playerBestAgeRows[0] ?? null;
const referenceMinShotsThreshold = storedBestAge?.min_total_shots ?? 80;
const minShotThresholds = [
  MIN_SHOTS_MIN,
  referenceMinShotsThreshold,
  200,
  400,
  600,
  MIN_SHOTS_MAX,
]
  .filter((value, index, values) => value !== null && values.indexOf(value) === index)
  .sort((left, right) => left - right);

const selectedChart = ref("team_scatter");
const minShots = ref(referenceMinShotsThreshold);
const chartRef = ref(null);
const isExportingCsv = ref(false);
const isDownloading = ref(false);

function getRangePercent(value) {
  return ((Number(value) - MIN_SHOTS_MIN) / (MIN_SHOTS_MAX - MIN_SHOTS_MIN)) * 100;
}

function buildTeamScatterNote() {
  const rows = teamEfficiencyRows.filter(
    (row) => row.avg_age !== null && row.goals_per_shot !== null,
  );

  if (rows.length === 0) {
    return "No team efficiency data is available for the scatter plot.";
  }

  const averageAge =
    rows.reduce((sum, row) => sum + row.avg_age, 0) / rows.length;
  const averageEfficiency =
    rows.reduce((sum, row) => sum + row.goals_per_shot, 0) / rows.length;

  return `All ${rows.length} teams are included. They average ${averageEfficiency.toFixed(3)} goals per shot at an average squad age of ${averageAge.toFixed(2)} years.`;
}

function buildOptimalAgeText() {
  const row = optimalAgeRows[0];

  if (!row) {
    return "";
  }

  const parts = [];
  if (
    row.estimated_peak_age !== null &&
    row.estimated_peak_goals_per_shot !== null
  ) {
    parts.push(
      `Estimated quadratic peak: ${row.estimated_peak_age.toFixed(2)} years and ${row.estimated_peak_goals_per_shot.toFixed(3)} goals per shot.`,
    );
  }

  const note = String(row.model_note ?? "").trim();
  if (note && note.toLowerCase() !== "nan") {
    parts.push(note);
  }

  return parts.join(" ");
}

function buildStoredBestAgeText() {
  if (
    !storedBestAge ||
    storedBestAge.best_age_int === null ||
    storedBestAge.goals_per_shot === null ||
    storedBestAge.min_total_shots === null
  ) {
    return "";
  }

  return `Stored best-age result at ${storedBestAge.min_total_shots} shots: age ${storedBestAge.best_age_int} with ${storedBestAge.goals_per_shot.toFixed(3)} goals per shot.`;
}

function buildResearchQuestionAnswer() {
  const optimalRow = optimalAgeRows[0] ?? null;
  const validTeamRows = teamEfficiencyRows.filter((row) => row.avg_age !== null);
  const parts = [];

  if (optimalRow) {
    const teamScope =
      optimalRow.n_teams !== null
        ? `Across ${optimalRow.n_teams} teams, `
        : "";

    if (optimalRow.pearson_r_age_efficiency !== null) {
      parts.push(
        `${teamScope}there is no single supported optimal average team age: shooting efficiency trends downward as squads get older (r = ${optimalRow.pearson_r_age_efficiency.toFixed(3)}).`,
      );
    } else {
      parts.push(
        `${teamScope}there is no single supported optimal average team age in the precomputed team-level results.`,
      );
    }

    if (
      optimalRow.estimated_peak_age !== null &&
      validTeamRows.length > 0
    ) {
      const observedMinAge = Math.min(...validTeamRows.map((row) => row.avg_age));
      const observedMaxAge = Math.max(...validTeamRows.map((row) => row.avg_age));

      if (
        optimalRow.estimated_peak_age < observedMinAge ||
        optimalRow.estimated_peak_age > observedMaxAge
      ) {
        parts.push(
          `The fitted peak is ${optimalRow.estimated_peak_age.toFixed(2)} years, but that lies outside the observed team-average range of ${observedMinAge.toFixed(2)}-${observedMaxAge.toFixed(2)} years.`,
        );
      } else if (optimalRow.estimated_peak_goals_per_shot !== null) {
        parts.push(
          `The fitted peak appears at ${optimalRow.estimated_peak_age.toFixed(2)} years with ${optimalRow.estimated_peak_goals_per_shot.toFixed(3)} goals per shot.`,
        );
      }
    }
  }

  if (
    storedBestAge &&
    storedBestAge.best_age_int !== null &&
    storedBestAge.goals_per_shot !== null
  ) {
    let bestAgeSentence = `At player level, the best observed age band is ${storedBestAge.best_age_int}`;

    if (storedBestAge.min_total_shots !== null) {
      bestAgeSentence += ` at the ${storedBestAge.min_total_shots}-shot threshold`;
    }

    bestAgeSentence += ` with ${storedBestAge.goals_per_shot.toFixed(3)} goals per shot`;

    if (storedBestAge.total_shots !== null && storedBestAge.players !== null) {
      bestAgeSentence += ` across ${storedBestAge.total_shots} shots from ${storedBestAge.players} players`;
    }

    parts.push(`${bestAgeSentence}.`);
  }

  if (parts.length === 0) {
    return "The precomputed RQ8 outputs do not support a single universal optimal age, so the charts should be read as observed age-efficiency patterns rather than a fixed rule.";
  }

  return parts.join(" ");
}

function buildTeamScatterFigure() {
  const rows = teamEfficiencyRows.filter(
    (row) => row.avg_age !== null && row.goals_per_shot !== null,
  );

  if (rows.length === 0) {
    return emptyFigure("No team efficiency data available");
  }

  const trend = computeLinearTrend(rows);
  const optimalRow = optimalAgeRows[0] ?? null;
  const minAge = Math.min(...rows.map((row) => row.avg_age));
  const maxAge = Math.max(...rows.map((row) => row.avg_age));
  const data = [
    {
      type: "scatter",
      mode: "markers",
      name: "Teams",
      x: rows.map((row) => row.avg_age),
      y: rows.map((row) => row.goals_per_shot),
      text: rows.map((row) => row.team),
      marker: {
        color: "#B22222",
        size: 11,
      },
      hovertemplate:
        "<b>%{text}</b><br>Average age: %{x:.2f}<br>Goals per shot: %{y:.3f}<extra></extra>",
    },
  ];
  const shapes = [];

  if (trend) {
    data.push({
      type: "scatter",
      mode: "lines",
      name: "Trend line",
      x: [minAge, maxAge],
      y: [
        trend.slope * minAge + trend.intercept,
        trend.slope * maxAge + trend.intercept,
      ],
      line: {
        color: "#444444",
        dash: "dash",
      },
      hoverinfo: "skip",
    });
  }

  if (
    optimalRow &&
    optimalRow.estimated_peak_age !== null &&
    optimalRow.estimated_peak_goals_per_shot !== null &&
    optimalRow.estimated_peak_age >= minAge &&
    optimalRow.estimated_peak_age <= maxAge
  ) {
    data.push({
      type: "scatter",
      mode: "markers",
      name: "Estimated peak",
      x: [optimalRow.estimated_peak_age],
      y: [optimalRow.estimated_peak_goals_per_shot],
      marker: {
        color: "#7A0010",
        size: 14,
        symbol: "star",
      },
      hovertemplate:
        "Estimated peak age: %{x:.2f}<br>Goals per shot: %{y:.3f}<extra></extra>",
    });

    shapes.push({
      type: "line",
      x0: optimalRow.estimated_peak_age,
      x1: optimalRow.estimated_peak_age,
      y0: 0,
      y1: 1,
      xref: "x",
      yref: "paper",
      line: {
        color: "#7A0010",
        dash: "dot",
        width: 1.5,
      },
    });
  }

  return {
    data,
    layout: {
      title: "Team Age vs Shot Efficiency",
      margin: { t: 64, r: 24, b: 72, l: 72 },
      paper_bgcolor: "#ffffff",
      plot_bgcolor: "#ffffff",
      legend: { orientation: "h", y: 1.12 },
      shapes,
      xaxis: {
        title: "Average Team Age",
      },
      yaxis: {
        title: "Goals per Shot",
      },
    },
  };
}

function getBestAgeRow(threshold) {
  const eligibleRows = playerAgeProfileRows
    .filter((row) => row.total_shots >= Number(threshold))
    .slice()
    .sort((left, right) => {
      if (right.goals_per_shot !== left.goals_per_shot) {
        return right.goals_per_shot - left.goals_per_shot;
      }
      if (right.total_shots !== left.total_shots) {
        return right.total_shots - left.total_shots;
      }
      if (right.total_goals !== left.total_goals) {
        return right.total_goals - left.total_goals;
      }
      return left.age_int - right.age_int;
    });

  return eligibleRows[0] ?? null;
}

function buildAgeProfileFigure(threshold) {
  const rows = playerAgeProfileRows
    .slice()
    .sort((left, right) => left.age_int - right.age_int);
  const bestRow = getBestAgeRow(threshold);

  if (rows.length === 0) {
    return emptyFigure("No player age profile data available");
  }

  const data = [
    {
      type: "bar",
      name: "Total shots",
      x: rows.map((row) => row.age_int),
      y: rows.map((row) => row.total_shots),
      yaxis: "y2",
      marker: {
        color: rows.map((row) =>
          row.total_shots >= Number(threshold)
            ? "rgba(178, 34, 34, 0.35)"
            : "rgba(110, 110, 110, 0.35)",
        ),
      },
      hovertemplate: "Age band: %{x}<br>Total shots: %{y}<extra></extra>",
    },
    {
      type: "scatter",
      mode: "lines+markers",
      name: "Goals per shot",
      x: rows.map((row) => row.age_int),
      y: rows.map((row) => row.goals_per_shot),
      customdata: rows.map((row) => [row.players, row.total_goals, row.total_shots]),
      line: {
        color: "#B22222",
        width: 2,
      },
      marker: {
        size: 8,
      },
      hovertemplate:
        "Age band: %{x}<br>Goals per shot: %{y:.3f}<br>Players: %{customdata[0]}<br>Total goals: %{customdata[1]}<br>Total shots: %{customdata[2]}<extra></extra>",
    },
  ];

  if (bestRow) {
    data.push({
      type: "scatter",
      mode: "markers",
      name: "Best eligible age",
      x: [bestRow.age_int],
      y: [bestRow.goals_per_shot],
      marker: {
        color: "#7A0010",
        size: 14,
        symbol: "star",
      },
      hovertemplate:
        "Best eligible age: %{x}<br>Goals per shot: %{y:.3f}<extra></extra>",
    });
  }

  return {
    data,
    layout: {
      title: "Player Age Profile by Goals per Shot and Volume",
      margin: { t: 64, r: 72, b: 72, l: 72 },
      paper_bgcolor: "#ffffff",
      plot_bgcolor: "#ffffff",
      legend: { orientation: "h", y: 1.12 },
      xaxis: {
        title: "Age Band",
      },
      yaxis: {
        title: "Goals per Shot",
      },
      yaxis2: {
        title: "Total Shots",
        overlaying: "y",
        side: "right",
        rangemode: "tozero",
      },
    },
  };
}

function buildAgeProfileText(threshold) {
  const bestRow = getBestAgeRow(threshold);
  const storedText = buildStoredBestAgeText();

  if (!bestRow) {
    return `No age band reaches the minimum threshold of ${Number(threshold)} total shots. ${storedText}`.trim();
  }

  return `With a minimum of ${Number(threshold)} shots per age band, age ${bestRow.age_int} leads with ${bestRow.goals_per_shot.toFixed(3)} goals per shot across ${bestRow.players} players. ${storedText}`.trim();
}

function buildFigure() {
  if (selectedChart.value === "team_scatter") {
    return buildTeamScatterFigure();
  }

  return buildAgeProfileFigure(minShots.value);
}

const plotDescription = computed(() => {
  if (selectedChart.value === "team_scatter") {
    return `${buildTeamScatterNote()} ${buildOptimalAgeText()}`.trim();
  }

  return buildAgeProfileText(minShots.value);
});

const researchQuestionAnswer = computed(() => buildResearchQuestionAnswer());

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
}

function buildDownloadFilename() {
  if (selectedChart.value === "age_profile") {
    return `rq8-player-age-profile-min-shots-${minShots.value}.png`;
  }

  return `rq8-${selectedChart.value}.png`;
}

function buildCsvFilename() {
  if (selectedChart.value === "age_profile") {
    return `rq8-player-age-profile-min-shots-${minShots.value}.csv`;
  }

  return `rq8-${selectedChart.value}.csv`;
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

function buildCurrentCsvRows() {
  if (selectedChart.value === "team_scatter") {
    return teamEfficiencyRows
      .filter((row) => row.avg_age !== null && row.goals_per_shot !== null)
      .map((row) => ({
        team: row.team,
        avg_age: row.avg_age,
        goals_per_shot: row.goals_per_shot,
      }));
  }

  return playerAgeProfileRows
    .slice()
    .sort((left, right) => left.age_int - right.age_int)
    .map((row) => ({
      age_int: row.age_int,
      total_shots: row.total_shots,
      goals_per_shot: row.goals_per_shot,
    }));
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

function handleResize() {
  if (chartRef.value) {
    Plotly.Plots.resize(chartRef.value);
  }
}

watch([selectedChart, minShots], async () => {
  await renderChart();
});

onMounted(async () => {
  window.addEventListener("resize", handleResize);
  await renderChart();
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);

  if (chartRef.value) {
    Plotly.purge(chartRef.value);
  }
});
</script>
