from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from .chroma_memory import (
    search_project_memory
)

import zipfile
import os
import threading
import logging
import traceback
from .models import Project, Analysis

from .langgraph_workflow import (
    build_workflow
)

from .chroma_memory import (
    save_project_memory
)

from django.http import JsonResponse

from .chat_utils import parse_json_request_body
 
# HOME PAGE

def home(request):
    return render(request, 'index.html')


# SIGNUP

def signup(request):

    if request.method == "POST":

        fullname = request.POST['fullname']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password != confirm_password:

            messages.error(
                request,
                "Passwords do not match"
            )

            return redirect('signup')

        if User.objects.filter(
            email=email
        ).exists():

            messages.error(
                request,
                "Email already registered"
            )

            return redirect('signup')

        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=fullname,
            password=password
        )

        user.save()

        messages.success(
            request,
            "Account created successfully"
        )

        return redirect('login')

    return render(
        request,
        'signup.html'
    )


# LOGIN

def login_page(request):

    if request.method == "POST":

        email = request.POST['email']
        password = request.POST['password']

        user = authenticate(
            request,
            username=email,
            password=password
        )

        if user is not None:

            login(
                request,
                user
            )

            return redirect(
                'dashboard'
            )

        messages.error(
            request,
            "Invalid email or password"
        )

        return redirect(
            'login'
        )

    return render(
        request,
        'login.html'
    )


# LOGOUT

def logout_page(request):

    logout(request)

    return redirect('home')


# DASHBOARD

def dashboard(request):

    if not request.user.is_authenticated:
        return redirect('login')

    projects = Project.objects.filter(
        user=request.user
    )

    latest_analysis = None
    latest_project = None

    if projects.exists():

        latest_project = projects.last()

        latest_analysis = Analysis.objects.filter(
            project=latest_project
        ).first()

    context = {

        'project_count': projects.count(),

        'analysis': latest_analysis,

        'latest_project': latest_project,

        'projects': projects.order_by(
            '-created_at'
        )

    }

    return render(
        request,
        'dashboard.html',
        context
    )


# PROJECT CHAT (Floating widget)

def project_chat(request, project_id: int):

    if not request.user.is_authenticated:
        return JsonResponse(
            {'error': 'Unauthorized'},
            status=401
        )

    if request.method != 'POST':
        return JsonResponse(
            {'error': 'POST required'},
            status=405
        )

    project = Project.objects.filter(
        id=project_id,
        user=request.user
    ).first()

    if not project:
        return JsonResponse(
            {'error': 'Project not found'},
            status=404
        )

    analysis = Analysis.objects.filter(
        project=project
    ).first()

    if not analysis:
        return JsonResponse(
            {
                'error':
                'No analysis found for this project.'
            },
            status=404
        )

    payload = parse_json_request_body(
        request
    )

    question = (
        payload.get('question')
        or ''
    ).strip()

    if not question:
        return JsonResponse(
            {
                'error':
                'question is required'
            },
            status=400
        )

    from .qwen_agent import (
        analyze_project
    )

    memory_result = search_project_memory(
        question
    )

    retrieved_context = ""

    try:

        retrieved_context = (
            memory_result[
                "documents"
            ][0][0]
        )

    except:

        retrieved_context = (
            "No project memory found."
        )

    prompt = f"""
You are CodeCompass AI.

Answer ONLY using the
retrieved project memory.

Project:
{project.name}

Retrieved Memory:

{retrieved_context}

Question:

{question}

Provide a concise answer.
"""

    try:

        raw = analyze_project(
            prompt
        )

        answer = (
            raw.strip()
            if isinstance(
                raw,
                str
            )
            else str(raw)
        )

        return JsonResponse({

            'answer': answer,

            'project_id':
            project_id,

            'question':
            question

        })

    except Exception as e:

        logging.getLogger(__name__).exception("CHATBOT ERROR: %s", e)

        return JsonResponse(
            {
                'error':
                'Failed to generate answer.'
            },
            status=500
        )

# DEMO


