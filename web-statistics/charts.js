const COLORS = {
  red: "#d20515",
  redDark: "#980211",
  redSoft: "rgba(210, 5, 21, 0.2)",
  neutral: "#575757",
  neutralSoft: "rgba(80, 80, 80, 0.25)",
  border: "#d9d9d9",
};

const GENERAL_TEAM_AGE_LABELS = [
  "RB Leipzig",
  "VfB Stuttgart",
  "Eintracht Frankfurt",
  "VfL Wolfsburg",
  "Borussia Dortmund",
  "Bayer Leverkusen",
  "TSG Hoffenheim",
  "Bayern Munich",
  "Borussia Monchengladbach",
  "St. Pauli",
  "FC Augsburg",
  "Werder Bremen",
  "Holstein Kiel",
  "SC Freiburg",
  "Mainz",
  "VfL Bochum",
  "1. FC Heidenheim 1846",
  "1. FC Union Berlin",
];

const GENERAL_TEAM_AGE_VALUES = [
  24.25, 24.94, 25.05, 25.17, 25.17, 25.42, 25.52, 25.75, 25.84, 26.03, 26.07,
  26.07, 26.53, 26.79, 27.41, 27.46, 27.53, 27.86,
];

const RQ4_ABS_LABELS = [
  "Lucas Hoeler",
  "Nico Schlotterbeck",
  "Felix Nmecha",
  "Timo Horn",
  "Pascal Gross",
  "Exequiel Palacios",
  "Keven Schlotterbeck",
  "Moritz Nicolas",
  "Florian Wirtz",
  "Benjamin Sesko",
];

const RQ4_ABS_HOME = [7.234, 7.252, 7.146, 5.973, 7.123, 6.969, 7.052, 7.271, 7.795, 7.208];
const RQ4_ABS_AWAY = [6.449, 6.479, 6.389, 6.708, 6.431, 6.304, 6.404, 6.636, 7.181, 6.614];

const RQ4_EXT_LABELS = [
  "Lucas Hoeler",
  "Nico Schlotterbeck",
  "Felix Nmecha",
  "Pascal Gross",
  "Exequiel Palacios",
  "Keven Schlotterbeck",
  "Timo Horn",
  "Jakov Medic",
  "Nathan Ngoumou",
  "Felix Agu",
  "Kamil Grabara",
  "Sebastiaan Bornauw",
];

const RQ4_EXT_DELTA = [0.785, 0.773, 0.757, 0.691, 0.665, 0.648, -0.735, -0.591, -0.588, -0.58, -0.574, -0.571];

const RQ4_MEAN_VALUES = [6.614, 6.578];

const RQ9_SCATTER = [
  { x: 24.251, y: 0.13, team: "RB Leipzig" },
  { x: 24.943, y: 0.136, team: "VfB Stuttgart" },
  { x: 25.048, y: 0.14, team: "Eintracht Frankfurt" },
  { x: 25.168, y: 0.128, team: "VfL Wolfsburg" },
  { x: 25.172, y: 0.147, team: "Borussia Dortmund" },
  { x: 25.419, y: 0.143, team: "Bayer Leverkusen" },
  { x: 25.516, y: 0.104, team: "TSG Hoffenheim" },
  { x: 25.752, y: 0.153, team: "Bayern Munich" },
  { x: 25.845, y: 0.132, team: "Borussia Monchengladbach" },
  { x: 26.033, y: 0.074, team: "St. Pauli" },
  { x: 26.067, y: 0.088, team: "FC Augsburg" },
  { x: 26.07, y: 0.126, team: "Werder Bremen" },
  { x: 26.529, y: 0.131, team: "Holstein Kiel" },
  { x: 26.786, y: 0.12, team: "SC Freiburg" },
  { x: 27.409, y: 0.131, team: "Mainz" },
  { x: 27.461, y: 0.076, team: "VfL Bochum" },
  { x: 27.525, y: 0.092, team: "1. FC Heidenheim 1846" },
  { x: 27.86, y: 0.084, team: "1. FC Union Berlin" },
];

const RQ9_TREND = [
  { x: 24.251, y: 0.144 },
  { x: 27.86, y: 0.093 },
];

const RQ9_RANK_LABELS = [
  "Bayern Munich",
  "Borussia Dortmund",
  "Bayer Leverkusen",
  "Eintracht Frankfurt",
  "VfB Stuttgart",
  "Borussia Monchengladbach",
  "Holstein Kiel",
  "Mainz",
  "RB Leipzig",
  "VfL Wolfsburg",
  "Werder Bremen",
  "SC Freiburg",
  "TSG Hoffenheim",
  "1. FC Heidenheim 1846",
  "FC Augsburg",
  "1. FC Union Berlin",
  "VfL Bochum",
  "St. Pauli",
];

