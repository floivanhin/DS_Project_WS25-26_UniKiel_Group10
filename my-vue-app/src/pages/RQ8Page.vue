<template>
  <div class="page">
    <section class="hero">
      <p class="kicker">RQ8</p>
      <h1 class="page-title">
        How does the average player age affect a team's efficiency?
      </h1>
      <p class="page-subtitle">{{ researchQuestionAnswer }}</p>
    </section>

    <section class="controls-card">
      <div class="control-block">
        <span class="control-label">Chart view</span>

        <div class="button-group">
          <button
            type="button"
            class="toggle-button"
            :class="{
              'toggle-button-active': selectedChart === 'team_scatter',
            }"
            @click="selectedChart = 'team_scatter'"
          >
            Team scatter
          </button>

          <button
            type="button"
            class="toggle-button"
            :class="{ 'toggle-button-active': selectedChart === 'age_profile' }"
            @click="selectedChart = 'age_profile'"
          >
            Age profile
          </button>
        </div>
      </div>

      <div
        v-if="selectedChart === 'age_profile'"
        class="control-block slider-block"
      >
        <label class="control-label" for="rq8MinShots">
          Minimum shots per age band:
          <span class="accent-value">{{ minShots }}</span>
        </label>

        <input
          id="rq8MinShots"
          v-model.number="minShots"
          class="range-control"
          type="range"
          min="50"
          max="800"
          step="10"
        />

        <div class="range-meta">{{ minShots }} shots</div>
        <div class="range-hints">
          <span>50</span>
          <span>800</span>
        </div>
      </div>

      <p class="selection-summary">
        Current selection:
        <strong>
          {{
            selectedChart === "team_scatter" ? "Team scatter" : "Age profile"
          }}
        </strong>
        <span v-if="selectedChart === 'age_profile'">
          - minimum shots: <strong>{{ minShots }}</strong>
        </span>
      </p>
    </section>

    <section class="description-box">
      {{ plotDescription }}
    </section>

    <section
      v-if="!teamRows.length || !ageRows.length"
      class="status-box error-box"
    >
      One or more RQ8 datasets are empty.
    </section>

    <template v-else>
      <section class="chart-card">
        <h2 class="section-title">
          {{
            selectedChart === "team_scatter"
              ? "Team age vs shot efficiency"
              : "Player age profile"
          }}
        </h2>

        <p class="chart-note">
          {{
            selectedChart === "team_scatter"
              ? "Each point represents one team. The dashed line shows the overall trend between average team age and goals per shot."
              : "This chart combines total shots by age band with goals-per-shot efficiency. Age bands below the chosen shot threshold are visually de-emphasized."
          }}
        </p>

        <div ref="chartRef" class="chart"></div>
      </section>

      <section class="chart-card chart-card-compact">
        <p
          v-if="selectedChart === 'team_scatter'"
          class="chart-note helper-text"
        >
          The dashed line shows the broad trend across all teams. It does not
          imply a causal effect of age on efficiency.
        </p>

        <p v-else class="chart-note helper-text">
          The shot cutoff prevents very small age groups from appearing more
          important than they actually are.
        </p>
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
import teamEfficiencyCsv from "../../data/rq8/rq8_team_age_vs_efficiency.csv?raw";
import optimalAgeCsv from "../../data/rq8/rq8_optimal_age_summary.csv?raw";
import playerAgeProfileCsv from "../../data/rq8/rq8_player_age_profile.csv?raw";
import playerBestAgeCsv from "../../data/rq8/rq8_player_best_age.csv?raw";

type TeamRow = {
  team: string;
  avgAge: number;
  goalsPerShot: number;
};

type AgeRow = {
  age: number;
  players: number;
  goals: number;
  shots: number;
  goalsPerShot: number;
};

type BestAgeRow = {
  minShots: number;
  age: number;
  goalsPerShot: number;
};

type OptimalRow = {
  pearson: number;
  peakAge: number;
  peakRate: number;
};

const chartRef = ref<HTMLDivElement | null>(null);
const selectedChart = ref<"team_scatter" | "age_profile">("team_scatter");
const minShots = ref(80);