def compute_metrics(total_files: int, total_lines: int, large_files: int, test_files: int, project_summary: str, detected_tech: set, total_classes: int=0, total_functions: int=0):
    """Compute health_score, risks_found, recommendations using stronger heuristics.
    Penalizes: missing tests, markup-only projects, large files, code markers, low code structure.
    """
    # Start from 100 and apply penalties
    health = 100

    # NO TESTS PENALTY (apply regardless of project size)
    if total_files > 0 and test_files == 0:
        health -= 15  # strong penalty for no tests

    # Markup-only project (HTML/CSS only, no backend code)
    has_code = bool(detected_tech & {"Python", "Java", "JavaScript", "TypeScript", "NodeJS", "Django", "Flask", "React"})
    if not has_code and total_files > 0:
        health -= 5  # small penalty for frontend-only

    # No code structure (0 classes and 0 functions)
    if total_files > 0 and total_classes == 0 and total_functions == 0 and has_code:
        health -= 8

    # Lines of code penalties (stronger)
    if total_lines > 20000:
        health -= 40
    elif total_lines > 12000:
        health -= 30
    elif total_lines > 7000:
        health -= 20
    elif total_lines > 3500:
        health -= 12
    elif total_lines > 1500:
        health -= 6

    # Large files penalty
    if large_files:
        health -= min(10, large_files * 2)

    # Presence of TODO/FIXME/HACK markers increases risk and lowers health
    markers = 0
    for token in ("TODO", "FIXME", "HACK"):
        markers += project_summary.count(token)
    if markers:
        health -= min(15, markers * 2)

    # Clamp health
    health = max(0, min(100, health))

    # Risk scoring (also based on missing tests and code structure)
    risks = 0
    if total_files > 0 and test_files == 0:
        risks += 2  # strong risk for no tests
    if total_lines > 3000:
        risks += 1
    if total_files > 50:
        risks += 1
    if large_files > 3:
        risks += 1
    if markers:
        risks += 1
    if has_code and total_classes == 0 and total_functions == 0 and total_files > 0:
        risks += 1  # risk if code files exist but no structure

    # Recommendations count: at least equal to risks, plus suggestions based on missing tests or large files
    recommendations = max(risks, 1)  # at least 1 recommendation
    if test_files == 0 and total_files > 0:
        recommendations += 1
    if large_files > 0:
        recommendations += 1

    return health, risks, recommendations


def demo(request):

    return render(
        request,
        'demo.html'
    )

# UPLOAD PAGE

def upload_page(request):

    if not request.user.is_authenticated:
        return redirect('login')

    return render(
        request,
        'upload.html'
    )


# ANALYSIS PAGE

def analysis_page(request):

    if not request.user.is_authenticated:
        return redirect('login')

    latest_project = Project.objects.filter(
        user=request.user
    ).last()

    analysis = None

    if latest_project:

        analysis = Analysis.objects.filter(
            project=latest_project
        ).first()

    context = {

        'project': latest_project,

        'analysis': analysis

    }

    return render(
        request,
        'analysis.html',
        context
    )


# ANALYSIS LOADING PAGE

def analysis_loading(request):

    if not request.user.is_authenticated:
        return redirect('login')

    return render(
        request,
        'analysis_loading.html'
    )

# REPORT PAGE

def report_page(request, project_id=None):

    if not request.user.is_authenticated:
        return redirect('login')

    projects = Project.objects.filter(
        user=request.user
    ).order_by('-created_at')

    latest_project = None

    if project_id:

        latest_project = Project.objects.filter(
            id=project_id,
            user=request.user
        ).first()

    else:

        latest_project = projects.first()

    analysis = None

    if latest_project:

        analysis = Analysis.objects.filter(
            project=latest_project
        ).first()

    context = {

        'projects': projects,

        'project': latest_project,

        'analysis': analysis

    }

    return render(
        request,
        'report.html',
        context
    )

