"use strict";


// =============================================================================
// Configuration
// =============================================================================


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


// =============================================================================
// Global state
// =============================================================================


let DATA_SOURCES = [];

let CURRENT_SOURCE = null;

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


// =============================================================================
// General helpers
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
// PCA axis labels
// =============================================================================


function getAxisLabel(axis) {

  const label =
    CURRENT_SOURCE
      ?.axis_labels
      ?.[axis];

  if (
    label
    && String(label).trim()
  ) {

    return String(label).trim();
  }

  return axis;
}


function readAxisLabelsFromCsv(rows) {

  if (
    !rows
    || !rows.length
  ) {

    return {};
  }


  const firstRow =
    rows[0];


  const labels = {};


  for (
    const axis
    of [
      "PC1",
      "PC2",
      "PC3"
    ]
  ) {

    const column =
      `${axis}_label`;

    const value =
      String(
        firstRow[column] ?? ""
      ).trim();


    if (
      value
      && value.toLowerCase() !== "nan"
    ) {

      labels[axis] =
        value;
    }
  }


  return labels;
}


function updateAxisLabelsFromCsv(
  rows
) {

  const csvLabels =
    readAxisLabelsFromCsv(
      rows
    );


  CURRENT_SOURCE.axis_labels = {

    ...(CURRENT_SOURCE.axis_labels ?? {}),

    ...csvLabels

  };
}


// =============================================================================
// Dataset header
// =============================================================================


function updateDatasetHeader() {

  if (!CURRENT_SOURCE) {
    return;
  }


  const axis1 =
    getAxisLabel(
      "PC1"
    );

  const axis2 =
    getAxisLabel(
      "PC2"
    );

  const axis3 =
    getAxisLabel(
      "PC3"
    );


  const eyebrow =
    document.getElementById(
      "dataset-eyebrow"
    );


  if (eyebrow) {

    eyebrow.textContent =
      `${CURRENT_SOURCE.league_name} · ${CURRENT_SOURCE.season_label}`;
  }


  const subtitle =
    document.querySelector(
      ".subtitle"
    );


  if (subtitle) {

    subtitle.textContent =
      `${axis1} · ${axis2} · ${axis3}`;
  }


  document.title =
    (
      `${CURRENT_SOURCE.league_name} `
      + `${CURRENT_SOURCE.season_label} — `
      + "3D Player Profiles"
    );
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

        pc1ObservedFeatures:
          parseNumber(
            row.PC1_observed_features
          ),

        pc1ImputedFeatures:
          parseNumber(
            row.PC1_imputed_features
          ),

        pc2ObservedFeatures:
          parseNumber(
            row.PC2_observed_features
          ),

        pc2ImputedFeatures:
          parseNumber(
            row.PC2_imputed_features
          ),

        pc3ObservedFeatures:
          parseNumber(
            row.PC3_observed_features
          ),

        pc3ImputedFeatures:
          parseNumber(
            row.PC3_imputed_features
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
// League selector
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
      (
        [id, name]
      ) => ({
        id,
        name
      })
    )

    .sort(
      (
        a,
        b
      ) =>
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
      (
        a,
        b
      ) =>
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


// =============================================================================
// Season selector
// =============================================================================


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


// =============================================================================
// Dataset selector events
// =============================================================================


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
// Clubs
// =============================================================================


function getPlayerClubs(
  player
) {

  return player.team

    .split("/")

    .map(
      item =>
        item.trim()
    )

    .filter(
      Boolean
    );
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
      of getPlayerClubs(
        player
      )
    ) {

      clubs.add(
        club
      );
    }
  }


  return [
    ...clubs
  ].sort(
    (
      a,
      b
    ) =>
      a.localeCompare(
        b
      )
  );
}


// =============================================================================
// Filters
// =============================================================================


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


