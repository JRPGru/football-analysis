"use strict";


const CONFIG = {

  manifestFile:
    "data_sources.json",

  colors: {
    GK: "#ff8c1a",
    DF: "#ffd84d",
    MF: "#35c66f",
    FW: "#3f8cff"
  },

  inactiveColor:
    "#666d76",

  markerSize:
    5.8
};


let DATA_SOURCES = [];

let CURRENT_SOURCE = null;

let ALL_PLAYERS = [];

let FILTER_STATE = {
  positions: new Set(),
  clubs: new Set(),
  minAge: null,
  maxAge: null
};


// =============================================================================
// Helpers
// =============================================================================


function parseNumber(value) {

  const number = Number(
    String(
      value ?? ""
    )
    .trim()
    .replace(",", ".")
  );

  return Number.isFinite(number)
    ? number
    : NaN;
}


function formatNumber(
  value,
  digits = 2
) {

  return Number.isFinite(value)
    ? value.toFixed(digits)
    : "–";
}


function formatInteger(value) {

  return Number.isFinite(value)
    ? Math.round(value).toString()
    : "–";
}


function escapeHtml(value) {

  const div =
    document.createElement("div");

  div.textContent =
    String(value);

  return div.innerHTML;
}


function escapeAttribute(value) {

  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}


// =============================================================================
// Player parsing
// =============================================================================


function preparePlayers(rows) {

  return rows
    .map(
      row => ({

        player:
          String(
            row.player ?? ""
          ).trim(),

        team:
          String(
            row.team ?? ""
          ).trim(),

        position:
          String(
            row.position ?? ""
          ).trim(),

        positionGroup:
          String(
            row.position_group ?? ""
          ).trim(),

        age:
          parseNumber(
            row.age
          ),

        minutes:
          parseNumber(
            row.minutes
          ),

        pc1:
          parseNumber(
            row.PC1
          ),

        pc2:
          parseNumber(
            row.PC2
          ),

        pc3:
          parseNumber(
            row.PC3
          ),

        shootingGoalsPer90:
          parseNumber(
            row.shooting_goals_per90
          ),

        shotsPer90:
          parseNumber(
            row.shots_per90
          ),

        shotsOnTargetPer90:
          parseNumber(
            row.shots_on_target_per90
          ),

        shotsOnTargetPct:
          parseNumber(
            row.shots_on_target_pct
          ),

        goalsPerShot:
          parseNumber(
            row.goals_per_shot
          ),

        goalsPerShotOnTarget:
          parseNumber(
            row.goals_per_shot_on_target
          ),

        penaltiesScoredPer90:
          parseNumber(
            row.penalties_scored_per90
          ),

        penaltyAttemptsPer90:
          parseNumber(
            row.penalty_attempts_per90
          ),

        pointsPerMatch:
          parseNumber(
            row.points_per_match
          ),

        teamGoalsForPer90:
          parseNumber(
            row.team_goals_for_per90
          ),

        teamGoalsAgainstPer90:
          parseNumber(
            row.team_goals_against_per90
          ),

        plusMinusPer90:
          parseNumber(
            row.plus_minus_per90
          ),

        onOffPer90:
          parseNumber(
            row.on_off_per90
          ),

        yellowCardsPer90:
          parseNumber(
            row.yellow_cards_per90
          ),

        redCardsPer90:
          parseNumber(
            row.red_cards_per90
          ),

        secondYellowCardsPer90:
          parseNumber(
            row.second_yellow_cards_per90
          ),

        foulsCommittedPer90:
          parseNumber(
            row.fouls_committed_per90
          ),

        foulsDrawnPer90:
          parseNumber(
            row.fouls_drawn_per90
          ),

        offsidesPer90:
          parseNumber(
            row.offsides_per90
          ),

        crossesPer90:
          parseNumber(
            row.crosses_per90
          ),

        interceptionsPer90:
          parseNumber(
            row.interceptions_per90
          ),

        tacklesWonPer90:
          parseNumber(
            row.tackles_won_per90
          ),

        ownGoalsPer90:
          parseNumber(
            row.own_goals_per90
          ),

        observedFeatures:
          parseNumber(
            row.observed_features
          ),

        imputedFeatures:
          parseNumber(
            row.imputed_features
          )
      })
    )

    .filter(
      player =>
        player.player
        && [
          "GK",
          "DF",
          "MF",
          "FW"
        ].includes(
          player.positionGroup
        )
        && Number.isFinite(
          player.pc1
        )
        && Number.isFinite(
          player.pc2
        )
        && Number.isFinite(
          player.pc3
        )
    );
}


