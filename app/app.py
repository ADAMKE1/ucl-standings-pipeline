"""
Application Streamlit : classement de la phase de ligue de la Ligue des Champions 2024-25,
reconstruit journée par journée par le pipeline (API-Football → BigQuery → dbt, orchestré par Airflow).

Lancer depuis la racine du repo :  streamlit run app/app.py
"""
import os
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
SNAPSHOT_DIR = APP_DIR / "data"
PROJECT = "ucl-pipeline"

# Zones de qualification de la phase de ligue (format 2024-25)
ZONES = [
    (1, 8, "Huitièmes de finale", "#d9f2e3"),
    (9, 24, "Barrages", "#fff1cc"),
    (25, 36, "Éliminé", "#eeeeee"),
]


def zone_of(rank: int) -> str:
    for low, high, label, _ in ZONES:
        if low <= rank <= high:
            return label
    return ""


ZONE_COLORS = {label: color for _, _, label, color in ZONES}

st.set_page_config(page_title="UCL 2024-25 · Classement", page_icon="⚽", layout="wide")


# ---------------------------------------------------------------- données
@st.cache_data(show_spinner="Chargement des données…")
def load_data():
    """Lit les tables dbt dans BigQuery. Si BigQuery est injoignable (pas d'internet,
    tables expirées…), utilise le dernier instantané CSV enregistré dans app/data/."""
    try:
        from dotenv import load_dotenv
        from google.cloud import bigquery

        load_dotenv(APP_DIR.parent / ".env")
        client = bigquery.Client(project=os.environ.get("GCP_PROJECT_ID", PROJECT))
        standings = client.query(
            f"SELECT * FROM `{PROJECT}.ucl_dbt.fct_standings_by_matchday`"
        ).to_dataframe()
        matches = client.query(f"SELECT * FROM `{PROJECT}.ucl_dbt.stg_matches`").to_dataframe()
        source = "BigQuery (en direct)"
        try:  # on rafraîchit l'instantané à chaque lecture réussie
            SNAPSHOT_DIR.mkdir(exist_ok=True)
            standings.to_csv(SNAPSHOT_DIR / "standings.csv", index=False)
            matches.to_csv(SNAPSHOT_DIR / "matches.csv", index=False)
        except OSError:
            pass
    except Exception:
        standings = pd.read_csv(SNAPSHOT_DIR / "standings.csv")
        matches = pd.read_csv(SNAPSHOT_DIR / "matches.csv")
        source = "Instantané CSV (BigQuery injoignable)"

    standings["zone"] = standings["rank"].map(zone_of)
    return standings, matches, source


try:
    standings, matches, source = load_data()
except FileNotFoundError:
    st.error(
        "Impossible de lire BigQuery, et aucun instantané CSV n'existe encore. "
        "Lance l'application une première fois avec accès à BigQuery."
    )
    st.stop()

last_md = int(standings["matchday"].max())
final = standings[standings["matchday"] == last_md].sort_values("rank")

# ---------------------------------------------------------------- en-tête
st.title("Ligue des Champions 2024-25 — le classement, journée par journée")
st.caption(
    "L'API ne fournit que le classement final. Ce pipeline le reconstruit après chacune des "
    "8 journées : API-Football → Python → BigQuery → dbt (19 tests) → orchestré par Airflow."
)

total_goals = int(matches["home_goals"].sum() + matches["away_goals"].sum())
c1, c2, c3, c4 = st.columns(4)
c1.metric("Matchs", len(matches))
c2.metric("Équipes", standings["team_id"].nunique())
c3.metric("Buts", total_goals)
c4.metric("Buts par match", f"{total_goals / len(matches):.2f}")

tab_class, tab_evol, tab_moves, tab_home, tab_goals = st.tabs(
    ["Classement", "Évolution du rang", "Remontées et chutes", "Domicile / extérieur", "Buts"]
)

