"use strict";


const CONFIG = {
  csvFile: "player_pca.csv",

  colors: {
    GK: "#ff8c1a",
    DF: "#ffd84d",
    MF: "#35c66f",
    FW: "#3f8cff"
  },

  labels: {
    GK: "Goalkeepers",
    DF: "Defenders",
    MF: "Midfielders",
    FW: "Forwards"
  },

  inactiveColor: "#68717c",
  inactiveOpacity: 0.20,
  activeOpacity: 0.90
};


let ALL_PLAYERS = [];
let FILTER_STATE = {
  positions: new Set(),
  clubs: new Set(),
  minAge: null,
  maxAge: null
};


function parseNumber(value) {
  if (value === null || value === undefined) {
    return NaN;
  }

  const cleaned = String(value)
    .trim()
    .replace(",", ".");

  if (cleaned === "") {
    return NaN;
  }

  const result = Number(cleaned);

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

    "PC1",
    "PC2",
    "PC3",

    "distance_per90",
    "sprints_per90",
    "intensive_runs_per90",
    "duels_won_per90",
    "aerial_duels_won_per90",
    "tackles_won_per90",
    "interceptions_per90",
    "fouls_committed_per90",
    "fouls_drawn_per90",
    "crosses_per90",
    "top_speed_kmh",

    "observed_features",
    "imputed_features"
  ];

  return requiredColumns.filter(
    column => !headers.includes(column)
  );
}


function preparePlayers(rows) {
  return rows
    .map(row => ({
      player: String(
        row.player ?? ""
      ).trim(),

      team: String(
        row.team ?? ""
      ).trim(),

      position: String(
        row.position ?? ""
      ).trim(),

      positionGroup: String(
        row.position_group ?? ""
      ).trim(),

      age: parseNumber(
        row.age
      ),

      minutes: parseNumber(
        row.minutes
      ),

      PC1: parseNumber(
        row.PC1
      ),

      PC2: parseNumber(
        row.PC2
      ),

      PC3: parseNumber(
        row.PC3
      ),

      observedFeatures: parseNumber(
        row.observed_features
      ),

      imputedFeatures: parseNumber(
        row.imputed_features
      ),

      distancePer90: parseNumber(
        row.distance_per90
      ),

      sprintsPer90: parseNumber(
        row.sprints_per90
      ),

      intensiveRunsPer90: parseNumber(
        row.intensive_runs_per90
      ),

      duelsWonPer90: parseNumber(
        row.duels_won_per90
      ),

      aerialDuelsWonPer90: parseNumber(
        row.aerial_duels_won_per90
      ),

      tacklesWonPer90: parseNumber(
        row.tackles_won_per90
      ),

      interceptionsPer90: parseNumber(
        row.interceptions_per90
      ),

      foulsCommittedPer90: parseNumber(
        row.fouls_committed_per90
      ),

      foulsDrawnPer90: parseNumber(
        row.fouls_drawn_per90
      ),

      crossesPer90: parseNumber(
        row.crosses_per90
      ),

      topSpeedKmh: parseNumber(
        row.top_speed_kmh
      )
    }))

    .filter(player =>
      player.player &&
      ["GK", "DF", "MF", "FW"]
        .includes(player.positionGroup) &&
      Number.isFinite(player.PC1) &&
      Number.isFinite(player.PC2) &&
      Number.isFinite(player.PC3)
    );
}


/*
--------------------------------------------------
CLUB HANDLING
--------------------------------------------------

If a player has:
"Bayern Munich / Augsburg"

then that player belongs to both club filters.
*/

function getPlayerClubs(player) {
  return player.team
    .split("/")
    .map(club => club.trim())
    .filter(Boolean);
}


function getAvailableClubs(players) {
  const clubs = new Set();

  for (const player of players) {
    for (const club of getPlayerClubs(player)) {
      clubs.add(club);
    }
  }

  return [...clubs].sort(
    (a, b) => a.localeCompare(b)
  );
}


/*
--------------------------------------------------
FILTER LOGIC
--------------------------------------------------
*/

function filtersAreActive() {
  return (
    FILTER_STATE.positions.size > 0 ||
    FILTER_STATE.clubs.size > 0 ||
    FILTER_STATE.minAge !== null ||
    FILTER_STATE.maxAge !== null
  );
}


