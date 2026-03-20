<template>
  <div class="page">
    <section class="hero">
      <h1 class="page-title">Bundesliga Statistics (Season 2024/2025)</h1>
      <p class="page-subtitle">
        This project analyzes data from the 2024-25 Bundesliga season. We
        explore patterns and relationships in football using multiple datasets
        and interactive visualizations.
      </p>
    </section>

    <section class="description-box">
      Using publicly available football and contextual datasets, we collected,
      cleaned, and merged match statistics to study how different factors
      influence match outcomes and team performance.
    </section>

    <section class="summary-grid">
      <div v-for="card in summaryCards" :key="card.label" class="summary-card">
        <span class="summary-label">{{ card.label }}</span>
        <strong class="summary-value summary-value-small">
          {{ card.value }}
        </strong>
      </div>
    </section>

    <section class="chart-card">
      <div class="section-header">
        <h2 class="section-title">How We Worked</h2>
        <span class="chart-note">
          A short overview of our project progress over four weeks.
        </span>
      </div>

      <div class="week-buttons">
        <button
          v-for="week in weeks"
          :key="week.id"
          type="button"
          class="toggle-button"
          :class="{ 'toggle-button-active': selectedWeek === week.id }"
          @click="selectedWeek = week.id"
        >
          {{ week.label }}
        </button>
      </div>

      <div class="week-card">
        <h3 class="week-title">{{ currentWeek.title }}</h3>
        <p class="week-text">{{ currentWeek.text }}</p>

        <div class="info-grid">
          <div class="info-box">
            <p class="info-box-label">Main focus</p>
            <p class="info-box-text">{{ currentWeek.focus }}</p>
          </div>

          <div class="info-box">
            <p class="info-box-label">Outcome</p>
            <p class="info-box-text">{{ currentWeek.outcome }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="chart-card">
      <h2 class="section-title">Research Questions</h2>

      <div class="table-wrapper">
        <table class="summary-table">
          <tbody>
            <tr v-for="question in researchQuestions" :key="question.path">
              <td>
                <strong>{{ question.label }}</strong>
              </td>
              <td>
                <RouterLink :to="question.path" class="brand-text">
                  {{ question.title }}
                </RouterLink>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="chart-card">
      <h2 class="section-title">Data & Sources</h2>
      <p class="chart-note">
        The analysis is based on a combination of publicly available data from
        multiple sources, including football statistics platforms, financial and
        performance databases, and external contextual data such as weather
        conditions.
      </p>
      <p class="chart-note">
        Match and team performance data were collected from sources like
        WhoScored, Understat, ESPN, and football-data.org, while additional
        contextual information was obtained via APIs such as API-Football and
        Visual Crossing (weather data). Financial and squad-related data were
        complemented using Capology.
      </p>
      <p class="chart-note">
        All datasets were preprocessed, cleaned, and merged to ensure
        consistency and comparability before being used in the visualizations
        presented in this project.
      </p>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";

type Week = {
  id: number;
  label: string;
  title: string;
  text: string;
  focus: string;
  outcome: string;
};

const summaryCards = [
  { label: "League", value: "Bundesliga 2024/25" },
  { label: "Focus", value: "Match patterns & performance" },
  { label: "Approach", value: "Data analysis + visualization" },
  { label: "Output", value: "Interactive dashboards" },
] as const;

const researchQuestions = [
  {
    label: "RQ1",
    path: "/rq1",
    title: "How do weather conditions influence total goals scored?",
  },
  {
    label: "RQ2",
    path: "/rq2",
    title: "How does the matchday affect the amount of goals?",
  },
  {
    label: "RQ3",
    path: "/rq3",
    title: "How does transition time correlate with goal probability?",
  },
  {
    label: "RQ4",
    path: "/rq4",
    title:
      "Which players perform particularly well in home matches and which in away matches?",
  },
  {
    label: "RQ5",
    path: "/rq5",
    title:
      "What is the relationship between payroll spending and league points?",
  },
  {
    label: "RQ6",
    path: "/rq6",
    title:
      "What is the relationship between arena capacity and the number of cards issued?",
  },
  {
    label: "RQ7",
    path: "/rq7",
    title:
      "How do substitutions affect the number of shots on goal in the second half?",
  },
  {
    label: "RQ8",
    path: "/rq8",
    title: "How does the average player age affect a team's efficiency?",
  },
] as const;

const weeks: Week[] = [
  {
    id: 1,
    label: "Week 1",
    title: "Week 1 - Topic selection and first planning",
    text: "In the first week, we explored several possible project topics, including movies, train services, and football. After discussing the available options, we gradually focused on football as the most promising topic for our project. During this phase, we also started defining possible research questions, discussed how to organize our work as a team, and attended university sessions that supported the project process.",
    focus:
      "Comparing possible topics, forming the team workflow, and drafting first research questions.",
    outcome:
      "We narrowed our project direction and built the initial foundation for the following weeks.",
  },
  {
    id: 2,
    label: "Week 2",
    title: "Week 2 - Final topic choice and feasibility check",
    text: "In the second week, we made the final decision to work on football data. After choosing the topic, we began checking whether the APIs and public data sources could actually provide the information needed to answer our questions. At the same time, we refined and improved our research questions so that they better matched the data that was realistically available.",
    focus:
      "Validating data availability and aligning research questions with accessible sources.",
    outcome:
      "We confirmed that football was a feasible topic and adjusted our questions to fit the available data.",
  },
  {
    id: 3,
    label: "Week 3",
    title: "Week 3 - API requests and data combination",
    text: "In the third week, we started building API requests and testing how the data was returned. The results came in different formats, especially CSV and JSON, so we developed scripts to process, clean, and combine these outputs. This phase was important because it transformed raw source data into a structured basis for our analyses and visualizations.",
    focus:
      "Querying APIs, inspecting returned data, and building scripts for cleaning and merging datasets.",
    outcome:
      "We created the technical data pipeline that made the later analyses possible.",
  },
  {
    id: 4,
    label: "Week 4",
    title: "Week 4 - Website implementation and poster creation",
    text: "In the fourth week, we moved from data preparation to presentation. We started implementing the website, designing the pages for the individual research questions, and preparing the visualizations for users. In parallel, we worked on the project poster to summarize the topic, methods, and results in a compact and understandable way.",
    focus:
      "Building the website, presenting the results, and summarizing the project visually.",
    outcome:
      "We turned our analysis into an interactive web project and prepared the final presentation materials.",
  },
];

const selectedWeek = ref(1);

const currentWeek = computed(() => {
  return weeks.find((week) => week.id === selectedWeek.value) ?? weeks[0];
});
</script>