def download_pdf(request):

    latest_project = Project.objects.filter(
        user=request.user
    ).last()

    analysis = None

    if latest_project:

        analysis = Analysis.objects.filter(
            project=latest_project
        ).first()

    response = HttpResponse(
        content_type='application/pdf'
    )

    response[
        'Content-Disposition'
    ] = 'attachment; filename="CodeCompass_Report.pdf"'

    p = canvas.Canvas(response)

    page_width, page_height = p._pagesize
    left_margin = 50
    right_margin = 50
    top_margin = 60
    bottom_margin = 50
    max_text_width = page_width - left_margin - right_margin

    # UI-like colors (matching theme variables used in CSS)
    bg = (6/255, 16/255, 18/255)          # #061012
    surface = (16/255, 35/255, 41/255)  # #102329-ish
    border = (45/255, 212/255, 191/255)  # #2dd4bf-ish
    gold = (242/255, 184/255, 75/255)    # #f2b84b
    accent = (20/255, 184/255, 166/255) # #14b8a6
    muted = (169/255, 187/255, 184/255)  # #a9bbb8

    def set_color(rgb):
        p.setFillColorRGB(*rgb)
        p.setStrokeColorRGB(*rgb)

    def draw_page_header(y_top):
        # Header background band
        header_h = 54
        p.setFillColorRGB(*surface)
        p.rect(left_margin-10, y_top - header_h, page_width - (left_margin-10) - (right_margin-10), header_h, fill=1, stroke=0)

        # Eyebrow
        p.setFillColorRGB(*accent)
        p.setFont("Helvetica-Bold", 10)
        eyebrow = "CodeCompass AI"
        p.drawString(left_margin, y_top - 18, eyebrow)

        # Title
        p.setFillColorRGB(*gold)
        p.setFont("Helvetica-Bold", 18)
        p.drawString(left_margin, y_top - 40, "Project Report")

        # Divider line
        p.setStrokeColorRGB(*border)
        p.setLineWidth(1)
        p.line(left_margin, y_top - header_h + 10, page_width - right_margin, y_top - header_h + 10)

        return y_top - header_h - 18

    def ensure_space(current_y, needed_height):
        nonlocal p
        if current_y - needed_height < bottom_margin:
            # new page: redraw header
            p.showPage()
            y_new = page_height
            # re-draw header content
            return draw_page_header(y_new)
        return current_y

    def draw_section_title(text, y):
        p.setFillColorRGB(*gold)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(left_margin, y, text)
        return y - 18

    def draw_wrapped(text, y, font_name="Helvetica", font_size=10, leading=13, color_rgb=None):
        if not text:
            return y

        from reportlab.lib.utils import simpleSplit

        if color_rgb:
            p.setFillColorRGB(*color_rgb)
        else:
            p.setFillColorRGB(*muted)

        p.setFont(font_name, font_size)
        wrapped_lines = simpleSplit(text, font_name, font_size, max_text_width)

        current_y = y
        for line in wrapped_lines:
            current_y = ensure_space(current_y, leading)
            p.drawString(left_margin, current_y, line)
            current_y -= leading
        return current_y

    # start at top after first header
    y = draw_page_header(page_height)


    if latest_project and analysis:
        # Project meta
        p.setFillColorRGB(*gold)
        p.setFont("Helvetica-Bold", 11)
        y = ensure_space(y, 22)
        p.drawString(left_margin, y, f"Project: {latest_project.name}")
        y -= 18

        summary_line = (
            f"Health Score: {analysis.health_score}%    |    "
            f"Risk Assessment: {analysis.risks_found} risks    |    "
            f"Recommendations: {analysis.recommendations}    |    "
            f"Total Files: {analysis.total_files}    |    "
            f"LOC: {analysis.lines_of_code}"
        )
        y = draw_wrapped(
            summary_line,
            y,
            font_name="Helvetica",
            font_size=10,
            leading=14,
            color_rgb=muted
        )

        if analysis.technologies:
            y -= 6
            y = draw_wrapped(
                f"Technologies: {analysis.technologies}",
                y,
                font_name="Helvetica",
                font_size=10,
                leading=14,
                color_rgb=muted
            )

        y -= 10

        sections = [
            ("Architecture Agent", analysis.architecture_report),
            ("Technical Debt Agent", analysis.technical_debt_report),
            ("Risk Prediction Agent", analysis.risk_report),
            ("Recommendation Agent", analysis.recommendation_report),
        ]

        for title, body in sections:
            y = ensure_space(y, 34)
            y = draw_section_title(title, y)
            y = draw_wrapped(body, y, font_name="Helvetica", font_size=10, leading=13, color_rgb=muted)
            y -= 10
    else:
        y = draw_wrapped(
            "No project analysis found yet. Please run an analysis first.",
            y,
            font_name="Helvetica",
            font_size=12,
            leading=16,
            color_rgb=muted
        )


    p.showPage()
    p.save()

    return response

# SAVE GITHUB PROJECT

