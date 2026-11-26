from pathlib import Path
import uuid

import streamlit as st
import streamlit.components.v1 as components

import accounts
import network
import notifications
import posts
import storage

ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def inject_orbit_theme():
    """Apply Orbit's cohesive visual system to Streamlit's rendered elements."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        :root { --orbit-blue:#2563EB; --orbit-deep:#153E75; --orbit-navy:#0B1730; --orbit-sky:#60A5FA; --orbit-pale:#EFF6FF; --orbit-bg:#F5F8FC; --orbit-text:#172033; --orbit-muted:#64748B; --orbit-border:#E2E8F0; }
        html,body,[class*="st-"]:not([data-testid="stIconMaterial"]),button,input,textarea { font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif; }
        [data-testid="stAppViewContainer"] { background:var(--orbit-bg); color:var(--orbit-text); }
        [data-testid="stMain"] { position:relative; background:transparent; }
        [data-testid="stMainBlockContainer"] { position:relative; isolation:isolate; z-index:1; }
        iframe[data-testid="stCustomComponentV1"] { position:fixed!important; inset:0!important; width:100vw!important; height:100vh!important; z-index:0!important; border:0!important; pointer-events:none!important; }
        [data-testid="stMainBlockContainer"] [data-testid="stElementContainer"]:not(:has(iframe[data-testid="stCustomComponentV1"])) { position:relative; z-index:1; }
        [data-testid="stHeader"] { position:relative; z-index:1; background:transparent; }
        h1,h2,h3 { color:var(--orbit-text); letter-spacing:-.03em; } h1 { font-weight:750; }
        [data-testid="stCaptionContainer"] { color:var(--orbit-muted); }
        [data-testid="stVerticalBlockBorderWrapper"] { background:#fff; border-color:var(--orbit-border)!important; border-radius:18px!important; box-shadow:0 10px 28px rgba(15,23,42,.055); }
        [data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stTabs"]) { padding:.45rem; }
        div[data-testid="stForm"] { background:#fff; border:1px solid var(--orbit-border); border-radius:16px; padding:1.25rem; box-shadow:0 6px 20px rgba(15,23,42,.04); }
        [data-testid="stSidebar"] { position:relative; z-index:2; background:var(--orbit-navy); border-right:1px solid rgba(255,255,255,.08); }
        [data-testid="stSidebar"]>div:first-child { background:var(--orbit-navy); }
        [data-testid="stSidebar"] * { color:#D7E4F7; }
        [data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3 { color:#fff; }
        .orbit-brand { display:flex; align-items:center; gap:.72rem; margin:.1rem 0 .5rem; }
        .orbit-mark { width:46px; height:46px; flex:0 0 46px; }
        .orbit-brand-name { color:var(--orbit-deep); font-size:1.55rem; font-weight:750; letter-spacing:-.04em; line-height:1.05; }
        .orbit-brand-sidebar .orbit-brand-name { color:#fff; font-size:1.42rem; }
        .orbit-brand-sidebar .orbit-mark { width:40px; height:40px; flex-basis:40px; }
        .orbit-sidebar-tagline { color:#9CB2D2; font-size:.78rem; margin:.1rem 0 1.1rem .1rem; }
        .orbit-signed-in { color:#D7E4F7; font-size:.88rem; line-height:1.4; margin:.55rem 0 .2rem; }
        .orbit-unread { display:flex; align-items:center; justify-content:space-between; color:#AFC2DF; font-size:.8rem; margin:.5rem 0 1rem; }
        .orbit-unread-count { background:rgba(96,165,250,.18); color:#BFDBFE; border-radius:999px; min-width:1.55rem; padding:.12rem .42rem; text-align:center; font-weight:700; }
        [data-testid="stSidebar"] [data-testid="stButton"] button { display:flex; align-items:center; justify-content:flex-start; gap:.7rem; width:100%; color:#CBD5E1!important; background:transparent!important; border:1px solid transparent!important; box-shadow:none!important; text-align:left; }
        [data-testid="stSidebar"] [data-testid="stButton"] button[data-testid="stBaseButton-primary"] { color:#fff!important; background:#2563EB!important; border-color:#2563EB!important; box-shadow:0 6px 16px rgba(37,99,235,.22)!important; font-weight:650; }
        [data-testid="stSidebar"] [data-testid="stButton"] button[data-testid="stBaseButton-secondary"]:hover { color:#fff!important; background:rgba(96,165,250,.14)!important; border-color:rgba(96,165,250,.2)!important; }
        [data-testid="stSidebar"] .st-key-sidebar_nav_home button::before,
        [data-testid="stSidebar"] .st-key-sidebar_nav_trending button::before,
        [data-testid="stSidebar"] .st-key-sidebar_nav_connections button::before,
        [data-testid="stSidebar"] .st-key-sidebar_nav_profile button::before,
        [data-testid="stSidebar"] .st-key-sidebar_nav_notifications button::before {
          content:""; display:block; width:21px; height:21px; flex:0 0 21px;
          background-color:#AFC2DF; -webkit-mask-position:center; mask-position:center;
          -webkit-mask-repeat:no-repeat; mask-repeat:no-repeat;
          -webkit-mask-size:contain; mask-size:contain;
        }
        [data-testid="stSidebar"] .st-key-sidebar_nav_home button::before { -webkit-mask-image:url("data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2024%2024'%3E%3Cpath%20d='M3,10.5L12,3l9,7.5v10.5H3zM9,21v-6h6v6'%20fill='none'%20stroke='black'%20stroke-width='2'%20stroke-linecap='round'%20stroke-linejoin='round'/%3E%3C/svg%3E"); mask-image:url("data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2024%2024'%3E%3Cpath%20d='M3,10.5L12,3l9,7.5v10.5H3zM9,21v-6h6v6'%20fill='none'%20stroke='black'%20stroke-width='2'%20stroke-linecap='round'%20stroke-linejoin='round'/%3E%3C/svg%3E"); }
        [data-testid="stSidebar"] .st-key-sidebar_nav_trending button::before { -webkit-mask-image:url("data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2024%2024'%3E%3Cpath%20d='M3,17l6,-6%204,4%208,-9M15,6h6v6'%20fill='none'%20stroke='black'%20stroke-width='2'%20stroke-linecap='round'%20stroke-linejoin='round'/%3E%3C/svg%3E"); mask-image:url("data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2024%2024'%3E%3Cpath%20d='M3,17l6,-6%204,4%208,-9M15,6h6v6'%20fill='none'%20stroke='black'%20stroke-width='2'%20stroke-linecap='round'%20stroke-linejoin='round'/%3E%3C/svg%3E"); }
        [data-testid="stSidebar"] .st-key-sidebar_nav_connections button::before { -webkit-mask-image:url("data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2024%2024'%3E%3Cpath%20d='M16,21v-2a4,4%200,0%200,-4,-4H8a4,4%200,0%200,-4,4v2M10,11a4,4%200,1%200,0,-8%204,4%200,0%200,0,8M20,21v-2a4,4%200,0%200,-3,-3.87M16,3.13a4,4%200,0%201,0,7.75'%20fill='none'%20stroke='black'%20stroke-width='2'%20stroke-linecap='round'%20stroke-linejoin='round'/%3E%3C/svg%3E"); mask-image:url("data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2024%2024'%3E%3Cpath%20d='M16,21v-2a4,4%200,0%200,-4,-4H8a4,4%200,0%200,-4,4v2M10,11a4,4%200,1%200,0,-8%204,4%200,0%200,0,8M20,21v-2a4,4%200,0%200,-3,-3.87M16,3.13a4,4%200,0%201,0,7.75'%20fill='none'%20stroke='black'%20stroke-width='2'%20stroke-linecap='round'%20stroke-linejoin='round'/%3E%3C/svg%3E"); }
        [data-testid="stSidebar"] .st-key-sidebar_nav_profile button::before { -webkit-mask-image:url("data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2024%2024'%3E%3Ccircle%20cx='12'%20cy='8'%20r='4'%20fill='none'%20stroke='black'%20stroke-width='2'/%3E%3Cpath%20d='M4,21a8,8%200,0%201,16,0'%20fill='none'%20stroke='black'%20stroke-width='2'%20stroke-linecap='round'/%3E%3C/svg%3E"); mask-image:url("data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2024%2024'%3E%3Ccircle%20cx='12'%20cy='8'%20r='4'%20fill='none'%20stroke='black'%20stroke-width='2'/%3E%3Cpath%20d='M4,21a8,8%200,0%201,16,0'%20fill='none'%20stroke='black'%20stroke-width='2'%20stroke-linecap='round'/%3E%3C/svg%3E"); }
        [data-testid="stSidebar"] .st-key-sidebar_nav_notifications button::before { -webkit-mask-image:url("data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2024%2024'%3E%3Cpath%20d='M18,9a6,6%200,0%200,-12,0c0,7%20-3,7%20-3,9h18c0,-2%20-3,-2%20-3,-9ZM10,21h4'%20fill='none'%20stroke='black'%20stroke-width='2'%20stroke-linecap='round'%20stroke-linejoin='round'/%3E%3C/svg%3E"); mask-image:url("data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2024%2024'%3E%3Cpath%20d='M18,9a6,6%200,0%200,-12,0c0,7%20-3,7%20-3,9h18c0,-2%20-3,-2%20-3,-9ZM10,21h4'%20fill='none'%20stroke='black'%20stroke-width='2'%20stroke-linecap='round'%20stroke-linejoin='round'/%3E%3C/svg%3E"); }
        [data-testid="stSidebar"] .st-key-sidebar_nav_home button[data-testid="stBaseButton-primary"]::before,
        [data-testid="stSidebar"] .st-key-sidebar_nav_trending button[data-testid="stBaseButton-primary"]::before,
        [data-testid="stSidebar"] .st-key-sidebar_nav_connections button[data-testid="stBaseButton-primary"]::before,
        [data-testid="stSidebar"] .st-key-sidebar_nav_profile button[data-testid="stBaseButton-primary"]::before,
        [data-testid="stSidebar"] .st-key-sidebar_nav_notifications button[data-testid="stBaseButton-primary"]::before { background-color:#BFDBFE; }
        [data-testid="stButton"] button,[data-testid="stFormSubmitButton"] button { border-radius:10px; border-color:var(--orbit-border); transition:all .18s ease; }
        [data-testid="stButton"] button:hover,[data-testid="stFormSubmitButton"] button:hover { color:var(--orbit-blue); border-color:var(--orbit-blue); box-shadow:0 4px 12px rgba(37,99,235,.12); }
        [data-testid="stFormSubmitButton"] button { background:#2563EB!important; background-image:none!important; border:1px solid #2563EB!important; color:#fff!important; box-shadow:0 7px 16px rgba(37,99,235,.18)!important; }
        [data-testid="stFormSubmitButton"] button:hover { background:#1D4ED8!important; background-image:none!important; border-color:#1D4ED8!important; color:#fff!important; box-shadow:0 9px 20px rgba(37,99,235,.25)!important; }
        [data-testid="stFormSubmitButton"] button:focus-visible { outline:3px solid rgba(96,165,250,.55)!important; outline-offset:2px; }
        button[kind="primary"],button[kind="primaryFormSubmit"] { background:#2563EB!important; color:#fff!important; border-color:#2563EB!important; }
        input:focus,textarea:focus { border-color:var(--orbit-blue)!important; box-shadow:0 0 0 1px var(--orbit-blue)!important; }
        [data-testid="stTabs"] [role="tab"][aria-selected="true"] { color:var(--orbit-blue); border-color:var(--orbit-blue); }
        [data-testid="stFileUploader"] section { background:#F8FAFF; border:1px dashed #B9CEF2; border-radius:12px; }
        [data-testid="stAlert"] { border-radius:12px; }
        .orbit-hero { max-width:560px; padding:1.5rem 1rem 2rem 0; }
        .orbit-hero-kicker,.orbit-page-kicker { color:var(--orbit-blue); text-transform:uppercase; letter-spacing:.12em; font-size:.75rem; font-weight:700; margin:2.5rem 0 .8rem; }
        .orbit-hero-title { color:var(--orbit-text); font-size:clamp(2.5rem,4vw,4rem); line-height:1.03; font-weight:800; letter-spacing:-.055em; margin:0 0 1rem; }
        .orbit-hero-copy { color:var(--orbit-muted); font-size:1.08rem; line-height:1.7; max-width:490px; }
        .orbit-page-kicker { margin:0 0 .25rem; font-size:.72rem; letter-spacing:.1em; }
        .orbit-page-subtitle { color:var(--orbit-muted); margin-top:-.2rem; margin-bottom:1.25rem; }
        .orbit-composer-heading { color:var(--orbit-text); font-size:1.05rem; font-weight:700; margin-bottom:.12rem; }
        @media(max-width:850px) { .orbit-hero { padding:1rem 0; } .orbit-hero-kicker { margin-top:1rem; } }
        @media(prefers-reduced-motion:reduce) { *,*::before,*::after { animation-duration:.01ms!important; transition-duration:.01ms!important; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def orbit_brand_markup(sidebar=False):
    """Return a connected-node logo and Orbit wordmark."""
    variant = "orbit-brand-sidebar" if sidebar else "orbit-brand-light"
    return f"""<div class="orbit-brand {variant}">
      <svg class="orbit-mark" viewBox="0 0 48 48" role="img" aria-label="Orbit network logo">
        <ellipse cx="24" cy="24" rx="19" ry="8.5" transform="rotate(-34 24 24)" fill="none" stroke="#60A5FA" stroke-width="2.2"/>
        <path d="M10.5 14.5 24 24l13.5 9.5" fill="none" stroke="#60A5FA" stroke-width="1.8" stroke-linecap="round"/>
        <circle cx="10.5" cy="14.5" r="3.4" fill="#2563EB" stroke="#EFF6FF" stroke-width="1.5"/>
        <circle cx="24" cy="24" r="4.1" fill="#60A5FA" stroke="#fff" stroke-width="1.5"/>
        <circle cx="37.5" cy="33.5" r="3.4" fill="#2563EB" stroke="#EFF6FF" stroke-width="1.5"/>
      </svg><span class="orbit-brand-name">Orbit</span>
    </div>"""


def render_network_background(intensity=0.22):
    """Render a lightweight, animated particle network beneath page content."""
    opacity = max(0.05, min(0.5, float(intensity)))
    html = f"""<!doctype html><html><head><style>
      html,body,canvas {{ width:100%; height:100%; margin:0; overflow:hidden; background:transparent; }}
      canvas {{ display:block; }}
    </style></head><body><canvas id="orbit-network" aria-hidden="true"></canvas>
    <script>
    (() => {{
      const canvas=document.getElementById("orbit-network"),ctx=canvas.getContext("2d",{{alpha:true}});
      const opacity={opacity:.3f}, reduced=matchMedia("(prefers-reduced-motion: reduce)").matches;
      let width=0,height=0,dpr=1,particles=[],lastFrame=0,lastTime=0;
      const maxParticles=58,linkDistance=158,rand=(a,b)=>a+Math.random()*(b-a);
      function resize() {{
        const r=canvas.getBoundingClientRect(); width=Math.max(1,r.width); height=Math.max(1,r.height);
        dpr=Math.min(devicePixelRatio||1,1.3); canvas.width=Math.round(width*dpr); canvas.height=Math.round(height*dpr); ctx.setTransform(dpr,0,0,dpr,0,0);
        const n=Math.min(maxParticles,Math.max(24,Math.round(width*height/22000)));
        while(particles.length<n) particles.push({{x:rand(0,width),y:rand(0,height),vx:rand(-10,10),vy:rand(-8,8),r:rand(1.25,2.35),glow:Math.random()<.16}});
        particles.length=n; draw();
      }}
      function draw() {{
        ctx.clearRect(0,0,width,height);
        for(let i=0;i<particles.length;i++) {{ const a=particles[i];
          for(let j=i+1;j<particles.length;j++) {{ const b=particles[j],dx=b.x-a.x,dy=b.y-a.y,d=Math.hypot(dx,dy);
            if(d<linkDistance) {{ ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.strokeStyle=`rgba(96,165,250,${{(1-d/linkDistance)*opacity*.52}})`;ctx.lineWidth=.8;ctx.stroke(); }}
          }}
          if(a.glow) {{ctx.shadowBlur=9;ctx.shadowColor="rgba(96,165,250,.42)";}}
          ctx.beginPath();ctx.arc(a.x,a.y,a.r,0,Math.PI*2);ctx.fillStyle=`rgba(37,99,235,${{opacity*1.6}})`;ctx.fill();ctx.shadowBlur=0;
        }}
      }}
      function tick(now) {{
        if(document.hidden) {{requestAnimationFrame(tick);return;}}
        if(now-lastFrame<33) {{requestAnimationFrame(tick);return;}}
        const dt=Math.min(.05,(now-(lastTime||now))/1000);lastTime=now;lastFrame=now;
        for(const p of particles) {{p.x+=p.vx*dt;p.y+=p.vy*dt;if(p.x<0){{p.x=0;p.vx=Math.abs(p.vx);}}else if(p.x>width){{p.x=width;p.vx=-Math.abs(p.vx);}}if(p.y<0){{p.y=0;p.vy=Math.abs(p.vy);}}else if(p.y>height){{p.y=height;p.vy=-Math.abs(p.vy);}}}}
        draw();requestAnimationFrame(tick);
      }}
      new ResizeObserver(resize).observe(canvas);resize();if(!reduced)requestAnimationFrame(tick);
    }})();
    </script></body></html>"""
    components.html(html, height=0, scrolling=False)


def _get_uploads_dir():
    """Return the dedicated uploads directory next to the active data folder."""
    return Path(storage.DATA_FOLDER).parent / "uploads"


def _resolve_image_path(image_path):
    """Resolve a stored relative or absolute image path to a Path object."""
    path = Path(image_path)
    if path.is_absolute():
        return path
    return Path(storage.DATA_FOLDER).parent / path


def _save_uploaded_image(uploaded_file):
    """Validate and save an uploaded PNG/JPG/JPEG image, returning (path_str, error_msg)."""
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix not in ALLOWED_IMAGE_EXTENSIONS:
        return None, "Only PNG, JPG, and JPEG images are allowed."

    data = uploaded_file.getvalue()
    if not data:
        return None, "Uploaded image file is empty."

    uploads_dir = _get_uploads_dir()
    uploads_dir.mkdir(parents=True, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}{suffix}"
    target_path = uploads_dir / unique_name
    target_path.write_bytes(data)

    return f"uploads/{unique_name}", None


def _cleanup_unused_image(image_path):
    """Delete an uploaded image file if no remaining post references it."""
    if not image_path:
        return
    if any(p.get("image_path") == image_path for p in st.session_state["posts"]):
        return
    resolved = _resolve_image_path(image_path)
    if resolved.exists() and resolved.is_file():
        resolved.unlink()



def init_session_state():
    """Load application data once per Streamlit session and initialize state keys."""
    if "data_loaded" not in st.session_state:
        try:
            students, connections, posts_list, notifs = storage.load_all_data()
        except ValueError as err:
            st.error(f"Unable to load application data: {err}")
            st.stop()

        st.session_state["students"] = students
        st.session_state["connections"] = connections
        st.session_state["posts"] = posts_list
        st.session_state["notifications"] = notifs
        st.session_state["data_loaded"] = True

    if "logged_in_user" not in st.session_state:
        st.session_state["logged_in_user"] = None

    if "flash_message" not in st.session_state:
        st.session_state["flash_message"] = None


def show_flash_message():
    """Display and clear any one-time status message stored across reruns."""
    flash = st.session_state.get("flash_message")
    if flash:
        level, text = flash
        if level == "success":
            st.success(text)
        else:
            st.error(text)
        st.session_state["flash_message"] = None


def render_auth_page():
    """Render the branded login and registration landing page."""
    show_flash_message()
    hero_col, auth_col = st.columns([1.05, .95], gap="large", vertical_alignment="center")

    with hero_col:
        st.markdown(orbit_brand_markup(), unsafe_allow_html=True)
        st.markdown(
            """
            <div class="orbit-hero">
              <div class="orbit-hero-kicker">A closer campus starts here</div>
              <h1 class="orbit-hero-title">Find your people.<br>Build your orbit.</h1>
              <p class="orbit-hero-copy">Meet students who share your interests, discover campus conversations, and grow a network that makes college feel more connected.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("Your campus. Your connections.")

    with auth_col:
        with st.container(border=True):
            st.markdown("### Welcome to Orbit")
            st.caption("Sign in or create your student account to get started.")
            login_tab, register_tab = st.tabs(["Login", "Register"])

            with login_tab:
                with st.form("login_form"):
                    username = st.text_input("Username", key="login_username")
                    password = st.text_input("Password", type="password", key="login_password")
                    submitted = st.form_submit_button("Log In", key="login_submit", type="primary", use_container_width=True)

                if submitted:
                    ok, msg = accounts.login_student(
                        st.session_state["students"], username, password, st.session_state
                    )
                    if ok:
                        st.session_state["flash_message"] = ("success", msg)
                        st.rerun()
                    else:
                        st.error(msg)

            with register_tab:
                with st.form("register_form"):
                    username = st.text_input("Username *", key="reg_username")
                    password = st.text_input("Password * (min 8 characters)", type="password", key="reg_password")
                    full_name = st.text_input("Full Name *", key="reg_full_name")
                    email = st.text_input("Email", key="reg_email")
                    department = st.text_input("Department (e.g. CSE, ECE)", key="reg_department")
                    year = st.number_input("Year", min_value=1, max_value=6, value=1, step=1, key="reg_year")
                    skills = st.text_input("Skills (comma-separated, e.g. Python, DSA)", key="reg_skills")
                    bio = st.text_area("Bio", key="reg_bio")
                    reg_submitted = st.form_submit_button("Create Account", key="reg_submit", type="primary", use_container_width=True)

                if reg_submitted:
                    ok, msg = accounts.register_student(
                        st.session_state["students"], st.session_state["connections"],
                        username, password, full_name, email=email, department=department,
                        year=int(year), skills=skills, bio=bio,
                    )
                    if ok:
                        storage.save_data("students.json", st.session_state["students"])
                        storage.save_data("connections.json", st.session_state["connections"])
                        st.success(f"{msg} You can now log in.")
                    else:
                        st.error(msg)