// =============================================================================
// League / season selectors
// =============================================================================


function getLeagues() {

  const map =
    new Map();

  for (
    const source
    of DATA_SOURCES
  ) {

    if (
      !map.has(
        source.league
      )
    ) {

      map.set(
        source.league,
        source.league_name
      );
    }
  }

  return [
    ...map.entries()
  ]
  .map(
    ([id, name]) => ({
      id,
      name
    })
  )
  .sort(
    (a, b) =>
      a.name.localeCompare(
        b.name
      )
  );
}


function getSourcesForLeague(
  league
) {

  return DATA_SOURCES
    .filter(
      source =>
        source.league === league
    )
    .sort(
      (a, b) =>
        b.season.localeCompare(
          a.season
        )
    );
}


function populateLeagueSelector() {

  const select =
    document.getElementById(
      "league-select"
    );

  const leagues =
    getLeagues();

  select.innerHTML =
    leagues
      .map(
        league => `
          <option
            value="${escapeAttribute(league.id)}"
          >
            ${escapeHtml(league.name)}
          </option>
        `
      )
      .join("");

  select.disabled =
    false;
}


function populateSeasonSelector(
  league,
  preferredSeason = null
) {

  const select =
    document.getElementById(
      "season-select"
    );

  const sources =
    getSourcesForLeague(
      league
    );

  select.innerHTML =
    sources
      .map(
        source => `
          <option
            value="${escapeAttribute(source.season)}"
          >
            ${escapeHtml(source.season_label)}
          </option>
        `
      )
      .join("");

  select.disabled =
    sources.length === 0;

  if (
    preferredSeason
    && sources.some(
      source =>
        source.season ===
        preferredSeason
    )
  ) {

    select.value =
      preferredSeason;
  }

  return sources;
}


function findSource(
  league,
  season
) {

  return DATA_SOURCES.find(
    source =>
      source.league === league
      && source.season === season
  );
}


async function handleLeagueChange() {

  const league =
    document.getElementById(
      "league-select"
    ).value;

  const sources =
    populateSeasonSelector(
      league
    );

  if (!sources.length) {
    return;
  }

  const source =
    sources[0];

  document.getElementById(
    "season-select"
  ).value =
    source.season;

  await loadSource(
    source
  );
}


async function handleSeasonChange() {

  const league =
    document.getElementById(
      "league-select"
    ).value;

  const season =
    document.getElementById(
      "season-select"
    ).value;

  const source =
    findSource(
      league,
      season
    );

  if (source) {

    await loadSource(
      source
    );
  }
}


// =============================================================================
// Clubs / filters
// =============================================================================


function getPlayerClubs(player) {

  return player.team
    .split("/")
    .map(
      item =>
        item.trim()
    )
    .filter(Boolean);
}


function getAvailableClubs() {

  const clubs =
    new Set();

  for (
    const player
    of ALL_PLAYERS
  ) {

    for (
      const club
      of getPlayerClubs(player)
    ) {

      clubs.add(club);
    }
  }

  return [...clubs].sort(
    (a, b) =>
      a.localeCompare(b)
  );
}


function resetFilters() {

  FILTER_STATE = {
    positions:
      new Set(),

    clubs:
      new Set(),

    minAge:
      null,

    maxAge:
      null
  };
}


function filtersActive() {

  return (
    FILTER_STATE.positions.size > 0
    || FILTER_STATE.clubs.size > 0
    || FILTER_STATE.minAge !== null
    || FILTER_STATE.maxAge !== null
  );
}


function playerMatches(player) {

  if (
    FILTER_STATE.positions.size
    && !FILTER_STATE.positions.has(
      player.positionGroup
    )
  ) {
    return false;
  }

  if (
    FILTER_STATE.clubs.size
  ) {

    const match =
      getPlayerClubs(player)
        .some(
          club =>
            FILTER_STATE.clubs.has(
              club
            )
        );

    if (!match) {
      return false;
    }
  }

  if (
    FILTER_STATE.minAge !== null
  ) {

    if (
      !Number.isFinite(player.age)
      || player.age <
        FILTER_STATE.minAge
    ) {
      return false;
    }
  }

  if (
    FILTER_STATE.maxAge !== null
  ) {

    if (
      !Number.isFinite(player.age)
      || player.age >
        FILTER_STATE.maxAge
    ) {
      return false;
    }
  }

  return true;
}