function playerMatches(
  player
) {

  // --------------------------------------------------------------------------
  // Position
  // --------------------------------------------------------------------------

  if (
    FILTER_STATE.positions.size

    && !FILTER_STATE.positions.has(
      player.positionGroup
    )
  ) {

    return false;
  }


  // --------------------------------------------------------------------------
  // Club
  // --------------------------------------------------------------------------

  if (
    FILTER_STATE.clubs.size
  ) {

    const match =
      getPlayerClubs(
        player
      )

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


  // --------------------------------------------------------------------------
  // Minimum age
  // --------------------------------------------------------------------------

  if (
    FILTER_STATE.minAge !== null
  ) {

    if (
      !Number.isFinite(
        player.age
      )

      || player.age <
        FILTER_STATE.minAge
    ) {

      return false;
    }
  }


  // --------------------------------------------------------------------------
  // Maximum age
  // --------------------------------------------------------------------------

  if (
    FILTER_STATE.maxAge !== null
  ) {

    if (
      !Number.isFinite(
        player.age
      )

      || player.age >
        FILTER_STATE.maxAge
    ) {

      return false;
    }
  }


  return true;
}


// =============================================================================
// Filter panel
// =============================================================================


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
          Math.min(
            ...ages
          )
        )

      : 16;


  const maxAge =
    ages.length

      ? Math.ceil(
          Math.max(
            ...ages
          )
        )

      : 45;


  const positions = [

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
              (
                [
                  code,
                  label
                ]
              ) => `

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

      : Number(
          min
        );


  FILTER_STATE.maxAge =
    max === ""

      ? null

      : Number(
          max
        );


  updatePlotFilters();
}


function clearFilters() {

  resetFilters();

  createFilterPanel();

  updatePlotFilters();
}


// =============================================================================
// Plot filtering
// =============================================================================


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
                (
                  !active

                  || playerMatches(
                    player
                  )
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


  const counter =
    document.getElementById(
      "filter-result-count"
    );


  if (counter) {

    counter.textContent =
      active

        ? (
            `${matches} of `
            + `${ALL_PLAYERS.length} `
            + "players match"
          )

        : (
            "No filters active · "
            + `${ALL_PLAYERS.length} players`
          );
  }
}


// =============================================================================
// Plot traces
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


  const pc1Label =
    getAxisLabel(
      "PC1"
    );


  const pc2Label =
    getAxisLabel(
      "PC2"
    );


  const pc3Label =
    getAxisLabel(
      "PC3"
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

          formatInteger(
            player.age
          ),

          formatInteger(
            player.minutes
          ),

          formatInteger(
            player.pc1ObservedFeatures
          ),

          formatInteger(
            player.pc1ImputedFeatures
          ),

          formatInteger(
            player.pc2ObservedFeatures
          ),

          formatInteger(
            player.pc2ImputedFeatures
          ),

          formatInteger(
            player.pc3ObservedFeatures
          ),

          formatInteger(
            player.pc3ImputedFeatures
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

        width:
          0.3,

        color:
          "rgba(255,255,255,.55)"

      }

    },


    hovertemplate:

      "<b>%{text}</b><br>"

      +

      "%{customdata[0]} · %{customdata[1]}<br>"

      +

      "Age: %{customdata[2]}<br>"

      +

      "Minutes: %{customdata[3]}<br><br>"


      +

      "<b>PCA profile</b><br>"

      +

      `${pc1Label}: %{x:.2f}<br>`

      +

      `${pc2Label}: %{y:.2f}<br>`

      +

      `${pc3Label}: %{z:.2f}<br><br>`


      +

      "<b>Data quality</b><br>"

      +

      `${pc1Label}: %{customdata[4]} observed, %{customdata[5]} imputed<br>`

      +

      `${pc2Label}: %{customdata[6]} observed, %{customdata[7]} imputed<br>`

      +

      `${pc3Label}: %{customdata[8]} observed, %{customdata[9]} imputed<br>`

      +

      "Overall: %{customdata[10]} observed, %{customdata[11]} imputed"

      +

      "<extra></extra>"

  };
}


// =============================================================================
// Plot
// =============================================================================


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


  const pc1Label =
    getAxisLabel(
      "PC1"
    );


  const pc2Label =
    getAxisLabel(
      "PC2"
    );


  const pc3Label =
    getAxisLabel(
      "PC3"
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

      l:
        0,

      r:
        0,

      b:
        0,

      t:
        20

    },


    scene: {

      bgcolor:
        "#11151a",


      // -----------------------------------------------------------------------
      // X = PC1
      // -----------------------------------------------------------------------

      xaxis: {

        ...axisCommon,

        title: {

          text:
            pc1Label

        }

      },


      // -----------------------------------------------------------------------
      // Y = PC2
      // -----------------------------------------------------------------------

      yaxis: {

        ...axisCommon,

        title: {

          text:
            pc2Label

        }

      },


      // -----------------------------------------------------------------------
      // Z = PC3
      // -----------------------------------------------------------------------

      zaxis: {

        ...axisCommon,

        title: {

          text:
            pc3Label

        }

      },


      camera: {

        eye: {

          x:
            1.55,

          y:
            1.55,

          z:
            1.15

        },


        up: {

          x:
            0,

          y:
            0,

          z:
            1

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
      (
        CURRENT_SOURCE?.id
        ?? "pca"
      )

  };


  await Plotly.newPlot(

    "player-cloud",

    traces,

    layout,

    {

      responsive:
        true,

      displaylogo:
        false,

      scrollZoom:
        true

    }

  );
}


// =============================================================================
// CSV loading
// =============================================================================


function parseCsv(
  url
) {

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


// =============================================================================
// Dataset loading
// =============================================================================


async function loadSource(
  source
) {

  CURRENT_SOURCE =
    source;


  resetFilters();


  const status =
    document.getElementById(
      "status"
    );


  const filterPanel =
    document.getElementById(
      "filter-panel"
    );


  if (filterPanel) {

    filterPanel.hidden =
      true;

    filterPanel.innerHTML =
      "";
  }


  status.textContent =
    (
      `Loading ${source.league_name}`
      + ` · ${source.season_label}…`
    );


  const result =
    await parseCsv(

      `${source.path}?v=${
        encodeURIComponent(
          source.modified ?? Date.now()
        )
      }`

    );


  if (
    !result.data
    || !result.data.length
  ) {

    throw new Error(

      `No player data found for `
      + `${source.league_name} `
      + `${source.season_label}.`

    );
  }


  // --------------------------------------------------------------------------
  // Axis labels
  // --------------------------------------------------------------------------
  //
  // Primary source:
  //     data_sources.json -> source.axis_labels
  //
  // Fallback:
  //     PC1_label / PC2_label / PC3_label in the PCA CSV
  //
  // --------------------------------------------------------------------------

  updateAxisLabelsFromCsv(
    result.data
  );


  // --------------------------------------------------------------------------
  // Players
  // --------------------------------------------------------------------------

  ALL_PLAYERS =
    preparePlayers(
      result.data
    );


  if (!ALL_PLAYERS.length) {

    throw new Error(

      `No valid PCA player rows found for `
      + `${source.league_name} `
      + `${source.season_label}.`

    );
  }


  // --------------------------------------------------------------------------
  // Update page text
  // --------------------------------------------------------------------------

  updateDatasetHeader();


  // --------------------------------------------------------------------------
  // Rebuild filters
  // --------------------------------------------------------------------------

  createFilterPanel();


  // --------------------------------------------------------------------------
  // Draw plot
  // --------------------------------------------------------------------------

  await renderPlot();


  // --------------------------------------------------------------------------
  // Position counts
  // --------------------------------------------------------------------------

  const positionCounts = {

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
    const player
    of ALL_PLAYERS
  ) {

    positionCounts[
      player.positionGroup
    ] += 1;
  }


  status.textContent =
    (
      `${source.league_name}`
      + ` · ${source.season_label}`
      + ` · ${ALL_PLAYERS.length} players`
      + ` · ${positionCounts.GK} GK`
      + ` · ${positionCounts.DF} DF`
      + ` · ${positionCounts.MF} MF`
      + ` · ${positionCounts.FW} FW`
    );


  // --------------------------------------------------------------------------
  // Store selected dataset in URL
  // --------------------------------------------------------------------------

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
// Manifest loading
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


  // --------------------------------------------------------------------------
  // League selector
  // --------------------------------------------------------------------------

  populateLeagueSelector();


  // --------------------------------------------------------------------------
  // Read requested source from URL
  // --------------------------------------------------------------------------

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


  // --------------------------------------------------------------------------
  // Season selector
  // --------------------------------------------------------------------------

  const sources =
    populateSeasonSelector(

      initialLeague,

      requestedSeason

    );


  if (!sources.length) {

    throw new Error(

      `No prepared seasons found for ${initialLeague}.`

    );
  }


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


  // --------------------------------------------------------------------------
  // Events
  // --------------------------------------------------------------------------

  document

    .getElementById(
      "league-select"
    )

    .addEventListener(
      "change",
      handleLeagueChange
    );


  document

    .getElementById(
      "season-select"
    )

    .addEventListener(
      "change",
      handleSeasonChange
    );


  // --------------------------------------------------------------------------
  // Initial dataset
  // --------------------------------------------------------------------------

  await loadSource(
    initialSource
  );
}


// =============================================================================
// Error display
// =============================================================================


function showError(
  error
) {

  console.error(
    error
  );


  const message =
    (
      error instanceof Error
    )

      ? error.message

      : String(
          error
        );


  const status =
    document.getElementById(
      "status"
    );


  if (status) {

    status.textContent =
      message;
  }


  const chart =
    document.getElementById(
      "player-cloud"
    );


  if (chart) {

    chart.innerHTML = `

      <div class="error">

        ${escapeHtml(message)}

      </div>

    `;
  }
}


// =============================================================================
// Start
// =============================================================================


loadManifest()

  .catch(
    showError
  );