def _format_timestamp(iso_string):
    """Convert an ISO-8601 timestamp to a readable string, returning it unchanged on error."""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(iso_string)
        return dt.strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return iso_string



def render_post_card(post, current_user, key_prefix="feed"):
    """Render a post with optional image, delete button, likes, comments, and replies."""
    post_id = post["post_id"]

    with st.container(border=True):
        col_author, col_time, col_action = st.columns([3, 2, 1])

        with col_author:
            st.markdown(f"**{post['username']}**")

        with col_time:
            st.caption(_format_timestamp(post.get("created_at", "")))

        with col_action:
            if post.get("username") == current_user:
                if st.button("🗑️ Delete", key=f"{key_prefix}_delete_{post_id}"):
                    old_image = post.get("image_path")
                    del_msg = posts.delete_post(
                        st.session_state["posts"],
                        post_id,
                        current_user,
                    )
                    if del_msg == "Post deleted successfully.":
                        storage.save_data("posts.json", st.session_state["posts"])
                        _cleanup_unused_image(old_image)
                        st.session_state["flash_message"] = ("success", del_msg)
                        st.rerun()
                    else:
                        st.warning(del_msg)

        if post.get("text"):
            st.write(post["text"])

        image_path = post.get("image_path")
        if image_path:
            resolved_img = _resolve_image_path(image_path)
            if resolved_img.exists():
                st.image(str(resolved_img), width="stretch")
            else:
                st.caption(f"Image not available: {image_path}")

        # ---------------- LIKES ----------------
        likes = post.get("likes", [])
        like_count = len(likes)

        if current_user in likes:
            like_button_label = f"❤️ Unlike ({like_count})"
        else:
            like_button_label = f"🤍 Like ({like_count})"

        if st.button(
            like_button_label,
            key=f"{key_prefix}_like_{post_id}"
        ):
            if current_user in likes:
                posts.unlike_post(
                    st.session_state["posts"],
                    post_id,
                    current_user
                )
            else:
                posts.like_post(
                    st.session_state["posts"],
                    post_id,
                    current_user,
                    st.session_state["notifications"]
                )

            storage.save_data("posts.json", st.session_state["posts"])
            storage.save_data("notifications.json", st.session_state["notifications"])
            st.rerun()

        # ---------------- COMMENTS ----------------
        comments = post.get("comments", [])

        st.markdown(f"**Comments ({posts.count_comments(comments)})**")

        # New comment form
        with st.form(key=f"{key_prefix}_comment_form_{post_id}", clear_on_submit=True):
            comment_text = st.text_input(
                "Write a comment...",
                key=f"{key_prefix}_comment_text_{post_id}"
            )

            submit_comment = st.form_submit_button("Comment")

            if submit_comment:
                message = posts.add_comment(
                    st.session_state["posts"],
                    post_id,
                    current_user,
                    comment_text or "",
                    st.session_state["notifications"]
                )

                if message == "Comment added.":
                    storage.save_data("posts.json", st.session_state["posts"])
                    storage.save_data("notifications.json", st.session_state["notifications"])
                    st.rerun()
                else:
                    st.warning(message)

        # Display comments and nested replies
        def render_comment(comment, target_post_id, depth=0):
            indent = "　" * depth

            st.markdown(f"{indent}**{comment['username']}**")
            st.markdown(f"{indent}{comment['text']}")
            st.caption(_format_timestamp(comment.get("created_at", "")))

            # Reply form
            with st.form(
                key=f"{key_prefix}_reply_form_{target_post_id}_{comment['comment_id']}",
                clear_on_submit=True,
            ):
                reply_text = st.text_input(
                    "Reply...",
                    key=f"{key_prefix}_reply_text_{target_post_id}_{comment['comment_id']}"
                )

                submit_reply = st.form_submit_button("Reply")

                if submit_reply:
                    message = posts.add_comment(
                        st.session_state["posts"],
                        target_post_id,
                        current_user,
                        reply_text or "",
                        st.session_state["notifications"],
                        parent_comment_id=comment["comment_id"]
                    )

                    if message == "Reply added.":
                        storage.save_data("posts.json", st.session_state["posts"])
                        storage.save_data("notifications.json", st.session_state["notifications"])
                        st.rerun()
                    else:
                        st.warning(message)

            # Recursively display replies
            for reply in comment.get("replies", []):
                render_comment(reply, target_post_id, depth + 1)

        for comment in comments:
            render_comment(comment, post_id)


