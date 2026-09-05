"use strict";

/*
Bundesliga 2025/26 — grouped PCA 3D visualization

Expected input:
    player_pca.csv

Axes:
    X = physical_score
    Y = offensive_score
    Z = defensive_score

Filters:
    - Position: multi-select
    - Club: multi-select
    - Age: min/max range

Filter behaviour:
    - no filter active:
        every player keeps normal position colour

    - filter active:
        matching players keep position colour

    - non-matching players:
        remain visible but become gray
*/


const CONFIG = {

  csvFile:
    "player_pca.csv",


  colors: {

    GK:
      "#ff8c1a",

    DF:
      "#ffd84d",

    MF:
      "#35c66f",

    FW:
      "#3f8cff"

  },


  labels: {

    GK:
      "Goalkeepers",

    DF:
      "Defenders",

    MF:
      "Midfielders",

    FW:
      "Forwards"

  },


  inactiveColor:
    "#666d76",


  activeOpacity:
    0.92,


  markerSize:
    5.8

};


let ALL_PLAYERS = [];


let FILTER_STATE = {

  positions:
    new Set(),

  clubs:
    new Set(),

  minAge:
    null,

  maxAge:
    null

};


// -----------------------------------------------------------------------------
// Parsing / validation
// -----------------------------------------------------------------------------


function parseNumber(value) {

  if (
    value === null ||
    value === undefined
  ) {

    return NaN;

  }


  const cleaned = String(value)

    .trim()

    .replace(
      ",",
      "."
    );


  if (
    cleaned === ""
  ) {

    return NaN;

  }


  const result =
    Number(cleaned);


  return Number.isFinite(result)

    ? result

    : NaN;

}


function validateColumns(headers) {

  const requiredColumns = [

    "player",
    "team",
    "position",
    "position_group",

    "age",
    "minutes",

    "physical_score",
    "offensive_score",
    "defensive_score",

    "distance_per90",
    "sprints_per90",
    "intensive_runs_per90",
    "top_speed_kmh",
    "sprints_per_km",
    "intensive_runs_per_km",

    "goals_per90",
    "assists_per90",
    "shots_per90",
    "shots_on_target_per90",
    "crosses_per90",
    "fouls_drawn_per90",
    "offsides_per90",
    "penalty_attempts_per90",

    "duels_won_per90",
    "aerial_duels_won_per90",
    "tackles_won_per90",
    "interceptions_per90",
    "fouls_committed_per90",
    "yellow_cards_per90",

    "observed_features",
    "imputed_features"

  ];


  return requiredColumns.filter(

    column =>
      !headers.includes(
        column
      )

  );

}


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


        physicalScore:
          parseNumber(
            row.physical_score
          ),


        offensiveScore:
          parseNumber(
            row.offensive_score
          ),


        defensiveScore:
          parseNumber(
            row.defensive_score
          ),


        // Physical

        distancePer90:
          parseNumber(
            row.distance_per90
          ),


        sprintsPer90:
          parseNumber(
            row.sprints_per90
          ),


        intensiveRunsPer90:
          parseNumber(
            row.intensive_runs_per90
          ),


        topSpeedKmh:
          parseNumber(
            row.top_speed_kmh
          ),


        sprintsPerKm:
          parseNumber(
            row.sprints_per_km
          ),


        intensiveRunsPerKm:
          parseNumber(
            row.intensive_runs_per_km
          ),


        // Offense

        goalsPer90:
          parseNumber(
            row.goals_per90
          ),


        assistsPer90:
          parseNumber(
            row.assists_per90
          ),


        shotsPer90:
          parseNumber(
            row.shots_per90
          ),


        shotsOnTargetPer90:
          parseNumber(
            row.shots_on_target_per90
          ),


        crossesPer90:
          parseNumber(
            row.crosses_per90
          ),


        foulsDrawnPer90:
          parseNumber(
            row.fouls_drawn_per90
          ),


        offsidesPer90:
          parseNumber(
            row.offsides_per90
          ),


        penaltyAttemptsPer90:
          parseNumber(
            row.penalty_attempts_per90
          ),


        // Defense

        duelsWonPer90:
          parseNumber(
            row.duels_won_per90
          ),


        aerialDuelsWonPer90:
          parseNumber(
            row.aerial_duels_won_per90
          ),


        tacklesWonPer90:
          parseNumber(
            row.tackles_won_per90
          ),


        interceptionsPer90:
          parseNumber(
            row.interceptions_per90
          ),


        foulsCommittedPer90:
          parseNumber(
            row.fouls_committed_per90
          ),


        yellowCardsPer90:
          parseNumber(
            row.yellow_cards_per90
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

        player.player &&

        [
          "GK",
          "DF",
          "MF",
          "FW"
        ].includes(
          player.positionGroup
        ) &&

        Number.isFinite(
          player.physicalScore
        ) &&

        Number.isFinite(
          player.offensiveScore
        ) &&

        Number.isFinite(
          player.defensiveScore
        )

    );

}