function createFilterPanel() {

  const panel =
    document.getElementById(
      "filter-panel"
    );

  const clubs =
    getAvailableClubs();

  const ages =
    ALL_PLAYERS
      .map(
        player =>
          player.age
      )
      .filter(
        Number.isFinite
      );

  const minAge =
    ages.length
      ? Math.floor(
          Math.min(...ages)
        )
      : 16;

  const maxAge =
    ages.length
      ? Math.ceil(
          Math.max(...ages)
        )
      : 45;

  const positions = [
    ["GK", "Goalkeepers"],
    ["DF", "Defenders"],
    ["MF", "Midfielders"],
    ["FW", "Forwards"]
  ];

  panel.innerHTML = `

    <div class="filter-grid">

      <div class="filter-section">

        <div class="filter-section-title">
          Position
        </div>

        <div class="filter-chip-list">

          ${positions
            .map(
              ([code, label]) => `
                <label class="filter-chip">

                  <input
                    type="checkbox"
                    class="position-filter"
                    value="${code}"
                  >

                  <span>
                    ${label}
                  </span>

                </label>
              `
            )
            .join("")}

        </div>

      </div>


      <div class="filter-section">

        <div class="filter-section-title">
          Club
        </div>

        <div class="club-filter-list">

          ${clubs
            .map(
              club => `
                <label class="filter-chip">

                  <input
                    type="checkbox"
                    class="club-filter"
                    value="${escapeAttribute(club)}"
                  >

                  <span>
                    ${escapeHtml(club)}
                  </span>

                </label>
              `
            )
            .join("")}

        </div>

      </div>


      <div class="filter-section">

        <div class="filter-section-title">
          Age
        </div>

        <div class="age-filter">

          <label>
            Min

            <input
              id="age-min"
              type="number"
              placeholder="${minAge}"
            >
          </label>

          <span class="age-separator">
            to
          </span>

          <label>
            Max

            <input
              id="age-max"
              type="number"
              placeholder="${maxAge}"
            >
          </label>

        </div>

      </div>

    </div>


    <div class="filter-footer">

      <div id="filter-result-count">
        No filters active ·
        ${ALL_PLAYERS.length} players
      </div>

      <button
        id="clear-filters"
        type="button"
      >
        Clear filters
      </button>

    </div>
  `;

  panel.hidden =
    false;

  document
    .querySelectorAll(
      ".position-filter, .club-filter"
    )
    .forEach(
      input =>
        input.addEventListener(
          "change",
          readFilters
        )
    );

  document
    .getElementById(
      "age-min"
    )
    .addEventListener(
      "input",
      readFilters
    );

  document
    .getElementById(
      "age-max"
    )
    .addEventListener(
      "input",
      readFilters
    );

  document
    .getElementById(
      "clear-filters"
    )
    .addEventListener(
      "click",
      clearFilters
    );
}


function readFilters() {

  FILTER_STATE.positions =
    new Set(
      [
        ...document.querySelectorAll(
          ".position-filter:checked"
        )
      ]
      .map(
        item =>
          item.value
      )
    );

  FILTER_STATE.clubs =
    new Set(
      [
        ...document.querySelectorAll(
          ".club-filter:checked"
        )
      ]
      .map(
        item =>
          item.value
      )
    );

  const min =
    document.getElementById(
      "age-min"
    ).value;

  const max =
    document.getElementById(
      "age-max"
    ).value;

  FILTER_STATE.minAge =
    min === ""
      ? null
      : Number(min);

  FILTER_STATE.maxAge =
    max === ""
      ? null
      : Number(max);

  updatePlotFilters();
}


function clearFilters() {

  resetFilters();

  createFilterPanel();

  updatePlotFilters();
}


function updatePlotFilters() {

  const active =
    filtersActive();

  let matches =
    0;

  [
    "GK",
    "DF",
    "MF",
    "FW"
  ]
  .forEach(
    (
      position,
      traceIndex
    ) => {

      const group =
        ALL_PLAYERS.filter(
          player =>
            player.positionGroup ===
            position
        );

      const colors =
        group.map(
          player => {

            const match =
              !active
              || playerMatches(
                player
              );

            if (match) {

              matches += 1;

              return CONFIG.colors[
                position
              ];
            }

            return CONFIG.inactiveColor;
          }
        );

      Plotly.restyle(
        "player-cloud",
        {
          "marker.color":
            [colors]
        },
        [traceIndex]
      );
    }
  );

  const counter =
    document.getElementById(
      "filter-result-count"
    );

  if (counter) {

    counter.textContent =
      active
        ? `${matches} of ${ALL_PLAYERS.length} players match`
        : `No filters active · ${ALL_PLAYERS.length} players`;
  }
}