def render_home_feed(current_user):
    """Render the post composer and the home feed for the logged-in user."""
    st.markdown(
        '<div class="orbit-page-kicker">Your campus network</div><h2>Home Feed</h2>'
        '<p class="orbit-page-subtitle">See what your connections are sharing and add something to the conversation.</p>',
        unsafe_allow_html=True,
    )

    # --- Post Composer (text, image, or text+image) ---
    with st.form("create_post_form", clear_on_submit=True):
        st.markdown("<div class='orbit-composer-heading'>Share an update</div><div class='orbit-page-subtitle'>A thought, a question, or a campus moment.</div>", unsafe_allow_html=True)
        post_text = st.text_area(
            "What's on your mind?",
            placeholder="Share something with your connections...",
            key="new_post_text",
            height=100,
        )
        uploaded_image = st.file_uploader(
            "Attach an image (optional — PNG, JPG, JPEG)",
            type=["png", "jpg", "jpeg"],
            key="new_post_image",
        )
        if uploaded_image is not None:
            st.image(uploaded_image, caption="Selected image preview", width="stretch")

        post_submitted = st.form_submit_button("Post", key="create_post_submit")

    if post_submitted:
        image_path = None
        if uploaded_image is not None:
            image_path, img_err = _save_uploaded_image(uploaded_image)
            if img_err:
                st.error(img_err)
                return

        msg = posts.create_post(
            st.session_state["posts"],
            current_user,
            post_text or "",
            image_path=image_path,
        )
        if msg == "Post created successfully.":
            storage.save_data("posts.json", st.session_state["posts"])
            st.session_state["flash_message"] = ("success", msg)
            st.rerun()
        else:
            _cleanup_unused_image(image_path)
            st.warning(msg)

    st.divider()

    # --- Feed: own posts + accepted connections' posts, newest first ---
    own = posts.view_own_posts(st.session_state["posts"], current_user)
    connections_feed = posts.home_feed(
        st.session_state["posts"],
        current_user,
        st.session_state["connections"],
    )

    # Merge and deduplicate by post_id, then sort newest first
    seen_ids = set()
    merged = []
    for post in own + connections_feed:
        if post["post_id"] not in seen_ids:
            seen_ids.add(post["post_id"])
            merged.append(post)
    merged.sort(key=lambda p: p["created_at"], reverse=True)

    if not merged:
        st.info("No posts yet. Create your first post above, or connect with other students to see their posts here.")
        return

    for post in merged:
        render_post_card(post, current_user)