def save_project(request):

    """Save GitHub URL entered from upload.html.

    GitHub flow previously only persisted the URL, so Analysis stayed empty.
    Now we auto-download the repo as a ZIP (default branch) and run the same
    ZIP-based analysis pipeline.
    """

    if request.method == "POST":

        # require authentication
        if not request.user.is_authenticated:
            return redirect('login')

        project_name = request.POST.get('project_name')
        github_url = (request.POST.get('github_url') or '').strip()

        project = Project.objects.create(
            user=request.user,
            name=project_name,
            github_url=github_url
        )

        # --- Auto-download GitHub repo as ZIP and analyze ---
        try:
            import io
            import re
            import requests
            from django.core.files.base import ContentFile

            # Normalize many common forms into owner/repo
            owner = None
            repo = None

            def _clean_repo_name(name: str) -> str:
                # strip .git and trailing slashes
                name = name.strip()
                if name.endswith('.git'):
                    name = name[:-4]
                if name.endswith('/'):
                    name = name[:-1]
                return name

            # Try direct HTTP/HTTPS URL
            m = re.match(r"^https?://(?:(?:www\.)?github\.com)/(?P<owner>[^/]+)/(?P<repo>[^/#?]+)", github_url)
            if m:
                owner = m.group('owner')
                repo = _clean_repo_name(m.group('repo'))

            # Try without scheme (github.com/owner/repo)
            if not owner:
                m2 = re.match(r"^(?:(?:www\.)?github\.com)/(?P<owner>[^/]+)/(?P<repo>[^/#?]+)", github_url)
                if m2:
                    owner = m2.group('owner')
                    repo = _clean_repo_name(m2.group('repo'))

            # Try SSH style: git@github.com:owner/repo.git
            if not owner and github_url.startswith('git@github.com:'):
                rest = github_url.split(':', 1)[1]
                parts = rest.split('/')
                if len(parts) >= 2:
                    owner = parts[0]
                    repo = _clean_repo_name(parts[1])

            # Try plain owner/repo
            if not owner:
                parts = github_url.split('/')
                if len(parts) == 2 and parts[0] and parts[1]:
                    owner = parts[0]
                    repo = _clean_repo_name(parts[1])

            if not owner or not repo:
                logging.getLogger(__name__).warning("Unsupported GitHub URL format: %s", github_url)
                raise ValueError("Unsupported GitHub URL format")

            logging.getLogger(__name__).info("Normalized GitHub URL to owner=%s repo=%s", owner, repo)

            # Download default-branch ZIP using GitHub's auto-archive endpoint
            # Example: https://github.com/<owner>/<repo>/archive/refs/heads/master.zip
            # We'll use /heads/main.zip if master doesn't work.
            zip_urls = [
                f"https://github.com/{owner}/{repo}/archive/refs/heads/main.zip",
                f"https://github.com/{owner}/{repo}/archive/refs/heads/master.zip",
                f"https://github.com/{owner}/{repo}/archive/refs/heads/master.zip?dummy=1",  # fallback
                # API zipball endpoint (may redirect to archive storage)
                f"https://api.github.com/repos/{owner}/{repo}/zipball",
            ]

            zip_bytes = None
            last_err = None
            headers = {"User-Agent": "CodeCompass/1.0"}
            for u in zip_urls:
                try:
                    r = requests.get(u, timeout=60, headers=headers)
                    if r.status_code == 200 and r.content:
                        zip_bytes = r.content
                        break
                    # Sometimes GitHub returns a redirect with 302 to an archive URL
                    if r.status_code in (302, 301) and r.headers.get('Location'):
                        try:
                            rr = requests.get(r.headers.get('Location'), timeout=60, headers=headers)
                            if rr.status_code == 200 and rr.content:
                                zip_bytes = rr.content
                                break
                        except Exception as _:
                            pass
                except Exception as e:
                    last_err = e

            if not zip_bytes:
                raise ValueError(f"Failed to download ZIP from GitHub. Last error: {last_err}")

            # Save ZIP to the existing project's zip_file field
            filename = f"{project.name}.zip"
            project.zip_file.save(filename, ContentFile(zip_bytes), save=True)

            # Run analysis in background thread and show loading UI immediately
            def _bg():
                try:
                    analyze_project_from_zip(project.id)
                except Exception:
                    logging.getLogger(__name__).exception("Background analysis failed for project=%s", project.id)

            threading.Thread(target=_bg, daemon=True).start()

            return redirect('analysis_loading')

            # Reuse the existing analysis logic by essentially doing what upload_zip does.
            # We call build_workflow via the same code path by duplicating the minimal
            # wrapper: create a local fake request is brittle, so run the core analysis
            # directly by reusing upload_zip's inner logic is best. For now, we redirect
            # to analysis_loading and let the user refresh? => not acceptable.
            # Therefore, we invoke the upload_zip logic by extracting it would require refactor.
            # Instead: call a small helper implemented inline below by delegating to a new
            # local function.

            # Inline analysis reuse (keeps changes minimal and ensures Analysis is created)
            # If we didn't return above (shouldn't happen), fall through to analysis.
            total_files = 0
            total_lines = 0
            total_classes = 0
            total_functions = 0
            large_files = 0
            test_files = 0
            detected_tech = set()
            project_summary = ""

            MAX_DECODE_BYTES = 256_000
            CODE_EXTENSIONS = {
                '.py', '.js', '.ts', '.java', '.jsx', '.tsx', '.html', '.css', '.json', '.md', '.yml', '.yaml', '.txt', '.xml'
            }
            BINARY_EXTENSIONS = {
                '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.pdf', '.zip', '.tar', '.gz', '.7z', '.rar',
                '.exe', '.dll', '.so', '.dylib', '.bin', '.class', '.jar', '.war', '.ear', '.mp3', '.mp4', '.mov', '.avi', '.mkv'
            }

            def _is_probably_binary(member_name: str) -> bool:
                lower = member_name.lower()
                if any(lower.endswith(ext) for ext in BINARY_EXTENSIONS):
                    return True
                if 'node_modules/' in lower or '.git/' in lower or lower.endswith('.lock'):
                    return True
                return False

            try:
                # Analyze from the saved zip_file on disk
                zip_path = project.zip_file.path
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    infos = zip_ref.infolist()
                    members = [info.filename for info in infos]

                    # GitHub archives typically wrap everything in a top-level folder:
                    #   repo-branch-root/<actual files...>
                    # Normalize by stripping that prefix, so counts/extension checks work.
                    top_prefix = None
                    for m in members:
                        if not m or m.endswith('/'):
                            continue
                        parts = m.split('/')
                        if len(parts) > 1:
                            top_prefix = parts[0]
                        break

                    for info in infos:
                        if info.is_dir():
                            continue

                        file_name = info.filename
                        if not file_name:
                            continue

                        normalized_name = file_name
                        if top_prefix and normalized_name.startswith(top_prefix + '/'):
                            normalized_name = normalized_name[len(top_prefix) + 1:]

                        # Count every non-directory member
                        total_files += 1

                        name_for_detection = normalized_name.lower()

                        if name_for_detection.endswith('.py'):
                            detected_tech.add("Python")
                        if name_for_detection.endswith('.html'):
                            detected_tech.add("HTML")
                        if name_for_detection.endswith('.css'):
                            detected_tech.add("CSS")
                        if name_for_detection.endswith('.js'):
                            detected_tech.add("JavaScript")
                        if name_for_detection.endswith('.java'):
                            detected_tech.add("Java")
                        if name_for_detection.endswith('.jsx'):
                            detected_tech.add("React")
                        if name_for_detection.endswith('.ts'):
                            detected_tech.add("TypeScript")
                        if "manage.py" in name_for_detection:
                            detected_tech.add("Django")
                        if "app.py" in name_for_detection:
                            detected_tech.add("Flask")
                        if "package.json" in name_for_detection:
                            detected_tech.add("NodeJS")

                        try:
                            with zip_ref.open(file_name) as f:
                                # Binary heuristic: apply to original member path
                                if _is_probably_binary(file_name):
                                    continue

                                raw = f.read(MAX_DECODE_BYTES)
                                content = raw.decode('utf-8', errors='ignore')

                                project_summary += (
                                    f"\nFILE: {normalized_name}\n"
                                    + content[:500]
                                    + "\n"
                                )

                                lines = content.splitlines()
                                total_lines += len(lines)

                                if len(lines) > 300:
                                    large_files += 1

                                for line in lines:
                                    stripped = line.strip()
                                    if stripped.startswith("class "):
                                        total_classes += 1
                                    if stripped.startswith("def "):
                                        total_functions += 1

                                if "test" in name_for_detection:
                                    test_files += 1
                        except Exception:
                            pass

                # Compute health score, risks, recommendations with helper
                health_score, risks_found, recommendations = compute_metrics(
                    total_files,
                    total_lines,
                    large_files,
                    test_files,
                    project_summary,
                    detected_tech,
                    total_classes,
                    total_functions,
                )

                tech_string = ", ".join(sorted(detected_tech))

                # Run AI workflow, but DO NOT let it break the metrics persistence.
                # If workflow fails, still save health_score/total_files/lines_of_code.
                result = {}
                try:
                    workflow = build_workflow()
                    result = workflow.invoke({
                        "total_files": total_files,
                        "lines_of_code": total_lines,
                        "health_score": health_score,
                        "technologies": tech_string,
                        "total_classes": total_classes,
                        "total_functions": total_functions,
                        "large_files": large_files,
                        "test_files": test_files,
                        "project_summary": project_summary,
                        "full_report": "",
                        "architecture_report": "",
                        "technical_debt_report": "",
                        "risk_report": "",
                        "recommendation_report": ""
                    })
                except Exception as workflow_err:
                    logging.getLogger(__name__).exception("GITHUB WORKFLOW ERROR: %s", workflow_err)

                # Ensure we only create/update once with computed metrics.
                logging.getLogger(__name__).info(
                    "Saving Analysis for project=%s: files=%d lines=%d health=%d",
                    project.name,
                    total_files,
                    total_lines,
                    health_score,
                )

                Analysis.objects.update_or_create(
                    project=project,
                    defaults={
                        "health_score": health_score,
                        "risks_found": risks_found,
                        "recommendations": recommendations,
                        "total_files": total_files,
                        "lines_of_code": total_lines,
                        "total_classes": total_classes,
                        "total_functions": total_functions,
                        "large_files": large_files,
                        "test_files": test_files,
                        "complexity": 0,
                        "maintainability": 0,
                        "technologies": tech_string,
                        "architecture_report": result.get("architecture_report", ""),
                        "technical_debt_report": result.get("technical_debt_report", ""),
                        "risk_report": result.get("risk_report", ""),
                        "recommendation_report": result.get("recommendation_report", ""),
                    }
                )

                # Only save memory if we actually produced reports.
                if result:
                    save_project_memory(
                        project.name,
                        result.get("architecture_report", ""),
                        result.get("technical_debt_report", ""),
                        result.get("risk_report", ""),
                        result.get("recommendation_report", ""),
                    )

            except Exception as analysis_err:
                logging.getLogger(__name__).exception("GITHUB ANALYSIS ERROR: %s", analysis_err)
                # Keep project but do not crash; metrics will remain defaults if we couldn't parse zip.

        except Exception as e:
            logging.getLogger(__name__).exception("GITHUB DOWNLOAD ERROR: %s", e)

    return redirect('upload')




