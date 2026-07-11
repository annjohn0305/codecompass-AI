from django.urls import path
from . import views

urlpatterns = [

    path('', views.home, name='home'),

    path('signup/', views.signup, name='signup'),

    path('login/', views.login_page, name='login'),

    path('logout/', views.logout_page, name='logout'),

    path('dashboard/', views.dashboard, name='dashboard'),

    path('demo/', views.demo, name='demo'),

    path('upload/', views.upload_page, name='upload'),

    path('analysis/', views.analysis_page, name='analysis'),

    path('report/', views.report_page, name='report'),

    path(
        'report/<int:project_id>/',
        views.report_page,
        name='project_report'
    ),

    path(
        'settings/',
        views.settings_page,
        name='settings'
    ),

    path(
        'save-project/',
        views.save_project,
        name='save_project'
    ),

    path(
        'projects/',
        views.projects_page,
        name='projects'
    ),

    path(
        'upload-zip/',
        views.upload_zip,
        name='upload_zip'
    ),

    path(
        'analysis-loading/',
        views.analysis_loading,
        name='analysis_loading'
    ),

    path(
        'download-pdf/',
        views.download_pdf,
        name='download_pdf'
    ),

    path(
        'what-if/<int:project_id>/',
        views.what_if_page,
        name='what_if_page'
    ),

    path(
        'what-if-api/<int:project_id>/',
        views.what_if_simulator,
        name='what_if_simulator'
    ),

    # Allow requests without a trailing slash (helps frontend fetch URLs)
    path(
        'what-if-api/<int:project_id>',
        views.what_if_simulator,
        name='what_if_simulator_no_slash'
    ),

    path(
        'chat-api/<int:project_id>/',
        views.project_chat,
        name='project_chat'
    ),

path(
    'timeline/<int:project_id>/',
    views.timeline_page,
    name='timeline'
),

path(
    'risks/<int:project_id>/',
    views.risks_page,
    name='risks'
),

path(
    'recommendations/<int:project_id>/',
    views.recommendations_page,
    name='recommendations'
),
]