def _render_student_profile_details(username, current_user, connections, students):
    """Render a student's public profile details, mutual friends, and degree."""
    profile = accounts.view_profile(students, username)
    if not profile:
        st.warning("Profile not available.")
        return

    st.markdown(f"**Full Name:** {profile.get('full_name', username)}")
    if profile.get("department"):
        st.markdown(f"**Department:** {profile['department']}")
    if profile.get("year") not in ("", None):
        st.markdown(f"**Year:** {profile['year']}")
    if profile.get("email"):
        st.markdown(f"**Email:** {profile['email']}")
    skills = profile.get("skills", [])
    if skills:
        st.markdown(f"**Skills:** {', '.join(skills)}")
    if profile.get("bio"):
        st.markdown(f"**Bio:** {profile['bio']}")

    friend_count = len(network.view_connections(connections, username))
    st.caption(f"Connections: {friend_count}")

    if username != current_user:
        mutual = network.mutual_connections(connections, current_user, username)
        degree = network.connection_degree(connections, current_user, username)
        mutual_text = ", ".join(mutual) if mutual else "None"
        degree_text = f"{degree}" if degree is not None else "Not connected"
        st.caption(f"Mutual connections ({len(mutual)}): {mutual_text} | Degree: {degree_text}")


def _send_connection_request_action(current_user, target_user):
    """Send a connection request, create notification, and persist changes."""
    msg = network.send_request(st.session_state["connections"], current_user, target_user)
    if msg == "Connection request sent.":
        notifications.notify_connection_request(
            st.session_state["notifications"],
            current_user,
            target_user,
        )
        storage.save_data("connections.json", st.session_state["connections"])
        storage.save_data("notifications.json", st.session_state["notifications"])
        st.session_state["flash_message"] = ("success", msg)
        st.rerun()
    else:
        st.warning(msg)