def what_if_page(request, project_id: int):
    if not request.user.is_authenticated:
        return redirect('login')

    projects = Project.objects.filter(
        user=request.user
    ).order_by('-created_at')

    project = Project.objects.filter(id=project_id, user=request.user).first()
    if not project:
        return redirect('projects')

    return render(
        request,
        'what_if.html',
        {
            'projects': projects,
            'project': project
        }
    )


def analyze_project_from_zip(project_id: int):
    """Background helper: open project's zip_file, compute metrics, run workflow, save Analysis and memory."""
    logger = logging.getLogger(__name__)
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        logger.error("analyze_project_from_zip: project %s not found", project_id)
        return

    try:
        zip_path = project.zip_file.path
        # reuse the same analysis heuristics as upload_zip
        total_files = 0
        total_lines = 0
        total_classes = 0
        total_functions = 0
        large_files = 0
        test_files = 0
        detected_tech = set()
        project_summary = ""

        MAX_DECODE_BYTES = 256_000
        BINARY_EXTENSIONS = {
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.pdf', '.zip', '.tar', '.gz', '.7z', '.rar',
            '.exe', '.dll', '.so', '.dylib', '.bin', '.class', '.jar', '.war', '.ear', '.mp3', '.mp4', '.mov', '.avi', '.mkv'
        }

        def _is_probably_binary(member_name: str) -> bool:
            lower = member_name.lower()
            if any(lower.endswith(ext) for ext in BINARY_EXTENSIONS):
                return True
            if 'node_modules/' in lower or '.git/' in lower or lower.endswith('.lock'):
                return True
            return False

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            infos = zip_ref.infolist()
            members = [info.filename for info in infos]
            top_prefix = None
            for m in members:
                if not m or m.endswith('/'):
                    continue
                parts = m.split('/')
                if len(parts) > 1:
                    top_prefix = parts[0]
                break

            for info in infos:
                if info.is_dir():
                    continue

                file_name = info.filename
                if not file_name:
                    continue

                normalized_name = file_name
                if top_prefix and normalized_name.startswith(top_prefix + '/'):
                    normalized_name = normalized_name[len(top_prefix) + 1:]

                total_files += 1

                name_for_detection = normalized_name.lower()

                if name_for_detection.endswith('.py'):
                    detected_tech.add("Python")
                if name_for_detection.endswith('.html'):
                    detected_tech.add("HTML")
                if name_for_detection.endswith('.css'):
                    detected_tech.add("CSS")
                if name_for_detection.endswith('.js'):
                    detected_tech.add("JavaScript")
                if name_for_detection.endswith('.java'):
                    detected_tech.add("Java")
                if name_for_detection.endswith('.jsx'):
                    detected_tech.add("React")
                if name_for_detection.endswith('.ts'):
                    detected_tech.add("TypeScript")
                if "manage.py" in name_for_detection:
                    detected_tech.add("Django")
                if "app.py" in name_for_detection:
                    detected_tech.add("Flask")
                if "package.json" in name_for_detection:
                    detected_tech.add("NodeJS")

                try:
                    with zip_ref.open(file_name) as f:
                        if _is_probably_binary(file_name):
                            continue

                        raw = f.read(MAX_DECODE_BYTES)
                        content = raw.decode('utf-8', errors='ignore')

                        project_summary += (
                            f"\nFILE: {normalized_name}\n" + content[:500] + "\n"
                        )

                        lines = content.splitlines()
                        total_lines += len(lines)

                        if len(lines) > 300:
                            large_files += 1

                        for line in lines:
                            stripped = line.strip()
                            if stripped.startswith("class "):
                                total_classes += 1
                            if stripped.startswith("def "):
                                total_functions += 1

                        if "test" in name_for_detection:
                            test_files += 1
                except Exception:
                    pass

        # compute scores using central helper
        health_score, risks_found, recommendations = compute_metrics(
            total_files,
            total_lines,
            large_files,
            test_files,
            project_summary,
            detected_tech,
            total_classes,
            total_functions,
        )

        tech_string = ", ".join(sorted(detected_tech))

        logger.info("Background analysis for project=%s: files=%d lines=%d health=%d", project.name, total_files, total_lines, health_score)

        result = {}
        try:
            workflow = build_workflow()
            result = workflow.invoke({
                "total_files": total_files,
                "lines_of_code": total_lines,
                "health_score": health_score,
                "technologies": tech_string,
                "total_classes": total_classes,
                "total_functions": total_functions,
                "large_files": large_files,
                "test_files": test_files,
                "project_summary": project_summary,
                "full_report": "",
                "architecture_report": "",
                "technical_debt_report": "",
                "risk_report": "",
                "recommendation_report": ""
            })
        except Exception:
            logger.exception("GITHUB WORKFLOW ERROR during background analysis for project=%s", project.id)

        Analysis.objects.update_or_create(
            project=project,
            defaults={
                "health_score": health_score,
                "risks_found": risks_found,
                "recommendations": recommendations,
                "total_files": total_files,
                "lines_of_code": total_lines,
                "total_classes": total_classes,
                "total_functions": total_functions,
                "large_files": large_files,
                "test_files": test_files,
                "complexity": 0,
                "maintainability": 0,
                "technologies": tech_string,
                "architecture_report": result.get("architecture_report", ""),
                "technical_debt_report": result.get("technical_debt_report", ""),
                "risk_report": result.get("risk_report", ""),
                "recommendation_report": result.get("recommendation_report", ""),
            }
        )

        if result:
            save_project_memory(
                project.name,
                result.get("architecture_report", ""),
                result.get("technical_debt_report", ""),
                result.get("risk_report", ""),
                result.get("recommendation_report", ""),
            )

    except Exception:
        logger.exception("ZIP ANALYSIS ERROR in background for project=%s", project_id)