function playerMatchesFilters(player) {

  /*
  Position filter
  */

  if (
    FILTER_STATE.positions.size > 0 &&
    !FILTER_STATE.positions.has(
      player.positionGroup
    )
  ) {
    return false;
  }


  /*
  Club filter

  Player only has to belong to ONE
  of the selected clubs.
  */

  if (FILTER_STATE.clubs.size > 0) {
    const playerClubs =
      getPlayerClubs(player);

    const matchesClub =
      playerClubs.some(
        club =>
          FILTER_STATE.clubs.has(club)
      );

    if (!matchesClub) {
      return false;
    }
  }


  /*
  Age filter

  Missing age cannot be considered
  a match when age filtering is active.
  */

  if (
    FILTER_STATE.minAge !== null ||
    FILTER_STATE.maxAge !== null
  ) {
    if (!Number.isFinite(player.age)) {
      return false;
    }

    if (
      FILTER_STATE.minAge !== null &&
      player.age < FILTER_STATE.minAge
    ) {
      return false;
    }

    if (
      FILTER_STATE.maxAge !== null &&
      player.age > FILTER_STATE.maxAge
    ) {
      return false;
    }
  }


  return true;
}


/*
--------------------------------------------------
FILTER UI
--------------------------------------------------
*/

function injectFilterStyles() {
  const style =
    document.createElement("style");

  style.textContent = `

    #pca-filter-panel {
      margin: 0 0 16px 0;
      padding: 16px;

      background: #11151a;
      border: 1px solid #26303a;
      border-radius: 14px;

      color: #e9eef5;

      font-family:
        Inter,
        system-ui,
        sans-serif;
    }


    .filter-grid {
      display: grid;

      grid-template-columns:
        minmax(180px, 1fr)
        minmax(240px, 2fr)
        minmax(200px, 1fr);

      gap: 22px;
    }


    .filter-section-title {
      margin-bottom: 8px;

      font-size: 13px;
      font-weight: 700;

      color: #cbd5df;

      text-transform: uppercase;
      letter-spacing: 0.05em;
    }


    .filter-checkboxes {
      display: flex;
      flex-wrap: wrap;

      gap: 7px;
    }


    .filter-checkbox {
      display: inline-flex;
      align-items: center;

      gap: 6px;

      padding: 6px 9px;

      border: 1px solid #34404c;
      border-radius: 7px;

      background: #151a20;

      font-size: 13px;

      cursor: pointer;

      user-select: none;
    }


    .filter-checkbox:hover {
      border-color: #66717d;
    }


    .filter-checkbox input {
      margin: 0;
      cursor: pointer;
    }


    #club-filter-list {
      max-height: 150px;

      overflow-y: auto;

      display: flex;
      flex-wrap: wrap;

      gap: 7px;

      padding-right: 5px;
    }


    .age-filter {
      display: flex;

      align-items: center;

      gap: 8px;
    }


    .age-filter input {
      width: 80px;

      padding: 7px 8px;

      background: #151a20;

      border: 1px solid #34404c;
      border-radius: 7px;

      color: #ffffff;

      font-size: 14px;
    }


    .age-filter span {
      color: #8995a2;
    }


    .filter-footer {
      display: flex;

      align-items: center;
      justify-content: space-between;

      gap: 12px;

      margin-top: 15px;

      padding-top: 12px;

      border-top: 1px solid #26303a;
    }


    #filter-result-count {
      font-size: 13px;

      color: #aeb8c2;
    }


    #clear-filters {
      padding: 7px 12px;

      border: 1px solid #40505f;
      border-radius: 7px;

      background: #151a20;

      color: #e9eef5;

      cursor: pointer;

      font-size: 13px;
    }


    #clear-filters:hover {
      background: #1d242c;
    }


    @media (max-width: 900px) {

      .filter-grid {
        grid-template-columns: 1fr;
      }

    }

  `;

  document.head.appendChild(style);
}