def _accept_connection_request_action(sender, current_user):
    """Accept an incoming request, notify sender, and persist changes."""
    msg = network.accept_request(st.session_state["connections"], sender, current_user)
    if msg == "Connection accepted.":
        notifications.notify_connection_accepted(
            st.session_state["notifications"],
            sender,
            current_user,
        )
        storage.save_data("connections.json", st.session_state["connections"])
        storage.save_data("notifications.json", st.session_state["notifications"])
        st.session_state["flash_message"] = ("success", msg)
        st.rerun()
    else:
        st.warning(msg)


def render_connections_page(current_user):
    """Render directory, requests, accepted connections, Jaccard suggestions, and BFS finder."""
    st.subheader("Connections")

    students = st.session_state["students"]
    connections = st.session_state["connections"]
    accepted_friends = set(network.view_connections(connections, current_user))
    pending_list = connections.get("pending", [])
    incoming_senders = {r["sender"] for r in pending_list if r["receiver"] == current_user}
    outgoing_receivers = {r["receiver"] for r in pending_list if r["sender"] == current_user}

    tab_dir, tab_req, tab_conn, tab_sug, tab_bfs = st.tabs([
        "Student Directory",
        f"Requests ({len(incoming_senders) + len(outgoing_receivers)})",
        f"My Connections ({len(accepted_friends)})",
        "People You May Know",
        "How You're Connected",
    ])

    # 1. Student Directory & Search
    with tab_dir:
        query = st.text_input(
            "Search students by username, name, department, or skills",
            key="directory_search",
        ).strip().lower()

        other_users = [u for u in students if u != current_user]
        if query:
            filtered = []
            for uname in other_users:
                prof = accounts.view_profile(students, uname) or {}
                haystack = " ".join([
                    uname,
                    prof.get("full_name", ""),
                    prof.get("department", ""),
                    " ".join(prof.get("skills", [])),
                ]).lower()
                if query in haystack:
                    filtered.append(uname)
            other_users = filtered

        if not other_users:
            st.info("No matching students found.")
        else:
            for uname in other_users:
                prof = accounts.view_profile(students, uname) or {}
                with st.container(border=True):
                    col_info, col_btn = st.columns([3, 2])
                    with col_info:
                        st.markdown(f"**{prof.get('full_name', uname)}** (`{uname}`)")
                        dept = prof.get("department", "")
                        skills = ", ".join(prof.get("skills", []))
                        meta = " | ".join(part for part in [dept, skills] if part)
                        if meta:
                            st.caption(meta)
                    with col_btn:
                        if uname in accepted_friends:
                            if st.button("Remove Connection", key=f"dir_remove_{uname}"):
                                msg = network.remove_connection(connections, current_user, uname)
                                if msg == "Connection removed.":
                                    storage.save_data("connections.json", connections)
                                    st.session_state["flash_message"] = ("success", msg)
                                    st.rerun()
                                else:
                                    st.warning(msg)
                        elif uname in outgoing_receivers:
                            if st.button("Cancel Request", key=f"dir_cancel_{uname}"):
                                msg = network.cancel_request(connections, current_user, uname)
                                if msg == "Connection request cancelled.":
                                    storage.save_data("connections.json", connections)
                                    st.session_state["flash_message"] = ("success", msg)
                                    st.rerun()
                                else:
                                    st.warning(msg)
                        elif uname in incoming_senders:
                            c1, c2 = st.columns(2)
                            with c1:
                                if st.button("Accept", key=f"dir_accept_{uname}"):
                                    _accept_connection_request_action(uname, current_user)
                            with c2:
                                if st.button("Reject", key=f"dir_reject_{uname}"):
                                    msg = network.reject_request(connections, uname, current_user)
                                    if msg == "Connection request rejected.":
                                        storage.save_data("connections.json", connections)
                                        st.session_state["flash_message"] = ("success", msg)
                                        st.rerun()
                                    else:
                                        st.warning(msg)
                        else:
                            if st.button("Connect", key=f"dir_connect_{uname}"):
                                _send_connection_request_action(current_user, uname)

                    with st.expander("View Profile"):
                        _render_student_profile_details(uname, current_user, connections, students)

    # 2. Pending Requests (Received & Sent)
    with tab_req:
        st.markdown("#### Incoming Requests")
        incoming = [r for r in pending_list if r["receiver"] == current_user]
        if not incoming:
            st.info("No incoming connection requests.")
        else:
            for req in incoming:
                sender = req["sender"]
                prof = accounts.view_profile(students, sender) or {}
                with st.container(border=True):
                    c_info, c_acc, c_rej = st.columns([3, 1, 1])
                    with c_info:
                        st.markdown(f"**{prof.get('full_name', sender)}** (`{sender}`) wants to connect.")
                    with c_acc:
                        if st.button("Accept", key=f"req_accept_{sender}"):
                            _accept_connection_request_action(sender, current_user)
                    with c_rej:
                        if st.button("Reject", key=f"req_reject_{sender}"):
                            msg = network.reject_request(connections, sender, current_user)
                            if msg == "Connection request rejected.":
                                storage.save_data("connections.json", connections)
                                st.session_state["flash_message"] = ("success", msg)
                                st.rerun()
                            else:
                                st.warning(msg)

        st.markdown("#### Sent Requests")
        outgoing = [r for r in pending_list if r["sender"] == current_user]
        if not outgoing:
            st.info("No outgoing connection requests.")
        else:
            for req in outgoing:
                receiver = req["receiver"]
                prof = accounts.view_profile(students, receiver) or {}
                with st.container(border=True):
                    c_info, c_can = st.columns([4, 1])
                    with c_info:
                        st.markdown(f"Request sent to **{prof.get('full_name', receiver)}** (`{receiver}`).")
                    with c_can:
                        if st.button("Cancel", key=f"req_cancel_{receiver}"):
                            msg = network.cancel_request(connections, current_user, receiver)
                            if msg == "Connection request cancelled.":
                                storage.save_data("connections.json", connections)
                                st.session_state["flash_message"] = ("success", msg)
                                st.rerun()
                            else:
                                st.warning(msg)

    # 3. Accepted Connections & Mutual Friends
    with tab_conn:
        friends = network.view_connections(connections, current_user)
        if not friends:
            st.info("You have no accepted connections yet.")
        else:
            for friend in friends:
                prof = accounts.view_profile(students, friend) or {}
                mutual = network.mutual_connections(connections, current_user, friend)
                with st.container(border=True):
                    c_info, c_rem = st.columns([4, 1])
                    with c_info:
                        st.markdown(f"**{prof.get('full_name', friend)}** (`{friend}`)")
                        mutual_str = ", ".join(mutual) if mutual else "None"
                        st.caption(f"Mutual connections ({len(mutual)}): {mutual_str}")
                    with c_rem:
                        if st.button("Remove", key=f"conn_remove_{friend}"):
                            msg = network.remove_connection(connections, current_user, friend)
                            if msg == "Connection removed.":
                                storage.save_data("connections.json", connections)
                                st.session_state["flash_message"] = ("success", msg)
                                st.rerun()
                            else:
                                st.warning(msg)

                    with st.expander("View Profile"):
                        _render_student_profile_details(friend, current_user, connections, students)

    # 4. Connection Suggestions (Jaccard Coefficient)
    with tab_sug:
        suggestions = network.suggest_connections(connections, current_user)
        if not suggestions:
            st.info("No connection suggestions yet. Connect with a few peers first to see mutual-friend suggestions.")
        else:
            for candidate, score in suggestions:
                prof = accounts.view_profile(students, candidate) or {}
                mutual = network.mutual_connections(connections, current_user, candidate)
                with st.container(border=True):
                    c_info, c_btn = st.columns([4, 1])
                    with c_info:
                        st.markdown(f"**{prof.get('full_name', candidate)}** (`{candidate}`)")
                        mutual_str = ", ".join(mutual) if mutual else "None"
                        st.caption(
                            f"Match score: {score:.2f} | "
                            f"Mutual connections ({len(mutual)}): {mutual_str}"
                        )
                    with c_btn:
                        if st.button("Connect", key=f"sug_connect_{candidate}"):
                            _send_connection_request_action(current_user, candidate)

    # 5. BFS Shortest Path Finder
    with tab_bfs:
        all_vertices = list(connections.get("accepted", {}).keys())
        if len(all_vertices) < 2:
            st.info("At least two registered students are needed to find a connection path.")
        else:
            default_start_idx = all_vertices.index(current_user) if current_user in all_vertices else 0
            c1, c2 = st.columns(2)
            with c1:
                start_user = st.selectbox(
                    "From Student",
                    all_vertices,
                    index=default_start_idx,
                    key="bfs_start_user",
                )
            with c2:
                end_options = [u for u in all_vertices if u != start_user]
                end_user = st.selectbox(
                    "To Student",
                    end_options,
                    key="bfs_end_user",
                )

            path = network.shortest_path(connections, start_user, end_user)
            degree = network.connection_degree(connections, start_user, end_user)
            if path is None:
                st.info(f"No connection path exists between '{start_user}' and '{end_user}'.")
            else:
                st.success(f"Connection chain ({degree} degree(s) of separation): " + " → ".join(path))