const RQ9_RANK_VALUES = [
  0.153, 0.147, 0.143, 0.14, 0.136, 0.132, 0.131, 0.131, 0.13, 0.128, 0.126,
  0.12, 0.104, 0.092, 0.088, 0.084, 0.076, 0.074,
];

const RQ9_AGE_LABELS = [18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 38, 39];
const RQ9_AGE_EFF = [0.0, 0.017, 0.123, 0.133, 0.131, 0.15, 0.092, 0.115, 0.118, 0.114, 0.092, 0.147, 0.089, 0.096, 0.147, 0.175, 0.105, 0.091, 0.062, 0.0, 0.0];
const RQ9_AGE_SHOTS = [1, 58, 212, 173, 427, 745, 500, 762, 651, 929, 628, 849, 540, 522, 468, 177, 133, 22, 32, 10, 5];

function initMenu() {
  const menuButton = document.querySelector(".menu-toggle");
  const nav = document.querySelector(".top-nav");

  if (!menuButton || !nav) return;

  menuButton.addEventListener("click", () => {
    nav.classList.toggle("open");
    menuButton.setAttribute("aria-expanded", nav.classList.contains("open") ? "true" : "false");
  });
}

function buildAxisGrid() {
  return { color: "#ececec" };
}

function renderOverviewCharts() {
  const chartNode = document.getElementById("teamAgeChart");
  if (!chartNode || typeof Chart === "undefined") return;

  new Chart(chartNode, {
    type: "bar",
    data: {
      labels: GENERAL_TEAM_AGE_LABELS,
      datasets: [
        {
          label: "Average age",
          data: GENERAL_TEAM_AGE_VALUES,
          borderColor: COLORS.redDark,
          backgroundColor: COLORS.redSoft,
          borderWidth: 1.5,
          borderRadius: 6,
        },
      ],
    },
    options: {
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label(context) {
              return `Age: ${context.raw.toFixed(2)}`;
            },
          },
        },
      },
      scales: {
        x: {
          ticks: {
            maxRotation: 55,
            minRotation: 55,
          },
          grid: { display: false },
        },
        y: {
          title: { display: true, text: "Years" },
          grid: buildAxisGrid(),
        },
      },
    },
  });
}

function renderRq4Charts() {
  if (typeof Chart === "undefined") return;

  const compareNode = document.getElementById("rq4CompareChart");
  if (compareNode) {
    new Chart(compareNode, {
      type: "bar",
      data: {
        labels: RQ4_ABS_LABELS,
        datasets: [
          {
            label: "Home avg rating",
            data: RQ4_ABS_HOME,
            backgroundColor: "rgba(210, 5, 21, 0.72)",
            borderColor: COLORS.redDark,
            borderWidth: 1,
            borderRadius: 6,
          },
          {
            label: "Away avg rating",
            data: RQ4_ABS_AWAY,
            backgroundColor: "rgba(73, 73, 73, 0.62)",
            borderColor: "#333",
            borderWidth: 1,
            borderRadius: 6,
          },
        ],
      },
      options: {
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "top" },
        },
        scales: {
          x: {
            ticks: {
              maxRotation: 55,
              minRotation: 55,
            },
            grid: { display: false },
          },
          y: {
            title: { display: true, text: "Rating" },
            grid: buildAxisGrid(),
          },
        },
      },
    });
  }

  const meanNode = document.getElementById("rq4MeanChart");
  if (meanNode) {
    new Chart(meanNode, {
      type: "bar",
      data: {
        labels: ["Home", "Away"],
        datasets: [
          {
            data: RQ4_MEAN_VALUES,
            backgroundColor: ["rgba(210, 5, 21, 0.76)", "rgba(80, 80, 80, 0.62)"],
            borderColor: [COLORS.redDark, "#353535"],
            borderWidth: 1,
            borderRadius: 8,
          },
        ],
      },
      options: {
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label(context) {
                return `Mean: ${context.raw.toFixed(3)}`;
              },
            },
          },
        },
        scales: {
          y: {
            min: 6.45,
            max: 6.68,
            grid: buildAxisGrid(),
          },
          x: {
            grid: { display: false },
          },
        },
      },
    });
  }

  const deltaNode = document.getElementById("rq4DeltaChart");
  if (deltaNode) {
    new Chart(deltaNode, {
      type: "bar",
      data: {
        labels: RQ4_EXT_LABELS,
        datasets: [
          {
            label: "Delta (home minus away)",
            data: RQ4_EXT_DELTA,
            borderWidth: 1,
            borderColor: RQ4_EXT_DELTA.map((value) => (value >= 0 ? COLORS.redDark : "#3f3f3f")),
            backgroundColor: RQ4_EXT_DELTA.map((value) => (value >= 0 ? "rgba(210, 5, 21, 0.68)" : "rgba(66, 66, 66, 0.68)")),
            borderRadius: 6,
          },
        ],
      },
      options: {
        maintainAspectRatio: false,
        indexAxis: "y",
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label(context) {
                return `Delta: ${context.raw.toFixed(3)}`;
              },
            },
          },
        },
        scales: {
          x: {
            title: { display: true, text: "Home minus Away" },
            grid: buildAxisGrid(),
          },
          y: {
            grid: { display: false },
          },
        },
      },
    });
  }
}

