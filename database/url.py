from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='HSDatabase'),
    path('download/<int:fileid>/', views.download, name='download'),
    path('back/', views.back, name='back'),
    path('browse/', views.browse, name='browse'),
    path('search/', views.search, name='search'),
    path('search/search/', views.look, name='Search'),
    path('blast/', views.blast, name='Blast'),
    path('kegg/', views.heatmap, name='KEGG'),
    path('kegg/show/', views.kegg, name='KEGG'),
    path('kegg/download/<path:filename>/', views.heatmap_download, name='Heatmap Download'),
    path('faq/', views.faq, name='Tutorial'),
    path('hsd/<int:species_id>/<int:page>/', views.hsd, name='hsd'),
    path('hsd_download/<path:filename>/<int:hsd_id>/', views.hsd_download, name='HSD Download'),
    path('hsd_detail/<int:hsd_id>/', views.hsd_detail, name='HSD Detail'),
    path('hsd_detail/alignments/', views.cluster_omega, name='HSD_Alignment'),
]