def settings_page(request):

    if not request.user.is_authenticated:
        return redirect('login')

    projects = Project.objects.filter(
        user=request.user
    ).order_by('-created_at')

    latest_project = projects.first()

    return render(
        request,
        'settings.html',
        {
            'projects': projects,
            'latest_project': latest_project
        }
    )


def what_if_simulator(request, project_id: int):
    if not request.user.is_authenticated:
        return redirect('login')


    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    project = Project.objects.filter(id=project_id, user=request.user).first()
    if not project:
        return JsonResponse({'error': 'Project not found'}, status=404)

    analysis = Analysis.objects.filter(project=project).first()
    if not analysis:
        return JsonResponse({'error': 'No analysis found for this project'}, status=404)

    try:
        import json
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        payload = {}

    scenario_input = (payload.get('scenario_input') or '').strip()
    scenario_type = (payload.get('scenario_type') or 'technology_swap').strip()

    if not scenario_input:
        return JsonResponse({'error': 'scenario_input is required'}, status=400)

    from .qwen_agent import analyze_project

    # Ask for multiple outcome branches; require strict JSON output.
    prompt = f"""
You are an expert software engineering decision assistant.

Context: We already analyzed the codebase of Project '{project.name}'.

Existing analysis:
- Health Score: {analysis.health_score}
- Risks Found: {analysis.risks_found}
- Recommendations count: {analysis.recommendations}
- Technologies detected: {analysis.technologies}

Architecture report:
{analysis.architecture_report}

Risk report:
{analysis.risk_report}

Recommendation report:
{analysis.recommendation_report}

User request (What-If):
{scenario_input}

Scenario type:
{scenario_type}

Task:
Return a JSON object with this exact structure:
{{
  "answers": [
    {{
      "title": "Outcome branch title",
      "likelihood": "Low|Medium|High",
      "impact": "Short impact summary",
      "changes": ["bulleted changes / consequences"],
      "reasoning": "1-3 short paragraphs grounded in the provided reports"
    }}
  ]
}}

Rules:
- Provide ALL plausible branches (at least 6). Include branches for: performance, maintainability, risks, migration/effort, security, and developer productivity/learning curve.
- Keep reasoning grounded; do NOT invent files or metrics not present.
- Output ONLY valid JSON (no markdown).
"""

    try:
        raw = analyze_project(prompt)
        # qwen_agent returns response.content; could already be JSON.
        import json
        parsed = json.loads(raw) if isinstance(raw, str) else raw

        # Ensure required structure.
        if not isinstance(parsed, dict) or 'answers' not in parsed:
            return JsonResponse({'answers': [{'title': 'Single outcome', 'likelihood': 'Medium', 'impact': '', 'changes': [], 'reasoning': str(parsed)}]})

        return JsonResponse(parsed)
    except Exception:
        # If model returned non-JSON text, wrap it.
        return JsonResponse({'answers': [{'title': 'Single outcome', 'likelihood': 'Medium', 'impact': '', 'changes': [], 'reasoning': 'Simulation failed to produce JSON.'}]})