function parseCsv(text: string): Record<string, string>[] {
  const lines = text
    .replace(/^\uFEFF/, "")
    .trim()
    .split(/\r?\n/)
    .filter(Boolean);

  if (lines.length < 2) {
    return [];
  }

  const splitLine = (line: string) => {
    const values: string[] = [];
    let current = "";
    let inQuotes = false;

    for (let index = 0; index < line.length; index += 1) {
      const character = line[index];

      if (character === '"') {
        if (inQuotes && line[index + 1] === '"') {
          current += '"';
          index += 1;
        } else {
          inQuotes = !inQuotes;
        }
      } else if (character === "," && !inQuotes) {
        values.push(current);
        current = "";
      } else {
        current += character;
      }
    }

    values.push(current);
    return values;
  };

  const headers = splitLine(lines[0]).map((value) => value.trim());

  return lines.slice(1).map((line) => {
    const values = splitLine(line);
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

const teamRows: TeamRow[] = parseCsv(teamEfficiencyCsv)
  .map((row) => {
    const avgAge = toNumber(row.avg_age);
    const goalsPerShot = toNumber(row.goals_per_shot);

    if (!row.team || avgAge === null || goalsPerShot === null) {
      return null;
    }

    return {
      team: row.team,
      avgAge,
      goalsPerShot,
    };
  })
  .filter((row): row is TeamRow => row !== null);

const optimalRow: OptimalRow | null =
  parseCsv(optimalAgeCsv)
    .map((row) => {
      const pearson = toNumber(row.pearson_r_age_efficiency);
      const peakAge = toNumber(row.estimated_peak_age);
      const peakRate = toNumber(row.estimated_peak_goals_per_shot);

      if (pearson === null || peakAge === null || peakRate === null) {
        return null;
      }

      return { pearson, peakAge, peakRate };
    })
    .find((row): row is OptimalRow => row !== null) ?? null;

const ageRows: AgeRow[] = parseCsv(playerAgeProfileCsv)
  .map((row) => {
    const age = toNumber(row.age_int);
    const players = toNumber(row.players);
    const goals = toNumber(row.total_goals);
    const shots = toNumber(row.total_shots);
    const goalsPerShot = toNumber(row.goals_per_shot);

    if (
      age === null ||
      players === null ||
      goals === null ||
      shots === null ||
      goalsPerShot === null
    ) {
      return null;
    }

    return { age, players, goals, shots, goalsPerShot };
  })
  .filter((row): row is AgeRow => row !== null)
  .sort((left, right) => left.age - right.age);

const storedBest: BestAgeRow | null =
  parseCsv(playerBestAgeCsv)
    .map((row) => {
      const minimumShots = toNumber(row.min_total_shots);
      const age = toNumber(row.best_age_int);
      const goalsPerShot = toNumber(row.goals_per_shot);

      if (minimumShots === null || age === null || goalsPerShot === null) {
        return null;
      }

      return { minShots: minimumShots, age, goalsPerShot };
    })
    .find((row): row is BestAgeRow => row !== null) ?? null;

if (storedBest) {
  minShots.value = storedBest.minShots;
}

function getAverage(values: number[]): number | null {
  if (values.length === 0) {
    return null;
  }

  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function getBestAge(threshold: number) {
  return (
    ageRows
      .filter((row) => row.shots >= threshold)
      .sort((left, right) => {
        if (right.goalsPerShot !== left.goalsPerShot) {
          return right.goalsPerShot - left.goalsPerShot;
        }
        if (right.shots !== left.shots) {
          return right.shots - left.shots;
        }
        return left.age - right.age;
      })[0] ?? null
  );
}

const averageTeamAge = getAverage(teamRows.map((row) => row.avgAge));
const averageTeamRate = getAverage(teamRows.map((row) => row.goalsPerShot));

const researchQuestionAnswer = (() => {
  const parts: string[] = [];

  if (optimalRow) {
    parts.push(
      optimalRow.pearson < 0
        ? `There is no single best average team age. Older teams tend to show slightly lower goals per shot (r = ${optimalRow.pearson.toFixed(3)}).`
        : `There is no single best average team age. Older teams tend to show slightly higher goals per shot (r = ${optimalRow.pearson.toFixed(3)}).`,
    );
  }

  if (storedBest) {
    parts.push(
      `In the player-age summary, age ${storedBest.age} performs best at the ${storedBest.minShots}-shot cutoff with ${storedBest.goalsPerShot.toFixed(3)} goals per shot.`,
    );
  }

  return parts.join(" ") || "Not enough usable RQ8 data was found.";
})();

const plotDescription = computed(() => {
  if (selectedChart.value === "team_scatter") {
    if (averageTeamAge === null || averageTeamRate === null) {
      return "Not enough team rows are available for the scatter plot.";
    }

    return `Each dot represents one team. Teams average ${averageTeamAge.toFixed(2)} years and ${averageTeamRate.toFixed(3)} goals per shot overall.`;
  }

  const bestAge = getBestAge(minShots.value);
  if (!bestAge) {
    return `No age band has at least ${minShots.value} shots.`;
  }

  return `With at least ${minShots.value} shots, age ${bestAge.age} has the best rate at ${bestAge.goalsPerShot.toFixed(3)} goals per shot.`;
});

function buildTeamScatterFigure() {
  const minAge = Math.min(...teamRows.map((row) => row.avgAge));
  const maxAge = Math.max(...teamRows.map((row) => row.avgAge));
  let trend: { slope: number; intercept: number } | null = null;

  if (teamRows.length >= 2) {
    let sumX = 0;
    let sumY = 0;
    let sumXY = 0;
    let sumX2 = 0;

    for (const row of teamRows) {
      sumX += row.avgAge;
      sumY += row.goalsPerShot;
      sumXY += row.avgAge * row.goalsPerShot;
      sumX2 += row.avgAge * row.avgAge;
    }

    const denominator = teamRows.length * sumX2 - sumX * sumX;
    if (denominator !== 0) {
      const slope = (teamRows.length * sumXY - sumX * sumY) / denominator;
      const intercept = (sumY - slope * sumX) / teamRows.length;
      trend = { slope, intercept };
    }
  }

  const data: Record<string, any>[] = [
    {
      type: "scatter",
      mode: "markers",
      name: "Teams",
      x: teamRows.map((row) => row.avgAge),
      y: teamRows.map((row) => row.goalsPerShot),
      text: teamRows.map((row) => row.team),
      marker: {
        color: "#b22222",
        size: 11,
      },
      hovertemplate:
        "<b>%{text}</b><br>Average age: %{x:.2f}<br>Goals per shot: %{y:.3f}<extra></extra>",
    },
  ];

  const shapes: Record<string, any>[] = [];

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
    optimalRow.peakAge >= minAge &&
    optimalRow.peakAge <= maxAge
  ) {
    data.push({
      type: "scatter",
      mode: "markers",
      name: "Estimated peak",
      x: [optimalRow.peakAge],
      y: [optimalRow.peakRate],
      marker: {
        color: "#7a0010",
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
        color: "#7a0010",
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
        title: "Average team age",
      },
      yaxis: {
        title: "Goals per shot",
      },
    },
  };
}

function buildAgeProfileFigure() {
  const bestAge = getBestAge(minShots.value);
  const data: Record<string, any>[] = [
    {
      type: "bar",
      name: "Total shots",
      x: ageRows.map((row) => row.age),
      y: ageRows.map((row) => row.shots),
      yaxis: "y2",
      marker: {
        color: ageRows.map((row) =>
          row.shots >= minShots.value
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
        color: "#b22222",
        width: 2,
      },
      marker: {
        size: 8,
      },
      hovertemplate:
        "Age band: %{x}<br>Goals per shot: %{y:.3f}<br>Players: %{customdata[0]}<br>Total goals: %{customdata[1]}<br>Total shots: %{customdata[2]}<extra></extra>",
    },
  ];

  if (bestAge) {
    data.push({
      type: "scatter",
      mode: "markers",
      name: "Best eligible age",
      x: [bestAge.age],
      y: [bestAge.goalsPerShot],
      marker: {
        color: "#7a0010",
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
      title: "Player age profile",
      margin: { t: 64, r: 72, b: 72, l: 72 },
      paper_bgcolor: "#ffffff",
      plot_bgcolor: "#ffffff",
      legend: { orientation: "h", y: 1.12 },
      xaxis: {
        title: "Age band",
      },
      yaxis: {
        title: "Goals per shot",
      },
      yaxis2: {
        title: "Total shots",
        overlaying: "y",
        side: "right",
        rangemode: "tozero",
      },
    },
  };
}

async function renderChart() {
  if (!chartRef.value) {
    return;
  }

  await nextTick();
  await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()));

  const figure =
    selectedChart.value === "team_scatter"
      ? buildTeamScatterFigure()
      : buildAgeProfileFigure();

  await Plotly.react(chartRef.value, figure.data, figure.layout, {
    responsive: true,
    displayModeBar: false,
  });
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
