// Behavioral port of navigator_grade/calculator.py. Keep rule and ranking changes
// synchronized with the Python reference implementation.

export const GRADE_REQUIREMENTS = Object.freeze({
  2: Object.freeze({ percentage: 55, averageHundredths: null }),
  3: Object.freeze({ percentage: 60, averageHundredths: 165 }),
  4: Object.freeze({ percentage: 75, averageHundredths: 195 }),
  5: Object.freeze({ percentage: 80, averageHundredths: 225 }),
  6: Object.freeze({ percentage: 90, averageHundredths: 270 }),
});

export function createRecord(totalOverall, levelCounts) {
  const values = [totalOverall, ...levelCounts];
  if (levelCounts.length !== 4 || values.some((value) => !Number.isInteger(value))) {
    throw new TypeError("Wszystkie wartości muszą być liczbami całkowitymi.");
  }
  if (values.some((value) => value < 0)) {
    throw new RangeError("Liczby kompetencji nie mogą być ujemne.");
  }
  const evaluated = levelCounts.reduce((sum, value) => sum + value, 0);
  if (evaluated > totalOverall) {
    throw new RangeError("Liczba ocenionych kompetencji nie może przekraczać wszystkich.");
  }
  return Object.freeze({
    totalOverall,
    levelCounts: Object.freeze([...levelCounts]),
    evaluated,
    acquired: levelCounts[1] + levelCounts[2] + levelCounts[3],
    remainingFuture: totalOverall - evaluated,
    levelSum: levelCounts.reduce((sum, count, level) => sum + level * count, 0),
  });
}

function requirementFor(targetGrade) {
  const requirement = GRADE_REQUIREMENTS[targetGrade];
  if (!Number.isInteger(targetGrade) || !requirement) {
    throw new RangeError("Ocena docelowa musi mieścić się w zakresie 2–6.");
  }
  return requirement;
}

function requiredAcquired(requirement, evaluated) {
  return Math.ceil((requirement.percentage * evaluated) / 100);
}

function requiredLevelSum(requirement, evaluated) {
  return requirement.averageHundredths === null
    ? 0
    : Math.ceil((requirement.averageHundredths * evaluated) / 100);
}

function stateMeets(state, requirement) {
  const evaluated = state.reduce((sum, value) => sum + value, 0);
  if (evaluated === 0) return false;
  const acquired = state[1] + state[2] + state[3];
  if (acquired < requiredAcquired(requirement, evaluated)) return false;
  if (requirement.averageHundredths === null) return true;
  const levelSum = state.reduce((sum, count, level) => sum + level * count, 0);
  return levelSum >= requiredLevelSum(requirement, evaluated);
}

export function acquisitionPercentage(record) {
  return record.evaluated === 0 ? null : (record.acquired / record.evaluated) * 100;
}

export function averageCompetencyLevel(record) {
  return record.evaluated === 0 ? null : record.levelSum / record.evaluated;
}

export function gradeRequirementsMet(targetGrade, record) {
  return stateMeets(record.levelCounts, requirementFor(targetGrade));
}

export function highestGradeMet(record) {
  for (const grade of [6, 5, 4, 3, 2]) {
    if (gradeRequirementsMet(grade, record)) return grade;
  }
  return null;
}

function stateKey(state) {
  return state.join(",");
}

function compareActions(left, right) {
  return (
    left.kind.localeCompare(right.kind) ||
    left.source - right.source ||
    left.target - right.target ||
    left.count - right.count
  );
}

function comparePlans(left, right) {
  for (let index = 0; index < Math.min(left.length, right.length); index += 1) {
    const comparison = compareActions(left[index], right[index]);
    if (comparison) return comparison;
  }
  return left.length - right.length;
}

function planKey(plan) {
  return plan.map(({ kind, source, target, count }) => `${kind}:${source}:${target}:${count}`).join("|");
}

function addAction(plan, action) {
  const actions = new Map(
    plan.map((item) => [`${item.kind}:${item.source}:${item.target}`, { ...item }]),
  );
  const key = `${action.kind}:${action.source}:${action.target}`;
  const existing = actions.get(key);
  actions.set(key, existing ? { ...existing, count: existing.count + 1 } : { ...action, count: 1 });
  return [...actions.values()].sort(compareActions);
}

function nextStates(state, totalOverall) {
  const results = [];
  for (let source = 0; source < 3; source += 1) {
    if (state[source] === 0) continue;
    for (let target = source + 1; target < 4; target += 1) {
      const changed = [...state];
      changed[source] -= 1;
      changed[target] += 1;
      results.push({ state: changed, action: { kind: "existing", source, target } });
    }
  }
  if (state.reduce((sum, value) => sum + value, 0) < totalOverall) {
    for (let target = 1; target < 4; target += 1) {
      const changed = [...state];
      changed[target] += 1;
      results.push({ state: changed, action: { kind: "future", source: -1, target } });
    }
  }
  return results;
}