def render_trending_page(current_user):
    """Render trending posts among accepted connections using the shared post card UI."""
    st.subheader("Trending Posts")
    trending = posts.trending_posts(
        st.session_state["posts"],
        current_user,
        st.session_state["connections"],
    )

    if not trending:
        st.info("No trending posts from your accepted connections yet.")
        return

    for post in trending:
        render_post_card(post, current_user, key_prefix="trending")


def render_notifications_page(current_user):
    """Render user notifications, read/unread status, and Mark All as Read."""
    st.subheader("Notifications")
    notifs = st.session_state["notifications"]
    items = notifications.view_notifications(notifs, current_user)
    unread = notifications.unread_count(notifs, current_user)

    c_info, c_btn = st.columns([3, 1])
    with c_info:
        st.caption(f"Total: {len(items)} | Unread: {unread}")
    with c_btn:
        if unread > 0:
            if st.button("Mark All as Read", key="mark_all_read_btn"):
                msg = notifications.mark_notifications_read(notifs, current_user)
                storage.save_data("notifications.json", notifs)
                st.session_state["flash_message"] = ("success", msg)
                st.rerun()

    if not items:
        st.info("You have no notifications yet.")
        return

    for item in reversed(items):
        status_label = "🔵 Unread" if not item.get("read", False) else "⚪ Read"
        with st.container(border=True):
            c_msg, c_time = st.columns([3, 2])
            with c_msg:
                st.markdown(f"{status_label} — {item.get('message', '')}")
            with c_time:
                st.caption(_format_timestamp(item.get("created_at", "")))


