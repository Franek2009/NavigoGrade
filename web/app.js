import {
  GRADE_REQUIREMENTS,
  acquisitionPercentage,
  analyzeGrade,
  averageCompetencyLevel,
  createRecord,
  futureOutlook,
  gradeRequirementsMet,
  highestGradeMet,
} from "./grading.js";

const form = document.querySelector("#grade-form");
const errorBox = document.querySelector("#form-error");
const results = document.querySelector("#results");

function integerFrom(value, emptyAsZero = false) {
  const text = value.trim();
  if (!text && emptyAsZero) return 0;
  if (!/^-?\d+$/.test(text)) throw new TypeError("Uzupełnij pola wymaganymi liczbami całkowitymi.");
  return Number(text);
}

function readForm() {
  const data = new FormData(form);
  return {
    record: createRecord(integerFrom(String(data.get("total"))), [
      integerFrom(String(data.get("level0")), true),
      integerFrom(String(data.get("level1")), true),
      integerFrom(String(data.get("level2")), true),
      integerFrom(String(data.get("level3")), true),
    ]),
    targetGrade: integerFrom(String(data.get("target"))),
  };
}

function heading(card, title) {
  card.replaceChildren();
  const element = document.createElement("h3");
  element.textContent = title;
  card.append(element);
}

function status(card, state, text) {
  const row = document.createElement("p");
  row.className = "status";
  const mark = document.createElement("span");
  mark.className = `status-mark ${state}`;
  mark.textContent = state === "success" ? "✓" : state === "failure" ? "✕" : "—";
  const label = document.createElement("span");
  label.textContent = text;
  row.append(mark, label);
  card.append(row);
}

function actions(card, items) {
  const list = document.createElement("ul");
  list.className = "action-list";
  for (const item of items) {
    const row = document.createElement("li");
    row.textContent = item;
    list.append(row);
  }
  card.append(list);
}

function competencies(count) {
  if (count === 1) return "kompetencję";
  if (![12, 13, 14].includes(count % 100) && [2, 3, 4].includes(count % 10)) return "kompetencje";
  return "kompetencji";
}

function futureAction(level, count) {
  return `${count} × przyszła kompetencja na poziomie ${level}`;
}

function planActions(plan) {
  const items = [];
  plan.futureLevels.forEach((count, level) => {
    if (count) items.push(futureAction(level, count));
  });
  for (const [source, target, count] of plan.upgrades) {
    items.push(
      source === 0
        ? `zdobądź ${count} ${competencies(count)} z poziomu 0 na poziomie co najmniej ${target}`
        : `popraw ${count} ${competencies(count)}: ${source} → ${target}`,
    );
  }
  return items;
}

function metric(label, value) {
  const item = document.createElement("div");
  item.className = "metric";
  const name = document.createElement("span");
  name.textContent = label;
  const result = document.createElement("strong");
  result.textContent = value;
  item.append(name, result);
  return item;
}

function renderCurrent(record) {
  const card = document.querySelector("#current-card");
  heading(card, "Obecnie");
  const percentage = acquisitionPercentage(record);
  const average = averageCompetencyLevel(record);
  const row = document.createElement("div");
  row.className = "metric-row";
  row.append(
    metric("Ocena", highestGradeMet(record) ?? "< 2"),
    metric("Zdobyte", `${record.acquired}/${record.evaluated}`),
    metric("Średnia", average === null ? "—" : average.toFixed(2)),
  );
  card.append(row);
  const summary = document.createElement("p");
  summary.className = "muted";
  summary.textContent = percentage === null
    ? "Brak ocenionych kompetencji."
    : `${percentage.toFixed(0)}% ocenionych kompetencji jest zdobytych.`;
  card.append(summary);
}