// -----------------------------------------------------------------------------
// Club helpers
// -----------------------------------------------------------------------------


function getPlayerClubs(player) {

  return player.team

    .split("/")

    .map(
      club =>
        club.trim()
    )

    .filter(Boolean);

}


function getAvailableClubs(players) {

  const clubs =
    new Set();


  for (
    const player of players
  ) {

    for (
      const club
      of getPlayerClubs(player)
    ) {

      clubs.add(
        club
      );

    }

  }


  return [...clubs].sort(

    (a, b) =>
      a.localeCompare(b)

  );

}


// -----------------------------------------------------------------------------
// Filter logic
// -----------------------------------------------------------------------------


function filtersAreActive() {

  return (

    FILTER_STATE.positions.size > 0 ||

    FILTER_STATE.clubs.size > 0 ||

    FILTER_STATE.minAge !== null ||

    FILTER_STATE.maxAge !== null

  );

}


function playerMatchesFilters(player) {

  // ---------------------------------------------------------------------------
  // Position
  // ---------------------------------------------------------------------------
  //
  // Multiple selected positions use OR.
  //
  // Example:
  //
  // DF + MF
  //
  // means:
  //
  // defender OR midfielder
  // ---------------------------------------------------------------------------

  if (

    FILTER_STATE.positions.size > 0 &&

    !FILTER_STATE.positions.has(
      player.positionGroup
    )

  ) {

    return false;

  }


  // ---------------------------------------------------------------------------
  // Club
  // ---------------------------------------------------------------------------

  if (
    FILTER_STATE.clubs.size > 0
  ) {

    const matchesClub =

      getPlayerClubs(player)

        .some(

          club =>
            FILTER_STATE.clubs.has(
              club
            )

        );


    if (
      !matchesClub
    ) {

      return false;

    }

  }


  // ---------------------------------------------------------------------------
  // Age
  // ---------------------------------------------------------------------------

  if (

    FILTER_STATE.minAge !== null ||

    FILTER_STATE.maxAge !== null

  ) {


    if (
      !Number.isFinite(
        player.age
      )
    ) {

      return false;

    }


    if (

      FILTER_STATE.minAge !== null &&

      player.age <
        FILTER_STATE.minAge

    ) {

      return false;

    }


    if (

      FILTER_STATE.maxAge !== null &&

      player.age >
        FILTER_STATE.maxAge

    ) {

      return false;

    }

  }


  return true;

}


// -----------------------------------------------------------------------------
// HTML escaping
// -----------------------------------------------------------------------------


function escapeHtml(text) {

  const element =
    document.createElement(
      "div"
    );


  element.textContent =
    String(text);


  return element.innerHTML;

}


function escapeHtmlAttribute(text) {

  return String(text)

    .replaceAll(
      "&",
      "&amp;"
    )

    .replaceAll(
      '"',
      "&quot;"
    )

    .replaceAll(
      "<",
      "&lt;"
    )

    .replaceAll(
      ">",
      "&gt;"
    );

}


// -----------------------------------------------------------------------------
// Filter UI
// -----------------------------------------------------------------------------