def render_profile_page(current_user):
    """Render the logged-in user's profile, edit form, and own posts."""
    st.subheader("My Profile")
    students = st.session_state["students"]
    connections = st.session_state["connections"]
    profile = accounts.view_profile(students, current_user)

    if profile is None:
        st.error("Profile not found.")
        return

    with st.container(border=True):
        _render_student_profile_details(current_user, current_user, connections, students)
        if profile.get("created_at"):
            st.caption(f"Joined: {_format_timestamp(profile['created_at'])}")

    with st.expander("Edit Profile"):
        current_year = profile.get("year", 1)
        year_val = current_year if isinstance(current_year, int) and 1 <= current_year <= 6 else 1
        with st.form("edit_profile_form"):
            full_name = st.text_input(
                "Full Name *",
                value=profile.get("full_name", ""),
                key="edit_full_name",
            )
            email = st.text_input(
                "Email",
                value=profile.get("email", ""),
                key="edit_email",
            )
            department = st.text_input(
                "Department",
                value=profile.get("department", ""),
                key="edit_department",
            )
            year = st.number_input(
                "Year",
                min_value=1,
                max_value=6,
                value=year_val,
                step=1,
                key="edit_year",
            )
            skills = st.text_input(
                "Skills (comma-separated)",
                value=", ".join(profile.get("skills", [])),
                key="edit_skills",
            )
            bio = st.text_area(
                "Bio",
                value=profile.get("bio", ""),
                key="edit_bio",
            )
            save_clicked = st.form_submit_button("Save Changes", key="edit_profile_submit")

        if save_clicked:
            ok, msg = accounts.update_profile(
                students,
                current_user,
                full_name=full_name,
                email=email,
                department=department,
                year=int(year),
                skills=skills,
                bio=bio,
            )
            if ok:
                storage.save_data("students.json", students)
                st.session_state["flash_message"] = ("success", msg)
                st.rerun()
            else:
                st.error(msg)

    st.divider()
    st.markdown("### My Posts")
    own_posts = sorted(
        posts.view_own_posts(st.session_state["posts"], current_user),
        key=lambda p: p["created_at"],
        reverse=True,
    )
    if not own_posts:
        st.info("You haven't created any posts yet.")
    else:
        for post in own_posts:
            render_post_card(post, current_user, key_prefix="profile")


