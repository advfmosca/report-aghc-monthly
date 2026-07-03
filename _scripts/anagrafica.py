"""Anagrafica 18 clienti AGHC — fonte di verità per il generatore mensile.

Aggiornamento 25/04/2026: aggiunto MONTEMAGNO in posizione alfabetica 14
(account Meta `Tenuta Montemagno Relais`, ID 752450855779035, MoM, budget TBD).

Campi per ogni cliente:
  meta_account_id   : str | None        → ID account Meta (Windsor.ai connector "facebook")
  meta_filter       : (op, keyword) | None → filtro campagna per account condivisi
  meta_filter_extra : list[str]         → keyword addizionali in OR (es. "MICE" per Adèsso 2025)
  tiktok_account_id : str | None        → ID account TikTok (può essere None se non gestito)
  confronto_meta    : "YoY" | "MoM"     → default confronto Meta
  confronto_tiktok  : "YoY" | "MoM" | None
  budget_annuo      : float             → budget annuo € (per calcolo % speso)
  note              : str               → note operative
"""

# Pesi mensili normalizzati del budget annuo (% del budget annuo)
BUDGET_WEIGHTS = {
    1: 3, 2: 3, 3: 5, 4: 10, 5: 15, 6: 15,
    7: 12, 8: 12, 9: 5, 10: 5, 11: 5, 12: 10,
}
# Split budget su clienti multi-canale: 80% Meta, 20% TikTok
META_SHARE = 0.80
TIKTOK_SHARE = 0.20