function createFilterPanel(players) {

  const panel =
    document.getElementById(
      "filter-panel"
    );


  if (!panel) {

    console.warn(
      "Missing #filter-panel in index.html"
    );

    return;

  }


  const clubs =
    getAvailableClubs(
      players
    );


  const ages = players

    .map(
      player =>
        player.age
    )

    .filter(
      Number.isFinite
    );


  const datasetMinAge =

    ages.length

      ? Math.floor(
          Math.min(
            ...ages
          )
        )

      : 0;


  const datasetMaxAge =

    ages.length

      ? Math.ceil(
          Math.max(
            ...ages
          )
        )

      : 100;


  panel.innerHTML = `

    <div class="filter-grid">


      <div class="filter-section">

        <div class="filter-section-title">
          Position
        </div>


        <div
          class="filter-chip-list"
          id="position-filter-list"
        >

          ${[

            [
              "GK",
              "Goalkeepers"
            ],

            [
              "DF",
              "Defenders"
            ],

            [
              "MF",
              "Midfielders"
            ],

            [
              "FW",
              "Forwards"
            ]

          ]

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


        <div
          class="club-filter-list"
          id="club-filter-list"
        >

          ${clubs

            .map(

              club => `

                <label class="filter-chip">

                  <input
                    type="checkbox"
                    class="club-filter"
                    value="${escapeHtmlAttribute(club)}"
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

            <span>
              Min
            </span>

            <input
              type="number"
              id="age-min"
              min="${datasetMinAge}"
              max="${datasetMaxAge}"
              placeholder="${datasetMinAge}"
            >

          </label>


          <span class="age-separator">
            to
          </span>


          <label>

            <span>
              Max
            </span>

            <input
              type="number"
              id="age-max"
              min="${datasetMinAge}"
              max="${datasetMaxAge}"
              placeholder="${datasetMaxAge}"
            >

          </label>

        </div>

      </div>


    </div>


    <div class="filter-footer">

      <div id="filter-result-count">

        No filters active ·
        ${players.length} players

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


  attachFilterEvents();

}


// -----------------------------------------------------------------------------
// Filter events
// -----------------------------------------------------------------------------


function attachFilterEvents() {

  document

    .querySelectorAll(
      ".position-filter, .club-filter"
    )

    .forEach(
      input => {

        input.addEventListener(

          "change",

          readFiltersFromUI

        );

      }
    );


  document

    .getElementById(
      "age-min"
    )

    ?.addEventListener(

      "input",

      readFiltersFromUI

    );


  document

    .getElementById(
      "age-max"
    )

    ?.addEventListener(

      "input",

      readFiltersFromUI

    );


  document

    .getElementById(
      "clear-filters"
    )

    ?.addEventListener(

      "click",

      clearFilters

    );

}


// -----------------------------------------------------------------------------
// Read filters
// -----------------------------------------------------------------------------


function readFiltersFromUI() {

  FILTER_STATE.positions =

    new Set(

      [
        ...document.querySelectorAll(
          ".position-filter:checked"
        )
      ]

      .map(
        element =>
          element.value
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
        element =>
          element.value
      )

    );


  const minAgeInput =
    document.getElementById(
      "age-min"
    );


  const maxAgeInput =
    document.getElementById(
      "age-max"
    );


  FILTER_STATE.minAge =

    (
      minAgeInput &&
      minAgeInput.value !== ""
    )

      ? Number(
          minAgeInput.value
        )

      : null;


  FILTER_STATE.maxAge =

    (
      maxAgeInput &&
      maxAgeInput.value !== ""
    )

      ? Number(
          maxAgeInput.value
        )

      : null;


  // If age limits were accidentally entered backwards:
  // Min = 30
  // Max = 20
  //
  // interpret this as:
  // 20 - 30

  if (

    FILTER_STATE.minAge !== null &&

    FILTER_STATE.maxAge !== null &&

    FILTER_STATE.minAge >
      FILTER_STATE.maxAge

  ) {


    const temp =
      FILTER_STATE.minAge;


    FILTER_STATE.minAge =
      FILTER_STATE.maxAge;


    FILTER_STATE.maxAge =
      temp;

  }


  updatePlotFilters();

}


// -----------------------------------------------------------------------------
// Clear filters
// -----------------------------------------------------------------------------


function clearFilters() {

  document

    .querySelectorAll(
      ".position-filter, .club-filter"
    )

    .forEach(
      input => {

        input.checked =
          false;

      }
    );


  const minAgeInput =
    document.getElementById(
      "age-min"
    );


  const maxAgeInput =
    document.getElementById(
      "age-max"
    );


  if (minAgeInput) {

    minAgeInput.value =
      "";

  }


  if (maxAgeInput) {

    maxAgeInput.value =
      "";

  }


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


  updatePlotFilters();

}