def render_logged_in_app(current_user):
    """Render Orbit navigation and the active page for a logged-in student."""
    profile = accounts.view_profile(st.session_state["students"], current_user)
    display_name = profile["full_name"] if profile else current_user

    st.sidebar.markdown(orbit_brand_markup(sidebar=True), unsafe_allow_html=True)
    st.sidebar.markdown('<div class="orbit-sidebar-tagline">Your campus. Your connections.</div>', unsafe_allow_html=True)
    st.sidebar.markdown(f"**Signed in as:** {display_name}")

    unread = notifications.unread_count(st.session_state["notifications"], current_user)
    st.sidebar.markdown(
        f'<div class="orbit-unread"><span>Unread notifications</span><span class="orbit-unread-count">{unread}</span></div>',
        unsafe_allow_html=True,
    )

    nav_items = [
        ("Home", "home"),
        ("Trending", "trending"),
        ("Connections", "connections"),
        ("Profile", "profile"),
        ("Notifications", "notifications"),
    ]
    if st.session_state.get("sidebar_navigation") not in {item[0] for item in nav_items}:
        st.session_state["sidebar_navigation"] = "Home"

    for page_name, key_suffix in nav_items:
        if st.sidebar.button(
            page_name,
            key=f"sidebar_nav_{key_suffix}",
            type="primary" if st.session_state["sidebar_navigation"] == page_name else "secondary",
            use_container_width=True,
        ):
            st.session_state["sidebar_navigation"] = page_name
            st.rerun()

    page = st.session_state["sidebar_navigation"]

    if st.sidebar.button("Logout", key="logout_button", use_container_width=True):
        ok, msg = accounts.logout_student(st.session_state)
        if ok:
            st.session_state["flash_message"] = ("success", msg)
            st.rerun()
        else:
            st.error(msg)

    st.title(f"Welcome, {display_name}!")
    st.caption("Stay connected to the people and conversations shaping your campus.")
    show_flash_message()

    if page == "Home":
        render_home_feed(current_user)
    elif page == "Trending":
        render_trending_page(current_user)
    elif page == "Connections":
        render_connections_page(current_user)
    elif page == "Profile":
        render_profile_page(current_user)
    elif page == "Notifications":
        render_notifications_page(current_user)


def main():
    st.set_page_config(page_title="Orbit", page_icon=str(Path(__file__).with_name("orbit_logo.svg")), layout="wide")
    inject_orbit_theme()
    init_session_state()

    current_user = accounts.get_current_user(st.session_state)
    render_network_background(intensity=0.34 if current_user is None else 0.18)
    if current_user is None:
        render_auth_page()
    else:
        render_logged_in_app(current_user)


if __name__ == "__main__":
    main()