# ---------------------------------------------------------------- 1. classement à une journée
with tab_class:
    md = st.slider("Classement après la journée", 1, last_md, last_md)
    table = standings[standings["matchday"] == md].sort_values(["rank", "team_name"])
    table = table[
        ["rank", "team_name", "matches_played", "points_cumul", "goal_diff_cumul", "goals_for_cumul", "zone"]
    ].rename(
        columns={
            "rank": "Rang",
            "team_name": "Équipe",
            "matches_played": "MJ",
            "points_cumul": "Pts",
            "goal_diff_cumul": "Diff.",
            "goals_for_cumul": "BP",
            "zone": "Zone",
        }
    )
    markers = {"Huitièmes de finale": "🟢", "Barrages": "🟡", "Éliminé": "⚪"}
    table["Zone"] = table["Zone"].map(lambda z: f"{markers.get(z, '')} {z}")
    st.dataframe(table, hide_index=True, width="stretch", height=36 * 35 + 38)
    st.caption(
        "Départage : points, différence de buts, buts marqués. Le règlement UEFA utilise davantage "
        "de critères : deux équipes à égalité parfaite peuvent être inversées par rapport au classement officiel. "
        "Les points et la différence de buts, eux, sont vérifiés par un test dbt contre le classement officiel."
    )

# ---------------------------------------------------------------- 2. évolution du rang
with tab_evol:
    default_teams = final["team_name"].head(4).tolist()
    teams = st.multiselect(
        "Équipes à comparer", sorted(standings["team_name"].unique()), default=default_teams
    )
    if teams:
        sel = standings[standings["team_name"].isin(teams)]
        bands = pd.DataFrame(
            [{"from": low - 0.5, "to": high + 0.5, "zone": label} for low, high, label, _ in ZONES]
        )
        band_layer = (
            alt.Chart(bands)
            .mark_rect(opacity=0.5)
            .encode(
                y=alt.Y("from:Q", scale=alt.Scale(reverse=True, domain=[0.5, 36.5])),
                y2="to:Q",
                color=alt.Color(
                    "zone:N",
                    scale=alt.Scale(domain=list(ZONE_COLORS), range=list(ZONE_COLORS.values())),
                    legend=alt.Legend(title="Zone"),
                ),
            )
        )
        lines = (
            alt.Chart(sel)
            .mark_line(point=True, strokeWidth=2.5)
            .encode(
                x=alt.X("matchday:O", title="Journée"),
                y=alt.Y("rank:Q", title="Rang", scale=alt.Scale(reverse=True, domain=[0.5, 36.5])),
                detail="team_name:N",
                strokeDash=alt.StrokeDash("team_name:N", legend=alt.Legend(title="Équipe")),
                tooltip=[
                    alt.Tooltip("team_name:N", title="Équipe"),
                    alt.Tooltip("matchday:O", title="Journée"),
                    alt.Tooltip("rank:Q", title="Rang"),
                    alt.Tooltip("points_cumul:Q", title="Points"),
                ],
            )
        )
        labels = (
            alt.Chart(sel[sel["matchday"] == last_md])
            .mark_text(align="left", dx=8, fontSize=12)
            .encode(x="matchday:O", y=alt.Y("rank:Q", scale=alt.Scale(reverse=True)), text="team_name:N")
        )
        st.altair_chart((band_layer + lines + labels).properties(height=520), width="stretch")
    else:
        st.info("Choisis au moins une équipe.")

    st.subheader("Le leader après chaque journée")
    leaders = (
        standings[standings["rank"] == 1]
        .groupby("matchday")
        .agg(Leader=("team_name", lambda s: " / ".join(sorted(s))), Points=("points_cumul", "max"))
        .reset_index()
        .rename(columns={"matchday": "Journée"})
    )
    st.dataframe(leaders, hide_index=True, width="stretch")

# ---------------------------------------------------------------- 3. remontées et chutes
with tab_moves:
    col_a, col_b = st.columns(2)
    md_from = col_a.selectbox("De la journée", list(range(1, last_md + 1)), index=min(3, last_md - 1))
    md_to = col_b.selectbox("À la journée", list(range(1, last_md + 1)), index=last_md - 1)
    if md_from >= md_to:
        st.warning("Choisis une journée de départ antérieure à la journée d'arrivée.")
    else:
        a = standings[standings["matchday"] == md_from][["team_name", "rank"]]
        b = standings[standings["matchday"] == md_to][["team_name", "rank"]]
        moves = a.merge(b, on="team_name", suffixes=("_from", "_to"))
        moves["places"] = moves["rank_from"] - moves["rank_to"]  # positif = remontée
        top = pd.concat(
            [moves.nlargest(6, "places"), moves.nsmallest(6, "places")]
        ).drop_duplicates("team_name")
        top["sens"] = top["places"].map(lambda p: "Remontée" if p > 0 else "Chute")
        chart = (
            alt.Chart(top)
            .mark_bar()
            .encode(
                x=alt.X("places:Q", title=f"Places gagnées entre la J{md_from} et la J{md_to}"),
                y=alt.Y("team_name:N", sort="-x", title=None),
                color=alt.Color(
                    "sens:N",
                    scale=alt.Scale(domain=["Remontée", "Chute"], range=["#2e8b57", "#c0392b"]),
                    legend=None,
                ),
                tooltip=[
                    alt.Tooltip("team_name:N", title="Équipe"),
                    alt.Tooltip("rank_from:Q", title=f"Rang J{md_from}"),
                    alt.Tooltip("rank_to:Q", title=f"Rang J{md_to}"),
                    alt.Tooltip("places:Q", title="Places"),
                ],
            )
            .properties(height=420)
        )
        st.altair_chart(chart, width="stretch")