function createFilterPanel(players) {

  injectFilterStyles();


  const chartCard =
    document.querySelector(
      ".chart-card"
    );

  if (!chartCard) {
    console.warn(
      "Could not find .chart-card for filter placement."
    );

    return;
  }


  const clubs =
    getAvailableClubs(players);


  const ages =
    players
      .map(player => player.age)
      .filter(Number.isFinite);


  const datasetMinAge =
    Math.floor(
      Math.min(...ages)
    );


  const datasetMaxAge =
    Math.ceil(
      Math.max(...ages)
    );


  const panel =
    document.createElement("section");


  panel.id =
    "pca-filter-panel";


  panel.innerHTML = `

    <div class="filter-grid">


      <div>

        <div class="filter-section-title">
          Position
        </div>

        <div
          class="filter-checkboxes"
          id="position-filter-list"
        >

          ${[
            ["GK", "Goalkeepers"],
            ["DF", "Defenders"],
            ["MF", "Midfielders"],
            ["FW", "Forwards"]
          ]
            .map(
              ([code, label]) => `

                <label class="filter-checkbox">

                  <input
                    type="checkbox"
                    class="position-filter"
                    value="${code}"
                  >

                  ${label}

                </label>

              `
            )
            .join("")}

        </div>

      </div>


      <div>

        <div class="filter-section-title">
          Club
        </div>

        <div id="club-filter-list">

          ${clubs
            .map(
              club => `

                <label class="filter-checkbox">

                  <input
                    type="checkbox"
                    class="club-filter"
                    value="${escapeHtmlAttribute(club)}"
                  >

                  ${escapeHtml(club)}

                </label>

              `
            )
            .join("")}

        </div>

      </div>


      <div>

        <div class="filter-section-title">
          Age
        </div>

        <div class="age-filter">

          <input
            type="number"
            id="age-min"
            min="${datasetMinAge}"
            max="${datasetMaxAge}"
            placeholder="${datasetMinAge}"
          >

          <span>
            to
          </span>

          <input
            type="number"
            id="age-max"
            min="${datasetMinAge}"
            max="${datasetMaxAge}"
            placeholder="${datasetMaxAge}"
          >

        </div>

      </div>


    </div>


    <div class="filter-footer">

      <div id="filter-result-count">
        No filters active
      </div>

      <button
        id="clear-filters"
        type="button"
      >
        Clear filters
      </button>

    </div>

  `;


  chartCard.parentNode.insertBefore(
    panel,
    chartCard
  );


  attachFilterEvents();
}


function escapeHtml(text) {
  const element =
    document.createElement("div");

  element.textContent =
    text;

  return element.innerHTML;
}


function escapeHtmlAttribute(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}


/*
--------------------------------------------------
FILTER EVENTS
--------------------------------------------------
*/

function attachFilterEvents() {

  document
    .querySelectorAll(
      ".position-filter"
    )
    .forEach(input => {

      input.addEventListener(
        "change",
        readFiltersFromUI
      );

    });


  document
    .querySelectorAll(
      ".club-filter"
    )
    .forEach(input => {

      input.addEventListener(
        "change",
        readFiltersFromUI
      );

    });


  document
    .getElementById(
      "age-min"
    )
    .addEventListener(
      "input",
      readFiltersFromUI
    );


  document
    .getElementById(
      "age-max"
    )
    .addEventListener(
      "input",
      readFiltersFromUI
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
    minAgeInput.value === ""
      ? null
      : Number(minAgeInput.value);


  FILTER_STATE.maxAge =
    maxAgeInput.value === ""
      ? null
      : Number(maxAgeInput.value);


  /*
  If user accidentally enters:
  min = 30
  max = 20

  swap them.
  */

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


function clearFilters() {

  document
    .querySelectorAll(
      ".position-filter, .club-filter"
    )
    .forEach(input => {
      input.checked = false;
    });


  document.getElementById(
    "age-min"
  ).value = "";


  document.getElementById(
    "age-max"
  ).value = "";


  FILTER_STATE = {
    positions: new Set(),
    clubs: new Set(),
    minAge: null,
    maxAge: null
  };


  updatePlotFilters();
}


/*
--------------------------------------------------
PLOT FILTER UPDATE
--------------------------------------------------
*/

function updatePlotFilters() {

  const active =
    filtersAreActive();


  let matchedPlayers = 0;


  const updates =
    ["GK", "DF", "MF", "FW"]
      .map(
        positionCode => {

          const group =
            ALL_PLAYERS.filter(
              player =>
                player.positionGroup ===
                positionCode
            );


          const colors =
            group.map(player => {

              const matches =
                !active ||
                playerMatchesFilters(player);


              if (matches) {
                matchedPlayers++;

                return CONFIG.colors[
                  positionCode
                ];
              }


              return CONFIG.inactiveColor;
            });


          const opacities =
            group.map(player => {

              const matches =
                !active ||
                playerMatchesFilters(player);


              return matches
                ? CONFIG.activeOpacity
                : CONFIG.inactiveOpacity;
            });


          return {
            positionCode,
            colors,
            opacities
          };

        }
      );


  updates.forEach(
    (update, traceIndex) => {

      Plotly.restyle(
        "player-cloud",

        {
          "marker.color": [
            update.colors
          ],

          "marker.opacity": [
            update.opacities
          ]
        },

        [traceIndex]
      );

    }
  );


  updateFilterStatus(
    active,
    matchedPlayers
  );
}


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
      `No filters active · ${ALL_PLAYERS.length} players`;

    return;
  }


  element.textContent =
    `${matchedPlayers} of ${ALL_PLAYERS.length} players match`;
}