// -----------------------------------------------------------------------------
// Update point colours after filtering
// -----------------------------------------------------------------------------


function updatePlotFilters() {

  const active =
    filtersAreActive();


  let matchedPlayers =
    0;


  const positionCodes = [

    "GK",
    "DF",
    "MF",
    "FW"

  ];


  positionCodes.forEach(

    (
      positionCode,
      traceIndex
    ) => {


      const group =

        ALL_PLAYERS.filter(

          player =>
            player.positionGroup ===
            positionCode

        );


      const colors =

        group.map(

          player => {


            const matches =

              !active ||

              playerMatchesFilters(
                player
              );


            if (matches) {

              matchedPlayers +=
                1;


              return CONFIG.colors[
                positionCode
              ];

            }


            return CONFIG.inactiveColor;

          }

        );


      Plotly.restyle(

        "player-cloud",

        {

          "marker.color":
            [
              colors
            ]

        },

        [
          traceIndex
        ]

      );

    }

  );


  updateFilterStatus(

    active,

    matchedPlayers

  );

}


// -----------------------------------------------------------------------------
// Filter status text
// -----------------------------------------------------------------------------


function updateFilterStatus(
  active,
  matchedPlayers
) {

  const element =
    document.getElementById(
      "filter-result-count"
    );


  if (!element) {
    return;
  }


  if (!active) {

    element.textContent =

      `No filters active · ` +
      `${ALL_PLAYERS.length} players`;


    return;

  }


  element.textContent =

    `${matchedPlayers} of ` +
    `${ALL_PLAYERS.length} players match`;

}


// -----------------------------------------------------------------------------
// Plot traces
// -----------------------------------------------------------------------------


