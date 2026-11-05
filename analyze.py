"""Capital investments in Ukraine: who pays (2015-2019) and what is financed (2010-2025).

Source: State Statistics Service of Ukraine (stat.gov.ua), data bank,
dataset "Capital investments (annual)". All values are NOMINAL (current prices, UAH).

Run:  python analyze.py
"""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

RAW = Path("data/raw/capital_investments_raw.csv")
CHARTS = Path("charts"); CHARTS.mkdir(exist_ok=True)
YEARS = [str(y) for y in range(2010, 2026)]
BLUE, ORANGE, GREY = "#1f5fbf", "#e07b00", "#8a8f98"

# ---------------------------------------------------------------- 1. load
df = pd.read_csv(RAW)
df.columns = [c.strip() for c in df.columns]          # remove stray spaces
df["Розріз"] = (df["Розріз"].str.replace("\xa0", " ", regex=False)
                .str.replace(r"\s+", " ", regex=True).str.strip())  # non-breaking & double spaces
# values are in thousands of UAH -> convert to billions
df[YEARS] = df[YEARS] / 1e6
df = df[df["Показник"] == "Обсяг капітальних інвестицій"]
df = df[df["Вид економічної діяльності"] == "Усього"]   # all industries together
country = df[df["Територіальний розріз"] == "Україна"]


def series(frame, **filters):
    for col, val in filters.items():
        frame = frame[frame[col] == val]
    return frame