# ---------------------------------------------------------------- 4. domicile / extérieur
with tab_home:
    m = matches.copy()
    m["Résultat"] = "Match nul"
    m.loc[m["home_goals"] > m["away_goals"], "Résultat"] = "Victoire à domicile"
    m.loc[m["home_goals"] < m["away_goals"], "Résultat"] = "Victoire à l'extérieur"
    counts = m["Résultat"].value_counts().rename_axis("Résultat").reset_index(name="Matchs")
    counts["Part"] = counts["Matchs"] / counts["Matchs"].sum()
    order = ["Victoire à domicile", "Match nul", "Victoire à l'extérieur"]
    chart = (
        alt.Chart(counts)
        .mark_bar()
        .encode(
            x=alt.X("Résultat:N", sort=order, title=None),
            y=alt.Y("Matchs:Q"),
            color=alt.Color(
                "Résultat:N", scale=alt.Scale(domain=order, range=["#1f5fa8", "#9aa5b1", "#d9822b"]), legend=None
            ),
            tooltip=["Résultat", "Matchs", alt.Tooltip("Part:Q", format=".0%")],
        )
        .properties(height=360)
    )
    left, right = st.columns([2, 1])
    left.altair_chart(chart, width="stretch")
    right.metric("Buts par match à domicile", f"{m['home_goals'].mean():.2f}")
    right.metric("Buts par match à l'extérieur", f"{m['away_goals'].mean():.2f}")
    home_share = (m["Résultat"] == "Victoire à domicile").mean()
    right.metric("Victoires à domicile", f"{home_share:.0%}")

# ---------------------------------------------------------------- 5. buts
with tab_goals:
    g = matches.assign(buts=matches["home_goals"] + matches["away_goals"])
    per_md = g.groupby("matchday")["buts"].agg(["sum", "mean"]).reset_index()
    per_md.columns = ["Journée", "Buts", "Buts par match"]
    chart = (
        alt.Chart(per_md)
        .mark_bar(color="#1f5fa8")
        .encode(
            x=alt.X("Journée:O"),
            y=alt.Y("Buts:Q"),
            tooltip=["Journée", "Buts", alt.Tooltip("Buts par match:Q", format=".2f")],
        )
        .properties(height=340)
    )
    st.altair_chart(chart, width="stretch")

    st.subheader("Les matchs les plus prolifiques")
    biggest = g.sort_values(["buts", "matchday"], ascending=[False, True]).head(5)
    biggest = biggest.assign(
        Match=biggest["home_team_name"] + " " + biggest["home_goals"].astype(str) + " - "
        + biggest["away_goals"].astype(str) + " " + biggest["away_team_name"]
    )[["matchday", "Match", "buts"]].rename(columns={"matchday": "Journée", "buts": "Buts"})
    st.dataframe(biggest, hide_index=True, width="stretch")

st.sidebar.markdown("### Source des données")
st.sidebar.write(source)
st.sidebar.markdown(
    "### Le pipeline\n"
    "1. **Ingestion** : Python interroge API-Football, une semaine à la fois.\n"
    "2. **Stockage brut** : une table BigQuery par semaine, écrasée à chaque chargement (idempotent).\n"
    "3. **Transformation** : 3 modèles dbt (staging → intermediate → mart).\n"
    "4. **Qualité** : 19 tests dbt, dont une comparaison avec le classement officiel.\n"
    "5. **Orchestration** : DAG Airflow hebdomadaire, saison rejouée par backfill."
)