function toOption(plan) {
  const upgrades = plan
    .filter((action) => action.kind === "existing")
    .map(({ source, target, count }) => [source, target, count]);
  const futureAcquisitions = plan
    .filter((action) => action.kind === "future")
    .map(({ target, count }) => [target, count]);
  const pointsGained = plan.reduce(
    (sum, action) =>
      sum + (action.kind === "existing" ? action.target - action.source : action.target) * action.count,
    0,
  );
  return {
    upgrades,
    futureAcquisitions,
    pointsGained,
    competenciesChanged: upgrades.reduce((sum, upgrade) => sum + upgrade[2], 0),
  };
}

function minimumPlans(record, requirement, limit = 3) {
  const start = [...record.levelCounts];
  if (stateMeets(start, requirement)) return [];
  let layer = new Map([[stateKey(start), { state: start, plans: new Map([["", []]]) }]]);
  const seenDepth = new Map([[stateKey(start), 0]]);
  let depth = 0;

  while (layer.size) {
    depth += 1;
    const nextLayer = new Map();
    const goals = new Map();
    for (const { state, plans } of layer.values()) {
      for (const transition of nextStates(state, record.totalOverall)) {
        const key = stateKey(transition.state);
        const previousDepth = seenDepth.get(key);
        if (previousDepth !== undefined && previousDepth < depth) continue;
        seenDepth.set(key, depth);
        if (!nextLayer.has(key)) nextLayer.set(key, { state: transition.state, plans: new Map() });
        for (const plan of plans.values()) {
          const nextPlan = addAction(plan, transition.action);
          const nextPlanKey = planKey(nextPlan);
          nextLayer.get(key).plans.set(nextPlanKey, nextPlan);
          if (stateMeets(transition.state, requirement)) {
            goals.set(`${key}/${nextPlanKey}`, { state: transition.state, plan: nextPlan });
          }
        }
      }
    }
    if (goals.size) {
      let candidates = [...goals.values()];
      const excess = ({ state }) => {
        const evaluated = state.reduce((sum, value) => sum + value, 0);
        const sum = state.reduce((total, count, level) => total + level * count, 0);
        return sum - requiredLevelSum(requirement, evaluated);
      };
      const minimumExcess = Math.min(...candidates.map(excess));
      candidates = candidates.filter((candidate) => excess(candidate) === minimumExcess);
      if (candidates.some(({ plan }) => plan.every((action) => action.kind !== "future"))) {
        candidates = candidates.filter(({ plan }) => plan.every((action) => action.kind !== "future"));
      }
      candidates.sort((left, right) => left.plan.length - right.plan.length || comparePlans(left.plan, right.plan));
      return candidates.slice(0, limit).map(({ plan }) => toOption(plan));
    }
    layer = nextLayer;
  }
  return [];
}

function* futureDistributions(count) {
  for (let level0 = 0; level0 <= count; level0 += 1) {
    for (let level1 = 0; level1 <= count - level0; level1 += 1) {
      for (let level2 = 0; level2 <= count - level0 - level1; level2 += 1) {
        yield [level0, level1, level2, count - level0 - level1 - level2];
      }
    }
  }
}

function minimumExistingPlan(current, future, requirement) {
  const finalState = (state) => state.map((value, index) => value + future[index]);
  if (stateMeets(finalState(current), requirement)) return [];
  let layer = new Map([[stateKey(current), { state: current, plans: new Map([["", []]]) }]]);
  const seenDepth = new Map([[stateKey(current), 0]]);
  let depth = 0;

  while (layer.size) {
    depth += 1;
    const nextLayer = new Map();
    const goals = [];
    for (const { state, plans } of layer.values()) {
      for (const transition of nextStates(state, current.reduce((sum, value) => sum + value, 0))) {
        if (transition.action.kind === "future") continue;
        const key = stateKey(transition.state);
        const previousDepth = seenDepth.get(key);
        if (previousDepth !== undefined && previousDepth < depth) continue;
        seenDepth.set(key, depth);
        if (!nextLayer.has(key)) nextLayer.set(key, { state: transition.state, plans: new Map() });
        for (const plan of plans.values()) {
          const nextPlan = addAction(plan, transition.action);
          nextLayer.get(key).plans.set(planKey(nextPlan), nextPlan);
          if (stateMeets(finalState(transition.state), requirement)) {
            goals.push({ state: transition.state, plan: nextPlan });
          }
        }
      }
    }
    if (goals.length) {
      const excess = ({ state }) => {
        const final = finalState(state);
        const sum = final.reduce((total, count, level) => total + level * count, 0);
        return sum - requiredLevelSum(requirement, final.reduce((total, value) => total + value, 0));
      };
      goals.sort((left, right) => excess(left) - excess(right) || comparePlans(left.plan, right.plan));
      return goals[0].plan;
    }
    layer = nextLayer;
  }
  return null;
}