CLIENTS = [
    {
        "nome": "Altafiumara",
        "meta_account_id": "1201395876543423",
        "meta_filter": None,
        "meta_filter_extra": [],
        "tiktok_account_id": None,
        "confronto_meta": "MoM",
        "confronto_tiktok": None,
        "budget_annuo": 23000,
        "note": "",
    },
    {
        "nome": "Castello",
        "meta_account_id": "1489903155429629",
        "meta_filter": None,
        "meta_filter_extra": [],
        "tiktok_account_id": None,
        "confronto_meta": "MoM",
        "confronto_tiktok": None,
        "budget_annuo": 14400,
        "note": "",
    },
    {
        "nome": "Della Piana",
        "meta_account_id": "911357333863123",
        "meta_filter": None,
        "meta_filter_extra": [],
        "tiktok_account_id": "7504967007843319824",  # Napoleone Ristorante New Srl
        "confronto_meta": "YoY",
        "confronto_tiktok": "MoM",
        "budget_annuo": 14000,
        "note": "Split confronto: Meta YoY, TikTok MoM",
    },
    {
        "nome": "Hannah",
        "meta_account_id": "1528485957725509",  # Hannah Hotels Collection (condiviso)
        "meta_filter": ("contains_excl", ("Hannah", "Terraces")),
        "meta_filter_extra": [],
        "tiktok_account_id": None,
        "confronto_meta": "YoY",
        "confronto_tiktok": None,
        "budget_annuo": 9000,
        "note": "",
    },
    {
        "nome": "Hannah Terraces",
        "meta_account_id": "1528485957725509",  # Hannah Hotels Collection (condiviso)
        "meta_filter": ("contains", "Terraces"),
        "meta_filter_extra": [],
        "tiktok_account_id": None,
        "confronto_meta": "MoM",
        "confronto_tiktok": None,
        "budget_annuo": 7200,
        "note": "",
    },
    {
        "nome": "Hemanaire",
        "meta_account_id": "217115315497718",  # CW CM 2020 - AP
        "meta_filter": None,
        "meta_filter_extra": [],
        "tiktok_account_id": None,  # presente ma non attivo
        "confronto_meta": "MoM",
        "confronto_tiktok": None,
        "budget_annuo": 15000,
        "note": "TikTok verrà attivato più avanti",
    },
    {
        "nome": "Livata",
        "meta_account_id": "4666471140299701",
        "meta_filter": None,
        "meta_filter_extra": [],
        "tiktok_account_id": None,
        "confronto_meta": "MoM",
        "confronto_tiktok": None,
        "budget_annuo": 15000,
        "note": "",
    },
    {
        "nome": "Lunetta",
        "meta_account_id": "687349689221880",
        "meta_filter": None,
        "meta_filter_extra": [],
        "tiktok_account_id": "7498330316248203280",  # Sigea S.R.L.
        "confronto_meta": "YoY",
        "confronto_tiktok": "MoM",
        "budget_annuo": 18000,
        "note": "Split confronto: Meta YoY, TikTok MoM",
    },
    {
        "nome": "Magari Estates",
        "meta_account_id": "1372615496521110",
        "meta_filter": None,
        "meta_filter_extra": [],
        "tiktok_account_id": None,  # presente ma non attivo
        "confronto_meta": "MoM",
        "confronto_tiktok": None,
        "budget_annuo": 24600,
        "note": "",
    },
    {
        "nome": "Marcella Royal",
        "meta_account_id": "821188209852436",  # MARCELLA ROYAL (condiviso)
        "meta_filter": ("contains_ci", "Marcella"),
        "meta_filter_extra": [],
        "tiktok_account_id": "7499093699838607377",  # La Carlina Srl
        "confronto_meta": "YoY",
        "confronto_tiktok": "MoM",
        "budget_annuo": 14400,
        "note": "Split confronto: Meta YoY, TikTok MoM",
    },
    {
        "nome": "Mare",
        "meta_account_id": "1432341844596179",
        "meta_filter": None,
        "meta_filter_extra": [],
        "tiktok_account_id": "7498679494010667009",  # F.LLI TIRANINI SRL
        "confronto_meta": "MoM",
        "confronto_tiktok": "MoM",
        "budget_annuo": 15000,
        "note": "",
    },
    {
        "nome": "Montemagno",
        "meta_account_id": "752450855779035",  # Tenuta Montemagno Relais
        "meta_filter": None,
        "meta_filter_extra": [],
        "tiktok_account_id": None,
        "confronto_meta": "MoM",
        "confronto_tiktok": None,
        "budget_annuo": 0,  # TBD — placeholder. Aggiornare quando definito.
        "note": "Aggiunto 25/04/2026 — budget annuo da definire (TBD).",
    },
    {
        "nome": "Puntebianche Resort",
        "meta_account_id": "1528485957725509",  # Hannah Hotels Collection (condiviso)
        "meta_filter": ("contains", "Puntebianche"),
        "meta_filter_extra": [],
        "tiktok_account_id": None,
        "confronto_meta": "MoM",
        "confronto_tiktok": None,
        "budget_annuo": 0,  # TBD — placeholder. Aggiornare quando definito.
        "note": "Aggiunto 02/07/2026 — campagne 'Puntebianche - AON' su account condiviso Hannah Hotels Collection (1528485957725509). Le ads NON rientrano in Hannah (filtro 'Hannah'). Budget annuo TBD.",
    },
    {
        "nome": "Terrazza Flavia",
        "meta_account_id": "821188209852436",  # MARCELLA ROYAL (condiviso)
        "meta_filter": ("contains_ci", "Terrazza"),
        "meta_filter_extra": [],
        "tiktok_account_id": None,
        "confronto_meta": "YoY",
        "confronto_tiktok": None,
        "budget_annuo": 7500,
        "note": "",
    },
    {
        "nome": "Villa Ermellina",
        "meta_account_id": "30233607946222961",
        "meta_filter": None,
        "meta_filter_extra": [],
        "tiktok_account_id": "7612666695502118929",  # Villa Ermellina Siena
        "confronto_meta": "MoM",
        "confronto_tiktok": "MoM",
        "budget_annuo": 16400,
        "note": "",
    },
    {
        "nome": "Villa Giada",
        "meta_account_id": "1849759899186169",
        "meta_filter": None,
        "meta_filter_extra": [],
        "tiktok_account_id": "7626418949391351815",  # attivo da Maggio 2026 (1° mese live)
        "confronto_meta": "MoM",
        "confronto_tiktok": "MoM",
        "budget_annuo": 21600,
        "note": "",
    },
    {
        "nome": "Villa Miliani",
        "meta_account_id": "1353024533007038",
        "meta_filter": None,
        "meta_filter_extra": [],
        "tiktok_account_id": None,
        "confronto_meta": "MoM",
        "confronto_tiktok": None,
        "budget_annuo": 6600,
        "note": "",
    },
]


def period_range(year: int, month: int) -> tuple[str, str]:
    """Ritorna (date_from, date_to) ISO per il mese dato."""
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    return f"{year:04d}-{month:02d}-01", f"{year:04d}-{month:02d}-{last_day:02d}"


def comparison_period(year: int, month: int, tipo: str) -> tuple[int, int]:
    """Ritorna (year, month) del periodo di confronto dato 'YoY' o 'MoM'."""
    if tipo == "YoY":
        return year - 1, month
    if tipo == "MoM":
        if month == 1:
            return year - 1, 12
        return year, month - 1
    raise ValueError(f"Tipo confronto sconosciuto: {tipo}")


MONTH_IT = {
    1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile",
    5: "Maggio", 6: "Giugno", 7: "Luglio", 8: "Agosto",
    9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre",
}
