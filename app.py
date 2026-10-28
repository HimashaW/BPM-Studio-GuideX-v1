"""BPM Studio - internal BPM automation platform. First tool: GuideX (Service Delivery Guide Generator).

Run locally:   streamlit run app.py
Deploy:        see README.md ("Hosting").

UI only: the generation logic lives in app_service.py / pipeline_core.py and is unchanged.
"""
from __future__ import annotations

import datetime
import hashlib

import streamlit as st

import app_service as svc
from render.task_flow import load_flow_rules

PLATFORM = "BPM Studio"
PLATFORM_TAGLINE = "From Process to Possibilities"
TOOL = "GuideX"
TOOL_DESC = "Service Delivery Guide Generator"
VERSION = "v1.0"

st.set_page_config(page_title=f"{PLATFORM} · {TOOL}", page_icon=":material/hexagon:", layout="wide",
                   initial_sidebar_state="expanded")


# ------------------------------------------------------------------ logos ---
def bpm_logo(size=40) -> str:
    """Hexagon overlapping a circle: raw information + continuous process."""
    return f'''<svg width="{size}" height="{size}" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-label="BPM Studio logo">
<defs><linearGradient id="bpmH" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0879D9"/><stop offset="1" stop-color="#00A6B2"/></linearGradient>
<linearGradient id="bpmC" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#00A6B2"/><stop offset="1" stop-color="#19C995"/></linearGradient></defs>
<polygon points="17,4 30,11.5 30,26.5 17,34 4,26.5 4,11.5" fill="url(#bpmH)"/>
<circle cx="30" cy="29" r="13" fill="url(#bpmC)" fill-opacity=".9" stroke="#fff" stroke-width="1.6"/></svg>'''


def guidex_icon(size=44) -> str:
    """Document with a forward arrow."""
    return f'''<svg width="{size}" height="{size}" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-label="GuideX icon">
<defs><linearGradient id="gxG" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#00A6B2"/><stop offset="1" stop-color="#0879D9"/></linearGradient></defs>
<rect width="48" height="48" rx="12" fill="url(#gxG)"/>
<path d="M15 9h13l8 8v21a2 2 0 0 1-2 2H15a2 2 0 0 1-2-2V11a2 2 0 0 1 2-2z" fill="#fff"/>
<path d="M28 9v8h8z" fill="#BFE9EE"/>
<path d="M18 29h11m-4-4 4 4-4 4" stroke="#0879D9" stroke-width="2.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>'''


