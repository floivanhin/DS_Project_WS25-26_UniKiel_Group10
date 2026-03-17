<template>
  <div>
    <h3>Research Question 5: What is the relationship between payroll spending and league points?</h3>
    <hr />
    <div>
      <label style="margin-right:12px;">
        <input type="radio" value="budget" v-model="choice" /> budget
      </label>
      <label>
        <input type="radio" value="budget_rank" v-model="choice" /> budget_rank
      </label>
    </div>

    <div ref="plot" class="plot-container" style="margin-top:12px"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from "vue";
import Plotly from "plotly.js-dist-min";

const choice = ref("budget");
const df = ref([]);
const plot = ref(null);
const csvPath = "/data/RQ5.csv";
const budgetCol = "budget(€)";
const yColumns = ["points", "league_position"];

// simple CSV fetch + small parser (handles quoted commas)
async function loadCSV(path) {
  const res = await fetch(path);
  const text = await res.text();
  return parseCSV(text);
}

function parseCSV(text) {
  if (!text) return [];
  const rows = text.trim().split(/\r?\n/).filter(Boolean);
  if (!rows.length) return [];
  const splitLine = line => {
    const cells = [];
    let cur = "", inQuotes = false;
    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      if (ch === '"') {
        if (inQuotes && line[i+1] === '"') { cur += '"'; i++; }
        else inQuotes = !inQuotes;
      } else if (ch === "," && !inQuotes) {
        cells.push(cur); cur = "";
      } else cur += ch;
    }
    cells.push(cur);
    return cells.map(c => c.trim());
  };
  const headers = splitLine(rows[0]).map(h => h.trim());
  return rows.slice(1).map(line => {
    const cols = splitLine(line);
    const obj = {};
    headers.forEach((h,i) => {
      let val = cols[i] === undefined ? "" : cols[i].trim();
      if (val === "") { obj[h] = null; return; }
      const numericCandidate = val.replace(/,/g, "");
      const num = Number(numericCandidate);
      obj[h] = (!Number.isNaN(num) && /^[+-]?\d+(\.\d+)?$/.test(numericCandidate)) ? num : (val.replace(/^"|"$/g, ""));
    });
    return obj;
  });
}

function drawPlot() {
  if (!df.value.length || !plot.value) return;
  const xCol = choice.value === "budget" ? budgetCol : "budget_rank";
  if (!(xCol in df.value[0])) { console.warn(`${xCol} not found`); return; }

  const availableY = yColumns.filter(c => c in df.value[0]);
  const traces = availableY.map((col, idx) => ({
    x: df.value.map(r => r[xCol]),
    y: df.value.map(r => r[col]),
    mode: "markers",
    type: "scatter",
    name: col,
    text: df.value.map(r => r.club || ""),
    hovertemplate: "<b>%{text}</b><br>" + xCol + ": %{x}<br>" + col + ": %{y}<extra></extra>",
    marker: { size: 9, opacity: 0.85 },
    yaxis: idx === 0 ? "y" : "y2"
  }));

  const layout = {
    title: `${xCol} vs ${availableY.join(" / ")}`,
    xaxis: { title: xCol, type: choice.value === "budget" ? "log" : "linear" },
    yaxis: { title: availableY[0] },
    margin: { t: 40, r: 60, l: 50, b: 70 },
    legend: { orientation: "h", y: -0.2 }
  };
  if (availableY.length > 1) {
    layout.yaxis2 = { title: availableY[1], overlaying: "y", side: "right" };
  }

  Plotly.react(plot.value, traces, layout, { responsive: true });
}

onMounted(async () => {
  df.value = await loadCSV(csvPath);
  drawPlot();
  window.addEventListener("resize", () => Plotly.Plots.resize(plot.value));
});

watch(choice, () => drawPlot());
</script>

<style scoped>
.plot-container {
  width: 100%;
  height: 600px;
}
@media (max-width: 600px) {
  .plot-container { height: 400px; }
}
</style>