function renderRq9Charts() {
  if (typeof Chart === "undefined") return;

  const scatterNode = document.getElementById("rq9ScatterChart");
  if (scatterNode) {
    new Chart(scatterNode, {
      type: "scatter",
      data: {
        datasets: [
          {
            label: "Teams",
            data: RQ9_SCATTER,
            backgroundColor: "rgba(210, 5, 21, 0.82)",
            borderColor: COLORS.redDark,
            pointRadius: 5.5,
            pointHoverRadius: 7,
          },
          {
            type: "line",
            label: "Trend line",
            data: RQ9_TREND,
            borderColor: "#444",
            borderWidth: 2,
            borderDash: [6, 5],
            pointRadius: 0,
            tension: 0,
          },
        ],
      },
      options: {
        maintainAspectRatio: false,
        parsing: false,
        plugins: {
          tooltip: {
            callbacks: {
              label(context) {
                const point = context.raw;
                const team = point.team ? `${point.team}: ` : "";
                return `${team}Age ${point.x.toFixed(2)}, Efficiency ${point.y.toFixed(3)}`;
              },
            },
          },
        },
        scales: {
          x: {
            title: { display: true, text: "Average team age" },
            grid: buildAxisGrid(),
          },
          y: {
            title: { display: true, text: "goals_per_shot" },
            grid: buildAxisGrid(),
          },
        },
      },
    });
  }

  const rankingNode = document.getElementById("rq9RankingChart");
  if (rankingNode) {
    new Chart(rankingNode, {
      type: "bar",
      data: {
        labels: RQ9_RANK_LABELS,
        datasets: [
          {
            label: "goals_per_shot",
            data: RQ9_RANK_VALUES,
            backgroundColor: RQ9_RANK_VALUES.map((_, index) =>
              index < 5 ? "rgba(210, 5, 21, 0.85)" : "rgba(85, 85, 85, 0.65)"
            ),
            borderColor: RQ9_RANK_VALUES.map((_, index) => (index < 5 ? COLORS.redDark : "#3e3e3e")),
            borderWidth: 1,
            borderRadius: 6,
          },
        ],
      },
      options: {
        maintainAspectRatio: false,
        indexAxis: "y",
        plugins: {
          legend: { display: false },
        },
        scales: {
          x: {
            title: { display: true, text: "goals_per_shot" },
            grid: buildAxisGrid(),
          },
          y: {
            ticks: {
              font: { size: 10 },
            },
            grid: { display: false },
          },
        },
      },
    });
  }

  const ageProfileNode = document.getElementById("rq9AgeProfileChart");
  if (ageProfileNode) {
    new Chart(ageProfileNode, {
      data: {
        labels: RQ9_AGE_LABELS,
        datasets: [
          {
            type: "bar",
            label: "Total shots",
            data: RQ9_AGE_SHOTS,
            yAxisID: "yShots",
            backgroundColor: "rgba(110, 110, 110, 0.45)",
            borderColor: "#5f5f5f",
            borderWidth: 1,
            borderRadius: 5,
          },
          {
            type: "line",
            label: "goals_per_shot",
            data: RQ9_AGE_EFF,
            yAxisID: "yEff",
            borderColor: COLORS.redDark,
            backgroundColor: "rgba(210, 5, 21, 0.2)",
            pointBackgroundColor: COLORS.red,
            pointBorderColor: COLORS.redDark,
            pointRadius: 4,
            tension: 0.25,
          },
        ],
      },
      options: {
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "top",
          },
        },
        scales: {
          x: {
            title: { display: true, text: "Age band" },
            grid: { display: false },
          },
          yEff: {
            type: "linear",
            position: "left",
            min: 0,
            title: { display: true, text: "goals_per_shot" },
            grid: buildAxisGrid(),
          },
          yShots: {
            type: "linear",
            position: "right",
            title: { display: true, text: "total_shots" },
            grid: { drawOnChartArea: false },
          },
        },
      },
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initMenu();

  const page = document.body.dataset.page;
  if (page === "overview") renderOverviewCharts();
  if (page === "rq4") renderRq4Charts();
  if (page === "rq9") renderRq9Charts();
});
