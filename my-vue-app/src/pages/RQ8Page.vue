<template>
  <div class="rq8-page">
    <section class="rq8-hero">
      <h1 class="rq8-page-title">
        Is there an ideal age for strong shooting efficiency?
      </h1>
      <p class="rq8-page-subtitle">{{ researchQuestionAnswer }}</p>
    </section>

    <section class="rq8-controls">
      <div class="rq8-control-block">
        <span class="rq8-control-label">Chart view</span>

        <div class="rq8-radio-group">
          <label class="rq8-radio-option">
            <input v-model="selectedChart" type="radio" value="team_scatter" />
            <span>Team scatter</span>
          </label>

          <label class="rq8-radio-option">
            <input v-model="selectedChart" type="radio" value="age_profile" />
            <span>Age profile</span>
          </label>
        </div>
      </div>

      <div v-if="selectedChart === 'age_profile'" class="rq8-control-block">
        <label class="rq8-control-label" for="rq8MinShots">
          Minimum shots per age band
        </label>
        <input
          id="rq8MinShots"
          v-model.number="minShots"
          class="rq8-range-control"
          type="range"
          min="50"
          max="800"
          step="10"
        />
        <div class="rq8-range-meta">{{ minShots }} shots</div>
      </div>
    </section>

    <section class="rq8-description">{{ plotDescription }}</section>

    <section class="rq8-chart-card">
      <div ref="chartRef" class="rq8-chart"></div>
    </section>

    <p v-if="selectedChart === 'team_scatter'" class="rq8-helper-text rq8-chart-note">
      The dashed line is just the overall trend across all teams, so it shows if
      efficiency generally goes up or down with team age.
    </p>

    <p v-if="selectedChart === 'age_profile'" class="rq8-helper-text rq8-chart-note">
      This chart groups players by age. The shot cutoff is there so one small age
      group with very few shots does not look more important than it is.
    </p>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import Plotly from "plotly.js-dist-min";
import teamEfficiencyCsv from "../../data/rq8/rq8_team_age_vs_efficiency.csv?raw";
import optimalAgeCsv from "../../data/rq8/rq8_optimal_age_summary.csv?raw";
import playerAgeProfileCsv from "../../data/rq8/rq8_player_age_profile.csv?raw";
import playerBestAgeCsv from "../../data/rq8/rq8_player_best_age.csv?raw";

// load the rq8 csv files
// reactive ui state
const chartRef = ref(null);
const selectedChart = ref("team_scatter");

// simple csv parser for these files
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

// wait so plotly sees the chart size
const waitForFrame = () =>
  new Promise((resolve) => {
    requestAnimationFrame(() => resolve());
  });

// keep only valid team rows
const teamRows = parseCsv(teamEfficiencyCsv)
  .map((row) => ({
    team: row.team,
    avgAge: num(row.avg_age),
    goalsPerShot: num(row.goals_per_shot),
  }))
  .filter((row) => row.team && row.avgAge !== null && row.goalsPerShot !== null);

// use the first summary row
const optimalRow =
  parseCsv(optimalAgeCsv)
    .map((row) => ({
      teams: num(row.n_teams),
      pearson: num(row.pearson_r_age_efficiency),
      peakAge: num(row.estimated_peak_age),
      peakRate: num(row.estimated_peak_goals_per_shot),
    }))[0] ?? null;

// player ages are already grouped
const ageRows = parseCsv(playerAgeProfileCsv)
  .map((row) => ({
    age: num(row.age_int),
    players: num(row.players),
    goals: num(row.total_goals),
    shots: num(row.total_shots),
    goalsPerShot: num(row.goals_per_shot),
  }))
  .filter(
    (row) =>
      row.age !== null &&
      row.players !== null &&
      row.goals !== null &&
      row.shots !== null &&
      row.goalsPerShot !== null,
  )
  .sort((a, b) => a.age - b.age);

// saved best age from the csv
const storedBest =
  parseCsv(playerBestAgeCsv)
    .map((row) => ({
      minShots: num(row.min_total_shots),
      age: num(row.best_age_int),
      goalsPerShot: num(row.goals_per_shot),
      shots: num(row.total_shots),
      players: num(row.players),
    }))[0] ?? null;

const minShots = ref(storedBest?.minShots ?? 80);

function getTrend(rows) {
  // calculate a simple trend line
  if (rows.length < 2) {
    return null;
  }

  let sumX = 0;
  let sumY = 0;
  let sumXY = 0;
  let sumX2 = 0;

  for (const row of rows) {
    sumX += row.avgAge;
    sumY += row.goalsPerShot;
    sumXY += row.avgAge * row.goalsPerShot;
    sumX2 += row.avgAge * row.avgAge;
  }

  const divider = rows.length * sumX2 - sumX * sumX;
  if (!divider) {
    return null;
  }

  const slope = (rows.length * sumXY - sumX * sumY) / divider;
  const intercept = (sumY - slope * sumX) / rows.length;
  return { slope, intercept };
}