// =============================================================================
// Plot
// =============================================================================


function makeTrace(
  position
) {

  const group =
    ALL_PLAYERS.filter(
      player =>
        player.positionGroup ===
        position
    );

  return {

    type:
      "scatter3d",

    mode:
      "markers",

    name:
      position,

    x:
      group.map(
        player =>
          player.pc1
      ),

    y:
      group.map(
        player =>
          player.pc2
      ),

    z:
      group.map(
        player =>
          player.pc3
      ),

    text:
      group.map(
        player =>
          player.player
      ),

    customdata:
      group.map(
        player => [

          player.team,
          player.position,
          formatInteger(player.age),
          formatInteger(player.minutes),

          formatNumber(
            player.shootingGoalsPer90
          ),

          formatNumber(
            player.shotsPer90
          ),

          formatNumber(
            player.shotsOnTargetPer90
          ),

          formatNumber(
            player.shotsOnTargetPct,
            1
          ),

          formatNumber(
            player.goalsPerShot
          ),

          formatNumber(
            player.goalsPerShotOnTarget
          ),

          formatNumber(
            player.pointsPerMatch
          ),

          formatNumber(
            player.plusMinusPer90
          ),

          formatNumber(
            player.onOffPer90
          ),

          formatNumber(
            player.foulsCommittedPer90
          ),

          formatNumber(
            player.foulsDrawnPer90
          ),

          formatNumber(
            player.crossesPer90
          ),

          formatNumber(
            player.interceptionsPer90
          ),

          formatNumber(
            player.tacklesWonPer90
          ),

          formatInteger(
            player.observedFeatures
          ),

          formatInteger(
            player.imputedFeatures
          )
        ]
      ),

    marker: {

      size:
        CONFIG.markerSize,

      color:
        CONFIG.colors[
          position
        ],

      opacity:
        0.92,

      line: {
        width: 0.3,
        color:
          "rgba(255,255,255,.55)"
      }
    },

    hovertemplate:

      "<b>%{text}</b><br>" +

      "%{customdata[0]} · %{customdata[1]}<br>" +

      "Age: %{customdata[2]}<br>" +

      "Minutes: %{customdata[3]}<br><br>" +


      "<b>PCA</b><br>" +

      "Shooting: %{x:.2f}<br>" +

      "Team success: %{y:.2f}<br>" +

      "Misc performance: %{z:.2f}<br><br>" +


      "<b>Shooting</b><br>" +

      "Goals / 90: %{customdata[4]}<br>" +

      "Shots / 90: %{customdata[5]}<br>" +

      "Shots on target / 90: %{customdata[6]}<br>" +

      "Shots on target: %{customdata[7]}%<br>" +

      "Goals / shot: %{customdata[8]}<br>" +

      "Goals / SOT: %{customdata[9]}<br><br>" +


      "<b>Team success</b><br>" +

      "Points / match: %{customdata[10]}<br>" +

      "+/- / 90: %{customdata[11]}<br>" +

      "On-Off / 90: %{customdata[12]}<br><br>" +


      "<b>Misc</b><br>" +

      "Fouls committed / 90: %{customdata[13]}<br>" +

      "Fouls drawn / 90: %{customdata[14]}<br>" +

      "Crosses / 90: %{customdata[15]}<br>" +

      "Interceptions / 90: %{customdata[16]}<br>" +

      "Tackles won / 90: %{customdata[17]}<br><br>" +


      "Observed PCA metrics: %{customdata[18]}<br>" +

      "Imputed PCA metrics: %{customdata[19]}" +

      "<extra></extra>"
  };
}