# PROJECTS PAGE

def projects_page(request):

    if not request.user.is_authenticated:
        return redirect('login')

    projects = Project.objects.filter(
        user=request.user
    )

    return render(
        request,
        'projects.html',
        {
            'projects': projects
        }
    )


# ZIP UPLOAD + ANALYSIS

def upload_zip(request):


    if request.method == "POST":


        project_name = request.POST.get(
            'project_name'
        )

        zip_file = request.FILES.get(
            'zip_file'
        )

        project = Project.objects.create(
            user=request.user,
            name=project_name,
            zip_file=zip_file
        )

        total_files = 0
        total_lines = 0

        total_classes = 0
        total_functions = 0

        large_files = 0
        test_files = 0

        detected_tech = set()

        project_summary = ""

        # --- Performance optimization knobs ---
        MAX_MEMBER_FILE_BYTES = 1_500_000
        MAX_DECODE_BYTES = 256_000
        MAX_SUMMARY_FILES = 25
        MAX_SUMMARY_CHARS = 10_000
        MAX_SUMMARY_LINES_PER_FILE = 400

        CODE_EXTENSIONS = {
            '.py', '.js', '.ts', '.java', '.jsx', '.tsx', '.html', '.css', '.json', '.md', '.yml', '.yaml', '.txt', '.xml'
        }

        BINARY_EXTENSIONS = {
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.pdf', '.zip', '.tar', '.gz', '.7z', '.rar',
            '.exe', '.dll', '.so', '.dylib', '.bin', '.class', '.jar', '.war', '.ear', '.mp3', '.mp4', '.mov', '.avi', '.mkv'
        }

        summary_files_added = 0

        def _is_probably_binary(member_name: str) -> bool:
            lower = member_name.lower()
            if any(lower.endswith(ext) for ext in BINARY_EXTENSIONS):
                return True
            if 'node_modules/' in lower or '.git/' in lower or lower.endswith('.lock'):
                return True
            return False

        def _allowed_for_metrics(member_name: str) -> bool:
            lower = member_name.lower()
            return any(lower.endswith(ext) for ext in CODE_EXTENSIONS)

        total_lines_cap_reached = False


        try:

            zip_path = project.zip_file.path


            with zipfile.ZipFile(
                zip_path,
                'r'
            ) as zip_ref:

                for file_name in zip_ref.namelist():

                    if file_name.endswith('/'):
                        continue

                    total_files += 1

                    # Technology Detection

                    if file_name.endswith('.py'):
                        detected_tech.add("Python")

                    if file_name.endswith('.html'):
                        detected_tech.add("HTML")

                    if file_name.endswith('.css'):
                        detected_tech.add("CSS")

                    if file_name.endswith('.js'):
                        detected_tech.add("JavaScript")

                    if file_name.endswith('.java'):
                        detected_tech.add("Java")

                    if file_name.endswith('.jsx'):
                        detected_tech.add("React")

                    if file_name.endswith('.ts'):
                        detected_tech.add("TypeScript")

                    if "manage.py" in file_name:
                        detected_tech.add("Django")

                    if "app.py" in file_name:
                        detected_tech.add("Flask")

                    if "package.json" in file_name:
                        detected_tech.add("NodeJS")

                    try:

                        with zip_ref.open(
                            file_name
                        ) as f:

                            # Skip likely binaries (heuristics)
                            if _is_probably_binary(file_name):
                                continue

                            # Decode only a prefix to keep this fast
                            raw = f.read(MAX_DECODE_BYTES)
                            content = raw.decode(
                                'utf-8',
                                errors='ignore'
                            )


                            # CODE SUMMARY FOR AI

                            project_summary += (
                                f"\nFILE: {file_name}\n"
                            )

                            project_summary += (
                                content[:500]
                            )

                            project_summary += "\n"

                            lines = content.splitlines()

                            total_lines += len(
                                lines
                            )

                            # Large File Detection

                            if len(lines) > 300:

                                large_files += 1

                            # Function & Class Detection

                            for line in lines:

                                stripped = line.strip()

                                if stripped.startswith(
                                    "class "
                                ):

                                    total_classes += 1

                                if stripped.startswith(
                                    "def "
                                ):

                                    total_functions += 1

                            # Test File Detection

                            if "test" in file_name.lower():

                                test_files += 1

                    except Exception:

                        pass

            # Compute scores using shared helper
            health_score, risks_found, recommendations = compute_metrics(
                total_files,
                total_lines,
                large_files,
                test_files,
                project_summary,
                detected_tech,
                total_classes,
                total_functions,
            )

            tech_string = ", ".join(
                sorted(detected_tech)
            )

            # LANGGRAPH WORKFLOW

            workflow = build_workflow()

            result = workflow.invoke({

                "total_files": total_files,

                "lines_of_code": total_lines,

                "health_score": health_score,

                "technologies": tech_string,

                "total_classes": total_classes,

                "total_functions": total_functions,

                "large_files": large_files,

                "test_files": test_files,

                "project_summary": project_summary,
                
                "full_report": "",

                "architecture_report": "",

                "technical_debt_report": "",

                "risk_report": "",

                "recommendation_report": ""

            })

            # SAVE TO DATABASE

            logging.getLogger(__name__).info(
                "Creating Analysis for project=%s: files=%d lines=%d health=%d",
                project.name,
                total_files,
                total_lines,
                health_score,
            )

            Analysis.objects.create(

                project=project,

                health_score=health_score,

                risks_found=risks_found,

                recommendations=recommendations,

                total_files=total_files,

                lines_of_code=total_lines,

                total_classes=total_classes,

                total_functions=total_functions,

                large_files=large_files,

                test_files=test_files,

                complexity=0,

                maintainability=0,

                technologies=tech_string,

                architecture_report=result[
                    "architecture_report"
                ],

                technical_debt_report=result[
                    "technical_debt_report"
                ],

                risk_report=result[
                    "risk_report"
                ],

                recommendation_report=result[
                    "recommendation_report"
                ]

            )

            # SAVE TO CHROMADB

            save_project_memory(

                project.name,

                result[
                    "architecture_report"
                ],

                result[
                    "technical_debt_report"
                ],

                result[
                    "risk_report"
                ],

                result[
                    "recommendation_report"
                ]

            )

        except Exception as e:

            print(
                "ZIP ANALYSIS ERROR:",
                e
            )

        return redirect(
            'analysis_loading'
        )

    return redirect(
        'upload'
    )