function renderTarget(record, targetGrade, analysis) {
  const card = document.querySelector("#target-card");
  const requirement = GRADE_REQUIREMENTS[targetGrade];
  heading(card, `Cel: ocena ${targetGrade}`);
  if (analysis.acquisitionRequirementMet === null) {
    status(card, "neutral", `Wymagane ${requirement.percentage}% — brak danych`);
  } else {
    status(
      card,
      analysis.acquisitionRequirementMet ? "success" : "failure",
      `Wymagane ${requirement.percentage}% zdobytych kompetencji`,
    );
  }
  if (requirement.averageHundredths === null) {
    status(card, "neutral", "Brak wymogu średniej dla oceny 2");
  } else {
    status(
      card,
      analysis.averageRequirementMet ? "success" : "failure",
      `Wymagana średnia ${(requirement.averageHundredths / 100).toFixed(2)}`,
    );
  }
}

function renderReach(record, targetGrade, outlook) {
  const card = document.querySelector("#reach-card");
  heading(card, "Jak osiągnąć");
  if (gradeRequirementsMet(targetGrade, record)) {
    status(card, "success", `Spełniasz wymagania na ocenę ${targetGrade}.`);
  } else if (!outlook.targetPlan) {
    status(card, "failure", "Ta ocena nie jest osiągalna w podanym układzie.");
  } else {
    actions(card, planActions(outlook.targetPlan));
  }
}

function renderMaintain(record, outlook) {
  const card = document.querySelector("#maintain-card");
  heading(card, "Jak utrzymać");
  if (!outlook.targetCurrentlyMet) {
    status(card, "neutral", "Dostępne po osiągnięciu celu.");
  } else if (record.remainingFuture === 0) {
    status(card, "success", "Nie pozostały żadne przyszłe kompetencje.");
  } else if (!outlook.targetPlan) {
    status(card, "failure", "Brak możliwego planu utrzymania oceny.");
  } else {
    const intro = document.createElement("p");
    intro.className = "muted";
    intro.textContent = `Z pozostałych ${record.remainingFuture} kompetencji wystarczy:`;
    card.append(intro);
    actions(
      card,
      outlook.targetPlan.futureLevels.flatMap((count, level) =>
        count ? [`${count} × poziom ${level}`] : []),
    );
  }
}

function renderNext(outlook) {
  const card = document.querySelector("#next-card");
  heading(card, "Do następnej oceny");
  if (outlook.nextGrade === null) {
    status(card, "success", "To najwyższa dostępna ocena.");
    return;
  }
  if (!outlook.nextGradePlan) {
    status(card, "failure", `Ocena ${outlook.nextGrade} nie jest osiągalna.`);
    return;
  }
  const intro = document.createElement("p");
  const grade = document.createElement("strong");
  grade.textContent = `Ocena ${outlook.nextGrade}`;
  intro.append(grade);
  card.append(intro);
  const distance = [];
  if (outlook.nextGradeAnalysis.additionalAcquiredNeeded) {
    distance.push(`Obecnie brakuje ${outlook.nextGradeAnalysis.additionalAcquiredNeeded} zdobytych kompetencji.`);
  }
  if (outlook.nextGradeAnalysis.missingLevelPoints) {
    distance.push(`Obecnie brakuje ${outlook.nextGradeAnalysis.missingLevelPoints} punktów poziomu.`);
  }
  for (const text of distance) {
    const paragraph = document.createElement("p");
    paragraph.className = "muted";
    paragraph.textContent = text;
    card.append(paragraph);
  }
  actions(card, planActions(outlook.nextGradePlan));
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  errorBox.hidden = true;
  try {
    const { record, targetGrade } = readForm();
    const analysis = analyzeGrade(targetGrade, record);
    const outlook = futureOutlook(targetGrade, record);
    renderCurrent(record);
    renderTarget(record, targetGrade, analysis);
    renderReach(record, targetGrade, outlook);
    renderMaintain(record, outlook);
    renderNext(outlook);
    results.hidden = false;
    results.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    results.hidden = true;
    errorBox.textContent = error.message;
    errorBox.hidden = false;
  }
});

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => navigator.serviceWorker.register("./sw.js"));
}