function getBestAge(threshold) {
  // get the best age above the shot limit
  const eligible = ageRows
    .filter((row) => row.shots >= Number(threshold))
    .slice()
    .sort((a, b) => {
      if (b.goalsPerShot !== a.goalsPerShot) {
        return b.goalsPerShot - a.goalsPerShot;
      }
      if (b.shots !== a.shots) {
        return b.shots - a.shots;
      }
      return a.age - b.age;
    });

  return eligible[0] ?? null;
}

// summary values for the page text
const averageTeamAge = average(teamRows.map((row) => row.avgAge));
const averageTeamRate = average(teamRows.map((row) => row.goalsPerShot));

// short answer for the title
const researchQuestionAnswer = (() => {
  const parts = [];

  // team summary text
  if (optimalRow?.pearson !== null) {
    if (optimalRow.pearson < 0) {
      parts.push(
        `There is no clear best average team age here. Older teams trend a bit lower in goals per shot (r = ${optimalRow.pearson.toFixed(3)}).`,
      );
    } else {
      parts.push(
        `There is no clear best average team age here. Older teams trend a bit higher in goals per shot (r = ${optimalRow.pearson.toFixed(3)}).`,
      );
    }
  }

  // player age summary text
  if (
    storedBest?.age !== null &&
    storedBest?.goalsPerShot !== null &&
    storedBest?.minShots !== null
  ) {
    parts.push(
      `In the player summary table, age ${storedBest.age} is best at the ${storedBest.minShots}-shot cutoff with ${storedBest.goalsPerShot.toFixed(3)} goals per shot.`,
    );
  }

  return parts.join(" ") || "Not enough usable RQ8 data was found.";
})();

const plotDescription = computed(() => {
  // text shown under the controls
  if (selectedChart.value === "team_scatter") {
    return `Each dot is a team. The dashed line shows the overall trend. Teams average ${averageTeamAge.toFixed(2)} years and ${averageTeamRate.toFixed(3)} goals per shot.`;
  }

  const best = getBestAge(minShots.value);
  if (!best) {
    return `No age band has at least ${minShots.value} shots.`;
  }

  return `With at least ${minShots.value} shots, age ${best.age} has the best rate at ${best.goalsPerShot.toFixed(3)} goals per shot.`;
});

function buildTeamScatterFigure() {
  // get the age range for the line
  const minAge = Math.min(...teamRows.map((row) => row.avgAge));
  const maxAge = Math.max(...teamRows.map((row) => row.avgAge));
  const trend = getTrend(teamRows);
  const data = [
    {
      type: "scatter",
      mode: "markers",
      name: "Teams",
      x: teamRows.map((row) => row.avgAge),
      y: teamRows.map((row) => row.goalsPerShot),
      text: teamRows.map((row) => row.team),
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
    // add the trend line
    data.push({
      type: "scatter",
      mode: "lines",
      name: "Trend line",
      x: [minAge, maxAge],
      y: [trend.slope * minAge + trend.intercept, trend.slope * maxAge + trend.intercept],
      line: {
        color: "#444444",
        dash: "dash",
      },
      hoverinfo: "skip",
    });
  }

  if (
    optimalRow?.peakAge !== null &&
    optimalRow?.peakRate !== null &&
    optimalRow.peakAge >= minAge &&
    optimalRow.peakAge <= maxAge
  ) {
    // mark the estimated peak age
    data.push({
      type: "scatter",
      mode: "markers",
      name: "Estimated peak",
      x: [optimalRow.peakAge],
      y: [optimalRow.peakRate],
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
      x0: optimalRow.peakAge,
      x1: optimalRow.peakAge,
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
      title: "Team age vs shot efficiency",
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

function buildAgeProfileFigure() {
  // chart for player age groups
  const best = getBestAge(minShots.value);

  // bars show shots and line shows efficiency
  const data = [
    {
      type: "bar",
      name: "Total shots",
      x: ageRows.map((row) => row.age),
      y: ageRows.map((row) => row.shots),
      yaxis: "y2",
      marker: {
        color: ageRows.map((row) =>
          row.shots >= Number(minShots.value)
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
      x: ageRows.map((row) => row.age),
      y: ageRows.map((row) => row.goalsPerShot),
      customdata: ageRows.map((row) => [row.players, row.goals, row.shots]),
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

  if (best) {
    // mark the best age on the chart
    data.push({
      type: "scatter",
      mode: "markers",
      name: "Best eligible age",
      x: [best.age],
      y: [best.goalsPerShot],
      marker: {
        color: "#7A0010",
        size: 14,
        symbol: "star",
      },
      hovertemplate: "Best eligible age: %{x}<br>Goals per shot: %{y:.3f}<extra></extra>",
    });
  }

  return {
    data,
    layout: {
      title: "Player age profile",
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

// choose which chart to show
const figure = computed(() =>
  selectedChart.value === "team_scatter"
    ? buildTeamScatterFigure()
    : buildAgeProfileFigure(),
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
watch([selectedChart, minShots], renderChart);

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