function makeTrace(
  players,
  positionCode
) {

  const group =

    players.filter(

      player =>
        player.positionGroup ===
        positionCode

    );


  return {

    type:
      "scatter3d",


    mode:
      "markers",


    name:
      CONFIG.labels[
        positionCode
      ],


    // -------------------------------------------------------------------------
    // Three grouped PCA axes
    // -------------------------------------------------------------------------

    x:

      group.map(
        player =>
          player.physicalScore
      ),


    y:

      group.map(
        player =>
          player.offensiveScore
      ),


    z:

      group.map(
        player =>
          player.defensiveScore
      ),


    text:

      group.map(
        player =>
          player.player
      ),


    // -------------------------------------------------------------------------
    // Hover information
    // -------------------------------------------------------------------------

    customdata:

      group.map(

        player => [

          // Basic info

          player.team,                    // 0
          player.position,                // 1
          player.age,                     // 2
          player.minutes,                 // 3


          // Physical

          player.distancePer90,           // 4
          player.sprintsPer90,            // 5
          player.intensiveRunsPer90,      // 6
          player.topSpeedKmh,             // 7
          player.sprintsPerKm,            // 8
          player.intensiveRunsPerKm,      // 9


          // Offense

          player.goalsPer90,              // 10
          player.assistsPer90,            // 11
          player.shotsPer90,              // 12
          player.shotsOnTargetPer90,      // 13
          player.crossesPer90,            // 14
          player.foulsDrawnPer90,         // 15
          player.offsidesPer90,           // 16
          player.penaltyAttemptsPer90,    // 17


          // Defense

          player.duelsWonPer90,           // 18
          player.aerialDuelsWonPer90,     // 19
          player.tacklesWonPer90,         // 20
          player.interceptionsPer90,      // 21
          player.foulsCommittedPer90,     // 22
          player.yellowCardsPer90,        // 23


          // Data quality
          Number.isFinite(player.observedFeatures)
          ? Math.round(player.observedFeatures).toString()
          : "–",                       // 24

          Number.isFinite(player.imputedFeatures)
          ? Math.round(player.imputedFeatures).toString()
          : "–"                        // 25

        ]

      ),


    marker: {

      size:
        CONFIG.markerSize,


      color:
        CONFIG.colors[
          positionCode
        ],


      opacity:
        CONFIG.activeOpacity,


      line: {

        width:
          0.3,

        color:
          "rgba(255,255,255,0.55)"

      }

    },


    hovertemplate:

      "<b>%{text}</b><br>" +

      "%{customdata[0]} · %{customdata[1]}<br>" +

      "Age: %{customdata[2]:.0f}<br>" +

      "Minutes: %{customdata[3]:.0f}<br>" +

      "<br>" +


      "<b>Profile scores</b><br>" +

      "Physical intensity: %{x:.2f}<br>" +

      "Offensive activity: %{y:.2f}<br>" +

      "Defensive activity: %{z:.2f}<br>" +

      "<br>" +


      "<b>Physical</b><br>" +

      "Distance / 90: %{customdata[4]:.2f} km<br>" +

      "Sprints / 90: %{customdata[5]:.1f}<br>" +

      "Intensive runs / 90: %{customdata[6]:.1f}<br>" +

      "Top speed: %{customdata[7]:.1f} km/h<br>" +

      "Sprints / km: %{customdata[8]:.2f}<br>" +

      "Intensive runs / km: %{customdata[9]:.2f}<br>" +

      "<br>" +


      "<b>Offense</b><br>" +

      "Goals / 90: %{customdata[10]:.2f}<br>" +

      "Assists / 90: %{customdata[11]:.2f}<br>" +

      "Shots / 90: %{customdata[12]:.2f}<br>" +

      "Shots on target / 90: %{customdata[13]:.2f}<br>" +

      "Crosses / 90: %{customdata[14]:.2f}<br>" +

      "Fouls drawn / 90: %{customdata[15]:.2f}<br>" +

      "Offsides / 90: %{customdata[16]:.2f}<br>" +

      "Penalty attempts / 90: %{customdata[17]:.2f}<br>" +

      "<br>" +


      "<b>Defense</b><br>" +

      "Duels won / 90: %{customdata[18]:.2f}<br>" +

      "Aerial duels won / 90: %{customdata[19]:.2f}<br>" +

      "Tackles won / 90: %{customdata[20]:.2f}<br>" +

      "Interceptions / 90: %{customdata[21]:.2f}<br>" +

      "Fouls committed / 90: %{customdata[22]:.2f}<br>" +

      "Yellow cards / 90: %{customdata[23]:.2f}<br>" +

      "<br>" +

      "Observed PCA metrics: %{customdata[24]}<br>" +

      "Imputed PCA metrics: %{customdata[25]}" +

      "<extra></extra>"

  };

}


// -----------------------------------------------------------------------------
// Render Plotly plot
// -----------------------------------------------------------------------------


function renderPlot(players) {

  const traces = [

    "GK",
    "DF",
    "MF",
    "FW"

  ]

    .map(

      position =>
        makeTrace(
          players,
          position
        )

    );


  // Shared axis styling.
  //
  // showbackground = false:
  // removes the large shaded 3D background planes
  //
  // showgrid = true:
  // keeps the Cartesian grid

  const axisCommon = {

    color:
      "#c7d0da",

    showbackground:
      false,

    showgrid:
      true,

    gridcolor:
      "#34404c",

    zeroline:
      true,

    zerolinecolor:
      "#66717d",

    showline:
      false

  };


  const layout = {

    paper_bgcolor:
      "#11151a",

    plot_bgcolor:
      "#11151a",


    font: {

      color:
        "#e9eef5",

      family:
        "Inter, system-ui, sans-serif"

    },


    margin: {

      l:
        0,

      r:
        0,

      b:
        0,

      t:
        20,

      pad:
        0

    },


    legend: {

      orientation:
        "h",

      x:
        0,

      y:
        1.03,

      bgcolor:
        "rgba(0,0,0,0)",

      font: {

        color:
          "#d8dee7"

      }

    },


    scene: {

      bgcolor:
        "#11151a",


      // -----------------------------------------------------------------------
      // X = Physical
      // -----------------------------------------------------------------------

      xaxis: {

        ...axisCommon,

        title: {

          text:
            "Physical intensity"

        }

      },


      // -----------------------------------------------------------------------
      // Y = Offense
      // -----------------------------------------------------------------------

      yaxis: {

        ...axisCommon,

        title: {

          text:
            "Offensive activity"

        }

      },


      // -----------------------------------------------------------------------
      // Z = Defense
      // -----------------------------------------------------------------------

      zaxis: {

        ...axisCommon,

        title: {

          text:
            "Defensive activity"

        }

      },


      // -----------------------------------------------------------------------
      // Camera
      // -----------------------------------------------------------------------

      camera: {

        eye: {

          x:
            1.55,

          y:
            1.55,

          z:
            1.15

        },


        // Keeps the Z direction upright.

        up: {

          x:
            0,

          y:
            0,

          z:
            1

        },


        // Orthographic avoids perspective distortion.

        projection: {

          type:
            "orthographic"

        }

      },


      // Turntable prevents free roll / flipping of the whole plot.

      dragmode:
        "turntable",


      aspectmode:
        "cube"

    },


    hoverlabel: {

      bgcolor:
        "#0b0d10",

      bordercolor:
        "#40505f",

      font: {

        color:
          "#ffffff",

        size:
          13

      }

    },


    uirevision:
      "bundesliga-grouped-pca-2025-26"

  };


  const plotConfig = {

    responsive:
      true,

    displaylogo:
      false,

    scrollZoom:
      true

  };


  return Plotly.newPlot(

    "player-cloud",

    traces,

    layout,

    plotConfig

  );

}