async function renderPlot() {

  const traces = [
    "GK",
    "DF",
    "MF",
    "FW"
  ].map(
    makeTrace
  );

  const axisCommon = {
    color: "#c7d0da",
    showbackground: false,
    showgrid: true,
    gridcolor: "#34404c",
    zeroline: true,
    zerolinecolor: "#66717d",
    showline: false
  };

  const layout = {

    paper_bgcolor:
      "#11151a",

    plot_bgcolor:
      "#11151a",

    font: {
      color: "#e9eef5",
      family:
        "Inter, system-ui, sans-serif"
    },

    margin: {
      l: 0,
      r: 0,
      b: 0,
      t: 20
    },

    scene: {

      bgcolor:
        "#11151a",

      xaxis: {
        ...axisCommon,

        title: {
          text:
            "Shooting profile (PC1)"
        }
      },

      yaxis: {
        ...axisCommon,

        title: {
          text:
            "Team success (PC2)"
        }
      },

      zaxis: {
        ...axisCommon,

        title: {
          text:
            "Misc performance (PC3)"
        }
      },

      camera: {

        eye: {
          x: 1.55,
          y: 1.55,
          z: 1.15
        },

        up: {
          x: 0,
          y: 0,
          z: 1
        },

        projection: {
          type:
            "orthographic"
        }
      },

      dragmode:
        "turntable",

      aspectmode:
        "cube"
    },

    hoverlabel: {
      bgcolor: "#0b0d10",
      bordercolor: "#40505f",
      font: {
        color: "#fff",
        size: 13
      }
    },

    uirevision:
      CURRENT_SOURCE?.id
      ?? "pca"
  };

  await Plotly.newPlot(
    "player-cloud",
    traces,
    layout,
    {
      responsive: true,
      displaylogo: false,
      scrollZoom: true
    }
  );
}


// =============================================================================
// CSV loading
// =============================================================================


function parseCsv(url) {

  return new Promise(
    (
      resolve,
      reject
    ) => {

      Papa.parse(
        url,
        {

          download:
            true,

          header:
            true,

          skipEmptyLines:
            true,

          complete:
            resolve,

          error:
            reject
        }
      );
    }
  );
}


async function loadSource(source) {

  CURRENT_SOURCE =
    source;

  resetFilters();

  const status =
    document.getElementById(
      "status"
    );

  status.textContent =
    `Loading ${source.league_name} · ${source.season_label}…`;

  const result =
    await parseCsv(
      `${source.path}?v=${encodeURIComponent(source.modified)}`
    );

  ALL_PLAYERS =
    preparePlayers(
      result.data
    );

  createFilterPanel();

  await renderPlot();

  document.getElementById(
    "dataset-eyebrow"
  ).textContent =
    `${source.league_name} · ${source.season_label}`;

  status.textContent =
    `${source.league_name} · ${source.season_label} · ${ALL_PLAYERS.length} players`;

  const url =
    new URL(
      window.location.href
    );

  url.searchParams.set(
    "league",
    source.league
  );

  url.searchParams.set(
    "season",
    source.season
  );

  history.replaceState(
    {},
    "",
    url
  );
}


// =============================================================================
// Manifest
// =============================================================================


async function loadManifest() {

  const response =
    await fetch(
      `${CONFIG.manifestFile}?v=${Date.now()}`,
      {
        cache:
          "no-store"
      }
    );

  if (!response.ok) {

    throw new Error(
      `Could not load ${CONFIG.manifestFile}`
    );
  }

  const manifest =
    await response.json();

  DATA_SOURCES =
    manifest.sources ?? [];

  if (!DATA_SOURCES.length) {

    throw new Error(
      "No prepared PCA datasets found."
    );
  }

  populateLeagueSelector();

  const params =
    new URLSearchParams(
      window.location.search
    );

  const requestedLeague =
    params.get(
      "league"
    );

  const requestedSeason =
    params.get(
      "season"
    );

  const leagues =
    getLeagues();

  let initialLeague =
    requestedLeague;

  if (
    !leagues.some(
      league =>
        league.id ===
        initialLeague
    )
  ) {

    initialLeague =
      leagues[0].id;
  }

  document.getElementById(
    "league-select"
  ).value =
    initialLeague;

  const sources =
    populateSeasonSelector(
      initialLeague,
      requestedSeason
    );

  let initialSource =
    sources.find(
      source =>
        source.season ===
        requestedSeason
    );

  if (!initialSource) {

    initialSource =
      sources[0];
  }

  document.getElementById(
    "season-select"
  ).value =
    initialSource.season;

  document.getElementById(
    "league-select"
  ).addEventListener(
    "change",
    handleLeagueChange
  );

  document.getElementById(
    "season-select"
  ).addEventListener(
    "change",
    handleSeasonChange
  );

  await loadSource(
    initialSource
  );
}


// =============================================================================
// Start
// =============================================================================


loadManifest()
  .catch(
    error => {

      console.error(
        error
      );

      document.getElementById(
        "status"
      ).textContent =
        error.message;
    }
  );