def timeline_page(request, project_id):

    if not request.user.is_authenticated:
        return redirect('login')

    projects = Project.objects.filter(
        user=request.user
    )

    project = Project.objects.filter(
        id=project_id,
        user=request.user
    ).first()

    return render(
        request,
        'timeline.html',
        {
            'projects': projects,
            'project': project
        }
    )

def risks_page(request, project_id):

    if not request.user.is_authenticated:
        return redirect('login')

    projects = Project.objects.filter(
        user=request.user
    )

    project = Project.objects.filter(
        id=project_id,
        user=request.user
    ).first()

    analysis = None

    if project:

        analysis = Analysis.objects.filter(
            project=project
        ).first()

    return render(
        request,
        'risks.html',
        {
            'projects': projects,
            'project': project,
            'analysis': analysis
        }
    )


def recommendations_page(request, project_id):

    if not request.user.is_authenticated:
        return redirect('login')

    projects = Project.objects.filter(
        user=request.user
    )

    project = Project.objects.filter(
        id=project_id,
        user=request.user
    ).first()

    analysis = None

    if project:

        analysis = Analysis.objects.filter(
            project=project
        ).first()

    return render(
        request,
        'recommendations.html',
        {
            'projects': projects,
            'project': project,
            'analysis': analysis
        }
    )