// -----------------------------------------------------------------------------
// Header status
// -----------------------------------------------------------------------------


function updateStatus(players) {

  const counts = {

    GK:
      0,

    DF:
      0,

    MF:
      0,

    FW:
      0

  };


  for (
    const player of players
  ) {

    if (

      counts[
        player.positionGroup
      ] !== undefined

    ) {

      counts[
        player.positionGroup
      ] += 1;

    }

  }


  const statusElement =

    document.getElementById(
      "status"
    );


  if (!statusElement) {
    return;
  }


  statusElement.textContent =

    `${players.length} players shown · ` +

    `${counts.GK} GK · ` +

    `${counts.DF} DF · ` +

    `${counts.MF} MF · ` +

    `${counts.FW} FW`;

}


// -----------------------------------------------------------------------------
// Error display
// -----------------------------------------------------------------------------


function showError(message) {

  const chartElement =

    document.getElementById(
      "player-cloud"
    );


  if (chartElement) {

    chartElement.innerHTML =

      `<div class="error">` +

      `<div>${message}</div>` +

      `</div>`;

  }


  const statusElement =

    document.getElementById(
      "status"
    );


  if (statusElement) {

    statusElement.textContent =
      "Could not load visualization";

  }

}


// -----------------------------------------------------------------------------
// Load PCA data
// -----------------------------------------------------------------------------


function loadData() {

  Papa.parse(

    CONFIG.csvFile,

    {

      download:
        true,

      header:
        true,

      dynamicTyping:
        true,

      skipEmptyLines:
        true,


      complete(results) {

        if (
          results.errors.length
        ) {

          console.warn(

            "CSV parser warnings:",

            results.errors

          );

        }


        const headers =

          results.meta.fields
          || [];


        const missingColumns =

          validateColumns(
            headers
          );


        if (
          missingColumns.length
        ) {

          showError(

            "The PCA CSV does not contain all expected columns.<br><br>" +

            "Missing:<br>" +

            missingColumns

              .map(

                column =>
                  `• ${column}`

              )

              .join(
                "<br>"
              )

          );


          return;

        }


        ALL_PLAYERS =

          preparePlayers(
            results.data
          );


        if (
          !ALL_PLAYERS.length
        ) {

          showError(

            "No valid grouped-PCA player rows were found."

          );


          return;

        }


        updateStatus(
          ALL_PLAYERS
        );


        createFilterPanel(
          ALL_PLAYERS
        );


        renderPlot(
          ALL_PLAYERS
        );


        updateFilterStatus(

          false,

          ALL_PLAYERS.length

        );

      },


      error(error) {

        console.error(
          error
        );


        showError(

          `Could not load "${CONFIG.csvFile}".<br><br>` +

          "Make sure player_pca.csv is in the same folder as index.html.<br><br>" +

          "For local testing run:<br>" +

          "python -m http.server 8000"

        );

      }

    }

  );

}


loadData();