/*
--------------------------------------------------
PLOT TRACE
--------------------------------------------------
*/

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


    x:
      group.map(
        player =>
          player.PC1
      ),

    y:
      group.map(
        player =>
          player.PC2
      ),

    z:
      group.map(
        player =>
          player.PC3
      ),


    text:
      group.map(
        player =>
          player.player
      ),


    customdata:
      group.map(player => [

        player.team,
        player.position,
        player.age,
        player.minutes,

        player.distancePer90,
        player.sprintsPer90,
        player.intensiveRunsPer90,

        player.duelsWonPer90,
        player.aerialDuelsWonPer90,

        player.tacklesWonPer90,
        player.interceptionsPer90,

        player.foulsCommittedPer90,
        player.foulsDrawnPer90,
        player.crossesPer90,

        player.topSpeedKmh,

        player.observedFeatures,
        player.imputedFeatures

      ]),


    marker: {

      size:
        5.5,

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

      "<br>" +


      "<b>PCA coordinates</b><br>" +

      "PC1: %{x:.2f}<br>" +
      "PC2: %{y:.2f}<br>" +
      "PC3: %{z:.2f}<br>" +

      "<br>" +


      "<b>Physical profile</b><br>" +

      "Distance / 90: %{customdata[4]:.2f} km<br>" +

      "Sprints / 90: %{customdata[5]:.1f}<br>" +

      "Intensive runs / 90: %{customdata[6]:.1f}<br>" +

      "Top speed: %{customdata[14]:.1f} km/h<br>" +

      "<br>" +


      "<b>Duels / defensive actions</b><br>" +

      "Duels won / 90: %{customdata[7]:.2f}<br>" +

      "Aerial duels won / 90: %{customdata[8]:.2f}<br>" +

      "Tackles won / 90: %{customdata[9]:.2f}<br>" +

      "Interceptions / 90: %{customdata[10]:.2f}<br>" +

      "<br>" +


      "<b>Other actions</b><br>" +

      "Fouls committed / 90: %{customdata[11]:.2f}<br>" +

      "Fouls drawn / 90: %{customdata[12]:.2f}<br>" +

      "Crosses / 90: %{customdata[13]:.2f}<br>" +

      "<br>" +


      "Minutes: %{customdata[3]:.0f}<br>" +

      "Observed PCA metrics: %{customdata[15]:.0f}<br>" +

      "Imputed PCA metrics: %{customdata[16]:.0f>" +


      "<extra></extra>"

  };

}


/*
--------------------------------------------------
PLOT
--------------------------------------------------
*/

function renderPlot(players) {

  const traces =
    [
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
      )

      .filter(
        trace =>
          trace.x.length > 0
      );


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

      l: 0,
      r: 0,
      b: 0,
      t: 20,
      pad: 0

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
        bgcolor: "#11151a",

        xaxis: {
            title: {
            text: "Running / physical intensity"
            },

            color: "#c7d0da",

            showbackground: false,
            showgrid: true,
            gridcolor: "#34404c",

            zeroline: true,
            zerolinecolor: "#66717d",

            showline: false
        },

        yaxis: {
            title: {
            text: "Duel profile"
            },

            color: "#c7d0da",

            showbackground: false,
            showgrid: true,
            gridcolor: "#34404c",

            zeroline: true,
            zerolinecolor: "#66717d",

            showline: false
        },

        zaxis: {
            title: {
            text: "Defensive activity"
            },

            color: "#c7d0da",

            showbackground: false,
            showgrid: true,
            gridcolor: "#34404c",

            zeroline: true,
            zerolinecolor: "#66717d",

            showline: false
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
            type: "orthographic"
            }
        },

        dragmode: "turntable",

        aspectmode: "cube"
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
      "bundesliga-pca-2025-26"

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


/*
--------------------------------------------------
STATUS
--------------------------------------------------
*/

function updateStatus(players) {

  const counts = {

    GK: 0,
    DF: 0,
    MF: 0,
    FW: 0

  };


  for (const player of players) {

    if (
      counts[
        player.positionGroup
      ] !== undefined
    ) {

      counts[
        player.positionGroup
      ]++;

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


/*
--------------------------------------------------
ERROR
--------------------------------------------------
*/

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


/*
--------------------------------------------------
LOAD DATA
--------------------------------------------------
*/

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
          results.meta.fields || [];


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

              .join("<br>")

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
            "No valid PCA player rows were found."
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

          "Make sure player_pca.csv is in the same folder as index.html."

        );

      }

    }

  );

}


loadData();