def stacked_share(ax, shares, colors, title):
    shares.T.plot(kind="bar", stacked=True, ax=ax, color=colors, width=.75)
    ax.set_title(title, loc="left", fontsize=11, fontweight="bold")
    ax.set_ylabel("% від загальної суми"); ax.set_xlabel("")
    ax.legend(frameon=False, fontsize=8, bbox_to_anchor=(1.01, 1), loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    plt.setp(ax.get_xticklabels(), rotation=0)


# ---------------------------------------------------------------- 2. who pays (2015-2019)
src = series(country, **{"Категорія розрізу": "Джерела фінансування",
                         "Витрати на придбання активів": "Загалом"})
src = src[src["Розріз"] != "Усього"].set_index("Розріз")[YEARS[5:10]]
groups = {
    "Власні кошти підприємств": ["Власні кошти підприємств та організацій"],
    "Кредити банків (українських)": ["Кредити банків та інші позики"],
    "Державний + місцеві бюджети": ["Кошти державного бюджету", "Кошти місцевих бюджетів"],
    "Населення (житло)": ["Кошти населення на будівництво житла"],
    "Іноземні кошти (інвестори + банки)": ["Кошти інвесторів-нерезидентів", "Кредити банків-нерезидентів"],
    "Інше": ["Інші джерела фінансування", "Кошти інвестиційних компаній, фондів тощо"],
}
grouped = pd.DataFrame({k: src.loc[v].sum() for k, v in groups.items()}).T
who_pays = (grouped / grouped.sum() * 100).round(1)
budgets = (src.loc[["Кошти державного бюджету", "Кошти місцевих бюджетів"]].sum() / src.sum() * 100).round(1)

fig, ax = plt.subplots(figsize=(9, 4.5))
stacked_share(ax, who_pays, ["#1f5fbf", "#e07b00", "#2e8b57", "#b04a9b", "#8a8f98", "#d1d5db"],
              "Хто фінансує капітальні інвестиції, 2015–2019 (% від загальної суми)")
fig.tight_layout(); fig.savefig(CHARTS / "1_who_pays_2015_2019.png", dpi=150); plt.close(fig)

# ---------------------------------------------------------------- 3. total volume 2010-2025
total = series(country, **{"Категорія розрізу": "Загалом", "Витрати на придбання активів": "Загалом"})[YEARS].iloc[0]
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.bar(total.index, total.values, color=[GREY if int(y) < 2022 else BLUE for y in total.index])
for x, v in zip(total.index, total.values):
    ax.text(x, v + 10, f"{v:.0f}", ha="center", fontsize=8)
ax.set_title("Капітальні інвестиції в Україні, млрд грн (поточні ціни, без поправки на інфляцію)",
             loc="left", fontsize=11, fontweight="bold")
ax.set_ylabel("млрд грн"); ax.spines[["top", "right"]].set_visible(False)
plt.setp(ax.get_xticklabels(), rotation=45)
fig.tight_layout(); fig.savefig(CHARTS / "2_total_2010_2025.png", dpi=150); plt.close(fig)

# ---------------------------------------------------------------- 4. what money buys (war years)
assets = series(country, **{"Категорія розрізу": "Види активів"})
spend = assets[assets["Розріз"] == "Усього"].set_index("Витрати на придбання активів")[YEARS[5:]]
spend_rows = {
    "Нові активи": "Витрати на придбання та створення нових активів",
    "Модернізація / реконструкція": "Витрати на поліпшення, вдосконалення, реконструкцію, модернізацію",
    "Капітальний ремонт": "Витрати на капітальний ремонт",
    "Куплені вживані активи": "Витрати на придбання активів, які були у використанні",
}
sp = pd.DataFrame({k: spend.loc[v] for k, v in spend_rows.items()}).T
spend_share = (sp / sp.sum() * 100).round(1)
fig, ax = plt.subplots(figsize=(9, 4.5))
stacked_share(ax, spend_share, ["#1f5fbf", "#2e8b57", "#e07b00", "#8a8f98"],
              "На що йдуть капітальні інвестиції, 2015–2025 (% від суми)")
fig.tight_layout(); fig.savefig(CHARTS / "3_spend_type_2015_2025.png", dpi=150); plt.close(fig)

# ---------------------------------------------------------------- 5. asset structure, before vs during war
types = assets[(assets["Витрати на придбання активів"] == "Загалом")].set_index("Розріз")[YEARS]
keep = {"Машини й обладнання": "Машини, обладнання та інвентар",
        "Нежитлові будівлі": "Нежитлові будівлі",
        "Інженерні споруди": "Інженерні споруди",
        "Житло": "Житлові будинки",
        "Транспорт": "Транспортні засоби"}
at = pd.DataFrame({k: types.loc[v] for k, v in keep.items()}).T
tot_assets = spend.drop(index="Загалом", errors="ignore").sum()  # the 4 expense types add up to the total (the "Усього/Загалом" row is empty after 2019)
asset_share = (at / tot_assets * 100).round(1)[["2019", "2021", "2022", "2023", "2024", "2025"]]
fig, ax = plt.subplots(figsize=(9, 4.5))
asset_share.T.plot(kind="bar", ax=ax, width=.8,
                   color=["#1f5fbf", "#e07b00", "#2e8b57", "#b04a9b", "#8a8f98"])
ax.set_title("Частка основних видів активів у капітальних інвестиціях (%)", loc="left", fontsize=11, fontweight="bold")
ax.set_ylabel("% від загальної суми"); ax.legend(frameon=False, fontsize=8, ncol=3)
ax.spines[["top", "right"]].set_visible(False); plt.setp(ax.get_xticklabels(), rotation=0)
fig.tight_layout(); fig.savefig(CHARTS / "4_asset_types.png", dpi=150); plt.close(fig)

# ---------------------------------------------------------------- 6. regions: growth 2025 vs 2021
oblasts = series(df, **{"Категорія розрізу": "Джерела фінансування"})["Територіальний розріз"].unique()
oblasts = [o for o in oblasts if o != "Україна"]
reg = df[(df["Територіальний розріз"].isin(oblasts)) & (df["Категорія розрізу"] == "Загалом")
         & (df["Витрати на придбання активів"] == "Загалом")].set_index("Територіальний розріз")
reg_growth = (reg["2025"] / reg["2021"]).dropna().sort_values()
fig, ax = plt.subplots(figsize=(8, 7))
ax.barh(reg_growth.index, reg_growth.values, color=[BLUE if v >= 1 else ORANGE for v in reg_growth.values])
ax.axvline(1, color="black", lw=.8)
ax.set_xlabel("2025 до 2021, у разів")
ax.set_title("Зміна капітальних інвестицій по областях: 2025 рік порівняно з 2021-м\n(у скільки разів більше або менше, поточні ціни; 1 = без змін)",
             loc="left", fontsize=11, fontweight="bold")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig(CHARTS / "5_regions_2025_vs_2021.png", dpi=150); plt.close(fig)

# ---------------------------------------------------------------- 7. print key numbers
print("\n== WHO PAYS, % (2015-2019) ==\n", who_pays.to_string())
print("\n== State+local budgets share, % ==\n", budgets.to_string())
print("\n== TOTAL, UAH bn ==\n", total.round(0).to_string())
print("\n== SPEND TYPE, % ==\n", spend_share.to_string())
print("\n== ASSET TYPES, % ==\n", asset_share.to_string())
print("\n== REGIONS 2025/2021 (x) ==\n", reg_growth.round(2).to_string())
who_pays.to_csv("data/who_pays_2015_2019.csv"); total.to_csv("data/total_2010_2025.csv")
spend_share.to_csv("data/spend_type_2015_2025.csv"); asset_share.to_csv("data/asset_types.csv")
reg_growth.to_csv("data/regions_2025_vs_2021.csv")