function makeFuturePlan(record, future, actionPlan) {
  const option = toOption(actionPlan);
  const finalLevels = [...record.levelCounts];
  for (const [source, target, count] of option.upgrades) {
    finalLevels[source] -= count;
    finalLevels[target] += count;
  }
  for (let level = 0; level < 4; level += 1) finalLevels[level] += future[level];
  const evaluated = finalLevels.reduce((sum, value) => sum + value, 0);
  const acquired = finalLevels[1] + finalLevels[2] + finalLevels[3];
  const finalLevelSum = finalLevels.reduce((sum, count, level) => sum + level * count, 0);
  return {
    futureLevels: [...future],
    upgrades: option.upgrades,
    actionCount: future[1] + future[2] + future[3] + option.competenciesChanged,
    finalAcquisitionPercentage: (acquired / evaluated) * 100,
    finalAverageLevel: finalLevelSum / evaluated,
    finalLevelSum,
  };
}

function compareUpgradeLists(left, right) {
  return JSON.stringify(left).localeCompare(JSON.stringify(right));
}

function reachPlan(record, targetGrade) {
  const requirement = requirementFor(targetGrade);
  const candidates = [];
  for (const future of futureDistributions(record.remainingFuture)) {
    const existingPlan = minimumExistingPlan(record.levelCounts, future, requirement);
    if (existingPlan !== null) candidates.push(makeFuturePlan(record, future, existingPlan));
  }
  if (!candidates.length) return null;
  const requiredSum = requiredLevelSum(requirement, record.totalOverall);
  candidates.sort((left, right) =>
    left.actionCount - right.actionCount ||
    left.finalLevelSum - requiredSum - (right.finalLevelSum - requiredSum) ||
    left.upgrades.length + left.futureLevels.filter(Boolean).length -
      (right.upgrades.length + right.futureLevels.filter(Boolean).length) ||
    left.futureLevels[3] - right.futureLevels[3] ||
    left.futureLevels[2] - right.futureLevels[2] ||
    left.futureLevels[1] - right.futureLevels[1] ||
    compareUpgradeLists(left.upgrades, right.upgrades),
  );
  return candidates[0];
}

function maintenancePlan(record, targetGrade) {
  const requirement = requirementFor(targetGrade);
  const candidates = [];
  for (const future of futureDistributions(record.remainingFuture)) {
    const final = record.levelCounts.map((value, index) => value + future[index]);
    if (stateMeets(final, requirement)) candidates.push(makeFuturePlan(record, future, []));
  }
  candidates.sort((left, right) => {
    const burden = (plan) => plan.futureLevels.reduce((sum, count, level) => sum + level * count, 0);
    return (
      burden(left) - burden(right) ||
      left.futureLevels[3] - right.futureLevels[3] ||
      left.futureLevels[2] - right.futureLevels[2] ||
      left.futureLevels.slice(1).reduce((sum, value) => sum + value, 0) -
        right.futureLevels.slice(1).reduce((sum, value) => sum + value, 0)
    );
  });
  return candidates[0] ?? null;
}

export function analyzeGrade(targetGrade, record) {
  const requirement = requirementFor(targetGrade);
  if (record.evaluated === 0) {
    return {
      targetGrade,
      acquisitionRequirementMet: null,
      averageRequirementMet: null,
      additionalAcquiredNeeded: null,
      requiredLevelSum: null,
      missingLevelPoints: null,
      upgradeOptions: minimumPlans(record, requirement),
    };
  }
  const requiredCount = requiredAcquired(requirement, record.evaluated);
  const requiredSum = requirement.averageHundredths === null
    ? null
    : requiredLevelSum(requirement, record.evaluated);
  return {
    targetGrade,
    acquisitionRequirementMet: record.acquired >= requiredCount,
    averageRequirementMet: requiredSum === null ? null : record.levelSum >= requiredSum,
    additionalAcquiredNeeded: Math.max(0, requiredCount - record.acquired),
    requiredLevelSum: requiredSum,
    missingLevelPoints: requiredSum === null ? null : Math.max(0, requiredSum - record.levelSum),
    upgradeOptions: minimumPlans(record, requirement),
  };
}

export function futureOutlook(targetGrade, record) {
  requirementFor(targetGrade);
  const targetCurrentlyMet = gradeRequirementsMet(targetGrade, record);
  const nextGrade = targetGrade < 6 ? targetGrade + 1 : null;
  return {
    targetGrade,
    targetCurrentlyMet,
    targetPlan: targetCurrentlyMet
      ? maintenancePlan(record, targetGrade)
      : reachPlan(record, targetGrade),
    nextGrade,
    nextGradeAnalysis: nextGrade === null ? null : analyzeGrade(nextGrade, record),
    nextGradePlan: nextGrade === null ? null : reachPlan(record, nextGrade),
  };
}
