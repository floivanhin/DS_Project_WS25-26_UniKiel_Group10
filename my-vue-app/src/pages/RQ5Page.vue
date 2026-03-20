<template>
  <div class="page">
    <section class="hero">
      <h1 class="page-title">
        What is the relationship between payroll spending and league points?
      </h1>
      <p class="page-subtitle">
        This page compares club payroll spending with sporting outcomes. You can
        switch between absolute budget and budget rank to see how financial
        strength relates to points and final league position.
      </p>
    </section>

    <section class="description-box">
      The scatter plot shows whether clubs with higher payrolls also tend to
      collect more points or finish in better league positions. The budget view
      uses a logarithmic x-axis because the spending gaps are large.
    </section>

    <section class="controls-card">
      <div class="control-block">
        <span class="control-label">X-axis metric</span>

        <div class="button-group">
          <button
            type="button"
            class="toggle-button"
            :class="{ 'toggle-button-active': choice === 'budget' }"
            @click="choice = 'budget'"
          >
            Budget
          </button>

          <button
            type="button"
            class="toggle-button"
            :class="{ 'toggle-button-active': choice === 'budget_rank' }"
            @click="choice = 'budget_rank'"
          >
            Budget rank
          </button>
        </div>
      </div>

      <p class="selection-summary">
        Current selection:
        <strong>{{ choice === "budget" ? "Budget" : "Budget rank" }}</strong>
      </p>
    </section>

    <section v-if="error" class="status-box error-box">
      {{ error }}
    </section>

    <section v-else class="chart-card">
      <h2 class="section-title">
        {{
          choice === "budget"
            ? "Budget vs points and league position"
            : "Budget rank vs points and league position"
        }}
      </h2>

      <p class="chart-note">
        {{
          choice === "budget"
            ? "This chart uses the club budget as the x-axis. Budget is displayed on a logarithmic scale to make differences between clubs easier to compare."
            : "This chart uses the budget rank as the x-axis, which makes it easier to compare financial order directly with sporting performance."
        }}
      </p>

      <div ref="plotRef" class="chart"></div>
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
import rq5Csv from "../../data/RQ5.csv?raw";

type Choice = "budget" | "budget_rank";

type ClubRow = {
  club: string;
  budget: number;
  budget_rank: number;
  points: number;
  league_position: number;
};

const choice = ref<Choice>("budget");
const plotRef = ref<HTMLDivElement | null>(null);
const error = ref("");

function parseCSV(text: string): Record<string, string | number | null>[] {
  const rows = text.trim().split(/\r?\n/).filter(Boolean);
  if (rows.length < 2) {
    return [];
  }

  const splitLine = (line: string) => {
    const cells: string[] = [];
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
        cells.push(current);
        current = "";
      } else {
        current += character;
      }
    }

    cells.push(current);
    return cells.map((cell) => cell.trim());
  };

  const headers = splitLine(rows[0]);

  return rows.slice(1).map((line) => {
    const values = splitLine(line);
    const row: Record<string, string | number | null> = {};

    headers.forEach((header, index) => {
      const rawValue = values[index] ?? "";
      if (rawValue === "") {
        row[header] = null;
        return;
      }

      const numericCandidate = rawValue.replace(/,/g, "");
      const numericValue = Number(numericCandidate);
      row[header] =
        !Number.isNaN(numericValue) &&
        /^[+-]?\d+(\.\d+)?$/.test(numericCandidate)
          ? numericValue
          : rawValue.replace(/^"|"$/g, "");
    });

    return row;
  });
}

const parsedRows = parseCSV(rq5Csv);
const budgetHeader = Object.keys(parsedRows[0] ?? {}).find((header) =>
  header.toLowerCase().startsWith("budget("),
);

const rows = computed<ClubRow[]>(() => {
  if (!budgetHeader) {
    return [];
  }

  return parsedRows
    .map((row) => {
      const club = String(row.club ?? "");
      const budget = Number(row[budgetHeader]);
      const budgetRank = Number(row.budget_rank);
      const points = Number(row.points);
      const leaguePosition = Number(row.league_position);

      if (
        !club ||
        !Number.isFinite(budget) ||
        !Number.isFinite(budgetRank) ||
        !Number.isFinite(points) ||
        !Number.isFinite(leaguePosition)
      ) {
        return null;
      }

      return {
        club,
        budget,
        budget_rank: budgetRank,
        points,
        league_position: leaguePosition,
      };
    })
    .filter((row): row is ClubRow => row !== null);
});

async function waitForChartReady(): Promise<void> {
  await nextTick();
  await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()));
}

async function renderChart() {
  await waitForChartReady();

  if (!plotRef.value || rows.value.length === 0) {
    return;
  }

  const xKey = choice.value;
  const xValues = rows.value.map((row) => row[xKey]);

  await Plotly.react(
    plotRef.value,
    [
      {
        x: xValues,
        y: rows.value.map((row) => row.points),
        mode: "markers",
        type: "scatter",
        name: "Points",
        text: rows.value.map((row) => row.club),
        hovertemplate:
          "<b>%{text}</b><br>" +
          `${choice.value === "budget" ? "Budget" : "Budget rank"}: %{x}<br>` +
          "Points: %{y}<extra></extra>",
        marker: {
          size: 10,
          opacity: 0.85,
          color: "#2563eb",
        },
        yaxis: "y",
      },
      {
        x: xValues,
        y: rows.value.map((row) => row.league_position),
        mode: "markers",
        type: "scatter",
        name: "League position",
        text: rows.value.map((row) => row.club),
        hovertemplate:
          "<b>%{text}</b><br>" +
          `${choice.value === "budget" ? "Budget" : "Budget rank"}: %{x}<br>` +
          "League position: %{y}<extra></extra>",
        marker: {
          size: 10,
          opacity: 0.85,
          color: "#dc2626",
        },
        yaxis: "y2",
      },
    ],
    {
      title:
        choice.value === "budget"
          ? "Budget vs points and league position"
          : "Budget rank vs points and league position",
      xaxis: {
        title: choice.value === "budget" ? "Budget (EUR)" : "Budget rank",
        type: choice.value === "budget" ? "log" : "linear",
      },
      yaxis: {
        title: "Points",
      },
      yaxis2: {
        title: "League position",
        overlaying: "y",
        side: "right",
        autorange: "reversed",
      },
      margin: { t: 60, r: 70, l: 60, b: 70 },
      legend: { orientation: "h", y: -0.2 },
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
  if (plotRef.value) {
    Plotly.Plots.resize(plotRef.value);
  }
}

watch(choice, async () => {
  await renderChart();
});

onMounted(async () => {
  if (!budgetHeader) {
    error.value = "Budget column not found in the CSV dataset.";
    return;
  }

  if (rows.value.length === 0) {
    error.value = "No rows found in the CSV dataset.";
    return;
  }

  window.addEventListener("resize", handleResize);
  await renderChart();
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);

  if (plotRef.value) {
    Plotly.purge(plotRef.value);
  }
});
</script>