# ------------------------------------------------------------------ styling --
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stMarkdown, button, input, textarea { font-family: 'Inter','Segoe UI',system-ui,sans-serif !important; }
.block-container { padding-top: 1.1rem; padding-bottom: 1.5rem; max-width: 1180px; }
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; height: 0; }
h1,h2,h3,h4 { color:#0B2D55; letter-spacing:-.01em; }

/* ---- sidebar (deep navy) ---- */
[data-testid="stSidebar"] { background:#0B2D55; border-right:0; }
[data-testid="stSidebar"] * { color:#DCE7F5; }
[data-testid="stSidebar"] .stButton button > div { justify-content:flex-start !important; width:100%; text-align:left; }
[data-testid="stSidebar"] .stButton button { justify-content:flex-start; text-align:left; border-radius:10px; font-weight:600; padding:.55rem .8rem; border:0; }
[data-testid="stSidebar"] .stButton button[kind="tertiary"] { background:transparent; color:#C5D5EA; }
[data-testid="stSidebar"] .stButton button[kind="tertiary"]:hover { background:rgba(255,255,255,.08); color:#fff; }
[data-testid="stSidebar"] .stButton button[kind="primary"] { background:#0879D9; color:#fff; box-shadow:none; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.12); }
.sb-brand { display:flex; align-items:center; gap:11px; padding: 4px 2px 2px 2px; }
.sb-brand .n { font-size:19px; font-weight:800; color:#fff !important; letter-spacing:-.01em; line-height:1.1; }
.sb-brand .t { font-size:11px; color:#8FB2D8 !important; letter-spacing:.02em; margin-top:2px; }
.sb-label { font-size:11px; font-weight:700; letter-spacing:.12em; text-transform:uppercase; color:#7FA3CC !important; margin: 6px 0 4px 4px; }
.sb-soon { border:1px dashed rgba(255,255,255,.22); border-radius:10px; padding:10px 12px; font-size:12.5px; color:#9DB9D9 !important; line-height:1.45; }
.sb-foot { font-size:11.5px; color:#7FA3CC !important; line-height:1.5; }

/* ---- header ---- */
.crumb { font-size:12.5px; color:#63758B; font-weight:500; }
.crumb b { color:#0B2D55; }
.page-title { font-size:26px; font-weight:800; color:#0B2D55; margin:2px 0 0 0; letter-spacing:-.02em; }
.id-chip { display:inline-flex; align-items:center; gap:8px; font-size:12.5px; font-weight:700; color:#0B2D55; padding:5px 10px 5px 6px;
  background:#fff; border:1px solid #E1E8F0; border-radius:999px; }

/* ---- cards ---- */
div[class*="st-key-card"] { background:#fff; border:1px solid #E1E8F0; border-radius:16px; padding:22px 24px; box-shadow:0 1px 2px rgba(11,45,85,.04), 0 6px 18px rgba(11,45,85,.04); }
.muted { color:#63758B; font-size:14px; line-height:1.55; }
.h-sec { font-size:17px; font-weight:700; color:#0B2D55; margin:0 0 2px 0; }
.tool-head { display:flex; align-items:center; gap:14px; margin-bottom:6px; }
.tool-head .tn { font-size:22px; font-weight:800; color:#0B2D55; line-height:1.1; }
.tool-head .td { font-size:13px; color:#63758B; }
.tag { display:inline-block; font-size:12px; font-weight:600; color:#0B6A9A; background:#E8F4FB; border:1px solid #CBE6F6; padding:4px 10px; border-radius:999px; margin:0 6px 6px 0; }
.tag.g { color:#0C7A5A; background:#E6F8F1; border-color:#BDEBDB; }
.chip { display:inline-block; font-size:12px; font-weight:600; padding:4px 10px; border-radius:8px; margin:0 6px 6px 0; }
.chip.ok { color:#0C7A5A; background:#E6F8F1; border:1px solid #BDEBDB; }
.chip.no { color:#B42318; background:#FEF0EE; border:1px solid #F8CFC9; }
.note { border-left:4px solid #00A6B2; background:#EFFAFB; border-radius:8px; padding:11px 14px; color:#0B4F63; font-size:13.5px; line-height:1.5; }
.note.warn { border-color:#E8A317; background:#FFF8E6; color:#6B4A00; }

/* ---- hero (home) ---- */
.hero { border-radius:20px; padding:34px 38px; background:linear-gradient(135deg,#0B2D55 0%,#0A4F8F 60%,#00859A 100%); position:relative; overflow:hidden; }
.hero::after { content:""; position:absolute; right:-60px; top:-60px; width:260px; height:260px; border-radius:50%; background:radial-gradient(circle,rgba(25,201,149,.35),transparent 70%); }
.hero h1 { color:#fff; font-size:36px; font-weight:800; margin:10px 0 8px 0; letter-spacing:-.02em; }
.hero p { color:#CFE0F3; font-size:16px; max-width:680px; line-height:1.6; margin:0; }
.hero .tl { display:inline-block; margin-top:14px; font-size:12.5px; font-weight:700; letter-spacing:.14em; text-transform:uppercase; color:#7EE6C5; }

/* ---- stepper ---- */
.stepper { display:flex; align-items:center; gap:0; margin: 4px 0 20px 0; }
.stp { display:flex; align-items:center; gap:10px; flex:1; }
.stp .c { width:30px; height:30px; flex:0 0 30px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:13px; font-weight:800;
  background:#fff; border:2px solid #CFDAE8; color:#63758B; }
.stp .l { font-size:13px; font-weight:600; color:#63758B; line-height:1.25; }
.stp .l small { display:block; font-weight:500; font-size:11.5px; color:#8A9BB0; }
.stp .bar { flex:1; height:2px; background:#DCE5F0; margin:0 12px; min-width:18px; }
.stp.done .c { background:#19C995; border-color:#19C995; color:#fff; }
.stp.done .bar { background:#19C995; }
.stp.done .l { color:#0B2D55; }
.stp.active .c { background:linear-gradient(135deg,#0879D9,#00A6B2); border-color:transparent; color:#fff; box-shadow:0 0 0 4px rgba(8,121,217,.15); }
.stp.active .l { color:#0B2D55; font-weight:700; }
.stp:last-child { flex:0 0 auto; }
.stp:last-child .bar { display:none; }

/* ---- KPIs ---- */
.kpis { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:6px 0 14px 0; }
.kpi { border-radius:14px; padding:14px 16px; background:#F5F8FC; border:1px solid #E1E8F0; }
.kpi .v { font-size:26px; font-weight:800; color:#0B2D55; line-height:1.1; }
.kpi .l { font-size:11.5px; letter-spacing:.08em; text-transform:uppercase; color:#63758B; font-weight:600; margin-top:4px; }
.kpi.warn .v { color:#B7791F; }

/* ---- buttons / inputs ---- */
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] { background:#0879D9; border:0; color:#fff; font-weight:700; border-radius:10px; padding:.6rem 1.1rem; }
.stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover { background:#0668BD; }
.stButton > button[kind="secondary"], .stDownloadButton > button[kind="secondary"] { border-radius:10px; font-weight:600; border:1px solid #CFDAE8; background:#fff; color:#0B2D55; }
.stButton > button[kind="secondary"]:hover, .stDownloadButton > button[kind="secondary"]:hover { border-color:#0879D9; color:#0879D9; }
[data-testid="stFileUploaderDropzone"] { border:2px dashed #9CC4EA; border-radius:16px; background:#F3F8FE; padding:34px 20px; }
[data-testid="stFileUploaderDropzone"] button { background:#0879D9; color:#fff; border:0; border-radius:10px; font-weight:700; }
[data-baseweb="input"] > div, [data-baseweb="select"] > div, [data-baseweb="textarea"] { border-radius:10px !important; border-color:#E1E8F0 !important; background:#fff !important; }
.stTabs [data-baseweb="tab"] { font-weight:600; color:#63758B; } .stTabs [aria-selected="true"] { color:#0879D9; }
.app-footer { text-align:center; margin-top:34px; padding:18px 8px 4px 8px; border-top:1px solid #E1E8F0; color:#63758B; font-size:12.5px; }
.app-footer b { color:#0B2D55; letter-spacing:.02em; }
@media (max-width:900px){ .kpis{grid-template-columns:repeat(2,1fr);} .stp .l small{display:none;} }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------- state --
S = st.session_state
S.setdefault("page", "home")
S.setdefault("gx_step", 1)
S.setdefault("gx_file", None)          # {"name","size","bytes","id"}
S.setdefault("gx_up_n", 0)             # bump to reset the uploader widget
S.setdefault("gx_replacing", False)
S.setdefault("gx_preview", None)       # {"key":..., "data":...}
S.setdefault("result", None)
S.setdefault("history", [])            # this session's generated guides (real data only)
# keep form values alive while their widgets are not on screen (other steps)
for _k in ("gx_product", "gx_doc_no", "gx_issue_no", "gx_issued_by", "gx_rev_no", "gx_rev_date", "gx_pptx",
           "gx_c_name", "gx_c_des", "gx_c_tel", "gx_c_mob", "gx_c_ext", "gx_c_mail", "gx_use_ai", "gx_ai_key", "gx_sheet"):
    if _k in S:
        S[_k] = S[_k]


def go(page=None, step=None):
    if page:
        S["page"] = page
    if step:
        S["gx_step"] = step


def clear_file():
    S["gx_file"] = None
    S["gx_preview"] = None
    S["result"] = None
    S["gx_step"] = 1
    S["gx_replacing"] = False
    S["gx_up_n"] += 1
    for k in ("gx_product", "gx_sheet"):
        S.pop(k, None)


def human_size(n: int) -> str:
    return f"{n/1024:.0f} KB" if n < 1024 * 1024 else f"{n/1024/1024:.1f} MB"


# ----------------------------------------------------------------- sidebar --
with st.sidebar:
    st.markdown(f'<div class="sb-brand">{bpm_logo(38)}<div><div class="n">{PLATFORM}</div>'
                f'<div class="t">{PLATFORM_TAGLINE}</div></div></div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown('<div class="sb-label">Workspace</div>', unsafe_allow_html=True)
    st.button("Home", key="nav_home", icon=":material/home:", use_container_width=True,
              type="primary" if S["page"] == "home" else "tertiary", on_click=go, kwargs={"page": "home"})
    st.button(TOOL, key="nav_guidex", icon=":material/description:", use_container_width=True,
              type="primary" if S["page"] == "guidex" else "tertiary", on_click=go, kwargs={"page": "guidex"})
    st.markdown("---")
    st.markdown('<div class="sb-label">More Tools</div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-soon">Additional BPM tools will appear here as they are released.</div>',
                unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(f'<div class="sb-foot">Uploaded files are processed in a temporary folder and discarded after each run.'
                f'<br><br>{PLATFORM} · {VERSION}</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------ header --
PAGE_TITLES = {"home": "Home", "guidex": TOOL}
h1, h2 = st.columns([2.8, 2.6], vertical_alignment="center")
with h1:
    crumb = f'<b>{PLATFORM}</b>' if S["page"] == "home" else f'{PLATFORM} &nbsp;›&nbsp; <b>{TOOL}</b>'
    st.markdown(f'<div class="crumb">{crumb}</div><div class="page-title">{PAGE_TITLES[S["page"]]}</div>',
                unsafe_allow_html=True)
with h2:
    r1, r2 = st.columns([1.35, 1], vertical_alignment="center")
    with r1:
        st.markdown(f'<div class="id-chip">{bpm_logo(20)} {PLATFORM}</div>', unsafe_allow_html=True)
    with r2:
        with st.popover("Help", icon=":material/help:", use_container_width=True):
            if S["page"] == "home":
                st.markdown(f"**{PLATFORM}** brings BPM automation tools together in one place. Open **{TOOL}** to "
                            "generate a Service Delivery Guide from your product configuration workbook.")
            else:
                st.markdown("**GuideX in four steps**\n\n1. Upload the product configuration workbook (.xlsx)\n"
                            "2. Review what was read from it\n3. Enter the document details and generate\n"
                            "4. Review the warnings and download your files\n\n"
                            "The workbook is the source of truth: nothing is added that it does not contain.")
st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)


# ---------------------------------------------------------------- HOME page --
def page_home():
    st.markdown(f"""
<div class="hero">{bpm_logo(54)}
<h1>Welcome to {PLATFORM}</h1>
<p>Transform business information into structured processes and practical documentation with a growing collection of BPM automation tools.</p>
<span class="tl">{PLATFORM_TAGLINE}</span></div>""", unsafe_allow_html=True)
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="h-sec">Available tools</div>', unsafe_allow_html=True)
    with st.container(key="card_guidex"):
        c1, c2 = st.columns([4, 1.2], vertical_alignment="center")
        with c1:
            st.markdown(f"""
<div class="tool-head">{guidex_icon(52)}<div><div class="tn">{TOOL}</div><div class="td">{TOOL_DESC}</div></div></div>
<div class="muted" style="margin:6px 0 10px 0">Generate structured Service Delivery Guides from product configuration and process data.</div>
<span class="tag">Excel Input</span><span class="tag">AI-Assisted Content (optional)</span><span class="tag">Automated Flowcharts</span>
<span class="tag">Word Export</span><span class="tag g">Editable PowerPoint</span>""", unsafe_allow_html=True)
        with c2:
            st.button(f"Open {TOOL}", key="open_guidex", type="primary", icon=":material/arrow_forward:",
                      use_container_width=True, on_click=go, kwargs={"page": "guidex"})
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="h-sec">Recent activity</div>', unsafe_allow_html=True)
    with st.container(key="card_recent"):
        if S["history"]:
            for h in reversed(S["history"][-5:]):
                st.markdown(f"**{h['product']}** — guide generated · {h['orders']} order types · {h['time']}")
            st.caption("Shown for this browser session only; files are not stored.")
        else:
            st.markdown('<div class="muted">No guides have been generated in this session yet. '
                        f'Open {TOOL} to create your first Service Delivery Guide.</div>', unsafe_allow_html=True)


# --------------------------------------------------------------- GuideX page -
STEP_META = [("Upload Source File", "Product workbook"), ("Review Extracted Information", "What was read"),
             ("Configure and Generate", "Document details"), ("Review and Download", "Your outputs")]


def stepper(active: int):
    html = ['<div class="stepper">']
    for i, (t, s) in enumerate(STEP_META, start=1):
        cls = "done" if i < active else ("active" if i == active else "")
        mark = "✓" if i < active else str(i)
        html.append(f'<div class="stp {cls}"><div class="c">{mark}</div><div class="l">{t}<small>{s}</small></div>'
                    f'<div class="bar"></div></div>')
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def tool_head():
    st.markdown(f'<div class="tool-head">{guidex_icon(46)}<div><div class="tn">{TOOL}</div>'
                f'<div class="td">{TOOL_DESC}</div></div></div>', unsafe_allow_html=True)


def step1():
    with st.container(key="card_upload"):
        tool_head()
        st.markdown('<div class="muted" style="margin-bottom:12px">Upload your product configuration workbook. GuideX reads it '
                    'and builds the Service Delivery Guide, swimlane flowcharts and an editable PowerPoint.</div>',
                    unsafe_allow_html=True)
        f = S["gx_file"]
        if f and not S["gx_replacing"]:
            c1, c2, c3 = st.columns([5, 1.1, 1.1], vertical_alignment="center")
            with c1:
                st.markdown(f'<div style="display:flex;align-items:center;gap:12px"><div style="font-size:30px">📗</div>'
                            f'<div><b style="color:#0B2D55">{f["name"]}</b><div class="muted" style="font-size:12.5px">'
                            f'{human_size(f["size"])} · Excel workbook · <span style="color:#0C7A5A;font-weight:600">Uploaded</span></div></div></div>',
                            unsafe_allow_html=True)
            with c2:
                if st.button("Replace", key="replace_file", use_container_width=True):
                    S["gx_replacing"] = True
                    st.rerun()
            with c3:
                st.button("Remove", key="remove_file", use_container_width=True, on_click=clear_file)
        else:
            up = st.file_uploader("Upload your product configuration workbook.", type=["xlsx"],
                                  key=f"gx_uploader_{S['gx_up_n']}",
                                  help="Excel .xlsx · up to 25 MB. Drag and drop or browse.")
            if up is not None:
                data = up.getvalue()
                fid = hashlib.md5(data).hexdigest()
                if not S["gx_file"] or S["gx_file"]["id"] != fid:
                    S["gx_preview"], S["result"] = None, None
                    for k in ("gx_product", "gx_sheet"):
                        S.pop(k, None)
                S["gx_file"] = {"name": up.name, "size": len(data), "bytes": data, "id": fid}
                S["gx_replacing"] = False
                st.rerun()
            if S["gx_replacing"]:
                st.button("Cancel replace", key="cancel_replace", on_click=lambda: S.update(gx_replacing=False))
        st.markdown('<div class="note" style="margin-top:14px"><b>The workbook is the source of truth.</b> The generated '
                    'document only contains what your workbook contains. AI, if you choose to use it, only helps word the '
                    'Introduction.</div>', unsafe_allow_html=True)
    if S["gx_file"] and not S["gx_replacing"]:
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        _, cn = st.columns([4, 1.4])
        with cn:
            st.button("Continue", key="s1_next", type="primary", icon=":material/arrow_forward:", icon_position="right",
                      use_container_width=True, on_click=go, kwargs={"step": 2})


def step2():
    f = S["gx_file"]
    info = svc.inspect_workbook(f["bytes"])
    with st.container(key="card_review"):
        st.markdown('<div class="h-sec">Review extracted information</div>', unsafe_allow_html=True)
        st.markdown('<div class="muted" style="margin-bottom:10px">This is what GuideX read from your workbook. Check it looks right before generating.</div>',
                    unsafe_allow_html=True)
        chips = "".join(f'<span class="chip {"ok" if c["found"] else "no"}">{"✓" if c["found"] else "✕"} {c["prefix"]} {c["label"]}</span>'
                        for c in info["checks"])
        st.markdown(chips, unsafe_allow_html=True)
        sheets = info["sheets"]
        if "gx_sheet" not in S or S["gx_sheet"] not in sheets:
            S["gx_sheet"] = info["detected"] if info["detected"] in sheets else sheets[0]
        if not info["detected"]:
            st.error("No sheet starting with “6.3” was found - that sheet holds the order-type task lists.")
        st.selectbox("Order-type task sheet", sheets, key="gx_sheet",
                     help="Detected automatically; change it only if your sheet has a different name.")
        pkey = (f["id"], S["gx_sheet"])
        if not S["gx_preview"] or S["gx_preview"]["key"] != pkey:
            with st.spinner("Reading the workbook…"):
                try:
                    S["gx_preview"] = {"key": pkey, "data": svc.preview_workbook(
                        f["bytes"], S["gx_sheet"], S.get("gx_product", ""))}
                except Exception as exc:                                  # noqa: BLE001
                    S["gx_preview"] = {"key": pkey, "error": f"{type(exc).__name__}: {exc}"}
        pv = S["gx_preview"]
        if "error" in pv:
            st.error("The workbook could not be read with this sheet selection.")
            with st.expander("Technical details"):
                st.code(pv["error"])
        else:
            d = pv["data"]
            warn_cls = "kpi warn" if d["warnings"] else "kpi"
            st.markdown(f"""<div class="kpis">
<div class="kpi"><div class="v">{len(d["order_types"])}</div><div class="l">Order types</div></div>
<div class="kpi"><div class="v">{d["total_tasks"]}</div><div class="l">Tasks</div></div>
<div class="kpi"><div class="v">{len(d["hierarchy"])}</div><div class="l">Product components</div></div>
<div class="{warn_cls}"><div class="v">{len(d["warnings"])}</div><div class="l">Items to review</div></div></div>""",
                        unsafe_allow_html=True)
            st.markdown("**Order types**")
            st.dataframe(
                [{"Order type": o["name"], "Tasks in workbook": o["tasks"], "Tasks in flowchart": o["in_flowchart"],
                  "Swimlanes": o["lanes"], "Decisions": o["decisions"]} for o in d["order_types"]],
                hide_index=True, use_container_width=True)
            st.caption("Some tasks (for example External/System tasks and rework helpers) are left out of the flowchart "
                       "by design; they remain in the task tables of the guide.")
            e1, e2 = st.columns(2)
            with e1:
                with st.expander(f"Product hierarchy · {len(d['hierarchy'])} node(s)"):
                    for n in d["hierarchy"]:
                        st.markdown(f"- **{n['name']}** · {n['kind']} · {n['attributes']} attribute(s)")
            with e2:
                with st.expander("Other content found"):
                    st.markdown(f"- Introduction paragraphs: **{d['intro_paragraphs']}**\n"
                                f"- Business rules: **{d['business_rules']}** ({d['business_rule_tables']} with tables)\n"
                                f"- Order scenarios: **{d['order_scenarios']}**")
            if d["warnings"]:
                with st.expander(f"⚠️ {len(d['warnings'])} item(s) to review in the workbook", expanded=True):
                    for w in d["warnings"]:
                        st.markdown(f"- {w}")
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    b1, _, b2 = st.columns([1.2, 3, 1.6])
    with b1:
        st.button("Back", key="s2_back", icon=":material/arrow_back:", use_container_width=True,
                  on_click=go, kwargs={"step": 1})
    with b2:
        ok = bool(S["gx_preview"]) and "error" not in S["gx_preview"]
        st.button("Continue", key="s2_next", type="primary", disabled=not ok, icon=":material/arrow_forward:",
                  icon_position="right", use_container_width=True, on_click=go, kwargs={"step": 3})


def _gemini_key_from_secrets():
    try:
        return st.secrets.get("GEMINI_API_KEY")
    except Exception:
        return None


def step3():
    f = S["gx_file"]
    S.setdefault("gx_product", svc.default_product_name(f["name"]))
    S.setdefault("gx_issued_by", "Business Process Management Section")
    S.setdefault("gx_rev_no", "0")
    S.setdefault("gx_issue_no", "0")
    S.setdefault("gx_rev_date", datetime.date.today())
    S.setdefault("gx_pptx", True)
    S.setdefault("gx_c_des", "DGM/BPM")
    with st.container(key="card_config"):
        st.markdown('<div class="h-sec">Configure and generate</div>', unsafe_allow_html=True)
        st.markdown('<div class="muted" style="margin-bottom:12px">These details appear on the cover and the document control pages.</div>',
                    unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("Product / service name *", key="gx_product", placeholder="e.g. CYS_EdgeDefend")
            st.text_input("Issued by", key="gx_issued_by")
            st.text_input("Revision number", key="gx_rev_no")
        with c2:
            st.text_input("Document number", key="gx_doc_no", placeholder="e.g. SDG-EDGE-001")
            st.text_input("Issue number", key="gx_issue_no")
            st.date_input("Revision date", key="gx_rev_date", format="DD/MM/YYYY")
        st.markdown("**Outputs**")
        st.toggle("Also create the editable PowerPoint with all flowcharts", key="gx_pptx",
                  help="Native shapes and connectors - edit any diagram you are not happy with.")
        with st.expander("Contact for inquiries (optional)"):
            k1, k2 = st.columns(2)
            with k1:
                st.text_input("Name", key="gx_c_name")
                st.text_input("Designation", key="gx_c_des")
                st.text_input("Telephone", key="gx_c_tel")
            with k2:
                st.text_input("Mobile", key="gx_c_mob")
                st.text_input("Extension", key="gx_c_ext")
                st.text_input("E-mail", key="gx_c_mail")
        server_key = _gemini_key_from_secrets()
        with st.expander("AI-assisted introduction (optional)"):
            st.markdown('<div class="note">AI only helps word the <b>Introduction</b>. It must not add specifications, systems, '
                        'process steps or rules that are not in the workbook. The flowcharts never depend on AI.</div>',
                        unsafe_allow_html=True)
            S.setdefault("gx_use_ai", bool(server_key))
            st.toggle("Use Gemini for the Introduction", key="gx_use_ai")
            if S["gx_use_ai"] and not server_key:
                st.text_input("Gemini API key", type="password", key="gx_ai_key",
                              help="Used for this run only; never stored.")

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    b1, _, b2 = st.columns([1.2, 3, 2.2])
    with b1:
        st.button("Back", key="s3_back", icon=":material/arrow_back:", use_container_width=True,
                  on_click=go, kwargs={"step": 2})
    ready = bool(S["gx_product"].strip()) and bool(S.get("gx_sheet"))
    with b2:
        go_gen = st.button("Generate Guide", key="s3_gen", type="primary", disabled=not ready,
                           icon=":material/auto_awesome:", use_container_width=True)
    if not S["gx_product"].strip():
        st.info("Enter the product / service name to continue.")

    if go_gen and ready:
        gemini_key = (server_key if S["gx_use_ai"] else None) or ((S.get("gx_ai_key") or None) if S["gx_use_ai"] else None)
        params = svc.GenParams(
            product=S["gx_product"].strip(), sheet=S["gx_sheet"], doc_no=S.get("gx_doc_no", "").strip(),
            issue_no=S["gx_issue_no"].strip(), issued_by=S["gx_issued_by"].strip(), revision_no=S["gx_rev_no"].strip(),
            revision_date=S["gx_rev_date"].strftime("%d.%m.%Y"), export_pptx=S["gx_pptx"], gemini_key=gemini_key,
            contacts=dict(contact_name=S.get("gx_c_name", ""), contact_designation=S.get("gx_c_des", ""),
                          contact_telephone=S.get("gx_c_tel", ""), contact_mobile=S.get("gx_c_mob", ""),
                          contact_extension=S.get("gx_c_ext", ""), contact_email=S.get("gx_c_mail", "")),
        )
        with st.status("Generating your Service Delivery Guide…", expanded=True) as status:
            try:
                out = svc.generate(f["bytes"], params, progress=lambda m: status.write(m))
                S["result"] = {"out": out, "file": f["id"], "product": params.product}
                S["history"].append({"product": params.product, "orders": len(out.order_types),
                                     "time": datetime.datetime.now().strftime("%H:%M")})
                status.update(label="Done — your files are ready", state="complete", expanded=False)
                S["gx_step"] = 4
                st.rerun()
            except ValueError as exc:
                status.update(label="Could not read the workbook", state="error")
                st.error(f"The workbook could not be processed: {exc}")
            except Exception as exc:                                      # noqa: BLE001
                status.update(label="Something went wrong", state="error")
                st.error("Generation failed. Please check the workbook and try again.")
                with st.expander("Technical details"):
                    st.code(f"{type(exc).__name__}: {exc}")


def step4():
    res = S["result"]
    if not res:
        st.info("Nothing generated yet.")
        st.button("Back to configuration", on_click=go, kwargs={"step": 3})
        return
    out = res["out"]
    total_tasks = sum(o["tasks"] for o in out.order_types)
    n_imgs = sum(o["images"] for o in out.order_types)
    with st.container(key="card_results"):
        st.markdown(f'<div class="h-sec">Your files · {res["product"]}</div>', unsafe_allow_html=True)
        warn_cls = "kpi warn" if out.warnings else "kpi"
        st.markdown(f"""<div class="kpis">
<div class="kpi"><div class="v">{len(out.order_types)}</div><div class="l">Order types</div></div>
<div class="kpi"><div class="v">{total_tasks}</div><div class="l">Tasks processed</div></div>
<div class="kpi"><div class="v">{n_imgs}</div><div class="l">Flowchart images</div></div>
<div class="{warn_cls}"><div class="v">{len(out.warnings)}</div><div class="l">Warnings to review</div></div></div>""",
                    unsafe_allow_html=True)
        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.download_button("Guide (.docx)", out.docx_bytes, out.docx_name,
                               "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                               type="primary", icon=":material/download:", use_container_width=True)
        with d2:
            if out.pptx_bytes:
                st.download_button("Editable (.pptx)", out.pptx_bytes, out.pptx_name,
                                   "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                                   icon=":material/download:", use_container_width=True)
            else:
                st.button("PowerPoint not created", disabled=True, use_container_width=True)
        with d3:
            st.download_button("Images (.zip)", out.flow_zip_bytes, out.flow_zip_name, "application/zip",
                               icon=":material/download:", use_container_width=True)
        with d4:
            st.download_button("Everything (.zip)", out.all_zip_bytes, out.all_zip_name, "application/zip",
                               icon=":material/download:", use_container_width=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if out.warnings:
            with st.expander(f"⚠️ {len(out.warnings)} item(s) to review before sharing the guide", expanded=True):
                for w in out.warnings:
                    st.markdown(f"- {w}")
        else:
            st.success("No warnings — the workbook looks clean.")
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    with st.container(key="card_preview"):
        st.markdown('<div class="h-sec">Flowchart preview</div>', unsafe_allow_html=True)
        names = [o["name"] for o in out.order_types if out.flow_images.get(o["name"])]
        if names:
            for tab, nm in zip(st.tabs(names), names):
                with tab:
                    imgs = out.flow_images[nm]
                    cols = st.columns(len(imgs)) if len(imgs) > 1 else [st.container()]
                    for i, (c, png) in enumerate(zip(cols, imgs), start=1):
                        with c:
                            st.image(png, caption=f"{nm} · part {i} of {len(imgs)}" if len(imgs) > 1 else nm,
                                     use_container_width=True)
        else:
            st.info("No flowcharts were produced — every task was excluded or had no lane.")
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    b1, _, b2 = st.columns([1.6, 3, 1.8])
    with b1:
        st.button("Back to settings", key="s4_back", icon=":material/arrow_back:", use_container_width=True,
                  on_click=go, kwargs={"step": 3})
    with b2:
        st.button("Start a new guide", key="s4_new", use_container_width=True, icon=":material/refresh:",
                  on_click=clear_file)


def page_guidex():
    # GuideX needs a file for steps 2-4
    if S["gx_step"] > 1 and not S["gx_file"]:
        S["gx_step"] = 1
    stepper(S["gx_step"])
    {1: step1, 2: step2, 3: step3, 4: step4}[S["gx_step"]]()


# ------------------------------------------------------------------ router --
if S["page"] == "home":
    page_home()
else:
    page_guidex()

st.markdown(f'<div class="app-footer"><b>{PLATFORM_TAGLINE}</b><br>{PLATFORM} · {TOOL} — {TOOL_DESC} · {VERSION}</div>',
            unsafe_allow_html=True)
